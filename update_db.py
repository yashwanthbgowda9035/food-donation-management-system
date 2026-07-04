import sqlite3

conn = sqlite3.connect("food.db")
cursor = conn.cursor()

try:
    cursor.execute("""
    ALTER TABLE donations
    ADD COLUMN image TEXT
    """)
    print("Image column added.")
except:
    print("Column already exists.")

conn.commit()
conn.close()