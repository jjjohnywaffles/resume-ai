"""
File: app.py
Author: Jonathan Hu
Date Created: 6/12/25
Last Modified: 6/24/25
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

from flask import Flask, render_template, request, jsonify, session
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
from flask import Flask
from flask_login import LoginManager

from .auth import auth as auth_blueprint 

def create_app():
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
        print("DEBUG: Initializing application components...")
        ai_analyzer = ResumeAnalyzer()
        print("DEBUG: AI Analyzer initialized successfully")
        
        db_manager = DatabaseManager()
        print("DEBUG: Database Manager initialized successfully")
        
        pdf_reader = PDFReader()
        print("DEBUG: PDF Reader initialized successfully")
        
        print("DEBUG: All application components initialized successfully")
    except Exception as e:
        print(f"ERROR: Error initializing components: {e}")
        import traceback
        traceback.print_exc()
        ai_analyzer = None
        db_manager = None
        pdf_reader = None
    

    # Flask-Login setup
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.get(user_id)

    app.register_blueprint(auth_blueprint)


    @app.route('/')
    def index():
        """Main page"""
        print("DEBUG: Serving main page")
        return render_template('index.html')
    
    @app.route('/analyze', methods=['POST'])
    def analyze():
        """Handle resume analysis"""
        print("DEBUG: === Starting resume analysis ===")
        
        if not all([ai_analyzer, db_manager, pdf_reader]):
            print("ERROR: System components not properly initialized")
            print(f"DEBUG: ai_analyzer: {ai_analyzer is not None}")
            print(f"DEBUG: db_manager: {db_manager is not None}")
            print(f"DEBUG: pdf_reader: {pdf_reader is not None}")
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
            
            print(f"DEBUG: Received form data:")
            print(f"DEBUG:   Name: '{name}'")
            print(f"DEBUG:   Job Title: '{job_title}'")
            print(f"DEBUG:   Company: '{company}'")
            print(f"DEBUG:   Job Description length: {len(job_description)} characters")
            
            # Validate inputs
            if not all([name, job_title, company, job_description]):
                print("ERROR: Missing required fields")
                print(f"DEBUG: name: {bool(name)}, job_title: {bool(job_title)}, company: {bool(company)}, job_description: {bool(job_description)}")
                return jsonify({
                    'success': False,
                    'error': 'Please fill in all required fields'
                }), 400
            
            # Handle file upload
            print("DEBUG: Processing file upload...")
            if 'resume' not in request.files:
                print("ERROR: No resume file in request")
                return jsonify({
                    'success': False,
                    'error': 'No resume file uploaded'
                }), 400
            
            file = request.files['resume']
            print(f"DEBUG: File received: {file.filename}")
            
            if file.filename == '' or not file.filename.lower().endswith('.pdf'):
                print("ERROR: Invalid file type or empty filename")
                return jsonify({
                    'success': False,
                    'error': 'Please upload a PDF file'
                }), 400
            
            # Save uploaded file temporarily
            filename = secure_filename(file.filename)
            temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            print(f"DEBUG: Saving file to: {temp_path}")
            file.save(temp_path)
            
            try:
                # Extract text from resume
                print("DEBUG: Extracting text from PDF...")
                resume_text = pdf_reader.extract_text_from_pdf(temp_path)
                print(f"DEBUG: Extracted text length: {len(resume_text)} characters")
                
                if resume_text.startswith("Error"):
                    print(f"ERROR: PDF extraction failed: {resume_text}")
                    return jsonify({
                        'success': False,
                        'error': resume_text
                    }), 400
                
                # UPDATED: Use concurrent extraction for speed improvement
                print("DEBUG: Starting concurrent data extraction...")
                extraction_result = ai_analyzer.extract_data_concurrent(resume_text, job_description)
                print(f"DEBUG: Extraction result keys: {extraction_result.keys()}")
                
                # Check for extraction errors
                if "error" in extraction_result:
                    print(f"ERROR: Data extraction failed: {extraction_result['error']}")
                    return jsonify({
                        'success': False,
                        'error': f'Data extraction failed: {extraction_result["error"]}'
                    }), 500
                
                # Extract the structured data from concurrent result
                resume_data = extraction_result["resume_data"]
                job_requirements = extraction_result["job_requirements"]
                
                print(f"DEBUG: Resume data extracted - Skills: {len(resume_data.get('skills', []))}")
                print(f"DEBUG: Job requirements extracted - Required skills: {len(job_requirements.get('required_skills', []))}")
                
                # Get detailed explanation and score
                print("DEBUG: Generating match score and explanation...")
                explanation_result = ai_analyzer.explain_match_score(resume_data, job_requirements)
                match_score = explanation_result["score"]
                explanation = explanation_result["explanation"]
                
                print(f"DEBUG: Match score calculated: {match_score}")
                print(f"DEBUG: Explanation length: {len(explanation)} characters")
                
                # Save to database
                print("DEBUG: About to save analysis to database...")
                print(f"DEBUG: Calling save_analysis with parameters:")
                print(f"DEBUG:   name: '{name}'")
                print(f"DEBUG:   job_title: '{job_title}'")
                print(f"DEBUG:   company: '{company}'")
                print(f"DEBUG:   match_score: {match_score}")
                
                save_result = db_manager.save_analysis(
                    name, resume_data, job_requirements, match_score,
                    explanation, job_title, company
                )
                
                if save_result:
                    print(f"DEBUG: Analysis saved successfully with ID: {save_result}")
                else:
                    print("ERROR: Failed to save analysis - save_result is None")
                
                # Store in session for explanation view
                print("DEBUG: Storing analysis in session...")
                session['last_analysis'] = {
                    'name': name,
                    'job_title': job_title,
                    'company': company,
                    'explanation': explanation
                }
                
                print("DEBUG: Preparing response...")
                response_data = {
                    'success': True,
                    'result': {
                        'name': name,
                        'job_title': job_title,
                        'company': company,
                        'match_score': match_score,
                        'resume_data': resume_data,
                        'job_requirements': job_requirements
                    }
                }
                
                print("DEBUG: === Analysis completed successfully ===")
                return jsonify(response_data)
                
            finally:
                # Clean up temporary file
                print("DEBUG: Cleaning up temporary file...")
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    print("DEBUG: Temporary file removed")
                    
        except Exception as e:
            print(f"ERROR: Analysis failed with exception: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': f'Analysis failed: {str(e)}'
            }), 500
    
    @app.route('/analyze_fast', methods=['POST'])
    def analyze_fast():
        """Handle resume analysis using the new optimized method"""
        print("DEBUG: === Starting FAST resume analysis ===")
        
        if not all([ai_analyzer, db_manager, pdf_reader]):
            print("ERROR: System components not properly initialized")
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
            
            print(f"DEBUG: FAST analysis - Name: {name}, Job: {job_title}, Company: {company}")
            
            # Validate inputs
            if not all([name, job_title, company, job_description]):
                print("ERROR: Missing required fields in fast analysis")
                return jsonify({
                    'success': False,
                    'error': 'Please fill in all required fields'
                }), 400
            
            # Handle file upload
            if 'resume' not in request.files:
                print("ERROR: No resume file in fast analysis")
                return jsonify({
                    'success': False,
                    'error': 'No resume file uploaded'
                }), 400
            
            file = request.files['resume']
            if file.filename == '' or not file.filename.lower().endswith('.pdf'):
                print("ERROR: Invalid file in fast analysis")
                return jsonify({
                    'success': False,
                    'error': 'Please upload a PDF file'
                }), 400
            
            # Save uploaded file temporarily
            filename = secure_filename(file.filename)
            temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(temp_path)
            
            try:
                # Extract text from resume
                print("DEBUG: FAST analysis - Extracting text from PDF...")
                resume_text = pdf_reader.extract_text_from_pdf(temp_path)
                
                if resume_text.startswith("Error"):
                    print(f"ERROR: FAST analysis PDF extraction failed: {resume_text}")
                    return jsonify({
                        'success': False,
                        'error': resume_text
                    }), 400
                
                # NEW: Use the complete fast analysis workflow
                print("DEBUG: FAST analysis - Using complete fast workflow...")
                analysis_result = ai_analyzer.analyze_resume_job_match_fast(resume_text, job_description)
                
                # Check for analysis errors
                if "error" in analysis_result:
                    print(f"ERROR: FAST analysis failed: {analysis_result['error']}")
                    return jsonify({
                        'success': False,
                        'error': f'Analysis failed: {analysis_result["error"]}'
                    }), 500
                
                # Extract results
                resume_data = analysis_result["resume_data"]
                job_requirements = analysis_result["job_requirements"]
                match_score = analysis_result["compatibility_score"]
                explanation = analysis_result["detailed_explanation"]
                
                print(f"DEBUG: FAST analysis results - Score: {match_score}")
                
                # Save to database
                print("DEBUG: FAST analysis - Saving to database...")
                save_result = db_manager.save_analysis(
                    name, resume_data, job_requirements, match_score,
                    explanation, job_title, company
                )
                
                if save_result:
                    print(f"DEBUG: FAST analysis saved with ID: {save_result}")
                else:
                    print("ERROR: FAST analysis - Failed to save")
                
                # Store in session for explanation view
                session['last_analysis'] = {
                    'name': name,
                    'job_title': job_title,
                    'company': company,
                    'explanation': explanation
                }
                
                print("DEBUG: === FAST analysis completed successfully ===")
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
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    
        except Exception as e:
            print(f"ERROR: FAST analysis failed with exception: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': f'Analysis failed: {str(e)}'
            }), 500
    
    @app.route('/explanation')
    def get_explanation():
        """Get detailed explanation for last analysis"""
        print("DEBUG: Getting explanation for last analysis")
        last_analysis = session.get('last_analysis')
        if not last_analysis:
            print("ERROR: No analysis found in session")
            return jsonify({
                'success': False,
                'error': 'No analysis available. Please run an analysis first.'
            }), 404
        
        print("DEBUG: Returning explanation from session")
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
        print("DEBUG: Getting analysis history...")
        
        if not db_manager:
            print("ERROR: Database manager not initialized")
            return jsonify({
                'success': False,
                'error': 'Database not initialized'
            }), 500
        
        try:
            print("DEBUG: Querying database for analyses...")
            analyses = db_manager.get_all_analyses()
            print(f"DEBUG: Found {len(analyses)} analyses in database")
            
            # Format analyses for display
            formatted_analyses = []
            for i, analysis in enumerate(analyses):
                print(f"DEBUG: Processing analysis {i+1}: {analysis.get('name', 'Unknown')}")
                formatted_analyses.append({
                    'name': analysis.get('name', ''),
                    'job_title': analysis.get('job_title', 'N/A'),
                    'company': analysis.get('company', 'N/A'),
                    'match_score': analysis.get('match_score', 0),
                    'timestamp': analysis.get('timestamp', datetime.utcnow()).strftime('%Y-%m-%d %H:%M')
                })
            
            # Sort by timestamp (newest first)
            formatted_analyses.sort(key=lambda x: x['timestamp'], reverse=True)
            
            print(f"DEBUG: Returning {len(formatted_analyses)} formatted analyses")
            return jsonify({
                'success': True,
                'analyses': formatted_analyses
            })
            
        except Exception as e:
            print(f"ERROR: Failed to retrieve history: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': f'Failed to retrieve history: {str(e)}'
            }), 500
    
    @app.route('/compare/<job_title>/<company>')
    def compare_candidates(job_title, company):
        """Compare candidates for a specific position"""
        print(f"DEBUG: Comparing candidates for {job_title} at {company}")
        
        if not db_manager:
            print("ERROR: Database manager not initialized for comparison")
            return jsonify({
                'success': False,
                'error': 'Database not initialized'
            }), 500
        
        try:
            candidates = db_manager.compare_candidates_for_position(job_title, company, 10)
            print(f"DEBUG: Found {len(candidates)} candidates for comparison")
            return jsonify({
                'success': True,
                'candidates': candidates
            })
        except Exception as e:
            print(f"ERROR: Failed to compare candidates: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': f'Failed to compare candidates: {str(e)}'
            }), 500
    
    @app.errorhandler(413)
    def too_large(e):
        """Handle file upload size errors"""
        print("ERROR: File upload too large")
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