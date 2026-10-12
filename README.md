# Phishing Email Simulator

A security awareness project built with Python, Flask, HTML, and SQLite.

## Current features
- Create personalised simulated email previews.
- Generate individual training links.
- Record link visits and the first visit time.
- Display results in a dashboard.
- Show an awareness page explaining phishing warning signs.

## Run locally

Requires Python 3.10 or later.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5001 in your browser.

## Current limitations
- Emails are previewed locally; they are not sent.
- Tracking links work only on the computer running the app.
- The dashboard does not yet have administrator authentication.
- Recorded visits may include automated scanners or forwarded links.

The local database contains participant information and is excluded
from version control.

## Planned improvements
- Administrator login and protected forms.
- Email delivery and campaign management.
- HTTPS deployment.
- Automated tests.

Use demo participants or participants approved for a security awareness exercise.