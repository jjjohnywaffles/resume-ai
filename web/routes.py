"""
File: routes.py
Author: Jonathan Hu
Date Created: 6/15/25
Last Modified: 7/5/25
Description: Profile and API Routes Module for ResumeMatchAI web application

This module contains Flask routes for user profile management and API endpoints.
It extends the main web application with additional functionality for authenticated users.

Routes Included:
- /profile: User profile page displaying account info, resume status, and analysis history
- /profile/update_resume: Handles resume upload/update for user profiles
- /api/status: Health check endpoint for API status
- /api/stats: Statistics endpoint (placeholder for future implementation)

Key Features:
- Resume filename display on profile page
- Secure file upload handling with temporary file cleanup
- AI-powered resume data extraction and storage
- User authentication required for profile routes
- Flash message feedback for user actions

Dependencies:
- Flask Blueprint for modular routing
- Flask-Login for authentication
- Core modules: DatabaseManager, PDFReader, ResumeAnalyzer
- Werkzeug for secure filename handling

Usage:
Register this blueprint in the main Flask app with:
app.register_blueprint(profile_routes, url_prefix='/profile')
"""

from flask import Blueprint, jsonify, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from core.database import DatabaseManager
from core.pdf_reader import PDFReader
from core.analyzer import ResumeAnalyzer
from werkzeug.utils import secure_filename
import os
import tempfile

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
    
    # Get user's resume status and filename
    user_data = db.get_user_by_id(current_user.id)
    has_resume = user_data.get('resume_data') is not None if user_data else False
    
    # Extract resume filename if available
    resume_filename = None
    if has_resume and user_data.get('resume_data', {}).get('original_format'):
        original_format = user_data['resume_data']['original_format']
        if isinstance(original_format, dict) and 'filename' in original_format:
            resume_filename = original_format['filename']
    
    return render_template('profile.html', 
                         user=current_user, 
                         reports=user_analyses,
                         has_resume=has_resume,
                         resume_filename=resume_filename)

@profile_routes.route('/profile/update_resume', methods=['POST'])
@login_required
def update_resume():
    """Handle resume upload/update for user profile"""
    temp_path = None  # Initialize temp_path to None
    
    if 'resume' not in request.files:
        flash('No resume file uploaded', 'error')
        return redirect(url_for('profile_routes.profile'))
    
    file = request.files['resume']
    if not file or file.filename == '' or not file.filename.lower().endswith('.pdf'):
        flash('Please upload a PDF file', 'error')
        return redirect(url_for('profile_routes.profile'))
    
    try:
        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        temp_path = os.path.join(tempfile.gettempdir(), filename)
        file.save(temp_path)
        
        # Extract text from resume
        pdf_reader = PDFReader()
        resume_text = pdf_reader.extract_text_from_pdf(temp_path)
        
        if resume_text.startswith("Error"):
            flash(f'Error processing PDF: {resume_text}', 'error')
            return redirect(url_for('profile_routes.profile'))
        
        # Extract resume data using AI
        ai_analyzer = ResumeAnalyzer()
        resume_data = ai_analyzer.extract_resume_data(resume_text)
        
        if "error" in resume_data:
            flash(f'Error analyzing resume: {resume_data["error"]}', 'error')
            return redirect(url_for('profile_routes.profile'))
        
        # Save to database
        db = DatabaseManager()
        original_resume_data = {
            'filename': filename,
            'content': file.read(),
            'content_type': 'application/pdf',
            'extracted_text': resume_text
        }
        
        # Update user's resume data
        success = db.update_user_resume(current_user.id, resume_data, original_resume_data)
        
        if success:
            flash('Resume updated successfully!', 'success')
        else:
            flash('Error updating resume', 'error')
            
    except Exception as e:
        flash(f'Error processing resume: {str(e)}', 'error')
    finally:
        # Clean up temporary file if it exists
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as cleanup_error:
                print(f"Warning: Could not clean up temporary file {temp_path}: {cleanup_error}")
    
    return redirect(url_for('profile_routes.profile'))
