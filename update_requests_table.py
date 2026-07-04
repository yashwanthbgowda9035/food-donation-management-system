import sqlite3

conn = sqlite3.connect("food.db")
cursor = conn.cursor()

try:
    cursor.execute("""
    ALTER TABLE requests
    ADD COLUMN pickup_date TEXT
    """)
except:
    pass

try:
    cursor.execute("""
    ALTER TABLE requests
    ADD COLUMN pickup_time TEXT
    """)
except:
    pass

conn.commit()
conn.close()

print("Table Updated")