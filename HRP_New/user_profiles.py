import sqlite3

conn = sqlite3.connect('users.db')
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS user_profiles (
    username TEXT PRIMARY KEY,
    full_name TEXT,
    age INTEGER,
    gender TEXT,
    email TEXT,
    phone TEXT,
    address TEXT,
    city TEXT,
    state TEXT,
    country TEXT,
    photo TEXT
)
''')

conn.commit()
conn.close()
print("✅ user table created.")