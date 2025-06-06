# ResumeMatchAI

An AI-powered resume analysis system that provides intelligent matching between candidates and job opportunities, with detailed compatibility insights and data management capabilities. It will analyzes resumes against job descriptions, assigns compatibility scores (1-100), and stores all data in MongoDB for persistence and retrieval.

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
  - Developer access to raw database queries

### Immediate Roadmap (Next 1-2 Weeks)
- **Enhanced Matching Algorithms**
  - Top-10 retrieval functions:
    - Find best job matches for a given resume
    - Find best candidate matches for a given job description
  - Improved prompt engineering for consistent scoring
  - Normalization of scores across different wording variations

- **Comprehensive Reporting**
  - Detailed explanations for compatibility scores
  - Actionable improvement suggestions:
    - For scores <50: Indicates poor fit with recommendations against applying
    - For scores ≥50: Provides specific keywords to incorporate
    - (Future) Automated resume enhancement suggestions

- **Basic User System**
  - Username/password authentication
  - Profile storage (name, contact info)
  - Resume and analysis history tracking

### Future Development
- **Advanced User Features**
  - Full user profiles with:
    - Contact information (phone, email, address)
    - Resume storage and management
    - Saved job searches and results
  - Admin privileges for developer access

- **Web Platform**
  - Hosted website deployment
  - Enhanced UI/UX design
  - Account management dashboard
  - Batch processing capabilities

## File Structures
| File                 | Description                          |
|----------------------|--------------------------------------|
| `ai_analyzer.py`     | AI analysis and scoring logic        |
| `config.py`          | Application configuration            |
| `database.py`        | MongoDB operations                  |
| `gui.py`             | Graphical user interface            |
| `main.py`            | Main application logic              |
| `pdf_reader.py`      | PDF parsing functionality           |
| `requirements.txt`   | Python dependencies                 |
| `run_gui.py`         | GUI entry point                     |

## Usage
- Launch the GUI application:
      bash
      python run_gui.py

## How It Works
- Upload your resume (PDF format)
- Paste the job description text
- The system will:
-   Parse and format the resume content
-   Analyze the job description
-   Compare both using AI
-   Generate a compatibility score (1-100) and explanation for the score
-   Store all results in MongoDB
- View and manage previous analyses through the MongoDB
