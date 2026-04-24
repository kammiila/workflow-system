from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
import sqlite3
from models import DB_NAME
from datetime import datetime

tasks_api = Blueprint('tasks_api', __name__)

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

@tasks_api.route('/api/tasks', methods=['GET'])
@login_required
def get_tasks():
    """Получить все задачи"""
    conn = get_db_connection()
    c = conn.cursor()
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    if current_user.role == 'admin':
        c.execute('''
            SELECT t.*, u.full_name as assignee_name 
            FROM tasks t 
            LEFT JOIN users u ON t.assigned_to = u.id 
            ORDER BY t.id DESC
        ''')
    else:
        c.execute('''
            SELECT t.*, u.full_name as assignee_name 
            FROM tasks t 
            LEFT JOIN users u ON t.assigned_to = u.id 
            WHERE t.assigned_to = ? OR t.created_by = ?
            ORDER BY t.id DESC
        ''', (current_user.id, current_user.id))
    
    tasks = []
    for row in c.fetchall():
        # Определяем статус для отображения
        status_display = row['status']
        is_overdue = False
        
        if row['status'] != 'completed' and row['due_date']:
            if row['due_date'] < today:
                status_display = 'Overdue'
                is_overdue = True
            elif row['status'] == 'pending':
                status_display = 'To Do'
            elif row['status'] == 'in_progress':
                status_display = 'In Progress'
            elif row['status'] == 'in_review':
                status_display = 'Review'
            elif row['status'] == 'completed':
                status_display = 'Completed'
        
        # Маппинг статуса в этап
        stage_map = {
            'pending': 'Planning',
            'in_progress': 'Development',
            'in_review': 'Review',
            'completed': 'Done'
        }
        
        tasks.append({
            'id': row['id'],
            'name': row['title'],
            'description': row['description'] or '',
            'assignee': row['assignee_name'] if row['assignee_name'] else 'Unassigned',
            'assignee_initials': get_initials(row['assignee_name']) if row['assignee_name'] else 'U',
            'stage': stage_map.get(row['status'], 'Planning'),
            'deadline': row['due_date'] if row['due_date'] else '',
            'priority': row['priority'].capitalize() if row['priority'] else 'Medium',
            'status': status_display,
            'is_overdue': is_overdue
        })
    
    conn.close()
    return jsonify(tasks)

@tasks_api.route('/api/tasks', methods=['POST'])
@login_required
def create_task():
    """Создать новую задачу"""
    data = request.json
    conn = get_db_connection()
    c = conn.cursor()
    
    # Находим ID исполнителя
    assignee_id = None
    if data.get('assignee'):
        c.execute('SELECT id FROM users WHERE full_name = ?', (data['assignee'],))
        user = c.fetchone()
        if user:
            assignee_id = user['id']
    
    # Маппинг этапа в статус
    status_map = {
        'Planning': 'pending',
        'Development': 'in_progress',
        'Review': 'in_review',
        'Testing': 'in_review',
        'Done': 'completed'
    }
    status = status_map.get(data.get('stage', 'Planning'), 'pending')
    
    c.execute('''
        INSERT INTO tasks (title, description, status, priority, assigned_to, created_by, due_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        data.get('name'),
        data.get('description', ''),
        status,
        data.get('priority', 'medium').lower(),
        assignee_id,
        current_user.id,
        data.get('deadline')
    ))
    
    task_id = c.lastrowid
    
    # Логируем активность
    c.execute('''
        INSERT INTO activities (user_id, user_name, action, task_title)
        VALUES (?, ?, ?, ?)
    ''', (current_user.id, current_user.full_name, 'created task', data.get('name')))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'task_id': task_id})

@tasks_api.route('/api/tasks/<int:task_id>', methods=['PUT'])
@login_required
def update_task(task_id):
    """Обновить задачу"""
    data = request.json
    conn = get_db_connection()
    c = conn.cursor()
    
    updates = []
    params = []
    
    if 'name' in data:
        updates.append('title = ?')
        params.append(data['name'])
    
    if 'description' in data:
        updates.append('description = ?')
        params.append(data['description'])
    
    if 'priority' in data:
        updates.append('priority = ?')
        params.append(data['priority'].lower())
    
    if 'assignee' in data and data['assignee']:
        c.execute('SELECT id FROM users WHERE full_name = ?', (data['assignee'],))
        user = c.fetchone()
        if user:
            updates.append('assigned_to = ?')
            params.append(user['id'])
    
    if 'stage' in data:
        status_map = {
            'Planning': 'pending',
            'Development': 'in_progress',
            'Review': 'in_review',
            'Testing': 'in_review',
            'Done': 'completed'
        }
        new_status = status_map.get(data['stage'], 'pending')
        updates.append('status = ?')
        params.append(new_status)
        
        if new_status == 'completed':
            updates.append('completed_at = CURRENT_TIMESTAMP')
    
    if 'deadline' in data:
        updates.append('due_date = ?')
        params.append(data['deadline'])
    
    if 'status' in data:
        status_map_api = {
            'To Do': 'pending',
            'In Progress': 'in_progress',
            'Review': 'in_review',
            'Completed': 'completed'
        }
        new_status = status_map_api.get(data['status'], 'pending')
        updates.append('status = ?')
        params.append(new_status)
        
        if new_status == 'completed':
            updates.append('completed_at = CURRENT_TIMESTAMP')
    
    if updates:
        params.append(task_id)
        c.execute(f'UPDATE tasks SET {", ".join(updates)} WHERE id = ?', params)
        
        # Добавляем активность
        c.execute('''
            INSERT INTO activities (user_id, user_name, action, task_title)
            VALUES (?, ?, ?, (SELECT title FROM tasks WHERE id = ?))
        ''', (current_user.id, current_user.full_name, 'updated task', task_id))
        
        conn.commit()
    
    conn.close()
    return jsonify({'success': True})

@tasks_api.route('/api/tasks/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    """Удалить задачу"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Получаем название задачи для активности
    c.execute('SELECT title FROM tasks WHERE id = ?', (task_id,))
    task = c.fetchone()
    
    if task:
        c.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        
        # Добавляем активность
        c.execute('''
            INSERT INTO activities (user_id, user_name, action, task_title)
            VALUES (?, ?, ?, ?)
        ''', (current_user.id, current_user.full_name, 'deleted task', task['title']))
        
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Task deleted successfully'})
    
    conn.close()
    return jsonify({'success': False, 'message': 'Task not found'}), 404

@tasks_api.route('/api/users/list', methods=['GET'])
@login_required
def get_users_list():
    """Получить список пользователей для назначения"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT id, full_name, username FROM users ORDER BY full_name')
    users = [{'id': row['id'], 'name': row['full_name'], 'username': row['username']} for row in c.fetchall()]
    conn.close()
    return jsonify(users)

def get_initials(name):
    """Получить инициалы из имени"""
    if not name:
        return 'U'
    parts = name.split()
    if len(parts) >= 2:
        return f"{parts[0][0]}{parts[1][0]}".upper()
    return name[:2].upper()