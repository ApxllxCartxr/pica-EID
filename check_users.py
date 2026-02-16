
from app.database import SessionLocal
from app.models.admin import AdminAccount

def check_users():
    db = SessionLocal()
    try:
        admins = db.query(AdminAccount).all()
        print(f"Found {len(admins)} admins:")
        for admin in admins:
            print(f"- ID: {admin.id}, Username: {admin.username}, Access Level: {admin.access_level}")
    except Exception as e:
        print(f"Error querying database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_users()
