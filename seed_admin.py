"""Run once to create the first superadmin account from env vars.
Usage: python seed_admin.py
"""
from app.core.config import settings
from app.core.security import hash_password
from app.db.base_models import Base
from app.db.session import SessionLocal, engine
from app.models.admin import AdminUser


def main() -> None:
    Base.metadata.create_all(bind=engine)  # safe no-op if tables already exist via Alembic

    db = SessionLocal()
    try:
        existing = db.query(AdminUser).filter(
            AdminUser.email == settings.first_superadmin_email
        ).first()
        if existing:
            print(f"Superadmin {settings.first_superadmin_email} already exists — skipping.")
            return

        admin = AdminUser(
            email=settings.first_superadmin_email,
            hashed_password=hash_password(settings.first_superadmin_password),
            full_name="Super Admin",
            is_superadmin=True,
        )
        db.add(admin)
        db.commit()
        print(f"Created superadmin: {settings.first_superadmin_email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
