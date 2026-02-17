import psycopg2
import sys

try:
    conn = psycopg2.connect(
        host="localhost",
        port=5434,
        database="prismid_db",
        user="prismid",
        password="prismid_secret"
    )
    cur = conn.cursor()
    
    # Check if table exists
    cur.execute("SELECT to_regclass('public.alembic_version');")
    if cur.fetchone()[0] is None:
        print("Table alembic_version does not exist. Creating and inserting.")
        cur.execute("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL PRIMARY KEY);")
        cur.execute("INSERT INTO alembic_version (version_num) VALUES ('0001_initial_schema');")
    else:
        print("Updating alembic_version...")
        cur.execute("DELETE FROM alembic_version;")
        cur.execute("INSERT INTO alembic_version (version_num) VALUES ('0001_initial_schema');")
        
    conn.commit()
    print("SUCCESS: Updated alembic_version to '0001_initial_schema'")
    conn.close()
except Exception as e:
    print(f"FAILED: {e}")
    sys.exit(1)
