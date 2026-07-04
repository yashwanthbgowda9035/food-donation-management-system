import sqlite3

conn = sqlite3.connect("food.db")
cursor = conn.cursor()

# recreate feedback table correctly
cursor.execute("DROP TABLE IF EXISTS feedback")

cursor.execute("""
CREATE TABLE feedback(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ngo_id INTEGER,
    rating INTEGER,
    message TEXT
)
""")

conn.commit()
conn.close()

print("Feedback table fixed successfully")