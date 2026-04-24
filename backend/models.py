from flask_login import UserMixin
import sqlite3
from datetime import datetime, timedelta
import os

DB_NAME = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'database.db')

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Таблица пользователей
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            full_name TEXT,
            avatar_color TEXT DEFAULT '#06B6D4'
        )
    ''')
    
    # Таблица задач
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'pending',
            priority TEXT DEFAULT 'medium',
            assigned_to INTEGER,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            due_date DATE,
            completed_at TIMESTAMP
        )
    ''')
    
    # Таблица активности
    c.execute('''
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            user_name TEXT,
            action TEXT,
            task_title TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Добавляем тестовые данные
    c.execute('SELECT COUNT(*) FROM users')
    if c.fetchone()[0] == 0:
        from werkzeug.security import generate_password_hash
        
        # Админ
        c.execute('INSERT INTO users (username, email, password, role, full_name) VALUES (?, ?, ?, ?, ?)',
                  ('admin', 'admin@procevia.com', generate_password_hash('admin123'), 'admin', 'Admin User'))
        
        # Пользователи
        users = [
            ('sarah', 'sarah@procevia.com', generate_password_hash('password123'), 'user', 'Sarah Johnson'),
            ('michael', 'michael@procevia.com', generate_password_hash('password123'), 'user', 'Michael Chen'),
            ('emma', 'emma@procevia.com', generate_password_hash('password123'), 'user', 'Emma Williams'),
            ('james', 'james@procevia.com', generate_password_hash('password123'), 'user', 'James Brown'),
            ('lisa', 'lisa@procevia.com', generate_password_hash('password123'), 'user', 'Lisa Anderson')
        ]
        
        for user in users:
            c.execute('INSERT INTO users (username, email, password, role, full_name) VALUES (?, ?, ?, ?, ?)', user)
        
        # Получаем ID пользователей
        c.execute('SELECT id, full_name FROM users')
        users_data = c.fetchall()
        
        # Задачи
        today = datetime.now().strftime('%Y-%m-%d')
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        next_week = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        last_week = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
        
        tasks = [
            ('Design system review', 'Review and approve design system', 'completed', 'high', users_data[0][0], users_data[0][0], last_week),
            ('API integration', 'Integrate REST API', 'in_progress', 'high', users_data[1][0], users_data[0][0], tomorrow),
            ('Database migration', 'Migrate to PostgreSQL', 'pending', 'medium', users_data[2][0], users_data[1][0], next_week),
            ('Bug fix #234', 'Fix authentication bug', 'in_review', 'high', users_data[3][0], users_data[2][0], last_week),
            ('Update documentation', 'Update API docs', 'pending', 'low', users_data[4][0], users_data[0][0], next_week),
            ('Performance optimization', 'Optimize queries', 'in_progress', 'medium', users_data[1][0], users_data[3][0], next_week),
            ('Security audit', 'Conduct security audit', 'pending', 'high', users_data[2][0], users_data[0][0], next_week),
        ]
        
        for task in tasks:
            c.execute('INSERT INTO tasks (title, description, status, priority, assigned_to, created_by, due_date) VALUES (?, ?, ?, ?, ?, ?, ?)', task)
        
        # Активности
        activities = [
            (users_data[0][0], 'Sarah Johnson', 'completed task', 'Design system review'),
            (users_data[1][0], 'Michael Chen', 'created task', 'API integration'),
            (users_data[2][0], 'Emma Williams', 'moved task to', 'Review stage'),
            (users_data[3][0], 'James Brown', 'commented on', 'Database migration'),
            (users_data[4][0], 'Lisa Anderson', 'assigned', 'Bug fix #234'),
        ]
        
        for activity in activities:
            c.execute('INSERT INTO activities (user_id, user_name, action, task_title) VALUES (?, ?, ?, ?)', activity)
    
    conn.commit()
    conn.close()
    print("Database initialized!")

def get_user_by_username(username):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT id, username, email, password, role, full_name, avatar_color FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    conn.close()
    if user:
        return User(user[0], user[1], user[2], user[3], user[4], user[5], user[6])
    return None

def get_user_by_id(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT id, username, email, password, role, full_name, avatar_color FROM users WHERE id = ?', (user_id,))
    user = c.fetchone()
    conn.close()
    if user:
        return User(user[0], user[1], user[2], user[3], user[4], user[5], user[6])
    return None

class User(UserMixin):
    def __init__(self, id, username, email, password, role, full_name=None, avatar_color='#06B6D4'):
        self.id = id
        self.username = username
        self.email = email
        self.password = password
        self.role = role
        self.full_name = full_name or username
        self.avatar_color = avatar_color