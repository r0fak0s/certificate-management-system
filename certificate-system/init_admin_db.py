import sqlite3
import os
from werkzeug.security import generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "certificates.db")

conn = sqlite3.connect(DB_PATH)

conn.execute("""
CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
)
""")

# create default admin
default_username = "admin"
default_password = "admin123"

password_hash = generate_password_hash(default_password)

conn.execute(
    "INSERT OR IGNORE INTO admins (username, password_hash) VALUES (?, ?)",
    (default_username, password_hash)
)

conn.commit()
conn.close()

print("✅ Admin table ready")
