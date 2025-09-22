import sqlite3

conn = sqlite3.connect('users.db')
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS predict (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    date TEXT NOT NULL,
    input_data TEXT NOT NULL,
    risks TEXT NOT NULL,
    highest_risk TEXT NOT NULL
)
''')

conn.commit()
conn.close()
print("✅ predict table created.")