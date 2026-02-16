
from app.database import SessionLocal
from app.models.admin import AdminAccount
from app.core.security import hash_password

def reset_password():
    db = SessionLocal()
    try:
        admin = db.query(AdminAccount).filter(AdminAccount.username == "admin").first()
        if admin:
            new_password = "Prismid@2026"
            admin.password_hash = hash_password(new_password)
            db.commit()
            print(f"Password for 'admin' reset to '{new_password}'")
        else:
            print("User 'admin' not found")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    reset_password()
