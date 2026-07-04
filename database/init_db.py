import sqlite3

conn = sqlite3.connect("food.db")
cursor = conn.cursor()

# USERS TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT,
    phone TEXT,
    password TEXT,
    role TEXT
)
""")

# DONATIONS TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS donations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    donor_id INTEGER,
    food_name TEXT,
    quantity TEXT,
    category TEXT,
    prepared_time TEXT,
    expiry_time TEXT,
    address TEXT,
    image TEXT,
    status TEXT DEFAULT 'Available'
)
""")
try:
    cursor.execute("ALTER TABLE donations ADD COLUMN image TEXT")
except:
    pass
# REQUESTS TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    donation_id INTEGER,
    ngo_id INTEGER,
    status TEXT DEFAULT 'Pending',
    pickup_date TEXT,
    pickup_time TEXT
)
""")

# FEEDBACK TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ngo_id INTEGER,
    rating TEXT,
    message TEXT
)
""")

cursor.execute("SELECT * FROM users WHERE role='admin'")
admin = cursor.fetchone()

if not admin:
    cursor.execute("""
    INSERT INTO users(name,email,phone,password,role)
    VALUES(?,?,?,?,?)
    """, ("Admin", "admin@gmail.com", "0000000000", "admin123", "admin"))

cursor.execute("""
CREATE TABLE IF NOT EXISTS donations (
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

conn.commit()
conn.close()

print("Database created successfully")