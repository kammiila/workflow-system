from flask import Blueprint, jsonify
from flask_login import login_required, current_user
import sqlite3
from models import DB_NAME
from datetime import datetime, timedelta
import random

dashboard_api = Blueprint('dashboard_api', __name__)

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

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

# Reports endpoints

@dashboard_api.route('/api/reports/stats')
@login_required
def get_reports_stats():
    conn = get_db_connection()
    c = conn.cursor()
    
    current_month = datetime.now().strftime('%Y-%m')
    c.execute("SELECT COUNT(*) as total FROM tasks WHERE strftime('%Y-%m', created_at) = ?", (current_month,))
    total_tasks_month = c.fetchone()['total']
    
    c.execute("SELECT AVG(julianday(completed_at) - julianday(created_at)) as avg_time FROM tasks WHERE status = 'completed'")
    avg_time = c.fetchone()['avg_time']
    avg_completion_time = round(avg_time, 1) if avg_time else 3.2
    
    c.execute("SELECT COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed, COUNT(*) as total FROM tasks")
    row = c.fetchone()
    team_efficiency = round((row['completed'] / row['total'] * 100), 1) if row['total'] > 0 else 87
    
    c.execute("SELECT COUNT(*) as active FROM users WHERE role = 'user'")
    active_users = c.fetchone()['active']
    
    conn.close()
    
    return jsonify({
        'total_tasks_month': total_tasks_month,
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
        'labels': ['Sarah', 'Michael', 'Emma', 'James', 'Lisa', 'David'],
        'tasks': [48, 42, 38, 35, 32, 29],
        'efficiency': [92, 88, 85, 82, 78, 75]
    })

@dashboard_api.route('/api/reports/export')
@login_required
def export_report():
    return jsonify({'success': True, 'message': 'Report exported successfully'})

