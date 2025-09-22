import sqlite3

conn = sqlite3.connect('users.db')
c = conn.cursor()

c.execute("SELECT id, username, password FROM users")
rows = c.fetchall()

print("📋 Registered Users:")
for row in rows:
    print(f"ID: {row[0]}, Username: {row[1]}, Hashed Password: {row[2]}")

conn.close()