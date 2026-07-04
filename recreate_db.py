import sqlite3

conn = sqlite3.connect("food.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    password TEXT NOT NULL,
    role TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS donations(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    donor_id INTEGER,
    food_name TEXT,
    quantity TEXT,
    category TEXT,
    prepared_time TEXT,
    expiry_time TEXT,
    address TEXT,
    status TEXT DEFAULT 'Available'
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS requests(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    donation_id INTEGER,
    ngo_id INTEGER,
    status TEXT DEFAULT 'Requested'
)
""")

conn.commit()
conn.close()

print("All tables created successfully!")