import sqlite3

conn = sqlite3.connect("food.db")
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(feedback)")
columns = cursor.fetchall()

print("FEEDBACK TABLE STRUCTURE:")
for col in columns:
    print(col)

conn.close()