from flask import Flask, render_template
from flask_login import LoginManager, login_required, current_user
from models import init_db, get_user_by_id
from auth import auth
from dashboard import dashboard_api
from tasks import tasks_api
import os

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
frontend_path = os.path.join(base_dir, 'frontend')

app = Flask(__name__, template_folder=frontend_path)
app.secret_key = 'your-secret-key-change-in-production'

# Инициализация БД
init_db()

# Flask-Login setup
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return get_user_by_id(int(user_id))

# Регистрация blueprint
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

@app.route('/reports')
@login_required
def reports_page():
    return render_template('reports.html')

@app.route('/users')
@login_required
def users_page():
    if current_user.role != 'admin':
        return "Access denied: Admin only", 403
    return render_template('users.html')

@app.route('/roles')
@login_required
def roles_page():
    if current_user.role != 'admin':
        return "Access denied: Admin only", 403
    return render_template('roles.html')

@app.route('/settings')
@login_required
def settings_page():
    return render_template('settings.html')

if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("Procevia Workflow System")
    print("=" * 50)
    print("Server: http://127.0.0.1:5000")
    print("Admin: admin / admin123")
    print("User: sarah / password123")
    print("=" * 50 + "\n")
    app.run(debug=True, host='127.0.0.1', port=5000)