import sqlite3
import bcrypt
import sys

code = sys.argv[1]
password = sys.argv[2]

hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

conn = sqlite3.connect("downloads.db")
cur = conn.cursor()
cur.execute("""
    CREATE TABLE IF NOT EXISTS university_credentials (
        university_code TEXT PRIMARY KEY,
        password_hash TEXT NOT NULL
    )
""")
cur.execute("""
    INSERT INTO university_credentials (university_code, password_hash)
    VALUES (?, ?)
    ON CONFLICT(university_code) DO UPDATE SET password_hash = excluded.password_hash
""", (code, hashed))
conn.commit()
print(f"Saved credentials for {code}")
conn.close()