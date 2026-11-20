"""Initialize the administrator table without creating a default account."""
import os
import sqlite3
DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "certificates.db"))
conn = sqlite3.connect(DB_PATH)
conn.execute("CREATE TABLE IF NOT EXISTS admins (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL)")
conn.commit()
conn.close()
print("Administrator table is ready. Create an account with: python create_admin.py")
