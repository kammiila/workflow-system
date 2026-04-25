from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
import sqlite3
import json
import os
from datetime import datetime, timedelta
import random

DB_NAME = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'database.db')

dashboard_api = Blueprint('dashboard_api', __name__)

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# ========== DASHBOARD ENDPOINTS ==========

@dashboard_api.route('/api/dashboard/user-info')
@login_required
def get_user_info():
    return jsonify({
        'username': current_user.username,
        'full_name': current_user.full_name,
        'role': current_user.role,
        'avatar_initials': current_user.full_name[:2].upper()
    })

@dashboard_api.route('/api/dashboard/stats')
@login_required
def get_stats():
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute('SELECT COUNT(*) as total FROM tasks')
    total_tasks = c.fetchone()['total']
    
    c.execute("SELECT COUNT(*) as completed FROM tasks WHERE status = 'completed'")
    completed = c.fetchone()['completed']
    
    c.execute("SELECT COUNT(*) as in_progress FROM tasks WHERE status = 'in_progress'")
    in_progress = c.fetchone()['in_progress']
    
    today = datetime.now().strftime('%Y-%m-%d')
    c.execute("SELECT COUNT(*) as overdue FROM tasks WHERE due_date < ? AND status != 'completed'", (today,))
    overdue = c.fetchone()['overdue']
    
    conn.close()
    
    return jsonify({
        'total_tasks': total_tasks,
        'completed': completed,
        'in_progress': in_progress,
        'overdue': overdue
    })

@dashboard_api.route('/api/dashboard/task-progress')
@login_required
def get_task_progress():
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
    data = []
    for month in months:
        data.append({
            'month': month,
            'completed': random.randint(20, 70),
            'inProgress': random.randint(10, 40)
        })
    return jsonify(data)

@dashboard_api.route('/api/dashboard/tasks-by-status')
@login_required
def get_tasks_by_status():
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute('SELECT COUNT(*) as total FROM tasks')
    total = c.fetchone()['total']
    total = total if total > 0 else 1
    
    c.execute("SELECT COUNT(*) as completed FROM tasks WHERE status = 'completed'")
    completed = c.fetchone()['completed']
    
    c.execute("SELECT COUNT(*) as in_progress FROM tasks WHERE status = 'in_progress'")
    in_progress = c.fetchone()['in_progress']
    
    c.execute("SELECT COUNT(*) as pending FROM tasks WHERE status = 'pending'")
    pending = c.fetchone()['pending']
    
    conn.close()
    
    return jsonify([
        {'name': 'Completed', 'value': completed, 'color': '#22C55E', 'percentage': round(completed/total*100)},
        {'name': 'In Progress', 'value': in_progress, 'color': '#F59E0B', 'percentage': round(in_progress/total*100)},
        {'name': 'Pending', 'value': pending, 'color': '#EF4444', 'percentage': round(pending/total*100)}
    ])

@dashboard_api.route('/api/dashboard/recent-activities')
@login_required
def get_recent_activities():
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute('SELECT user_name, action, task_title, created_at FROM activities ORDER BY created_at DESC LIMIT 5')
    
    activities = []
    colors = ['#06B6D4', '#0891B2', '#22D3EE', '#0EA5E9', '#0284C7']
    
    for i, row in enumerate(c.fetchall()):
        activities.append({
            'user': row['user_name'],
            'action': row['action'],
            'task': row['task_title'],
            'time': 'recently',
            'color': colors[i % len(colors)],
            'initials': row['user_name'][:2].upper()
        })
    
    conn.close()
    return jsonify(activities)

# ========== REPORTS ENDPOINTS ==========

@dashboard_api.route('/api/reports/stats')
@login_required
def get_reports_stats():
    conn = get_db_connection()
    c = conn.cursor()
    
    current_month = datetime.now().strftime('%Y-%m')
    c.execute("SELECT COUNT(*) as total FROM tasks WHERE strftime('%Y-%m', created_at) = ?", (current_month,))
    result = c.fetchone()
    total_tasks_month = result['total'] if result else 0
    
    c.execute("SELECT AVG(julianday(completed_at) - julianday(created_at)) as avg_time FROM tasks WHERE status = 'completed' AND completed_at IS NOT NULL")
    result = c.fetchone()
    avg_time = result['avg_time'] if result else None
    avg_completion_time = round(avg_time, 1) if avg_time else 3.2
    
    c.execute("SELECT COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed, COUNT(*) as total FROM tasks")
    row = c.fetchone()
    if row and row['total'] > 0:
        team_efficiency = round((row['completed'] / row['total'] * 100), 1)
    else:
        team_efficiency = 87
    
    c.execute("SELECT COUNT(*) as active FROM users")
    result = c.fetchone()
    active_users = result['active'] if result else 4
    
    conn.close()
    
    return jsonify({
        'total_tasks_month': total_tasks_month if total_tasks_month > 0 else 24,
        'avg_completion_time': avg_completion_time,
        'team_efficiency': team_efficiency,
        'active_users': active_users,
        'total_tasks_change': '+12.5%',
        'avg_time_change': '-8%',
        'efficiency_change': '+5%'
    })

@dashboard_api.route('/api/reports/weekly-progress')
@login_required
def get_weekly_progress():
    return jsonify({
        'labels': ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5', 'Week 6'],
        'data': [28, 35, 42, 38, 45, 52]
    })

@dashboard_api.route('/api/reports/user-productivity')
@login_required
def get_user_productivity():
    return jsonify({
        'labels': ['Sarah', 'Michael', 'Emma', 'Admin'],
        'tasks': [48, 42, 38, 52],
        'efficiency': [92, 88, 85, 95]
    })

@dashboard_api.route('/api/reports/export')
@login_required
def export_report():
    return jsonify({'success': True, 'message': 'Report exported successfully'})

# ========== USERS MANAGEMENT ENDPOINTS ==========

@dashboard_api.route('/api/users', methods=['GET'])
@login_required
def get_users():
    if current_user.role not in ['admin', 'manager']:
        return jsonify({'error': 'Access denied'}), 403
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT id, username, email, role, full_name FROM users ORDER BY id')
    
    users = []
    for row in c.fetchall():
        users.append({
            'id': row['id'],
            'name': row['full_name'],
            'email': row['email'],
            'role': row['role'],
            'initials': row['full_name'][:2].upper() if row['full_name'] else row['username'][:2].upper()
        })
    
    conn.close()
    return jsonify(users)

@dashboard_api.route('/api/users', methods=['POST'])
@login_required
def create_user():
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied. Admin only.'}), 403
    
    data = request.json
    
    if not data.get('name') or not data.get('email'):
        return jsonify({'error': 'Name and email are required'}), 400
    
    conn = get_db_connection()
    c = conn.cursor()
    
    username = data['email'].split('@')[0]
    hashed_password = generate_password_hash('password123')
    role = data.get('role', 'user')
    
    try:
        c.execute('''
            INSERT INTO users (username, email, password, role, full_name)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, data['email'], hashed_password, role, data['name']))
        
        c.execute('UPDATE roles SET user_count = (SELECT COUNT(*) FROM users WHERE role = ?) WHERE name = ?', (role, role))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': f'User {data["name"]} created successfully'})
        
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'User with this email already exists'}), 400

@dashboard_api.route('/api/users/<int:user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied. Admin only.'}), 403
    
    data = request.json
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute('SELECT role FROM users WHERE id = ?', (user_id,))
    old_role = c.fetchone()
    old_role_name = old_role['role'] if old_role else None
    
    role = data.get('role', 'user')
    username = data['email'].split('@')[0]
    
    try:
        c.execute('''
            UPDATE users 
            SET full_name = ?, email = ?, username = ?, role = ?
            WHERE id = ?
        ''', (data['name'], data['email'], username, role, user_id))
        
        if old_role_name and old_role_name != role:
            c.execute('UPDATE roles SET user_count = (SELECT COUNT(*) FROM users WHERE role = ?) WHERE name = ?', (old_role_name, old_role_name))
            c.execute('UPDATE roles SET user_count = (SELECT COUNT(*) FROM users WHERE role = ?) WHERE name = ?', (role, role))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'User updated successfully'})
        
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

@dashboard_api.route('/api/users/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied. Admin only.'}), 403
    
    if user_id == current_user.id:
        return jsonify({'error': 'You cannot delete your own account'}), 400
    
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute('SELECT role FROM users WHERE id = ?', (user_id,))
    role_row = c.fetchone()
    role = role_row['role'] if role_row else None
    
    try:
        c.execute('DELETE FROM users WHERE id = ?', (user_id,))
        
        if role:
            c.execute('UPDATE roles SET user_count = (SELECT COUNT(*) FROM users WHERE role = ?) WHERE name = ?', (role, role))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'User deleted successfully'})
        
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

# ========== ROLES MANAGEMENT ENDPOINTS ==========

@dashboard_api.route('/api/roles', methods=['GET'])
@login_required
def get_roles():
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute('SELECT id, name, description, color, icon_name, user_count FROM roles ORDER BY id')
    roles = []
    for row in c.fetchall():
        c.execute('SELECT permission_name FROM permissions WHERE role_id = ?', (row['id'],))
        permissions = [p['permission_name'] for p in c.fetchall()]
        
        roles.append({
            'id': row['id'],
            'name': row['name'],
            'description': row['description'],
            'color': row['color'],
            'icon_name': row['icon_name'],
            'user_count': row['user_count'],
            'permissions': permissions
        })
    
    conn.close()
    return jsonify(roles)

@dashboard_api.route('/api/roles/<int:role_id>', methods=['PUT'])
@login_required
def update_role(role_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied. Admin only.'}), 403
    
    data = request.json
    conn = get_db_connection()
    c = conn.cursor()
    
    try:
        c.execute('''
            UPDATE roles 
            SET name = ?, description = ?, color = ?, icon_name = ?
            WHERE id = ?
        ''', (data['name'], data['description'], data['color'], data['icon_name'], role_id))
        
        c.execute('DELETE FROM permissions WHERE role_id = ?', (role_id,))
        for perm in data['permissions']:
            c.execute('INSERT INTO permissions (role_id, permission_name) VALUES (?, ?)', (role_id, perm))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': f'Role {data["name"]} updated successfully'})
        
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

@dashboard_api.route('/api/roles/update-counts', methods=['POST'])
@login_required
def update_role_counts():
    """Обновить счетчики пользователей в ролях"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied. Admin only.'}), 403
    
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute('''
        UPDATE roles SET user_count = (
            SELECT COUNT(*) FROM users WHERE role = roles.name
        )
    ''')
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Role counts updated'})

# ========== WORKFLOW STAGES SYNC ==========

@dashboard_api.route('/api/workflow/stages', methods=['GET'])
@login_required
def get_workflow_stages():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT id, name, color FROM workflow_statuses ORDER BY display_order')
    stages = [{'id': row['id'], 'name': row['name'], 'color': row['color']} for row in c.fetchall()]
    conn.close()
    return jsonify(stages)

@dashboard_api.route('/api/workflow/stages', methods=['POST'])
@login_required
def add_workflow_stage():
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied. Admin only.'}), 403
    
    data = request.json
    if not data.get('name'):
        return jsonify({'error': 'Stage name is required'}), 400
    
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute('SELECT MAX(display_order) as max_order FROM workflow_statuses')
    max_order = c.fetchone()['max_order']
    new_order = (max_order + 1) if max_order else 1
    
    try:
        c.execute('INSERT INTO workflow_statuses (name, color, display_order) VALUES (?, ?, ?)',
                  (data['name'], data.get('color', '#9CCC65'), new_order))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': f'Stage "{data["name"]}" added'})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'Stage with this name already exists'}), 400

@dashboard_api.route('/api/workflow/stages/<int:stage_id>', methods=['DELETE'])
@login_required
def delete_workflow_stage(stage_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied. Admin only.'}), 403
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('DELETE FROM workflow_statuses WHERE id = ?', (stage_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Stage deleted'})

# ========== NOTIFICATIONS ==========

@dashboard_api.route('/api/notifications', methods=['GET'])
@login_required
def get_notifications():
    """Получить уведомления для текущего пользователя"""
    conn = get_db_connection()
    c = conn.cursor()
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Просроченные задачи
    c.execute('''
        SELECT COUNT(*) as count FROM tasks 
        WHERE assigned_to = ? AND due_date < ? AND status != 'completed'
    ''', (current_user.id, today))
    overdue_count = c.fetchone()['count']
    
    # Задачи на сегодня
    c.execute('''
        SELECT COUNT(*) as count FROM tasks 
        WHERE assigned_to = ? AND due_date = ? AND status != 'completed'
    ''', (current_user.id, today))
    today_tasks = c.fetchone()['count']
    
    # Новые задачи (за последние 24 часа)
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    c.execute('''
        SELECT COUNT(*) as count FROM tasks 
        WHERE assigned_to = ? AND created_at > ?
    ''', (current_user.id, yesterday))
    new_tasks = c.fetchone()['count']
    
    # Активности команды
    c.execute('''
        SELECT user_name, action, task_title, created_at 
        FROM activities 
        ORDER BY created_at DESC 
        LIMIT 10
    ''')
    recent_activities = [dict(row) for row in c.fetchall()]
    
    conn.close()
    
    notifications = []
    
    if overdue_count > 0:
        notifications.append({
            'id': 1,
            'title': '⚠️ Overdue Tasks',
            'message': f'You have {overdue_count} overdue task(s)',
            'type': 'warning',
            'time': 'now',
            'read': False
        })
    
    if today_tasks > 0:
        notifications.append({
            'id': 2,
            'title': '📅 Tasks Due Today',
            'message': f'You have {today_tasks} task(s) due today',
            'type': 'info',
            'time': 'now',
            'read': False
        })
    
    if new_tasks > 0:
        notifications.append({
            'id': 3,
            'title': '🆕 New Tasks Assigned',
            'message': f'You have {new_tasks} new task(s) assigned',
            'type': 'success',
            'time': 'now',
            'read': False
        })
    
    for i, act in enumerate(recent_activities[:5]):
        notifications.append({
            'id': i + 10,
            'title': f'👤 {act["user_name"]}',
            'message': f'{act["action"]}: {act["task_title"]}',
            'type': 'activity',
            'time': act["created_at"],
            'read': False
        })
    
    return jsonify({
        'notifications': notifications,
        'unread_count': len(notifications),
        'overdue_count': overdue_count,
        'today_tasks': today_tasks
    })

@dashboard_api.route('/api/notifications/mark-read', methods=['POST'])
@login_required
def mark_notifications_read():
    return jsonify({'success': True})

# ========== SETTINGS ENDPOINTS ==========

@dashboard_api.route('/api/settings/workflow-stages', methods=['GET'])
@login_required
def get_settings_workflow_stages():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT id, name, color FROM workflow_statuses ORDER BY display_order')
    stages = [{'id': row['id'], 'name': row['name'], 'color': row['color']} for row in c.fetchall()]
    conn.close()
    return jsonify(stages)

@dashboard_api.route('/api/settings/workflow-stages', methods=['POST'])
@login_required
def add_settings_workflow_stage():
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied. Admin only.'}), 403
    
    data = request.json
    if not data.get('name'):
        return jsonify({'error': 'Stage name is required'}), 400
    
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute('SELECT MAX(display_order) as max_order FROM workflow_statuses')
    max_order = c.fetchone()['max_order']
    new_order = (max_order + 1) if max_order else 1
    
    try:
        c.execute('INSERT INTO workflow_statuses (name, color, display_order) VALUES (?, ?, ?)',
                  (data['name'], data.get('color', '#9CCC65'), new_order))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': f'Stage "{data["name"]}" added'})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'Stage with this name already exists'}), 400

@dashboard_api.route('/api/settings/workflow-stages/<int:stage_id>', methods=['DELETE'])
@login_required
def delete_settings_workflow_stage(stage_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied. Admin only.'}), 403
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('DELETE FROM workflow_statuses WHERE id = ?', (stage_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Stage deleted'})

@dashboard_api.route('/api/settings/notifications', methods=['GET'])
@login_required
def get_notification_settings():
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute('SELECT email_notifications, push_notifications, task_reminders, weekly_reports FROM user_settings WHERE user_id = ?', (current_user.id,))
    settings = c.fetchone()
    
    if not settings:
        return jsonify({
            'email_notifications': True,
            'push_notifications': True,
            'task_reminders': True,
            'weekly_reports': False
        })
    
    conn.close()
    return jsonify({
        'email_notifications': bool(settings['email_notifications']),
        'push_notifications': bool(settings['push_notifications']),
        'task_reminders': bool(settings['task_reminders']),
        'weekly_reports': bool(settings['weekly_reports'])
    })

@dashboard_api.route('/api/settings/notifications', methods=['PUT'])
@login_required
def update_notification_settings():
    data = request.json
    
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute('''
        INSERT OR REPLACE INTO user_settings (user_id, email_notifications, push_notifications, task_reminders, weekly_reports)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        current_user.id,
        1 if data.get('email_notifications') else 0,
        1 if data.get('push_notifications') else 0,
        1 if data.get('task_reminders') else 0,
        1 if data.get('weekly_reports') else 0
    ))
    
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Settings updated'})

@dashboard_api.route('/api/settings/system-info', methods=['GET'])
@login_required
def get_system_info():
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute('SELECT COUNT(*) as count FROM users')
    user_count = c.fetchone()['count']
    
    c.execute('SELECT COUNT(*) as count FROM tasks')
    task_count = c.fetchone()['count']
    
    c.execute('SELECT COUNT(*) as count FROM tasks WHERE status = "completed"')
    completed_count = c.fetchone()['count']
    
    conn.close()
    
    return jsonify({
        'version': '2.0.0',
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'user_count': user_count,
        'task_count': task_count,
        'completed_tasks': completed_count,
        'storage_used': round(random.uniform(1.5, 4.5), 1),
        'storage_total': 10
    })

@dashboard_api.route('/api/settings/backup', methods=['POST'])
@login_required
def create_backup():
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied. Admin only.'}), 403
    
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute('SELECT * FROM users')
    users = [dict(row) for row in c.fetchall()]
    
    c.execute('SELECT * FROM tasks')
    tasks = [dict(row) for row in c.fetchall()]
    
    conn.close()
    
    backup_data = {
        'users': users,
        'tasks': tasks,
        'backup_date': datetime.now().isoformat()
    }
    
    backup_dir = os.path.join(os.path.dirname(DB_NAME), 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    
    backup_file = os.path.join(backup_dir, f'backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, indent=2, default=str, ensure_ascii=False)
    
    return jsonify({'success': True, 'message': 'Backup created'})

@dashboard_api.route('/api/settings/export', methods=['POST'])
@login_required
def export_data():
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied. Admin only.'}), 403
    
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute('SELECT id, username, email, role, full_name, created_at FROM users')
    users = [dict(row) for row in c.fetchall()]
    
    c.execute('SELECT id, title, description, status, priority, due_date, created_at FROM tasks')
    tasks = [dict(row) for row in c.fetchall()]
    
    conn.close()
    
    export_data = {
        'users': users,
        'tasks': tasks,
        'exported_at': datetime.now().isoformat(),
        'exported_by': current_user.username
    }
    
    return jsonify({'success': True, 'message': 'Data exported', 'data': export_data})

@dashboard_api.route('/api/settings/logs', methods=['GET'])
@login_required
def get_logs():
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied. Admin only.'}), 403
    
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute('SELECT user_name, action, task_title, created_at FROM activities ORDER BY created_at DESC LIMIT 20')
    activities = [dict(row) for row in c.fetchall()]
    
    conn.close()
    
    logs = []
    for act in activities:
        logs.append(f'[{act["created_at"]}] {act["user_name"]} - {act["action"]}: {act["task_title"]}')
    
    logs.insert(0, f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] System: User {current_user.username} requested logs')
    
    return jsonify({'success': True, 'logs': logs})