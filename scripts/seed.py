"""
Seed script — creates initial Superadmin account and sample divisions.
Idempotent: safe to run multiple times.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine, Base
from app.models.admin import AdminAccount, AccessLevel
from app.models.division import Division
from app.models.role import Role
from app.core.security import hash_password
from app.config import settings


def seed():
    # Create tables
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # --- Seed Superadmin ---
        existing_admin = db.query(AdminAccount).filter(
            AdminAccount.username == settings.SEED_ADMIN_USERNAME
        ).first()

        if not existing_admin:
            admin = AdminAccount(
                username=settings.SEED_ADMIN_USERNAME,
                password_hash=hash_password(settings.SEED_ADMIN_PASSWORD),
                email="admin@prismid.local",
                display_name="System Administrator",
                access_level=AccessLevel.SUPERADMIN,
            )
            db.add(admin)
            print(f"✓ Created Superadmin: {settings.SEED_ADMIN_USERNAME}")
        else:
            print(f"⏩ Superadmin '{settings.SEED_ADMIN_USERNAME}' already exists")

        # --- Seed Divisions ---
        default_divisions = [
            ("Engineering", "Software and hardware engineering"),
            ("Operations", "Business operations and logistics"),
            ("Human Resources", "HR and people management"),
            ("Marketing", "Marketing and communications"),
            ("Finance", "Finance and accounting"),
            ("Research", "Research and development"),
        ]

        for name, desc in default_divisions:
            if not db.query(Division).filter(Division.name == name).first():
                db.add(Division(name=name, description=desc))
                print(f"  ✓ Created division: {name}")

        # --- Seed Default Roles ---
        default_roles = [
            ("Software Engineer", "Develops and maintains software applications", 5),
            ("Data Analyst", "Analyzes data and generates insights", 4),
            ("Project Manager", "Manages projects and coordinates teams", 6),
            ("Designer", "Creates visual and UX designs", 4),
            ("DevOps Engineer", "Manages infrastructure and CI/CD", 6),
            ("Security Analyst", "Ensures system and data security", 7),
            ("Team Lead", "Leads and mentors team members", 7),
            ("Director", "Oversees division strategy and operations", 9),
        ]

        for name, desc, level in default_roles:
            if not db.query(Role).filter(Role.name == name).first():
                db.add(Role(name=name, description=desc, clearance_level=level))
                print(f"  ✓ Created role: {name} (clearance: {level})")

        db.commit()
        print("\n✅ Seed completed successfully!")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
