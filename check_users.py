import sqlite3

conn = sqlite3.connect("food.db")
cursor = conn.cursor()

cursor.execute("SELECT id, name, email, password, role FROM users")

users = cursor.fetchall()

for user in users:
    print(user)

conn.close()