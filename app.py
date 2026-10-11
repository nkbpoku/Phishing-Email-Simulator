import secrets
import sqlite3
from pathlib import Path

from flask import (
    Flask,
    abort,
    redirect,
    render_template,
    request,
    url_for,
)

app = Flask(__name__)

DATABASE = Path(__file__).parent / "simulator.db"


def connect_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def initialise_database():
    with connect_db() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS simulations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                subject TEXT NOT NULL,
                message TEXT NOT NULL,
                token TEXT NOT NULL UNIQUE,
                visits INTEGER NOT NULL DEFAULT 0,
                first_visit TEXT
            )
        """)


@app.route("/", methods=["GET", "POST"])
def home():
    error = None

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        subject = request.form.get("subject", "").strip()
        message = request.form.get("message", "").strip()

        if not all([name, email, subject, message]):
            error = "Please complete every field."
        elif len(name) > 100 or len(email) > 254:
            error = "The name or email address is too long."
        elif email.count("@") != 1 or any(
            character.isspace() for character in email
        ):
            error = "Enter a valid email address."
        elif len(subject) > 200 or len(message) > 5000:
            error = "Use a subject under 201 characters and a message under 5001."
        else:
            token = secrets.token_urlsafe(24)

            with connect_db() as connection:
                cursor = connection.execute("""
                    INSERT INTO simulations
                        (name, email, subject, message, token)
                    VALUES (?, ?, ?, ?, ?)
                """, (name, email, subject, message, token))

                simulation_id = cursor.lastrowid

            return redirect(
                url_for("preview", simulation_id=simulation_id)
            )

    with connect_db() as connection:
        simulations = connection.execute("""
            SELECT * FROM simulations ORDER BY id DESC
        """).fetchall()

    visited = sum(row["visits"] > 0 for row in simulations)

    return render_template(
        "index.html",
        simulations=simulations,
        visited=visited,
        error=error,
    )


@app.route("/preview/<int:simulation_id>")
def preview(simulation_id):
    with connect_db() as connection:
        simulation = connection.execute("""
            SELECT * FROM simulations WHERE id = ?
        """, (simulation_id,)).fetchone()

    if simulation is None:
        abort(404)

    # Fixed localhost address for this local demonstration.
    tracking_link = (
        "http://127.0.0.1:5001"
        + url_for("track", token=simulation["token"])
    )

    return render_template(
        "email.html",
        simulation=simulation,
        tracking_link=tracking_link,
    )


@app.route("/t/<token>")
def track(token):
    with connect_db() as connection:
        cursor = connection.execute("""
            UPDATE simulations
            SET visits = visits + 1,
                first_visit = COALESCE(
                    first_visit,
                    strftime('%Y-%m-%d %H:%M:%S', 'now')
                )
            WHERE token = ?
        """, (token,))

        if cursor.rowcount == 0:
            abort(404)

    return render_template("training.html")


@app.after_request
def protect_response(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


initialise_database()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001)