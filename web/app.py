"""
File: app.py
Author: Jonathan Hu
Date Created: 6/12/25
Last Modified: 6/25/25
Description: Main Flask application server for the Resume Analyzer web application.
             Handles HTTP routes, file uploads, and coordinates between the AI analyzer,
             database, and PDF reader components to provide resume-job matching analysis.
Dependencies: Flask, werkzeug, ai_analyzer, database, pdf_reader, config
Routes:
    - GET  /           : Main page with analysis form
    - POST /analyze    : Process resume and job description
    - GET  /explanation: Retrieve detailed scoring explanation
    - GET  /history    : View all previous analyses
    - GET  /compare    : Compare candidates for specific positions
"""

"""
File: web/app.py
Author: Enhanced Authentication System
Date Created: 7/1/25
Description: Enhanced Flask application with complete authentication system,
             user management, and improved security features.
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_cors import CORS
from flask_login import LoginManager, login_required, current_user
import os
import tempfile
from datetime import datetime
from werkzeug.utils import secure_filename

# Import from core modules
from core.analyzer import ResumeAnalyzer
from core.database import DatabaseManager, User
from core.pdf_reader import PDFReader
from config import get_config

# Initialize global variables
ai_analyzer = None
db_manager = None
pdf_reader = None

def filter_by_search_term(jobs, search_term):
    """Filter jobs by search term"""
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
    """Create and configure Flask application with authentication"""
    global ai_analyzer, db_manager, pdf_reader
    
    app = Flask(__name__, template_folder='../templates')
    
    # Get configuration
    config = get_config()
    app.secret_key = config.SECRET_KEY
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()
    
    # Security settings
    app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
    # Setup CORS
    CORS(app)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        """Load user for Flask-Login"""
        return User.get(user_id)
    
    # Initialize components
    try:
        ai_analyzer = ResumeAnalyzer()
        db_manager = DatabaseManager()
        pdf_reader = PDFReader()
        print("✅ Application components initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing components: {e}")
        ai_analyzer = None
        db_manager = None
        pdf_reader = None

    # Register authentication blueprint
    from web.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)
    
    # Register additional routes
    from web.routes import additional_routes
    app.register_blueprint(additional_routes)

    # Main routes
    @app.route('/')
    def index():
        """Main page - accessible to everyone"""
        return render_template('index.html')
    
    @app.route('/analyze', methods=['POST'])
    def analyze():
        """Handle resume analysis - accessible to everyone"""
        if not all([ai_analyzer, db_manager, pdf_reader]):
            return jsonify({
                'success': False,
                'error': 'System not properly initialized. Please check configuration.'
            }), 500
        
        try:
            # Get form data
            name = request.form.get('name', '').strip()
            job_title = request.form.get('job_title', '').strip()
            company = request.form.get('company', '').strip()
            job_description = request.form.get('job_description', '').strip()
            
            print(f"📝 Form data received:")
            print(f"   Name: {name}")
            print(f"   Job Title: {job_title}")
            print(f"   Company: {company}")
            print(f"   Job Description length: {len(job_description)} chars")
            
            # Validate inputs
            if not all([name, job_title, company, job_description]):
                return jsonify({
                    'success': False,
                    'error': 'Please fill in all required fields'
                }), 400
            
            # Handle file upload
            if 'resume' not in request.files:
                return jsonify({
                    'success': False,
                    'error': 'No resume file uploaded'
                }), 400
            
            file = request.files['resume']
            if file.filename == '' or not file.filename.lower().endswith('.pdf'):
                return jsonify({
                    'success': False,
                    'error': 'Please upload a PDF file'
                }), 400
            
            print(f"📄 File received: {file.filename}")
            
            # Capture original PDF content
            file.seek(0)
            original_pdf_content = file.read()
            file.seek(0)
            
            # Save uploaded file temporarily
            filename = secure_filename(file.filename)
            temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(temp_path)
            
            print(f"💾 File saved to: {temp_path}")
            
            try:
                # Extract text from resume
                print("📖 Extracting text from PDF...")
                resume_text = pdf_reader.extract_text_from_pdf(temp_path)
                
                if resume_text.startswith("Error"):
                    print(f"❌ PDF extraction failed: {resume_text}")
                    return jsonify({
                        'success': False,
                        'error': resume_text
                    }), 400
                
                print(f"✅ Text extracted successfully, length: {len(resume_text)} chars")
                print(f"📝 First 200 chars: {resume_text[:200]}...")
                
                # Use fast concurrent extraction
                print("🔍 Starting AI analysis...")
                analysis_result = ai_analyzer.analyze_resume_job_match_fast(resume_text, job_description)
                
                print(f"📊 Analysis result type: {type(analysis_result)}")
                print(f"📊 Analysis result: {analysis_result}")
                
                # Check if analysis_result is None
                if analysis_result is None:
                    print("❌ Analysis returned None")
                    return jsonify({
                        'success': False,
                        'error': 'Analysis returned no results. Please check the AI analyzer configuration.'
                    }), 500
                
                # Check if analysis_result is a dictionary and has error
                if isinstance(analysis_result, dict) and "error" in analysis_result:
                    print(f"❌ Analysis returned error: {analysis_result['error']}")
                    return jsonify({
                        'success': False,
                        'error': f'Analysis failed: {analysis_result["error"]}'
                    }), 500
                
                # Initialize default values
                match_score = 0
                resume_data = {}
                job_requirements = {}
                explanation = ""
                
                # Handle different possible response structures
                if isinstance(analysis_result, dict):
                    print("📋 Analysis result is a dictionary with keys:", list(analysis_result.keys()))
                    
                    # Try to extract match score from various possible keys
                    if "compatibility_score" in analysis_result:
                        match_score = analysis_result["compatibility_score"]
                    elif "match_score" in analysis_result:
                        match_score = analysis_result["match_score"]
                    elif "score" in analysis_result:
                        match_score = analysis_result["score"]
                    else:
                        print("⚠️ No recognizable score field found in dict")
                    
                    # Extract other data with fallbacks
                    resume_data = analysis_result.get("resume_data", {})
                    job_requirements = analysis_result.get("job_requirements", {})
                    explanation = analysis_result.get("detailed_explanation", "")
                    
                    # If no structured explanation, try to use the whole result as explanation
                    if not explanation:
                        explanation = str(analysis_result)
                        
                elif isinstance(analysis_result, str):
                    # If analysis_result is a string (the detailed explanation)
                    print("📋 Analysis result is a string, treating as explanation")
                    explanation = analysis_result
                    
                    # Try to extract score from the explanation text
                    import re
                    score_patterns = [
                        r'FINAL COMPATIBILITY SCORE:\s*(\d+)/100',
                        r'FINAL SCORE:\s*(\d+)/100',
                        r'SCORE:\s*(\d+)/100',
                        r'Score:\s*(\d+)',
                        r'(\d+)/100'
                    ]
                    
                    for pattern in score_patterns:
                        match = re.search(pattern, explanation)
                        if match:
                            match_score = int(match.group(1))
                            print(f"✅ Extracted score from text: {match_score}")
                            break
                    
                    if match_score == 0:
                        print("⚠️ Could not extract score from explanation text")
                        
                else:
                    # Handle other types
                    print(f"⚠️ Analysis result is unexpected type: {type(analysis_result)}")
                    explanation = str(analysis_result)
                
                print(f"✅ Final extracted values:")
                print(f"   Score: {match_score}")
                print(f"   Resume data: {type(resume_data)} with {len(resume_data) if isinstance(resume_data, dict) else 0} keys")
                print(f"   Job requirements: {type(job_requirements)} with {len(job_requirements) if isinstance(job_requirements, dict) else 0} keys")
                print(f"   Explanation length: {len(explanation)} chars")
                
                # Save to database with original PDF content
                print("💾 Saving to database...")
                original_resume_data = {
                    'filename': filename,
                    'content': original_pdf_content,
                    'content_type': 'application/pdf',
                    'extracted_text': resume_text
                }
                
                try:
                    db_manager.save_analysis(
                        name, resume_data, job_requirements, match_score,
                        explanation, job_title, company,
                        original_resume=original_resume_data
                    )
                    print("✅ Saved to database successfully")
                except Exception as db_error:
                    print(f"⚠️ Database save failed: {db_error}")
                    # Continue anyway, don't fail the whole request
                
                # Store in session for explanation view
                session['last_analysis'] = {
                    'name': name,
                    'job_title': job_title,
                    'company': company,
                    'explanation': explanation
                }
                
                # Prepare response
                response_data = {
                    'success': True,
                    'result': {
                        'name': name,
                        'job_title': job_title,
                        'company': company,
                        'match_score': match_score,
                        'resume_data': resume_data,
                        'job_requirements': job_requirements,
                        'explanation': explanation
                    }
                }
                
                print("✅ Analysis completed successfully")
                print(f"📤 Sending response with score: {match_score}")
                
                return jsonify(response_data)
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    print(f"🗑️ Cleaned up temp file: {temp_path}")
                    
        except Exception as e:
            print(f"❌ CRITICAL ERROR in analyze route: {e}")
            print(f"❌ Error type: {type(e)}")
            import traceback
            print(f"❌ Full traceback:\n{traceback.format_exc()}")
            
            return jsonify({
                'success': False,
                'error': f'Analysis failed: {str(e)}'
            }), 500
    
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
    
    @app.route('/jobs')
    def show_jobs():
        """Display job listings"""
        if not db_manager:
            return jsonify({
                'success': False, 
                'error': 'Database not initialized'
            }), 500

        search_query = request.args.get('search', '').strip()

        try:
            all_jobs = db_manager.get_all_jobs()
            filtered_jobs = filter_by_search_term(all_jobs, search_query)
            return render_template('jobs.html', jobs=filtered_jobs, search=search_query)

        except Exception as e:
            return jsonify({
                'success': False, 
                'error': f'Failed to retrieve jobs: {str(e)}'
            }), 500
    
    # Protected routes (require authentication)
    @app.route('/dashboard')
    @login_required
    def dashboard():
        """User dashboard - requires login"""
        try:
            # Get user statistics
            user_stats = db_manager.get_user_stats(current_user.id)
            
            if not user_stats:
                user_stats = {
                    "total_analyses": 0,
                    "average_score": 0,
                    "best_score": 0,
                    "recent_analyses": []
                }
            
            # Format user data for template
            user_data = {
                'name': current_user.name,
                'email': current_user.email,
                'member_since': current_user.created_at.strftime('%B %Y'),
                'has_resume': current_user.has_resume
            }
            
            # Format recent analyses
            formatted_analyses = []
            for analysis in user_stats.get('recent_analyses', []):
                formatted_analyses.append({
                    'job_title': analysis.get('job_title', 'N/A'),
                    'company': analysis.get('company', 'N/A'),
                    'match_score': analysis.get('match_score', 0),
                    'timestamp': analysis.get('timestamp', datetime.utcnow()).strftime('%Y-%m-%d %H:%M')
                })
            
            return render_template('profile.html', 
                                 user=user_data,
                                 stats=user_stats,
                                 recent_analyses=formatted_analyses)
            
        except Exception as e:
            print(f"Dashboard error: {e}")
            flash('Error loading dashboard. Please try again.', 'error')
            return redirect(url_for('index'))
    
    @app.route('/download_resume/<user_id>')
    @login_required
    def download_resume(user_id):
        """Download original resume file - requires login"""
        # Security check: users can only download their own resumes
        if current_user.id != user_id and not current_user.is_admin:
            flash('You can only download your own resume.', 'error')
            return redirect(url_for('auth.profile'))
        
        if not db_manager:
            return jsonify({
                'success': False,
                'error': 'Database not initialized'
            }), 500
        
        try:
            original_resume = db_manager.get_original_resume(user_id)
            if not original_resume:
                flash('Resume not found.', 'error')
                return redirect(url_for('auth.profile'))
            
            from flask import make_response
            response = make_response(original_resume['content'])
            response.headers['Content-Type'] = original_resume.get('content_type', 'application/pdf')
            response.headers['Content-Disposition'] = f'attachment; filename="{original_resume.get("filename", "resume.pdf")}"'
            return response
            
        except Exception as e:
            flash(f'Failed to download resume: {str(e)}', 'error')
            return redirect(url_for('auth.profile'))
    
    @app.route('/users_with_resumes')
    @login_required
    def get_users_with_resumes():
        """Get all users that have resumes - admin only"""
        # This could be restricted to admin users only
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
    
    # Error handlers
    @app.errorhandler(413)
    def too_large(e):
        """Handle file upload size errors"""
        return jsonify({
            'success': False,
            'error': 'File too large. Maximum size is 16MB.'
        }), 413
    
    @app.errorhandler(404)
    def not_found(e):
        """Handle 404 errors"""
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(e):
        """Handle 500 errors"""
        return render_template('500.html'), 500
    
    # Context processors for templates
    @app.context_processor
    def inject_user():
        """Make current_user available in all templates"""
        return dict(current_user=current_user)
    
    @app.context_processor
    def inject_app_info():
        """Inject application information into templates"""
        return dict(
            app_name="Resume Analyzer",
            app_version="2.0.0"
        )
    
    # Before request handlers
    @app.before_request
    def security_headers():
        """Add security headers to responses"""
        pass  # Headers will be added in after_request
    
    @app.after_request
    def after_request(response):
        """Add security headers to all responses"""
        # Security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Cache control for static files
        if request.endpoint and 'static' in request.endpoint:
            response.headers['Cache-Control'] = 'public, max-age=31536000'
        
        return response
    
    # CLI commands for development
    @app.cli.command()
    def init_db():
        """Initialize the database with indexes"""
        try:
            db = DatabaseManager()
            db._create_indexes()
            print("✅ Database initialized successfully")
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
    
    @app.cli.command()
    def create_admin():
        """Create an admin user"""
        try:
            db = DatabaseManager()
            
            name = input("Enter admin name: ")
            email = input("Enter admin email: ")
            password = input("Enter admin password: ")
            
            user_id = db.create_user(name, email, password)
            if user_id:
                print(f"✅ Admin user created successfully: {email}")
            else:
                print("❌ Failed to create admin user")
                
        except Exception as e:
            print(f"❌ Error creating admin user: {e}")
    
    # Development routes (only in debug mode)
    if app.debug:
        @app.route('/debug/session')
        def debug_session():
            """Debug route to view session data"""
            return jsonify(dict(session))
        
        @app.route('/debug/user')
        def debug_user():
            """Debug route to view current user data"""
            if current_user.is_authenticated:
                return jsonify({
                    'authenticated': True,
                    'user_id': current_user.id,
                    'email': current_user.email,
                    'name': current_user.name
                })
            else:
                return jsonify({'authenticated': False})
    
    print("🚀 Enhanced Resume Analyzer with Authentication initialized")
    return app

# Application factory pattern
def run_app():
    """Run the application"""
    app = create_app()
    
    print("Starting Enhanced Resume Analyzer Web Interface...")
    print("Features:")
    print("  ✅ User Registration & Login")
    print("  ✅ Password Encryption")
    print("  ✅ Session Management")
    print("  ✅ User Profiles & Analytics")
    print("  ✅ Resume Analysis")
    print("  ✅ Security Headers")
    print("  ✅ Error Handling")
    print("")
    print("Access at: http://localhost:5000")
    print("  - Home: http://localhost:5000/")
    print("  - Login: http://localhost:5000/auth/login")
    print("  - Register: http://localhost:5000/auth/signup")
    print("")
    
    app.run(debug=True, port=5000)

if __name__ == '__main__':
    run_app()