import psycopg2
import sys

passwords = [
    "prismid_secret", "admin", "postgres", "password", 
    "accord", "accord_secret", "accord_crm", "accord_crm_secret",
    "secret", "123456", "docker"
]

for p in passwords:
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5435,
            database="prismid_db",
            user="prismid",
            password=p
        )
        print(f"SUCCESS: Password is '{p}'")
        conn.close()
        sys.exit(0)
    except Exception as e:
        # print(f"Failed with {p}: {e}")
        pass

print("FAILED: Could not find password.")
sys.exit(1)
