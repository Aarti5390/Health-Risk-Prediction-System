import sqlite3

conn = sqlite3.connect('users.db')
c = conn.cursor()

c.execute("SELECT * FROM predict")
rows = c.fetchall()

print("📊 Contents of 'predict' table:")
for row in rows:
    print(row)

conn.close()
