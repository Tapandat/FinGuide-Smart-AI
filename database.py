
import sqlite3

conn = sqlite3.connect("finance.db")

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT,
    amount REAL,
    note TEXT
)
""")

conn.commit()
conn.close()

print("Database Created Successfully")
