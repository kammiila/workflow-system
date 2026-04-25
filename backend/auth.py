from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from models import get_user_by_username, DB_NAME
import sqlite3

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = get_user_by_username(username)
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        role = request.form.get('role', 'user')
        
        if not username or len(username) < 3:
            flash('Username must be at least 3 characters', 'danger')
            return render_template('register.html')
        
        if not password or len(password) < 6:
            flash('Password must be at least 6 characters', 'danger')
            return render_template('register.html')
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        try:
            hashed_pw = generate_password_hash(password)
            db_role = role if role in ['admin', 'manager', 'user', 'observer'] else 'user'
            full_name = username.title()
            
            c.execute('''
                INSERT INTO users (username, email, password, role, full_name) 
                VALUES (?, ?, ?, ?, ?)
            ''', (username, email, hashed_pw, db_role, full_name))
            
            c.execute('UPDATE roles SET user_count = (SELECT COUNT(*) FROM users WHERE role = ?) WHERE name = ?', (db_role, db_role))
            
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('auth.login'))
        except sqlite3.IntegrityError:
            flash('Username already exists', 'danger')
        finally:
            conn.close()
    
    return render_template('register.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'info')
    return redirect(url_for('auth.login'))