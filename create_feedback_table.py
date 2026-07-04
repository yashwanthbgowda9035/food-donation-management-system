import sqlite3

conn = sqlite3.connect("food.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS feedback(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    donation_id INTEGER,
    ngo_id INTEGER,
    rating INTEGER,
    feedback TEXT
)
""")

conn.commit()
conn.close()

print("Feedback table created")