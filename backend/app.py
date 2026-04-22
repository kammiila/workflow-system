from flask import Flask, render_template
from flask_login import LoginManager, login_required, current_user
from models import init_db, get_user_by_username, DB_NAME
from auth import auth
import sqlite3

app = Flask(__name__, template_folder='../frontend')
app.secret_key = 'your-secret-key-change-in-production'

# Инициализация БД
init_db()

# Flask-Login setup
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT id, username, password, role FROM users WHERE id = ?', (user_id,))
    user = c.fetchone()
    conn.close()
    if user:
        from models import User
        return User(user[0], user[1], user[2], user[3])
    return None

# Регистрация blueprint
app.register_blueprint(auth)

# Пример защищенных страниц (ролевой доступ – соответствует вашему Proposal)
@app.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return "Access denied: Admin only", 403
    return f"Admin Dashboard – Welcome {current_user.username}"

@app.route('/user')
@login_required
def user_dashboard():
    # Роль 'user' имеет доступ
    if current_user.role not in ['user', 'admin']:
        return "Access denied", 403
    return f"User Dashboard – Welcome {current_user.username}"

@app.route('/')
def home():
    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)