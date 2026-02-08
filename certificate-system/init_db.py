import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "certificates.db")

conn = sqlite3.connect(DB_PATH)

conn.execute("""
CREATE TABLE IF NOT EXISTS certificates (
    id TEXT PRIMARY KEY,
    name TEXT,
    event TEXT,
    dob TEXT,
    gender TEXT,
    phone TEXT,
    nationality TEXT,
    email Adress TEXT,
    address TEXT,
    state TEXT,
    nin TEXT
)
""")

conn.commit()
conn.close()

print("Database initialized successfully")
