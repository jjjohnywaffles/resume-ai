# ResumeMatchAI
**Authors:** Jonathan Hu, Tianjiao Dong

**Last Update:** 7/5/25

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

### User Authentication System ✅
- **User Registration**: Create accounts with unique email addresses
- **User Login**: Secure authentication with password hashing
- **Profile Management**: View personal analysis history and statistics
- **Guest Access**: Use analyzer without registration (analyses not saved to profile)
- **Session Management**: Secure login/logout functionality

### Data Management
- MongoDB integration for persistent storage
- Stores all analysis results with timestamps
- User-specific analysis history and profile data
- Web-based history viewing and retrieval
- Position-based candidate comparison

### Dual Interface Options
- **Web Interface**: Clean, functional web UI accessible via browser with real-time analysis, loading indicators, and modal windows for detailed explanations
- **Desktop GUI**: Native desktop application with the same core functionality

## Project Structure

```
resume-analyzer/
├── run_web.py              # Web application entry point
├── run_gui.py              # Desktop GUI entry point
├── config.py               # Application configuration
├── requirements.txt        # Python dependencies
├── env_template.txt        # Environment variables template
├── .env                    # Environment variables (create from template)
├── .gitignore             # Git ignore rules
│
├── core/                   # Business Logic
│   ├── analyzer.py         # AI analysis and scoring logic (Claude API)
│   ├── pdf_reader.py       # PDF text extraction
│   └── database.py         # MongoDB operations with user management
│
├── web/                    # Web Interface
│   ├── app.py             # Flask application and main routes
│   ├── auth.py            # Authentication routes (login/signup/logout)
│   └── routes.py          # Profile and additional routes
│
├── gui/                    # Desktop Interface
│   └── app.py             # Tkinter desktop application
│
└── templates/              # HTML Templates
    ├── base.html          # Base template with navigation
    ├── index.html         # Main analysis form and results
    ├── login.html         # User login form
    ├── signup.html        # User registration form
    ├── profile.html       # User profile and analysis history
    └── jobs.html          # Job listings (if implemented)
```

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- MongoDB database (local or cloud)
- Anthropic API key (for Claude AI analysis)

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
   Copy `env_template.txt` to `.env` and fill in your API keys:
   ```env
   # API Keys (Required for AI analysis)
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   
   # Database Configuration
   MONGODB_URI=mongodb://localhost:27017/
   DATABASE_NAME=resume_analyzer
   
   # Flask Secret Key (change this to a secure random string)
   SECRET_KEY=your-secret-key-change-this-to-something-secure
   ```

4. **Run the application**

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

#### Guest Users (No Registration Required)
1. **Access** the application at `http://localhost:5000`
2. **Complete the analysis form:**
   - Enter your name
   - Specify job title and company
   - Upload resume (PDF format, max 16MB)
   - Paste the job description
3. **Analyze**: Click "Analyze Resume" to process
4. **Review results**: Get compatibility score and detailed breakdown

#### Registered Users
1. **Sign up** for an account or **login** to existing account
2. **Use the analyzer** - same as guest users
3. **Access your profile** to view:
   - Personal analysis history
   - Resume upload status
   - Statistics and trends
4. **All analyses are automatically saved** to your profile

### Authentication Features
- **Registration**: Create account with email and password
- **Login**: Secure authentication with session management
- **Profile**: View personal analysis history and statistics
- **Logout**: Secure session termination

### Desktop GUI
- Same functionality as web interface in a native desktop application
- Suitable for offline use or desktop-preferred workflows
- Results display in tabbed interface with detailed breakdowns

### API Endpoints (for developers)
- `POST /analyze` - Submit resume and job description for analysis
- `GET /explanation` - Retrieve detailed explanation for last analysis
- `GET /history` - Get all previous analyses
- `GET /compare/<job_title>/<company>` - Compare candidates for a position
- `POST /signup` - User registration
- `POST /login` - User authentication
- `GET /logout` - User logout
- `GET /profile` - User profile (requires authentication)

## How It Works

1. **PDF Processing**: Extracts text from uploaded resume using PyPDF2
2. **AI Analysis**: 
   - Sends resume text to Anthropic Claude for structured data extraction
   - Analyzes job description for requirements
   - Generates compatibility score using custom scoring algorithm
3. **Score Calculation**:
   - Base score: 100 points
   - Deductions for missing requirements (-7 to -15 points each)
   - Experience gap penalties (-10 to -30 points)
   - Education mismatch deductions (-5 to -20 points)
   - Bonuses for preferred qualifications (+3 to +5 points each)
   - Final score constrained to 15-95 range for consistency
4. **Data Storage**: All results saved to MongoDB with user association
5. **User Management**: Secure authentication and profile management
6. **Result Display**: Interface shows scores, breakdowns, and explanations

## Technical Stack

- **Backend**: Flask (Python web framework)
- **AI/ML**: Anthropic Claude API (primary), OpenAI GPT (fallback)
- **Database**: MongoDB with PyMongo
- **Authentication**: Flask-Login with password hashing
- **Frontend**: HTML, CSS, JavaScript (vanilla)
- **Desktop GUI**: Tkinter (Python standard library)
- **PDF Processing**: PyPDF2
- **Environment**: Python 3.8+
- **Configuration**: python-dotenv for environment management

## Development

### Adding New Features

The modular structure makes it easy to add new functionality:

1. **Core Logic**: Add new analysis methods to `core/analyzer.py`
2. **Authentication**: Add routes to `web/auth.py`
3. **Web Interface**: Add routes to `web/app.py` or `web/routes.py`
4. **Desktop Interface**: Extend `gui/app.py`
5. **Database**: Add new queries to `core/database.py`

### Code Organization Philosophy

- **`core/`**: Pure business logic, no UI dependencies
- **`web/`**: Flask-specific code and web routes
  - `app.py`: Main application and analysis routes
  - `auth.py`: Authentication routes
  - `routes.py`: Profile and additional routes
- **`gui/`**: Desktop-specific interface code
- **`templates/`**: HTML templates for web interface

### Contributing

1. Follow the existing code structure
2. Add new features to appropriate modules
3. Maintain the clean import pattern
4. Test both web and GUI interfaces
5. Ensure authentication is properly implemented for protected routes

## Security Considerations

- API keys stored in environment variables
- File upload validation (PDF only, size limits)
- Input sanitization for web forms
- Password hashing using Werkzeug security
- Session-based authentication with Flask-Login
- User authentication required for profile access
- Prepared for encryption/hashing when user system is implemented