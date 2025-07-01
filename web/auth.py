"""
File: web/auth.py
Author: Enhanced Authentication System
Date Created: 7/1/25
Description: Clean authentication system with user registration, login, logout,
             password encryption, session management, and profile functionality.
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from core.database import DatabaseManager, User
import re
from datetime import datetime

# Create authentication blueprint
auth = Blueprint('auth', __name__, url_prefix='/auth')

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    return True, "Password is valid"

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    """User registration endpoint"""
    # Redirect if already logged in
    if current_user.is_authenticated:
        flash('You are already logged in!', 'info')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validate inputs
        errors = []
        
        if not name:
            errors.append("Full name is required")
        elif len(name) < 2:
            errors.append("Name must be at least 2 characters long")
        
        if not email:
            errors.append("Email is required")
        elif not validate_email(email):
            errors.append("Please enter a valid email address")
        
        if not password:
            errors.append("Password is required")
        else:
            is_valid, message = validate_password(password)
            if not is_valid:
                errors.append(message)
        
        if password != confirm_password:
            errors.append("Passwords do not match")
        
        # Display validation errors
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('signup.html')
        
        # Try to create user
        try:
            db = DatabaseManager()
            
            # Check if email already exists
            if db.get_user_by_email(email):
                flash('An account with this email already exists. Please use a different email or login.', 'error')
                return render_template('signup.html')
            
            # Create user with encrypted password
            user_id = db.create_user(name, email, password)
            
            if user_id:
                # Get the created user and log them in
                user_data = db.get_user_by_id(user_id)
                if user_data:
                    user = User(user_data)
                    login_user(user, remember=True)
                    flash(f'Welcome {name}! Your account has been created successfully.', 'success')
                    
                    # Log registration
                    print(f"New user registered: {email} at {datetime.utcnow()}")
                    
                    return redirect(url_for('index'))
                else:
                    flash('Account created but login failed. Please try logging in manually.', 'warning')
                    return redirect(url_for('auth.login'))
            else:
                flash('Failed to create account. Please try again.', 'error')
                
        except Exception as e:
            print(f"Registration error: {e}")
            flash('An error occurred during registration. Please try again.', 'error')
    
    return render_template('signup.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    """User login endpoint"""
    # Redirect if already logged in
    if current_user.is_authenticated:
        flash('You are already logged in!', 'info')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # Get form data
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember_me = request.form.get('remember_me') == 'on'
        
        # Validate inputs
        if not email or not password:
            flash('Please enter both email and password', 'error')
            return render_template('login.html')
        
        if not validate_email(email):
            flash('Please enter a valid email address', 'error')
            return render_template('login.html')
        
        try:
            db = DatabaseManager()
            user_data = db.verify_user(email, password)
            
            if user_data:
                user = User(user_data)
                login_user(user, remember=remember_me)
                
                # Log successful login
                print(f"User logged in: {email} at {datetime.utcnow()}")
                
                flash(f'Welcome back, {user_data.get("name", "User")}!', 'success')
                
                # Redirect to next page or index
                next_page = request.args.get('next')
                if next_page and next_page.startswith('/'):  # Security check
                    return redirect(next_page)
                else:
                    return redirect(url_for('index'))
            else:
                flash('Invalid email or password. Please try again.', 'error')
                
        except Exception as e:
            print(f"Login error: {e}")
            flash('An error occurred during login. Please try again.', 'error')
    
    return render_template('login.html')

@auth.route('/logout', methods=['GET', 'POST'])
def logout():
    """Enhanced logout endpoint with debugging"""
    print(f"🔓 LOGOUT ROUTE CALLED - Method: {request.method}")
    print(f"🔓 Current user authenticated: {current_user.is_authenticated}")
    print(f"🔓 Current user type: {type(current_user)}")
    
    if current_user.is_authenticated:
        user_name = current_user.name
        user_email = current_user.email
        user_id = current_user.id
        
        print(f"🔓 Attempting to logout user: {user_name} ({user_email}) - ID: {user_id}")
        
        # Clear session first
        session_keys = list(session.keys())
        print(f"🔓 Session keys before logout: {session_keys}")
        
        # Logout user using Flask-Login
        logout_user()
        
        # Manually clear all session data
        session.clear()
        
        print(f"🔓 After logout_user() - Is authenticated: {current_user.is_authenticated}")
        print(f"🔓 Session cleared - Keys remaining: {list(session.keys())}")
        
        # Log successful logout
        print(f"🔓 User logged out successfully: {user_email} at {datetime.utcnow()}")
        
        flash(f'Goodbye {user_name}! You have been logged out successfully.', 'success')
    else:
        print("🔓 LOGOUT CALLED: No user was logged in")
        flash('You were not logged in.', 'info')
    
    print(f"🔓 Redirecting to index...")
    response = redirect(url_for('index'))
    
    # Additional security: Clear any remaining cookies
    response.set_cookie('session', '', expires=0)
    response.set_cookie('remember_token', '', expires=0)
    
    return response

@auth.route('/debug-user')
def debug_user():
    """Debug route to check current user status"""
    if not app.debug:  # Only allow in debug mode
        return "Debug mode only", 403
    
    user_info = {
        'is_authenticated': current_user.is_authenticated,
        'user_type': type(current_user).__name__,
        'session_keys': list(session.keys()),
        'session_data': dict(session)
    }
    
    if current_user.is_authenticated:
        user_info.update({
            'user_id': current_user.id,
            'user_name': current_user.name,
            'user_email': current_user.email
        })
    
    return jsonify(user_info)
@auth.route('/profile')
@login_required
def profile():
    """User profile page"""
    try:
        db = DatabaseManager()
        
        # Get user's analysis history
        user_analyses = []
        try:
            # Get all analyses and filter by current user's name or email
            all_analyses = db.get_all_analyses(limit=50)
            user_analyses = [
                analysis for analysis in all_analyses 
                if analysis.get('name', '').lower() == current_user.name.lower()
            ]
            
            # Sort by timestamp (newest first)
            user_analyses.sort(key=lambda x: x.get('timestamp', datetime.min), reverse=True)
            
        except Exception as e:
            print(f"Error fetching user analyses: {e}")
            user_analyses = []
        
        # Get user's resume data if available
        user_data = db.get_user_by_id(current_user.id)
        has_resume = bool(user_data and user_data.get('resume_data'))
        
        # Calculate user statistics
        total_analyses = len(user_analyses)
        if total_analyses > 0:
            avg_score = sum(a.get('match_score', 0) for a in user_analyses) / total_analyses
            best_score = max(a.get('match_score', 0) for a in user_analyses)
            recent_analyses = user_analyses[:5]  # Last 5 analyses
        else:
            avg_score = 0
            best_score = 0
            recent_analyses = []
        
        # Format analyses for display
        formatted_analyses = []
        for analysis in recent_analyses:
            formatted_analyses.append({
                'job_title': analysis.get('job_title', 'N/A'),
                'company': analysis.get('company', 'N/A'),
                'match_score': analysis.get('match_score', 0),
                'timestamp': analysis.get('timestamp', datetime.utcnow()).strftime('%Y-%m-%d %H:%M')
            })
        
        profile_data = {
            'user': {
                'name': current_user.name,
                'email': current_user.email,
                'member_since': user_data.get('created_at', datetime.utcnow()).strftime('%B %Y') if user_data else 'Unknown',
                'has_resume': has_resume
            },
            'stats': {
                'total_analyses': total_analyses,
                'average_score': round(avg_score, 1),
                'best_score': best_score
            },
            'recent_analyses': formatted_analyses
        }
        
        return render_template('profile.html', **profile_data)
        
    except Exception as e:
        print(f"Profile error: {e}")
        flash('Error loading profile. Please try again.', 'error')
        return redirect(url_for('index'))

@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change user password"""
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validate inputs
        if not all([current_password, new_password, confirm_password]):
            flash('Please fill in all password fields', 'error')
            return redirect(url_for('auth.profile'))
        
        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return redirect(url_for('auth.profile'))
        
        # Validate new password strength
        is_valid, message = validate_password(new_password)
        if not is_valid:
            flash(message, 'error')
            return redirect(url_for('auth.profile'))
        
        try:
            db = DatabaseManager()
            
            # Verify current password
            if not db.verify_user(current_user.email, current_password):
                flash('Current password is incorrect', 'error')
                return redirect(url_for('auth.profile'))
            
            # Update password
            if db.update_user_password(current_user.id, new_password):
                flash('Password changed successfully!', 'success')
            else:
                flash('Failed to change password. Please try again.', 'error')
                
        except Exception as e:
            print(f"Password change error: {e}")
            flash('An error occurred while changing password. Please try again.', 'error')
    
    return redirect(url_for('auth.profile'))

@auth.route('/delete-account', methods=['POST'])
@login_required
def delete_account():
    """Delete user account (with confirmation)"""
    password = request.form.get('password', '')
    confirm_deletion = request.form.get('confirm_deletion') == 'DELETE'
    
    if not password:
        flash('Please enter your password to confirm account deletion', 'error')
        return redirect(url_for('auth.profile'))
    
    if not confirm_deletion:
        flash('Please type DELETE to confirm account deletion', 'error')
        return redirect(url_for('auth.profile'))
    
    try:
        db = DatabaseManager()
        
        # Verify password
        if not db.verify_user(current_user.email, password):
            flash('Incorrect password. Account deletion cancelled.', 'error')
            return redirect(url_for('auth.profile'))
        
        # Delete user account
        if db.deactivate_user(current_user.id):
            # Log account deletion
            print(f"Account deleted: {current_user.email} at {datetime.utcnow()}")
            
            # Logout user
            logout_user()
            session.clear()
            
            flash('Your account has been deleted successfully. We\'re sorry to see you go!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Failed to delete account. Please try again.', 'error')
            
    except Exception as e:
        print(f"Account deletion error: {e}")
        flash('An error occurred while deleting account. Please try again.', 'error')
    
    return redirect(url_for('auth.profile'))

# Additional utility functions for the auth system
def get_current_user_analyses(limit=10):
    """Get current user's analyses"""
    if not current_user.is_authenticated:
        return []
    
    try:
        db = DatabaseManager()
        all_analyses = db.get_all_analyses(limit=100)
        user_analyses = [
            analysis for analysis in all_analyses 
            if analysis.get('name', '').lower() == current_user.name.lower()
        ]
        return user_analyses[:limit]
    except:
        return []