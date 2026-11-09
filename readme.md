# User Registration System

A Flask-based registration application with server-side validation, an administrator login, user records, profile details, and CSV export. This is an academic project; review the security notes before using real personal information.

## Features

- Registration form with client-side and server-side validation
- SQLite by default, configurable through `DATABASE_URL`
- Password hashing with Werkzeug
- Administrator login and protected dashboard
- User detail view, search/pagination, and CSV export
- Profile photo support
- Environment-based configuration; no default administrator password is created

## Technology

- Python, Flask, Flask-SQLAlchemy, Flask-Login
- HTML, CSS, JavaScript
- SQLite by default (other SQLAlchemy-compatible databases can be configured)

## Project layout

```text
Registration_Form/
├── app.py
├── create_admin.py
├── requirements.txt
├── .env.example
├── templates/
│   ├── index.html
│   ├── admin_login.html
│   ├── admin_dashboard.html
│   └── user_detail.html
└── static/
    ├── script.js
    └── style.css
```

The original root-level HTML/CSS/JS files are retained as reference copies; Flask serves the copies under `templates/` and `static/`.

## Setup (Windows PowerShell)

1. Clone the repository and open its folder.
2. Create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

4. Create your local environment file:

   ```powershell
   Copy-Item .env.example .env
   ```

5. Generate a unique Flask secret key:

   ```powershell
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

   Put the generated value in `.env` as `SECRET_KEY=...`. Keep `.env` private and never commit it.

6. Create the database tables and your own administrator account:

   ```powershell
   python create_admin.py
   ```

   The script asks for the username, email, and password interactively. Password input is hidden; choose a unique password of at least 12 characters. No starter credentials are supplied.

7. Start the application:

   ```powershell
   python app.py
   ```

8. Open `http://127.0.0.1:5000`. Administrator login is at `/admin/login`.

## Environment variables

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Required, unique random Flask signing key |
| `DATABASE_URL` | Optional database URL; defaults to local SQLite |
| `CSC_API_KEY` | Optional key for the Country/State/City lookup integration |
| `FLASK_DEBUG` | Defaults to `false`; enable only for local development |
| `HOST` / `PORT` | Defaults to `127.0.0.1` / `5000` |
| `COOKIE_SECURE` | Set to `true` when served over HTTPS |
| `LOG_LEVEL` | Defaults to `INFO` |

## Security notes

- Never commit `.env`, API keys, database credentials, or real user data.
- The app no longer creates a predictable default administrator account. Run `python create_admin.py` to create one.
- Use HTTPS and set `COOKIE_SECURE=true` when deploying.
- This project has not been independently security-tested. Before production use, add CSRF protection for state-changing forms, rate limiting for authentication and validation endpoints, robust authorization checks, and privacy controls for exported personal data.
- If an API key or password was ever committed, revoke/rotate it. Deleting the file from the latest commit does not remove it from Git history.

## Database

The default database is SQLite. Back up the database file before upgrades or schema changes. Set `DATABASE_URL` in `.env` to use another SQLAlchemy-supported database; install its corresponding driver.

## Academic use

This repository demonstrates a small full-stack registration workflow using Flask, SQLAlchemy, authentication, validation, and basic data export. Features and limitations should be described accurately during project demonstrations.
