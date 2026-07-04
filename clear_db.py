import sqlite3

conn = sqlite3.connect("food.db")
cursor = conn.cursor()

cursor.execute("DELETE FROM users")
cursor.execute("DELETE FROM donations")
cursor.execute("DELETE FROM requests")
cursor.execute("DELETE FROM feedback")

conn.commit()
conn.close()

print("Database cleared successfully")