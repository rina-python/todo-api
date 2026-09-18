import sqlite3

conn = sqlite3.connect('todo.db')
cur = conn.cursor()

print("=== USERS ===")
cur.execute('SELECT id, email FROM users')
for row in cur.fetchall():
    print(row)

print("\n=== TASKS ===")
cur.execute('SELECT id, title, owner_id FROM tasks')
for row in cur.fetchall():
    print(row)

conn.close()