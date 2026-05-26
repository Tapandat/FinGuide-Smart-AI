import sqlite3

conn = sqlite3.connect("finance.db")
cursor = conn.cursor()

# Users table (email unique for Google OAuth)
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    email TEXT UNIQUE,
    password BLOB
)
""")

# Expenses table
cursor.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    category TEXT,
    amount REAL,
    note TEXT
)
""")

# Income table
cursor.execute("""
CREATE TABLE IF NOT EXISTS income (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    source TEXT,
    amount REAL
)
""")

conn.commit()
conn.close()

print("Database Created Successfully")
