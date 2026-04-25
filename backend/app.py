from flask import Flask, render_template
from flask_login import LoginManager, login_required, current_user
from models import init_db, get_user_by_id
from auth import auth
from dashboard import dashboard_api
from tasks import tasks_api
import os

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
frontend_path = os.path.join(base_dir, 'frontend')

if not os.path.exists(frontend_path):
    frontend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../frontend')
    frontend_path = os.path.abspath(frontend_path)

app = Flask(__name__, template_folder=frontend_path)
app.secret_key = 'your-secret-key-change-in-production'

init_db()

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return get_user_by_id(int(user_id))

app.register_blueprint(auth)
app.register_blueprint(dashboard_api)
app.register_blueprint(tasks_api)

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/tasks')
@login_required
def tasks_page():
    return render_template('tasks.html')

@app.route('/workflow')
@login_required
def workflow_page():
    return render_template('workflow.html')

@app.route('/users')
@login_required
def users_page():
    if current_user.role not in ['admin', 'manager']:
        return render_template('access_denied.html', page='Users', required_role='Admin or Manager', user_role=current_user.role)
    return render_template('users.html')

@app.route('/roles')
@login_required
def roles_page():
    if current_user.role != 'admin':
        return render_template('access_denied.html', page='Roles', required_role='Admin', user_role=current_user.role)
    return render_template('roles.html')

@app.route('/reports')
@login_required
def reports_page():
    return render_template('reports.html')

@app.route('/settings')
@login_required
def settings_page():
    if current_user.role != 'admin':
        return render_template('access_denied.html', page='Settings', required_role='Admin', user_role=current_user.role)
    return render_template('settings.html')

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("🎯 Procevia Workflow System")
    print("=" * 60)
    print("📱 Server: http://127.0.0.1:5000")
    print("=" * 60)
    print("👑 ADMIN: admin / admin123")
    print("📊 MANAGER: michael / password123")
    print("👤 TEAM MEMBER: sarah / password123")
    print("👁️ OBSERVER: emma / password123")
    print("=" * 60 + "\n")
    app.run(debug=True, host='127.0.0.1', port=5000)