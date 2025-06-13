# ResumeMatchAI
# Authors: Jonathan Hu, Tianjiao Dong

An AI-powered resume analysis system that provides intelligent matching between candidates and job opportunities, with detailed compatibility insights and data management capabilities. It analyzes resumes against job descriptions, assigns compatibility scores (1-100), and stores all data in MongoDB for persistence and retrieval.

### Current Functionality
- **AI-Powered Analysis Engine**
  - Parses resumes from PDF format
  - Processes job descriptions from text input
  - Generates compatibility scores (1-100) using advanced prompt engineering
  - Provides detailed score breakdowns across multiple dimensions:
    - Education (weighted by degree level and graduation recency)
    - Experience (relevance and duration)
    - Skills (keyword matching and minimum qualification checks)
    - Resume quality (writing clarity and structure)

- **Data Management**
  - MongoDB integration for persistent storage
  - Stores all analysis results with timestamps
  - Web-based history viewing and retrieval
  - Position-based candidate comparison

- **Web Interface Features**
  - Clean, functional web UI accessible via browser
  - Real-time analysis with loading indicators
  - Modal windows for detailed explanations
  - Responsive design for various screen sizes
  - Session-based result caching

### Immediate Roadmap (Next 1-2 Weeks)
- **Enhanced Matching Algorithms**
  - Top-10 retrieval functions:
    - Find best job matches for a given resume
    - Find best candidate matches for a given job description
  - Improved prompt engineering for consistent scoring
  - Normalization of scores across different wording variations

- **Comprehensive Reporting**
  - Enhanced detailed explanations for compatibility scores
  - Actionable improvement suggestions:
    - For scores <50: Indicates poor fit with recommendations against applying
    - For scores ≥50: Provides specific keywords to incorporate
    - Automated resume enhancement suggestions

- **Basic User System**
  - Username/password authentication
  - Profile storage (name, contact info)
  - Resume and analysis history tracking per user

### Future Development
- **Advanced User Features**
  - Full user profiles with:
    - Contact information (phone, email, address)
    - Resume storage and management
    - Saved job searches and results
  - Admin privileges for developer access
  - Role-based access control

- **Platform Enhancements**
  - Cloud hosting deployment (AWS/Heroku/Azure)
  - Enhanced UI/UX design with modern framework
  - RESTful API for third-party integrations
  - Batch processing capabilities
  - Export functionality (PDF reports, CSV data)

## File Structure

### Web Application Files
| File                      | Description                                |
|---------------------------|--------------------------------------------|
| `app.py`                  | Flask application server and routes        |
| `templates/base.html`     | Base HTML template with common styling     |
| `templates/index.html`    | Main page with analysis form and results   |

### Core Analysis Files
| File                 | Description                          |
|----------------------|--------------------------------------|
| `ai_analyzer.py`     | AI analysis and scoring logic        |
| `config.py`          | Application configuration            |
| `database.py`        | MongoDB operations                   |
| `pdf_reader.py`      | PDF parsing functionality            |
| `requirements.txt`   | Python dependencies                  |

### Legacy Desktop Files (Optional)
| File                 | Description                          |
|----------------------|--------------------------------------|
| `gui.py`             | Tkinter graphical interface (deprecated) |
| `main.py`            | CLI application logic (optional)     |
| `run_gui.py`         | GUI entry point (deprecated)         |


## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- MongoDB database (local or cloud)
- OpenAI API key

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/ResumeMatchAI.git
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   Create a `.env` file in the root directory:
   ```
   OPENAI_API_KEY=your-openai-api-key
   MONGODB_URI=your-mongodb-connection-string
   ```
   If you are new and just starting, contact Jonathan Hu for a copy of the .env file

4. **Run the web application**
   ```bash
   python app.py
   ```

5. **Access the application**
   Open your browser and navigate to `http://localhost:5000`

## Usage

### Web Interface
1. **Access the application** at `http://localhost:5000`
2. **Fill in the analysis form:**
   - Enter candidate name
   - Specify job title and company
   - Upload resume (PDF format, max 16MB)
   - Paste the job description
3. **Click "Analyze Resume"** to process
4. **View results:**
   - Compatibility score (1-100)
   - Extracted skills and experience
   - Job requirements breakdown
5. **Additional features:**
   - Click "View Detailed Explanation" for scoring methodology
   - Click "View History" to see all previous analyses
   - Use "Clear All" to reset the form

### API Endpoints (for developers)
- `POST /analyze` - Submit resume and job description for analysis
- `GET /explanation` - Retrieve detailed explanation for last analysis
- `GET /history` - Get all previous analyses
- `GET /compare/<job_title>/<company>` - Compare candidates for a position

## How It Works
1. **PDF Processing**: Extracts text from uploaded resume using PyPDF2
2. **AI Analysis**: 
   - Sends resume text to OpenAI GPT-4 for structured data extraction
   - Analyzes job description for requirements
   - Generates compatibility score using custom scoring algorithm
3. **Score Calculation**:
   - Base score: 100 points
   - Deductions for missing requirements
   - Bonuses for preferred qualifications
   - Final score normalized to 0-100 range
4. **Data Storage**: All results saved to MongoDB with timestamps
5. **Result Display**: Web interface shows scores, breakdowns, and explanations

## Technical Stack
- **Backend**: Flask (Python web framework)
- **AI/ML**: OpenAI GPT-4 API
- **Database**: MongoDB
- **Frontend**: HTML, CSS, JavaScript (vanilla)
- **PDF Processing**: PyPDF2
- **Environment**: Python 3.8+

## Security Considerations
- API keys stored in environment variables
- File upload validation (PDF only, size limits)
- Input sanitization for web forms
- Session-based temporary storage
- No user authentication (currently)
