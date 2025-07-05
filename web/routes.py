"""
File: routes.py
Author: Jonathan Hu
Date Created: 6/15/25
Last Modified: 6/15/25
Description: Additional Routes Module for future expansion of web functionality
"""

from flask import Blueprint, jsonify, render_template
from flask_login import login_required, current_user
from core.database import DatabaseManager

# Create blueprint for profile and extra routes
profile_routes = Blueprint('profile_routes', __name__)

@profile_routes.route('/api/status')
def api_status():
    """API status endpoint"""
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'service': 'Resume Analyzer API'
    })

@profile_routes.route('/api/stats')
def api_stats():
    """Basic statistics endpoint - for future implementation"""
    return jsonify({
        'total_analyses': 0,  # TODO: Implement actual stats
        'active_users': 0,
        'message': 'Stats endpoint - coming soon'
    })

@profile_routes.route('/profile')
@login_required
def profile():
    """User profile page showing account info and analysis history"""
    db = DatabaseManager()
    
    # Get user's analysis history
    user_analyses = db.get_user_analyses(current_user.id)
    
    # Get user's resume status
    user_data = db.get_user_by_id(current_user.id)
    has_resume = user_data.get('resume_data') is not None if user_data else False
    
    return render_template('profile.html', 
                         user=current_user, 
                         reports=user_analyses,
                         has_resume=has_resume)

# Register this blueprint in your main app with:
# app.register_blueprint(profile_routes, url_prefix='/profile')


"""
File: routes.py
Author: Lavin Ma
Date Created: 6/24/25
Last Modified: 6/24/25
Description:
Contains additional frontend routes for the ResumeMatchAI web app.

Includes:
- User Profile Page Route: Renders the user profile page with their info and analysis reports (using dummy information rn).
"""

from flask import render_template  # Make sure this is at the top with other imports

# Add this new route to render the user profile page
@profile_routes.route('/profile')
def user_profile():
    # Dummy user data for testing
    user = {
        "name": "Lavin Ma",
        "email": "lavin@example.com",
        "resume_data": True  # Change to False to test no resume case
    }

    # Dummy report data for testing
    reports = [
        {
            "job_title": "Software Engineer",
            "company": "Tech Corp",
            "match_score": 87,
            "timestamp": "2025-06-20"
        },
        {
            "job_title": "Data Analyst",
            "company": "Data Inc",
            "match_score": 79,
            "timestamp": "2025-06-10"
        }
    ]

    return render_template('profile.html', user=user, reports=reports)
