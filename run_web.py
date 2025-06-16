"""
Web Application Entry Point
Entry point for the Flask web application
"""

from web.app import create_app

def main():
    """Start the web application"""
    app = create_app()
    print("Starting Resume Analyzer Web Interface...")
    print("Access at: http://localhost:5000")
    app.run(debug=True, port=5000)

if __name__ == '__main__':
    main()
