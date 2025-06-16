# ResumeMatchAI
**Authors:** Jonathan Hu, Tianjiao Dong

**Last Update:** 6/15/25

An AI-powered resume analysis system that provides intelligent matching between candidates and job opportunities, with detailed compatibility insights and data management capabilities. It analyzes resumes against job descriptions, assigns compatibility scores (1-100), and stores all data in MongoDB for persistence and retrieval.

## Current Functionality

### AI-Powered Analysis Engine
- Parses resumes from PDF format
- Processes job descriptions from text input
- Generates compatibility scores (1-100) using advanced prompt engineering
- Provides detailed score breakdowns across multiple dimensions:
  - Education (weighted by degree level and graduation recency)
  - Experience (relevance and duration)
  - Skills (keyword matching and minimum qualification checks)
  - Resume quality (writing clarity and structure)

### Data Management
- MongoDB integration for persistent storage
- Stores all analysis results with timestamps
- Web-based history viewing and retrieval
- Position-based candidate comparison

### Dual Interface Options
- **Web Interface**: Clean, functional web UI accessible via browser with real-time analysis, loading indicators, and modal windows for detailed explanations
- **Desktop GUI**: Native desktop application with the same core functionality

## Roadmap

### Immediate Development (Next 1-2 Weeks)
- **Enhanced Matching Algorithms**
  - Top-10 retrieval functions for best job/candidate matches
  - Improved prompt engineering for consistent scoring
  - Normalization of scores across different wording variations

- **Enhanced Reporting**
  - Detailed explanations for compatibility scores
  - Actionable improvement suggestions based on score ranges
  - Automated resume enhancement recommendations

- **Basic User System**
  - Username/password authentication
  - Profile storage and resume history tracking per user

### Future Development
- **Advanced User Features**
  - Full user profiles with contact information and resume management
  - Admin privileges and role-based access control
  - Saved job searches and results

- **Platform Enhancements**
  - Cloud hosting deployment through STEM Up
  - Enhanced UI/UX design
  - Batch processing capabilities
  - Export functionality (PDF reports, CSV data)

## Project Structure

The codebase uses a **minimal packages architecture** for improved maintainability and clarity:

```
resume-analyzer/
├── run_web.py              # Web application entry point
├── run_gui.py              # Desktop GUI entry point
├── config.py               # Application configuration
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (create from template)
├── .gitignore             # Git ignore rules
│
├── core/                   # Business Logic (no __init__.py needed)
│   ├── analyzer.py         # AI analysis and scoring logic
│   ├── pdf_reader.py       # PDF text extraction
│   └── database.py         # MongoDB operations
│
├── web/                    # Web Interface
│   ├── app.py             # Flask application and routes
│   └── routes.py          # Additional routes (for future expansion)
│
├── gui/                    # Desktop Interface
│   └── app.py             # Tkinter desktop application
│
└── templates/              # HTML Templates
    ├── base.html          # Base template with styling
    └── index.html         # Main analysis form and results
```

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- MongoDB database (local or cloud)
- OpenAI API key

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/ResumeMatchAI.git
   cd ResumeMatchAI
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   Create a `.env` file in the root directory:
   ```env
   OPENAI_API_KEY=your-openai-api-key
   MONGODB_URI=your-mongodb-connection-string
   DATABASE_NAME=resume_analyzer
   SECRET_KEY=your-secret-key-here
   ```
   > **Note**: Contact Jonathan Hu for a copy of the `.env` file if you're new to the project

4. **Choose your interface and run**

   **Web Interface (Recommended):**
   ```bash
   python run_web.py
   ```
   Then open your browser to `http://localhost:5000`

   **Desktop GUI:**
   ```bash
   python run_gui.py
   ```

## Usage

### Web Interface
1. **Access** the application at `http://localhost:5000`
2. **Complete the analysis form:**
   - Enter candidate name
   - Specify job title and company
   - Upload resume (PDF format, max 16MB)
   - Paste the job description
3. **Analyze**: Click "Analyze Resume" to process
4. **Review results:**
   - Compatibility score (1-100)
   - Extracted skills and experience
   - Job requirements breakdown
5. **Additional features:**
   - "View Detailed Explanation" for scoring methodology
   - "View History" to see all previous analyses
   - "Clear All" to reset the form

### Desktop GUI
- Same functionality as web interface in a native desktop application
- Suitable for offline use or desktop-preferred workflows
- Results display in tabbed interface with detailed breakdowns

### API Endpoints (for developers)
- `POST /analyze` - Submit resume and job description for analysis
- `GET /explanation` - Retrieve detailed explanation for last analysis
- `GET /history` - Get all previous analyses
- `GET /compare/<job_title>/<company>` - Compare candidates for a position

## How It Works

1. **PDF Processing**: Extracts text from uploaded resume using PyPDF2
2. **AI Analysis**: 
   - Sends resume text to OpenAI GPT-4o-mini for structured data extraction
   - Analyzes job description for requirements
   - Generates compatibility score using custom scoring algorithm
3. **Score Calculation**:
   - Base score: 100 points
   - Deductions for missing requirements (-7 to -15 points each)
   - Experience gap penalties (-10 to -30 points)
   - Education mismatch deductions (-5 to -20 points)
   - Bonuses for preferred qualifications (+3 to +5 points each)
   - Final score constrained to 15-95 range for consistency
4. **Data Storage**: All results saved to MongoDB with timestamps
5. **Result Display**: Interface shows scores, breakdowns, and explanations

## Technical Stack

- **Backend**: Flask (Python web framework)
- **AI/ML**: OpenAI GPT-4o-mini API
- **Database**: MongoDB with PyMongo
- **Frontend**: HTML, CSS, JavaScript (vanilla)
- **Desktop GUI**: Tkinter (Python standard library)
- **PDF Processing**: PyPDF2
- **Environment**: Python 3.8+
- **Configuration**: python-dotenv for environment management

## Development

### Adding New Features

The minimal packages structure makes it easy to add new functionality:

1. **Core Logic**: Add new analysis methods to `core/analyzer.py`
2. **Web Interface**: Add routes to `web/app.py` 
3. **Desktop Interface**: Extend `gui/app.py`
4. **Database**: Add new queries to `core/database.py`

### Code Organization Philosophy

- **`core/`**: Pure business logic, no UI dependencies
- **`web/`**: Flask-specific code and web routes
- **`gui/`**: Desktop-specific interface code
- **`templates/`**: HTML templates for web interface

### Contributing

1. Follow the existing code structure
2. Add new features to appropriate modules
3. Maintain the clean import pattern
4. Test both web and GUI interfaces

## Security Considerations

- API keys stored in environment variables
- File upload validation (PDF only, size limits)
- Input sanitization for web forms
- Session-based temporary storage
- No user authentication (planned for future releases)
- Prepared for encryption/hashing when user system is implemented