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
            email TEXT UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            full_name TEXT,
            avatar_color TEXT DEFAULT '#06B6D4',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Таблица ролей
    c.execute('''
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            color TEXT,
            icon_name TEXT,
            user_count INTEGER DEFAULT 0
        )
    ''')
    
    # Таблица разрешений
    c.execute('''
        CREATE TABLE IF NOT EXISTS permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_id INTEGER,
            permission_name TEXT,
            FOREIGN KEY (role_id) REFERENCES roles (id)
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
    
    # Таблица workflow статусов
    c.execute('''
        CREATE TABLE IF NOT EXISTS workflow_statuses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            color TEXT,
            display_order INTEGER DEFAULT 0
        )
    ''')
    
    # Таблица настроек пользователя
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            email_notifications INTEGER DEFAULT 1,
            push_notifications INTEGER DEFAULT 1,
            task_reminders INTEGER DEFAULT 1,
            weekly_reports INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Таблица уведомлений
    c.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT,
            message TEXT,
            type TEXT,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Добавляем дефолтные статусы workflow
    c.execute('SELECT COUNT(*) FROM workflow_statuses')
    if c.fetchone()[0] == 0:
        default_statuses = [
            ('To Do', '#EF4444', 1),
            ('In Progress', '#F59E0B', 2),
            ('In Review', '#8B5CF6', 3),
            ('Done', '#22C55E', 4)
        ]
        c.executemany('INSERT INTO workflow_statuses (name, color, display_order) VALUES (?, ?, ?)', default_statuses)
    
    # Добавляем роли
    c.execute('SELECT COUNT(*) FROM roles')
    if c.fetchone()[0] == 0:
        roles_data = [
            ('admin', 'Full system access and management', '#EF4444', 'shield', 0),
            ('manager', 'Team and project management', '#06B6D4', 'users', 0),
            ('user', 'Task execution and updates', '#22C55E', 'users', 0),
            ('observer', 'Read-only access', '#6B7280', 'eye', 0)
        ]
        
        for role in roles_data:
            c.execute('INSERT INTO roles (name, description, color, icon_name, user_count) VALUES (?, ?, ?, ?, ?)', role)
        
        # Добавляем разрешения для ролей
        c.execute('SELECT id, name FROM roles')
        roles = c.fetchall()
        
        permissions_data = {
            'admin': [
                'manage_all_workflows', 'create_delete_users', 'assign_roles', 'access_all_reports',
                'system_configuration', 'backup_restore', 'edit_roles', 'view_users', 'edit_users', 'delete_users'
            ],
            'manager': [
                'create_manage_workflows', 'assign_tasks', 'view_team_reports', 'approve_workflow_stages',
                'manage_team_schedules', 'view_users'
            ],
            'user': [
                'view_assigned_tasks', 'update_task_status', 'add_comments', 'upload_attachments', 'view_team_calendar'
            ],
            'observer': [
                'view_workflows', 'view_reports', 'export_data'
            ]
        }
        
        for role in roles:
            role_name = role[1]
            role_id = role[0]
            if role_name in permissions_data:
                for perm in permissions_data[role_name]:
                    c.execute('INSERT INTO permissions (role_id, permission_name) VALUES (?, ?)', (role_id, perm))
    
    # Добавляем тестовых пользователей
    c.execute('SELECT COUNT(*) FROM users')
    if c.fetchone()[0] == 0:
        from werkzeug.security import generate_password_hash
        
        users_data = [
            ('admin', 'admin@procevia.com', generate_password_hash('admin123'), 'admin', 'Admin User'),
            ('michael', 'michael@procevia.com', generate_password_hash('password123'), 'manager', 'Michael Chen'),
            ('sarah', 'sarah@procevia.com', generate_password_hash('password123'), 'user', 'Sarah Johnson'),
            ('emma', 'emma@procevia.com', generate_password_hash('password123'), 'observer', 'Emma Williams'),
        ]
        
        for user in users_data:
            c.execute('INSERT INTO users (username, email, password, role, full_name) VALUES (?, ?, ?, ?, ?)', user)
        
        # Обновляем счетчики пользователей в ролях
        c.execute('''
            UPDATE roles SET user_count = (
                SELECT COUNT(*) FROM users WHERE role = roles.name
            )
        ''')
        
        # Получаем ID пользователей
        c.execute('SELECT id, full_name FROM users')
        users = c.fetchall()
        
        # Задачи
        today = datetime.now().strftime('%Y-%m-%d')
        next_week = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        last_week = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
        
        tasks = [
            ('Design system review', 'Review and approve design system', 'completed', 'high', users[0][0], users[0][0], last_week),
            ('API integration', 'Integrate REST API', 'in_progress', 'high', users[2][0], users[0][0], next_week),
            ('Database migration', 'Migrate to PostgreSQL', 'pending', 'medium', users[1][0], users[0][0], next_week),
        ]
        
        for task in tasks:
            c.execute('INSERT INTO tasks (title, description, status, priority, assigned_to, created_by, due_date) VALUES (?, ?, ?, ?, ?, ?, ?)', task)
        
        # Активности
        activities = [
            (users[0][0], 'Admin User', 'created system', 'Procevia'),
            (users[2][0], 'Sarah Johnson', 'completed task', 'Design system review'),
            (users[1][0], 'Michael Chen', 'started task', 'API integration'),
        ]
        
        for activity in activities:
            c.execute('INSERT INTO activities (user_id, user_name, action, task_title) VALUES (?, ?, ?, ?)', activity)
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

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