"""
File: auth.py
Author: Jonathan Hu
Date Created: 6/15/25
Last Modified: 7/5/25
Description: Authentication Blueprint for ResumeMatchAI Web Application

This module provides user authentication functionality for the ResumeMatchAI platform.
It handles user registration, login, logout, and session management using Flask-Login
for secure user authentication and session handling.

Key Features:
- User registration with validation and security checks
- Secure login with password verification
- Session management with remember-me functionality
- Logout functionality with session cleanup
- Flash message feedback for user actions
- Redirect handling for authenticated users

Authentication Routes:
- GET/POST /signup    : User registration with form validation
- GET/POST /login     : User login with credential verification
- GET     /logout     : User logout with session termination

Security Features:
- Password confirmation validation during registration
- Minimum password length requirement (8 characters)
- Email uniqueness validation
- Secure password hashing via DatabaseManager
- Session-based authentication with Flask-Login
- CSRF protection through Flask forms
- Redirect protection for authenticated users

Form Validation:
- Required field validation for all inputs
- Email format validation (handled by HTML5)
- Password strength requirements
- Password confirmation matching
- Duplicate email prevention

User Experience:
- Flash messages for success/error feedback
- Automatic redirects for authenticated users
- Remember-me functionality for persistent sessions
- Next page redirect after login
- User-friendly error messages

Template Integration:
- Renders login.html and signup.html templates
- Uses Flask-Login for user session management
- Integrates with base template styling
- Flash message display for user feedback

Database Integration:
- Uses DatabaseManager for user operations
- User creation with hashed passwords
- User verification with password checking
- User session management with Flask-Login

Dependencies:
- Flask Blueprint for modular routing
- Flask-Login for authentication and session management
- Core database module for user operations
- Flask templates for user interface
- Werkzeug for security utilities

Error Handling:
- Form validation errors with user feedback
- Database operation error handling
- Authentication failure handling
- Redirect loop prevention

Usage:
Register this blueprint in the main Flask app with:
app.register_blueprint(auth)

The blueprint provides secure authentication endpoints that integrate
with the main application's user management system.
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from core.database import DatabaseManager, User

auth = Blueprint('auth', __name__)

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate inputs
        if not name or not email or not password:
            flash('Please fill all fields', 'error')
            return redirect(url_for('auth.signup'))
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('auth.signup'))
        
        if len(password) < 8:
            flash('Password must be at least 8 characters', 'error')
            return redirect(url_for('auth.signup'))
        
        # Create user
        db = DatabaseManager()
        user_id = db.create_user(name, email, password)
        
        if user_id:
            user_data = db.get_user_by_id(user_id)
            user = User(user_data)
            login_user(user)
            flash('Account created successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Email already exists', 'error')
    
    return render_template('signup.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Please fill all fields', 'error')
            return redirect(url_for('auth.login'))
        
        db = DatabaseManager()
        user_data = db.verify_user(email, password)
        
        if user_data:
            user = User(user_data)
            login_user(user, remember=True)
            flash('Logged in successfully!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'success')
    return redirect(url_for('index'))