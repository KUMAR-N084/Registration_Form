"""Create an administrator account without storing its password in source code."""
import getpass
import re

from werkzeug.security import generate_password_hash

from app import Admin, app, db


def main():
    with app.app_context():
        db.create_all()
        username = input("Admin username: ").strip()
        email = input("Admin email: ").strip().lower()

        if not re.fullmatch(r"[A-Za-z0-9_.-]{3,50}", username):
            raise SystemExit("Username must be 3-50 characters (letters, numbers, _, ., -).")
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            raise SystemExit("Enter a valid email address.")
        if Admin.query.filter_by(admin_username=username).first():
            raise SystemExit("That admin username already exists.")
        if Admin.query.filter_by(admin_email=email).first():
            raise SystemExit("That admin email already exists.")

        password = getpass.getpass("New admin password (minimum 12 characters): ")
        confirmation = getpass.getpass("Confirm password: ")
        if len(password) < 12:
            raise SystemExit("Use a password with at least 12 characters.")
        if password != confirmation:
            raise SystemExit("Passwords do not match.")

        admin = Admin(
            admin_username=username,
            admin_email=email,
            password_hash=generate_password_hash(password),
        )
        db.session.add(admin)
        db.session.commit()
        print(f"Administrator account '{username}' created successfully.")


if __name__ == "__main__":
    main()
