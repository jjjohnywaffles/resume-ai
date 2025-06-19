"""
File: database.py
Author: Jonathan Hu
Date Created: 6/12/25
Last Modified: 6/17/25
Description: Improved database management module for MongoDB operations with 
            three-collection schema. Handles database connections, queries, 
            and data persistence for resume analyses while maintaining 
            backward compatibility with existing Flask application.
Classes:
   - DatabaseManager: MongoDB interface with three collection architecture
Collections:
   - users: Stores user information and resume data
   - jobs: Stores job descriptions and requirements
   - analyses: Links users to jobs with analysis results and scores
Methods:
   - save_analysis(): Store analysis results across three collections
   - get_all_analyses(): Fetch all stored analyses with legacy format
   - compare_candidates_for_position(): Compare candidates for same position
   - _save_user_resume(): Internal method to store user and resume data
   - _save_job(): Internal method to store job posting information
   - Various query methods maintaining existing Flask app compatibility
"""

from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
from config import get_config

from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

config = get_config()

class User(UserMixin):
    """User class for Flask-Login integration"""
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.email = user_data.get('email')
        self.name = user_data.get('name')
        self.created_at = user_data.get('created_at')
    
    @staticmethod
    def get(user_id):
        try:
            user_data = DatabaseManager().get_user_by_id(user_id)
            if user_data:
                return User(user_data)
            return None
        except:
            return None


class DatabaseManager:
    """Updated database manager with three-collection schema"""
    
    def __init__(self):
        try:
            # Use your existing configuration
            connection_string = getattr(config, 'MONGODB_URI', 'mongodb://localhost:27017/')
            db_name = getattr(config, 'DATABASE_NAME', 'resume_analyzer')
            
            self.client = MongoClient(connection_string)
            self.db = self.client[db_name]
            
            # Three collections as requested
            self.users_collection = self.db.users           # User + Resume data
            self.jobs_collection = self.db.jobs             # Job descriptions
            self.analyses_collection = self.db.analyses     # Analysis results with references
            
            print("DatabaseManager initialized with three-collection schema")
            
        except Exception as e:
            print(f"Error initializing database: {e}")
            raise
    
    def save_analysis(self, email, resume_data, job_requirements, match_score, 
                     explanation, job_title, company):
        """
        Now saves to three collections instead of one
        """
        try:
            # Save user and resume data
            user_id = self._save_user_resume(email, resume_data)
            
            # Save job data  
            job_id = self._save_job(job_title, company, job_requirements)
            
            # Save analysis with references to user and job
            analysis_doc = {
                "user_id": user_id,
                "job_id": job_id,
                "match_score": match_score,
                "explanation": explanation,
                "timestamp": datetime.utcnow(),
                
                # Keep legacy fields
                "name": name,
                "job_title": job_title,
                "company": company,
                "resume_data": resume_data,
                "job_requirements": job_requirements
            }
            
            result = self.analyses_collection.insert_one(analysis_doc)
            return result.inserted_id
            
        except Exception as e:
            print(f"Error saving analysis: {e}")
            return None
        
    def get_user_by_email(self, email):
        """Find user by email"""
        return self.users_collection.find_one({"email": email})

    def get_user_by_id(self, user_id):
        """Find user by ID"""
        try:
            return self.users_collection.find_one({"_id": ObjectId(user_id)})
        except:
            return None
        
    def verify_user(self, email, password):
        """Verify user credentials"""
        user = self.get_user_by_email(email)
        if user and check_password_hash(user['password'], password):
            return user
        return None
    

    def create_user(self, name, email, password):
        """Create new user with hashed password"""
        if self.get_user_by_email(email):
            return None  # User already exists
    
        hashed_password = generate_password_hash(password)
        user_doc = {
            "name": name,
            "email": email,
            "password": hashed_password,
            "resume_data": None, 
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = self.users_collection.insert_one(user_doc)
        return str(result.inserted_id)
        
    
    def _save_user_resume(self, email, resume_data):
        """Save user and their resume data"""
        try:
            # Check if user already exists
            existing_user = self.get_user_by_email(email)
            
            if existing_user:
                # Update existing user's resume
                self.users_collection.update_one(
                    {"_id": existing_user["_id"]},
                    {
                        "$set": {
                            "resume_data": resume_data,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                return existing_user["_id"]
                
        except Exception as e:
            print(f"Error saving user: {e}")
            return None
    
    def _save_job(self, job_title, company, job_requirements):
        """Save job description data"""
        try:
            # Check if job already exists
            existing_job = self.jobs_collection.find_one({
                "job_title": job_title,
                "company": company,
                "job_requirements": job_requirements
            })
            
            if existing_job:
                return existing_job["_id"]
            
            # Create new job
            job_doc = {
                "job_title": job_title,
                "company": company,
                "job_requirements": job_requirements,
                "created_at": datetime.utcnow()
            }
            
            result = self.jobs_collection.insert_one(job_doc)
            return result.inserted_id
            
        except Exception as e:
            print(f"Error saving job: {e}")
            return None
    
    def get_all_analyses(self, limit=100):

        try:
            analyses = list(self.analyses_collection.find().sort("timestamp", -1).limit(limit))
            return analyses
        except Exception as e:
            print(f"Error getting analyses: {e}")
            return []
    
    def compare_candidates_for_position(self, job_title, company, limit=10):

        try:
            candidates = list(
                self.analyses_collection.find({
                    "job_title": job_title,
                    "company": company
                }).sort("match_score", -1).limit(limit)
            )
            return candidates
        except Exception as e:
            print(f"Error comparing candidates: {e}")
            return []


# Schema Documentation
"""
NEW DATABASE STRUCTURE:

1. users collection:
{
    "_id": ObjectId,
    "name": "John Doe",
    "resume_data": {
        "skills": [...],
        "experience": [...],
        "education": [...]
    },
    "created_at": ISODate,
    "updated_at": ISODate
}

2. jobs collection:
{
    "_id": ObjectId,
    "job_title": "Software Engineer",
    "company": "Tech Corp",
    "job_requirements": {
        "required_skills": [...],
        "preferred_skills": [...],
        "experience_required": "...",
        "education_required": "...",
        "responsibilities": [...]
    },
    "created_at": ISODate
}

3. analyses collection:
{
    "_id": ObjectId,
    "user_id": ObjectId,      // Reference to users collection
    "job_id": ObjectId,       // Reference to jobs collection
    "match_score": 85,
    "explanation": "...",
    "timestamp": ISODate,
    
    // Legacy fields (kept for Flask app compatibility)
    "name": "John Doe",
    "job_title": "Software Engineer",
    "company": "Tech Corp", 
    "resume_data": {...},
    "job_requirements": {...}
}

"""