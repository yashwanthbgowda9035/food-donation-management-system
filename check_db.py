import sqlite3

conn = sqlite3.connect("food.db")
cursor = conn.cursor()

tables = ["users", "donations", "requests", "feedback"]

for t in tables:
    try:
        cursor.execute(f"SELECT * FROM {t}")
        print(f"\n{t} → OK")
        print(cursor.fetchall())
    except Exception as e:
        print(f"\n{t} → ERROR: {e}")

conn.close()