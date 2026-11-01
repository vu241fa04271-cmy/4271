"""Create a demo account with sample trusted contacts.

Run from the backend folder:
    python seed.py

Idempotent: re-running updates the demo user's contacts rather than duplicating.
"""
from werkzeug.security import generate_password_hash

from app import create_app
from extensions import db
from models import TrustedContact, User

DEMO_EMAIL = "demo@womensafety.org"
DEMO_PASSWORD = "demo1234"


def main():
    app = create_app()
    with app.app_context():
        user = User.query.filter_by(email=DEMO_EMAIL).first()
        if not user:
            user = User(
                name="Demo User",
                email=DEMO_EMAIL,
                password_hash=generate_password_hash(DEMO_PASSWORD),
            )
            db.session.add(user)
            db.session.commit()
            print(f"Created demo user: {DEMO_EMAIL}")
        else:
            print(f"Demo user already exists: {DEMO_EMAIL}")

        sample_contacts = [
            {"name": "Mom", "phone": "+91 98XXXXXX01", "email": "mom@example.com"},
            {"name": "Sister", "phone": "+91 98XXXXXX02", "email": "sister@example.com"},
            {"name": "Best Friend", "phone": "+91 98XXXXXX03", "email": "friend@example.com"},
        ]

        existing = {c.name for c in user.contacts}
        added = 0
        for c in sample_contacts:
            if c["name"] not in existing:
                db.session.add(TrustedContact(user_id=user.id, **c))
                added += 1
        db.session.commit()
        print(f"Trusted contacts on demo account: {len(user.contacts)} ({added} added).")
        print("Login with:")
        print(f"   email:    {DEMO_EMAIL}")
        print(f"   password: {DEMO_PASSWORD}")


if __name__ == "__main__":
    main()
