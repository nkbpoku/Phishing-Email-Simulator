import os
import re
import sqlite3
from datetime import timedelta
from pathlib import Path

import click
from dotenv import load_dotenv
from flask import redirect, render_template, request, session, url_for
from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import check_password_hash, generate_password_hash


class Admin(UserMixin):
    def __init__(self, row):
        self.id = str(row["id"])
        self.username = row["username"]


def initialise_auth(app, connect_db):
    load_dotenv(Path(__file__).parent / ".env")

    secret_key = os.environ.get("SECRET_KEY", "")
    if len(secret_key) < 32:
        raise RuntimeError(
            "Set SECRET_KEY in .env to your generated private key."
        )

    app.config.update(
        SECRET_KEY=secret_key,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        PERMANENT_SESSION_LIFETIME=timedelta(hours=1),
        SESSION_REFRESH_EACH_REQUEST=False,
        MAX_CONTENT_LENGTH=100_000,
    )

    # Secure cookies will be enabled when we deploy with HTTPS.
    CSRFProtect(app)

    login_manager = LoginManager()
    login_manager.login_view = "login"
    login_manager.login_message = None
    login_manager.init_app(app)

    with connect_db() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            )
        """)

    # Perform a password check even when the username does not exist.
    dummy_hash = generate_password_hash(os.urandom(32).hex())

    @login_manager.user_loader
    def load_admin(admin_id):
        with connect_db() as connection:
            row = connection.execute(
                "SELECT id, username FROM admins WHERE id = ?",
                (admin_id,),
            ).fetchone()

        return Admin(row) if row else None

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("home"))

        error = None

        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")

            with connect_db() as connection:
                row = connection.execute(
                    "SELECT * FROM admins WHERE username = ?",
                    (username,),
                ).fetchone()

            stored_hash = row["password_hash"] if row else dummy_hash
            valid_password = check_password_hash(stored_hash, password)

            if row and valid_password:
                session.clear()
                login_user(Admin(row), remember=False)
                session.permanent = True
                return redirect(url_for("home"))

            error = "Incorrect username or password."

        return render_template("login.html", error=error)

    @app.route("/logout", methods=["POST"])
    @login_required
    def logout():
        logout_user()
        session.clear()
        return redirect(url_for("login"))

    @app.cli.command("create-admin")
    def create_admin():
        """Create an administrator through the local terminal."""
        username = click.prompt("Admin username").strip()

        if not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", username):
            raise click.ClickException(
                "Use 1–64 letters, numbers, dots, underscores, or hyphens."
            )

        password = click.prompt(
            "Admin password",
            hide_input=True,
            confirmation_prompt=True,
        )

        if len(password) < 12:
            raise click.ClickException(
                "Choose a password with at least 12 characters."
            )

        try:
            with connect_db() as connection:
                connection.execute("""
                    INSERT INTO admins (username, password_hash)
                    VALUES (?, ?)
                """, (username, generate_password_hash(password)))
        except sqlite3.IntegrityError:
            raise click.ClickException("That username already exists.")

        click.echo("Administrator created successfully.")