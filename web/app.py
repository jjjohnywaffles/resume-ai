"""
File: app.py
Author: Jonathan Hu
Date Created: 6/12/25
Last Modified: 7/5/25
Description: Main Flask Application Server for ResumeMatchAI Web Application

This is the core Flask application that serves as the web server for the ResumeMatchAI
platform. It handles all HTTP routes, coordinates between different components,
and provides the main API endpoints for resume analysis functionality.

Key Features:
- Resume analysis with AI-powered matching
- User authentication and profile management
- File upload handling with security measures
- Database integration for storing analyses and user data
- PDF text extraction and processing
- Real-time analysis results with detailed explanations
- Analysis history and comparison features
- Job listings and search functionality

Core Components:
- AI Analyzer: Processes resumes and job descriptions using OpenAI API
- Database Manager: Handles MongoDB operations for data persistence
- PDF Reader: Extracts text content from uploaded PDF files
- Authentication System: User registration, login, and session management

HTTP Routes:
- GET  /                    : Main analysis page with form interface
- POST /analyze            : Standard resume analysis endpoint
- POST /analyze_fast       : Optimized fast analysis endpoint
- GET  /explanation        : Retrieve detailed scoring explanations
- GET  /history            : View all previous analyses
- GET  /compare/<job>/<company> : Compare candidates for specific positions
- GET  /download_resume/<user_id> : Download user resume files
- GET  /jobs               : Browse available job listings
- GET  /users_with_resumes : Admin endpoint for user management

Authentication Routes (via auth blueprint):
- GET/POST /login          : User login interface
- GET/POST /signup         : User registration interface
- GET  /logout             : User logout functionality

Profile Routes (via profile_routes blueprint):
- GET  /profile            : User profile page
- POST /profile/update_resume : Resume upload/update functionality
- GET  /api/status         : API health check endpoint
- GET  /api/stats          : Statistics endpoint (placeholder)

Security Features:
- File upload validation and sanitization
- Secure filename handling with werkzeug
- Maximum file size limits (16MB)
- CORS configuration for cross-origin requests
- User authentication and session management
- Input validation and error handling

Configuration:
- Environment-based configuration via config.py
- Secret key management for session security
- Temporary file handling for uploads
- Database connection management
- API key management for AI services

Dependencies:
- Flask: Web framework
- Flask-Login: User authentication
- Flask-CORS: Cross-origin resource sharing
- Werkzeug: File upload utilities
- Core modules: analyzer, database, pdf_reader
- Configuration: config.py for settings

Error Handling:
- 413 error handler for large file uploads
- Comprehensive exception handling in routes
- User-friendly error messages
- Graceful degradation when components fail

Usage:
This application is the main entry point for the ResumeMatchAI web service.
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import os
import tempfile
from datetime import datetime
from werkzeug.utils import secure_filename

# Import from core modules (clean imports)
from core.analyzer import ResumeAnalyzer
from core.database import DatabaseManager, User
from core.pdf_reader import PDFReader
from config import get_config
from flask_login import LoginManager, login_required, current_user

from .auth import auth as auth_blueprint
from web.routes import profile_routes  # updated import

ai_analyzer = None
db_manager = None
pdf_reader = None # just added 

def filter_by_search_term(jobs, search_term):
    if not search_term:
        return jobs
    search_term = search_term.lower()
    filtered = []

    for job in jobs:
        title = job.get("title", "").lower()
        description = job.get("description", "").lower()

        if search_term in title or search_term in description:
            filtered.append(job)
    return filtered

def create_app():
    global ai_analyzer, db_manager, pdf_reader
    """Create and configure Flask application"""
    app = Flask(__name__, template_folder='../templates')
    
    # Get configuration
    config = get_config()
    app.secret_key = config.SECRET_KEY
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()
    
    # Setup CORS
    CORS(app)
    
    # Initialize components
    try:
        ai_analyzer = ResumeAnalyzer()
        print("Using real ResumeAnalyzer with API keys")
    except Exception as e:
        print(f"Error initializing ResumeAnalyzer: {e}")
        ai_analyzer = None
    try:
        db_manager = DatabaseManager()
        pdf_reader = PDFReader()
        print("Database and PDF reader initialized successfully")
    except Exception as e:
        print(f"Error initializing database or PDF reader: {e}")
        db_manager = None
        pdf_reader = None
    

    # Flask-Login setup
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.get(user_id)

    # Register blueprints
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(profile_routes)


    @app.route('/')
    def index():
        """Main page - analyzer accessible to everyone"""
        has_resume = False
        if current_user.is_authenticated:
            db = DatabaseManager()
            user_data = db.get_user_by_id(current_user.id)
            has_resume = user_data.get('resume_data') is not None if user_data else False
        
        return render_template('index.html', has_resume=has_resume)
    
    @app.route('/analyze', methods=['POST'])
    def analyze():
        """Handle resume analysis - works for both authenticated and guest users"""
        if not all([ai_analyzer, db_manager, pdf_reader]):
            return jsonify({
                'success': False,
                'error': 'System not properly initialized. Please check configuration.'
            }), 500
        
        temp_path = None  # Initialize temp_path to None
        
        try:
            # Get form data - use current user's name if authenticated, otherwise use provided name
            name = request.form.get('name', '').strip()
            if not name:
                if current_user.is_authenticated:
                    name = current_user.name
                else:
                    name = "Guest User"
            
            job_title = request.form.get('job_title', '').strip()
            company = request.form.get('company', '').strip()
            job_description = request.form.get('job_description', '').strip()
            
            # Validate inputs
            if not all([name, job_title, company, job_description]):
                return jsonify({
                    'success': False,
                    'error': 'Please fill in all required fields'
                }), 400
            
            # Handle resume input (file upload or saved resume)
            resume_option = request.form.get('resume_option', 'upload')
            
            if resume_option == 'saved' and current_user.is_authenticated:
                # Use saved resume
                user_data = db_manager.get_user_by_id(current_user.id)
                if not user_data or not user_data.get('resume_data'):
                    return jsonify({
                        'success': False,
                        'error': 'No saved resume found. Please upload a resume first.'
                    }), 400
                
                # Get saved resume data
                saved_resume = user_data['resume_data']
                resume_text = saved_resume.get('original_format', {}).get('extracted_text', '')
                filename = saved_resume.get('original_format', {}).get('filename', 'saved_resume.pdf')
                original_pdf_content = saved_resume.get('original_format', {}).get('content', b'')
                
                if not resume_text:
                    return jsonify({
                        'success': False,
                        'error': 'Saved resume text not found. Please upload a new resume.'
                    }), 400
            else:
                # Handle file upload
                if 'resume' not in request.files:
                    return jsonify({
                        'success': False,
                        'error': 'No resume file uploaded'
                    }), 400
                
                file = request.files['resume']
                if not file or file.filename == '' or not file.filename.lower().endswith('.pdf'):
                    return jsonify({
                        'success': False,
                        'error': 'Please upload a PDF file'
                    }), 400
                
                # CAPTURE ORIGINAL PDF CONTENT
                file.seek(0)  # Ensure we're at the start of the file
                original_pdf_content = file.read()  # Read the binary content
                file.seek(0)  # Reset for saving to disk
                
                # Save uploaded file temporarily
                filename = secure_filename(file.filename)
                temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(temp_path)
            
            # Extract text from resume (use temp_path only if it exists)
            if temp_path:
                resume_text = pdf_reader.extract_text_from_pdf(temp_path)
            else:
                # For saved resumes, we already have the text
                resume_text = resume_text  # This is already extracted from saved_resume
            
            if resume_text.startswith("Error"):
                return jsonify({
                    'success': False,
                    'error': resume_text
                }), 400
            
            # UPDATED: Use concurrent extraction for speed improvement
            extraction_result = ai_analyzer.extract_data_concurrent(resume_text, job_description)
            
            # Check for extraction errors
            if "error" in extraction_result:
                return jsonify({
                    'success': False,
                    'error': f'Data extraction failed: {extraction_result["error"]}'
                }), 500
            
            # Extract the structured data from concurrent result
            resume_data = extraction_result["resume_data"]
            job_requirements = extraction_result["job_requirements"]
            
            # Get detailed explanation and score
            explanation_result = ai_analyzer.explain_match_score(resume_data, job_requirements)
            match_score = explanation_result["score"]
            explanation = explanation_result["explanation"]
            
            # Save to database WITH ORIGINAL PDF CONTENT
            original_resume_data = {
                'filename': filename,
                'content': original_pdf_content,
                'content_type': 'application/pdf',
                'extracted_text': resume_text
            }
            
            # Save analysis - only save user_id if authenticated
            user_id = current_user.id if current_user.is_authenticated else None
            db_manager.save_analysis(
                name, resume_data, job_requirements, match_score,
                explanation, job_title, company, 
                original_resume=original_resume_data,
                user_id=user_id
            )
            
            # Store in session for explanation view
            session['last_analysis'] = {
                'name': name,
                'job_title': job_title,
                'company': company,
                'explanation': explanation
            }
            
            return jsonify({
                'success': True,
                'result': {
                    'name': name,
                    'job_title': job_title,
                    'company': company,
                    'match_score': match_score,
                    'resume_data': resume_data,
                    'job_requirements': job_requirements
                }
            })
                
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Analysis failed: {str(e)}'
            }), 500
        finally:
            # Clean up temporary file if it exists
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception as cleanup_error:
                    print(f"Warning: Could not clean up temporary file {temp_path}: {cleanup_error}")
    
    @app.route('/analyze_fast', methods=['POST'])
    def analyze_fast():
        """Handle resume analysis using the new optimized method"""
        if not all([ai_analyzer, db_manager, pdf_reader]):
            return jsonify({
                'success': False,
                'error': 'System not properly initialized. Please check configuration.'
            }), 500
        
        temp_path = None  # Initialize temp_path to None
        
        try:
            # Get form data
            name = request.form.get('name', '').strip()
            job_title = request.form.get('job_title', '').strip()
            company = request.form.get('company', '').strip()
            job_description = request.form.get('job_description', '').strip()
            
            # Validate inputs
            if not all([name, job_title, company, job_description]):
                return jsonify({
                    'success': False,
                    'error': 'Please fill in all required fields'
                }), 400
            
            # Handle resume input (file upload or saved resume)
            resume_option = request.form.get('resume_option', 'upload')
            
            if resume_option == 'saved' and current_user.is_authenticated:
                # Use saved resume
                user_data = db_manager.get_user_by_id(current_user.id)
                if not user_data or not user_data.get('resume_data'):
                    return jsonify({
                        'success': False,
                        'error': 'No saved resume found. Please upload a resume first.'
                    }), 400
                
                # Get saved resume data
                saved_resume = user_data['resume_data']
                resume_text = saved_resume.get('original_format', {}).get('extracted_text', '')
                filename = saved_resume.get('original_format', {}).get('filename', 'saved_resume.pdf')
                original_pdf_content = saved_resume.get('original_format', {}).get('content', b'')
                
                if not resume_text:
                    return jsonify({
                        'success': False,
                        'error': 'Saved resume text not found. Please upload a new resume.'
                    }), 400
            else:
                # Handle file upload
                if 'resume' not in request.files:
                    return jsonify({
                        'success': False,
                        'error': 'No resume file uploaded'
                    }), 400
                
                file = request.files['resume']
                if not file or file.filename == '' or not file.filename.lower().endswith('.pdf'):
                    return jsonify({
                        'success': False,
                        'error': 'Please upload a PDF file'
                    }), 400
                
                # CAPTURE ORIGINAL PDF CONTENT
                file.seek(0)  # Ensure we're at the start of the file
                original_pdf_content = file.read()  # Read the binary content
                file.seek(0)  # Reset for saving to disk
                
                # Save uploaded file temporarily
                filename = secure_filename(file.filename)
                temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(temp_path)
                
                # Extract text from resume
                resume_text = pdf_reader.extract_text_from_pdf(temp_path)
                
                if resume_text.startswith("Error"):
                    return jsonify({
                        'success': False,
                        'error': resume_text
                    }), 400
            
            # NEW: Use the complete fast analysis workflow
            analysis_result = ai_analyzer.analyze_resume_job_match_fast(resume_text, job_description)
            
            # Check for analysis errors
            if "error" in analysis_result:
                return jsonify({
                    'success': False,
                    'error': f'Analysis failed: {analysis_result["error"]}'
                }), 500
            
            # Extract results
            resume_data = analysis_result["resume_data"]
            job_requirements = analysis_result["job_requirements"]
            match_score = analysis_result["compatibility_score"]
            explanation = analysis_result["detailed_explanation"]
            
            # Save to database WITH ORIGINAL PDF CONTENT
            original_resume_data = {
                'filename': filename,
                'content': original_pdf_content,
                'content_type': 'application/pdf',
                'extracted_text': resume_text
            }
            
            # Save analysis - only save user_id if authenticated
            user_id = current_user.id if current_user.is_authenticated else None
            db_manager.save_analysis(
                name, resume_data, job_requirements, match_score,
                explanation, job_title, company,
                original_resume=original_resume_data,
                user_id=user_id
            )
            
            # Store in session for explanation view
            session['last_analysis'] = {
                'name': name,
                'job_title': job_title,
                'company': company,
                'explanation': explanation
            }
            
            return jsonify({
                'success': True,
                'result': {
                    'name': name,
                    'job_title': job_title,
                    'company': company,
                    'match_score': match_score,
                    'resume_data': resume_data,
                    'job_requirements': job_requirements
                }
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Analysis failed: {str(e)}'
            }), 500
        finally:
            # Clean up temporary file if it exists
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception as cleanup_error:
                    print(f"Warning: Could not clean up temporary file {temp_path}: {cleanup_error}")
    
    @app.route('/explanation')
    def get_explanation():
        """Get detailed explanation for last analysis"""
        last_analysis = session.get('last_analysis')
        if not last_analysis:
            return jsonify({
                'success': False,
                'error': 'No analysis available. Please run an analysis first.'
            }), 404
        
        return jsonify({
            'success': True,
            'explanation': last_analysis['explanation'],
            'name': last_analysis['name'],
            'job_title': last_analysis['job_title'],
            'company': last_analysis['company']
        })
    
    @app.route('/history')
    def history():
        """Get analysis history"""
        if not db_manager:
            return jsonify({
                'success': False,
                'error': 'Database not initialized'
            }), 500
        
        try:
            analyses = db_manager.get_all_analyses()
            
            # Format analyses for display
            formatted_analyses = []
            for analysis in analyses:
                formatted_analyses.append({
                    'name': analysis.get('name', ''),
                    'job_title': analysis.get('job_title', 'N/A'),
                    'company': analysis.get('company', 'N/A'),
                    'match_score': analysis.get('match_score', 0),
                    'timestamp': analysis.get('timestamp', datetime.utcnow()).strftime('%Y-%m-%d %H:%M')
                })
            
            # Sort by timestamp (newest first)
            formatted_analyses.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return jsonify({
                'success': True,
                'analyses': formatted_analyses
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Failed to retrieve history: {str(e)}'
            }), 500
    
    @app.route('/compare/<job_title>/<company>')
    def compare_candidates(job_title, company):
        """Compare candidates for a specific position"""
        if not db_manager:
            return jsonify({
                'success': False,
                'error': 'Database not initialized'
            }), 500
        
        try:
            candidates = db_manager.compare_candidates_for_position(job_title, company, 10)
            return jsonify({
                'success': True,
                'candidates': candidates
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Failed to compare candidates: {str(e)}'
            }), 500
    
    # ROUTES FOR RESUME MANAGEMENT
    @app.route('/download_resume/<user_id>')
    def download_resume(user_id):
        """Download original resume file"""
        if not db_manager:
            return jsonify({
                'success': False,
                'error': 'Database not initialized'
            }), 500
        
        try:
            original_resume = db_manager.get_original_resume(user_id)
            if not original_resume:
                return jsonify({
                    'success': False,
                    'error': 'Resume not found'
                }), 404
            
            from flask import make_response
            response = make_response(original_resume['content'])
            response.headers['Content-Type'] = original_resume.get('content_type', 'application/pdf')
            response.headers['Content-Disposition'] = f'attachment; filename="{original_resume.get("filename", "resume.pdf")}"'
            return response
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Failed to download resume: {str(e)}'
            }), 500
    
    @app.route('/jobs')
    def show_jobs():
        if not db_manager:
            return jsonify({'success': False, 
                            'error': 'Database not initialized'
                            }), 500

        search_query = request.args.get('search', '').strip()

        try:
            all_jobs = db_manager.get_all_jobs()
            filtered_jobs = filter_by_search_term(all_jobs, search_query)
            return render_template('jobs.html', jobs=filtered_jobs, search=search_query)

        except Exception as e:
            return jsonify({'success': False, 
                            'error': f'Failed to retrieve jobs: {str(e)}'}), 
            500

    @app.route('/users_with_resumes')
    def get_users_with_resumes():
        """Get all users that have resumes"""
        if not db_manager:
            return jsonify({
                'success': False,
                'error': 'Database not initialized'
            }), 500
        
        try:
            users = db_manager.get_all_users_with_resumes()
            
            # Format for display
            formatted_users = []
            for user in users:
                resume_data = user.get('resume_data', {})
                formatted_users.append({
                    'user_id': str(user['_id']),
                    'name': user.get('name', ''),
                    'has_original_resume': 'original_format' in resume_data,
                    'filename': resume_data.get('original_format', {}).get('filename', 'N/A') if isinstance(resume_data.get('original_format'), dict) else 'N/A',
                    'upload_date': resume_data.get('upload_timestamp', user.get('created_at', datetime.utcnow())).strftime('%Y-%m-%d %H:%M'),
                    'created_at': user.get('created_at', datetime.utcnow()).strftime('%Y-%m-%d %H:%M')
                })
            
            return jsonify({
                'success': True,
                'users': formatted_users
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Failed to retrieve users: {str(e)}'
            }), 500
    
    @app.errorhandler(413)
    def too_large(e):
        """Handle file upload size errors"""
        return jsonify({
            'success': False,
            'error': 'File too large. Maximum size is 16MB.'
        }), 413
    
    return app

if __name__ == '__main__':
    app = create_app()
    print("Starting Resume Analyzer Web Interface...")
    print("Access at: http://localhost:5000")
    app.run(debug=True, port=5000)