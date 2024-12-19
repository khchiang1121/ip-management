import json
import bcrypt
from flask import Flask, render_template, request, redirect, url_for, Blueprint, flash, session
from flask_login import login_user, logout_user, current_user, login_required, UserMixin, LoginManager
from utils.common import role_required
import os

# Define constants
USER_FILE = './member.json'

# User class to represent a logged-in user
class User(UserMixin):
    pass

#flask login相關
login_manager = LoginManager()
# https://stackoverflow.com/questions/33724161/flask-login-shows-401-instead-of-redirecting-to-login-view
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'   # 好像沒效果，待修https://iter01.com/180317.html
login_manager.login_message = 'Access denied.'  # 好像沒效果，待修

@login_manager.user_loader
def user_loader(username):
    # Now load the users from the file
    with open(USER_FILE, 'r') as file:
        users = json.load(file)
    
    # If the username is not in the users dictionary, return an empty string or redirect to registration page
    if username not in users:
        return None
    user = User()
    user.id = username
    user.username = username
    user.role = users[username]['role']
    return user

# Blueprint for authentication routes
auth_bp = Blueprint('auth', __name__)

# Utility function to read users from the member file
def read_users():
    """Reads the users data from the member.json file."""
    if not os.path.exists(USER_FILE) or os.path.getsize(USER_FILE) == 0:
        return {}
    with open(USER_FILE, 'r') as file:
        return json.load(file)

# Utility function to write users to the member file
def write_users(users):
    """Writes the users data to the member.json file."""
    with open(USER_FILE, 'w') as file:
        json.dump(users, file, indent=4)

# Register route (admin only)
@auth_bp.route('/register/', methods=['GET', 'POST'])
@login_required
@role_required("Admin")
def register():
    if request.method == "POST":
        users = read_users()

        # Check if username already exists
        username = request.form['username']
        if username in users:
            flash('此帳號已註冊')
            return render_template('register.html', username=username, role=request.form['role'])

        # Check if passwords match
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if password != confirm_password:
            flash('密碼與確認密碼不同')
            return render_template('register.html', username=username, role=request.form['role'])

        # Hash password before storing
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Add new user to the dictionary
        users[username] = {'password': hashed_password.decode('utf-8'), 'role': request.form['role']}

        # Save users back to the file
        write_users(users)

        flash('新增成功')
        return redirect(url_for('index'))

    return render_template('register.html')

# Login route
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        return render_template("login.html")

    # Handle POST request for login
    username = request.form['username']
    password = request.form['password']
    users = read_users()

    if username in users:
        # Retrieve stored hashed password
        stored_password = users[username]['password']

        # Verify the provided password against the stored hash
        if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
            user = User()
            user.id = username
            login_user(user)

            # Redirect user to the next page or the home page
            dest_url = request.args.get('next', url_for('index'))
            return redirect(dest_url)

    flash('登入失敗')
    return redirect(url_for('auth.login'))  # Redirect to the login page if login fails

# Logout route
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))
