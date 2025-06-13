"""
File: app.py
Author: Jonathan Hu
Date Created: 6/12/25
Last Modified: 6/12/25
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
import os
import json
from werkzeug.utils import secure_filename
from datetime import datetime
import tempfile
from ai_analyzer import AIAnalyzer
from database import DatabaseManager
from pdf_reader import PDFReader
import config

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a random secret key
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

# Initialize components
try:
    ai_analyzer = AIAnalyzer()
    db_manager = DatabaseManager()
    pdf_reader = PDFReader()
except Exception as e:
    print(f"Error initializing components: {e}")
    ai_analyzer = None
    db_manager = None
    pdf_reader = None

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    """Handle resume analysis"""
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
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        if not file.filename.lower().endswith('.pdf'):
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
            resume_text = pdf_reader.extract_text_from_pdf(temp_path)
            
            if resume_text.startswith("Error"):
                return jsonify({
                    'success': False,
                    'error': resume_text
                }), 400
            
            # Extract structured data
            resume_data = ai_analyzer.extract_resume_data(resume_text)
            job_requirements = ai_analyzer.extract_job_requirements(job_description)
            
            # Get detailed explanation and score
            explanation_result = ai_analyzer.explain_match_score(resume_data, job_requirements)
            match_score = explanation_result["score"]
            explanation = explanation_result["explanation"]
            
            # Save to database
            db_manager.save_analysis(
                name, resume_data, job_requirements, match_score,
                explanation, job_title, company
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
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except Exception as e:
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

@app.errorhandler(413)
def too_large(e):
    return jsonify({
        'success': False,
        'error': 'File too large. Maximum size is 16MB.'
    }), 413

if __name__ == '__main__':
    app.run(debug=True, port=5000)