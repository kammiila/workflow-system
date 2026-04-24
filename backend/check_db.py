import sqlite3
import os

DB_NAME = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'database.db')

conn = sqlite3.connect(DB_NAME)
c = conn.cursor()

# Проверяем пользователей
c.execute('SELECT id, username, full_name FROM users')
users = c.fetchall()
print("=== USERS ===")
for user in users:
    print(f"ID: {user[0]}, Username: {user[1]}, Name: {user[2]}")

# Проверяем задачи
c.execute('SELECT id, title, status, assigned_to FROM tasks')
tasks = c.fetchall()
print("\n=== TASKS ===")
for task in tasks:
    print(f"ID: {task[0]}, Title: {task[1]}, Status: {task[2]}, Assigned to: {task[3]}")

conn.close()