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
    elif current_user.role == 'manager':
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
                status_display = 'In Review'
        
        # Map internal status codes to workflow stage display names (use canonical names stored in workflow_statuses)
        status_to_stage = {
            'pending': 'To Do',
            'in_progress': 'In Progress',
            'in_review': 'In Review',
            'completed': 'Done'
        }
        
        tasks.append({
            'id': row['id'],
            'name': row['title'],
            'description': row['description'] or '',
            'assignee': row['assignee_name'] if row['assignee_name'] else 'Unassigned',
            'assignee_initials': row['assignee_name'][:2].upper() if row['assignee_name'] else 'U',
            'stage': status_to_stage.get(row['status'], 'To Do'),
            'status_raw': row['status'],
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
    if current_user.role not in ['admin', 'manager']:
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.json
    conn = get_db_connection()
    c = conn.cursor()
    
    assignee_id = None
    if data.get('assignee'):
        c.execute('SELECT id FROM users WHERE full_name = ?', (data['assignee'],))
        user = c.fetchone()
        if user:
            assignee_id = user['id']
    
    status_map = {'Planning': 'pending', 'Development': 'in_progress', 'Review': 'in_review', 'Testing': 'in_review', 'Done': 'completed'}
    status = status_map.get(data.get('stage', 'Planning'), 'pending')
    
    c.execute('''
        INSERT INTO tasks (title, description, status, priority, assigned_to, created_by, due_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (data.get('name'), data.get('description', ''), status, data.get('priority', 'medium').lower(), assignee_id, current_user.id, data.get('deadline')))
    
    task_id = c.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'task_id': task_id})

@tasks_api.route('/api/tasks/<int:task_id>', methods=['PUT'])
@login_required
def update_task(task_id):
    if current_user.role not in ['admin', 'manager']:
        return jsonify({'error': 'Access denied'}), 403
    
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
    if 'status' in data:
        status_map = {'To Do': 'pending', 'In Progress': 'in_progress', 'Review': 'in_review', 'Completed': 'completed'}
        db_status = status_map.get(data['status'], 'pending')
        updates.append('status = ?')
        params.append(db_status)
        if db_status == 'completed':
            updates.append('completed_at = CURRENT_TIMESTAMP')
    if 'assignee' in data and data['assignee']:
        c.execute('SELECT id FROM users WHERE full_name = ?', (data['assignee'],))
        user = c.fetchone()
        if user:
            updates.append('assigned_to = ?')
            params.append(user['id'])
    if 'deadline' in data:
        updates.append('due_date = ?')
        params.append(data['deadline'])
    
    if updates:
        params.append(task_id)
        c.execute(f'UPDATE tasks SET {", ".join(updates)} WHERE id = ?', params)
        conn.commit()
    
    conn.close()
    return jsonify({'success': True})

@tasks_api.route('/api/tasks/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied. Admin only.'}), 403
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@tasks_api.route('/api/users/list', methods=['GET'])
@login_required
def get_users_list():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT id, full_name, username FROM users ORDER BY full_name')
    users = [{'id': row['id'], 'name': row['full_name'], 'username': row['username']} for row in c.fetchall()]
    conn.close()
    return jsonify(users)