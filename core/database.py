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
   - DatabaseManager: MongoDB interface with three-collection architecture
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

config = get_config()

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
    
    def save_analysis(self, name, resume_data, job_requirements, match_score, 
                     explanation, job_title, company):
        """
        EXACT SAME METHOD SIGNATURE - no changes to your Flask app needed
        Now saves to three collections instead of one
        """
        try:
            # Save user and resume data
            user_id = self._save_user_resume(name, resume_data)
            
            # Save job data  
            job_id = self._save_job(job_title, company, job_requirements)
            
            # Save analysis with references to user and job
            analysis_doc = {
                "user_id": user_id,
                "job_id": job_id,
                "match_score": match_score,
                "explanation": explanation,
                "timestamp": datetime.utcnow(),
                
                # Keep legacy fields for your existing Flask app
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
    
    def _save_user_resume(self, name, resume_data):
        """Save user and their resume data"""
        try:
            # Check if user already exists
            existing_user = self.users_collection.find_one({"name": name})
            
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
            else:
                # Create new user
                user_doc = {
                    "name": name,
                    "resume_data": resume_data,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                result = self.users_collection.insert_one(user_doc)
                return result.inserted_id
                
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
        """
        EXACT SAME RETURN FORMAT - your Flask app expects this format
        """
        try:
            analyses = list(self.analyses_collection.find().sort("timestamp", -1).limit(limit))
            return analyses
        except Exception as e:
            print(f"Error getting analyses: {e}")
            return []
    
    def compare_candidates_for_position(self, job_title, company, limit=10):
        """
        EXACT SAME RETURN FORMAT - your Flask app expects this format
        """
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