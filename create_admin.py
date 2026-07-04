import sqlite3

conn = sqlite3.connect("food.db")
cursor = conn.cursor()

cursor.execute("""
INSERT INTO users(name,email,phone,password,role)
VALUES(?,?,?,?,?)
""", ("Admin", "admin@gmail.com", "9999999999", "admin123", "admin"))

conn.commit()
conn.close()

print("Admin created")