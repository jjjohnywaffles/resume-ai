"""
File: database.py
Author: Jonathan Hu
Date Created: 6/12/25
Last Modified: 6/24/25
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
    """Database manager with dual resume storage - users collection + separate resumes table"""
    
    def __init__(self):
        try:
            # Use your existing configuration
            connection_string = getattr(config, 'MONGODB_URI', 'mongodb://localhost:27017/')
            db_name = getattr(config, 'DATABASE_NAME', 'resume_analyzer')
            
            self.client = MongoClient(connection_string)
            self.db = self.client[db_name]
            
            # FOUR collections
            self.users_collection = self.db.users           # User info + resume data
            self.resumes_collection = self.db.resumes       # Dedicated resumes table
            self.jobs_collection = self.db.jobs             # Job descriptions
            self.analyses_collection = self.db.analyses     # Analysis results
            
            print("DatabaseManager initialized - dual resume storage (users + resumes tables)")
            
        except Exception as e:
            print(f"Error initializing database: {e}")
            raise
    
    def save_analysis(self, name, resume_data, job_requirements, match_score, 
                 explanation, job_title, company):
        """
        Save analysis with DUAL resume storage
        """
        try:
            print(f"    💾 Saving analysis for: {name}")
            
            # Save user WITH resume data (original approach)
            user_mongodb_id = self._save_user_resume(name, resume_data)
            if user_mongodb_id is None:
                print(f"    ❌ User save failed - cannot continue")
                return None
            print(f"    ✅ User saved with _id: {user_mongodb_id}")
            
            # ALSO save resume data to separate resumes table
            resume_mongodb_id = self._save_resume_separately(user_mongodb_id, name, resume_data)
            if resume_mongodb_id is None:
                print(f"    ⚠️ Separate resume save failed, but continuing...")
            else:
                print(f"    ✅ Resume also saved separately with _id: {resume_mongodb_id}")
            
            # Save job data  
            job_mongodb_id = self._save_job(job_title, company, job_requirements)
            if job_mongodb_id is None:
                print(f"    ❌ Job save failed - cannot continue")
                return None
            print(f"    ✅ Job saved with _id: {job_mongodb_id}")
            
            # Save analysis with references
            analysis_doc = {
                "user_ref": user_mongodb_id,        # Reference to users._id
                "resume_ref": resume_mongodb_id,     # Reference to resumes._id (could be None)
                "job_ref": job_mongodb_id,          # Reference to jobs._id  
                "match_score": match_score,
                "explanation": explanation,
                "timestamp": datetime.utcnow(),
                
                # Keep legacy fields for backward compatibility
                "name": name,
                "job_title": job_title,
                "company": company,
                "resume_data": resume_data,
                "job_requirements": job_requirements
            }
            
            result = self.analyses_collection.insert_one(analysis_doc)
            print(f"    ✅ Analysis saved successfully with _id: {result.inserted_id}")
            return result.inserted_id
            
        except Exception as e:
            print(f"    ❌ Error saving analysis: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _save_user_resume(self, name, resume_data):
        """Save user WITH resume data in users collection (original approach)"""
        try:
            print(f"      👤 Processing user with resume: {name}")
            
            # Check if user already exists by name
            existing_user = self.users_collection.find_one({"name": name})
            
            if existing_user:
                # Update existing user's resume data
                self.users_collection.update_one(
                    {"_id": existing_user["_id"]},
                    {
                        "$set": {
                            "resume_data": resume_data,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                print(f"      🔄 Updated existing user with resume: {name}")
                return existing_user["_id"]
            else:
                # Create new user WITH resume data
                user_doc = {
                    "name": name,
                    "email": None,  # Guest user
                    "password": None,
                    "resume_data": resume_data,    # Resume data stored here
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                
                result = self.users_collection.insert_one(user_doc)
                print(f"      ➕ Created new user with resume: {name} with _id: {result.inserted_id}")
                return result.inserted_id
                
        except Exception as e:
            print(f"      ❌ Error saving user with resume: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _save_resume_separately(self, user_id, name, resume_data):
        """ALSO save resume data to separate resumes table"""
        try:
            print(f"      📄 Also saving resume separately for: {name}")
            
            # Check if resume already exists for this user
            existing_resume = self.resumes_collection.find_one({"user_ref": user_id})
            
            if existing_resume:
                # Update existing separate resume
                self.resumes_collection.update_one(
                    {"_id": existing_resume["_id"]},
                    {
                        "$set": {
                            "resume_data": resume_data,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                print(f"      🔄 Updated separate resume for: {name}")
                return existing_resume["_id"]
            else:
                # Create new separate resume
                resume_doc = {
                    "user_ref": user_id,           # Reference to user
                    "candidate_name": name,        # For easy searching
                    "resume_data": resume_data,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                
                result = self.resumes_collection.insert_one(resume_doc)
                print(f"      ➕ Created separate resume for: {name} with _id: {result.inserted_id}")
                return result.inserted_id
                
        except Exception as e:
            print(f"      ⚠️ Error saving separate resume: {e}")
            # Don't fail the whole process if separate resume save fails
            return None
    
    def _save_job(self, job_title, company, job_requirements):
        """Save job description data"""
        try:
            print(f"      💼 Processing job: {job_title} at {company}")
            
            # Check if job already exists
            existing_job = self.jobs_collection.find_one({
                "job_title": job_title,
                "company": company,
                "job_requirements": job_requirements
            })
            
            if existing_job:
                print(f"      🔄 Job already exists with _id: {existing_job['_id']}")
                return existing_job["_id"]
            
            # Create new job
            job_doc = {
                "job_title": job_title,
                "company": company,
                "job_requirements": job_requirements,
                "created_at": datetime.utcnow()
            }
            
            result = self.jobs_collection.insert_one(job_doc)
            print(f"      ➕ Created new job with _id: {result.inserted_id}")
            return result.inserted_id
            
        except Exception as e:
            print(f"      ❌ Error saving job: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    # Resume management methods
    def get_resume_by_user_id(self, user_id):
        """Get resume from separate resumes table"""
        try:
            return self.resumes_collection.find_one({"user_ref": ObjectId(user_id)})
        except Exception as e:
            print(f"Error getting separate resume: {e}")
            return None
    
    def get_user_with_resume(self, user_id):
        """Get user with embedded resume data from users table"""
        try:
            return self.users_collection.find_one({"_id": ObjectId(user_id)})
        except Exception as e:
            print(f"Error getting user with resume: {e}")
            return None
    
    def get_all_resumes(self, limit=100):
        """Get all resumes from separate resumes table"""
        try:
            resumes = list(self.resumes_collection.find().sort("created_at", -1).limit(limit))
            print(f"    📄 Found {len(resumes)} resumes in separate table")
            return resumes
        except Exception as e:
            print(f"Error getting resumes: {e}")
            return []
    
    def get_all_users_with_resumes(self, limit=100):
        """Get all users with embedded resume data"""
        try:
            users = list(self.users_collection.find({"resume_data": {"$exists": True}}).sort("created_at", -1).limit(limit))
            print(f"    👤 Found {len(users)} users with embedded resume data")
            return users
        except Exception as e:
            print(f"Error getting users with resumes: {e}")
            return []
    
    def search_resumes_by_skills(self, skills):
        """Search resumes by skills in separate resumes table"""
        try:
            query = {"resume_data.skills": {"$in": skills}}
            resumes = list(self.resumes_collection.find(query))
            return resumes
        except Exception as e:
            print(f"Error searching resumes: {e}")
            return []
    
    # Existing methods (unchanged)
    def get_user_by_email(self, email):
        """Find user by email"""
        return self.users_collection.find_one({"email": email})

    def get_user_by_id(self, user_id):
        """Find user by MongoDB _id"""
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
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = self.users_collection.insert_one(user_doc)
        return str(result.inserted_id)
    
    def get_all_analyses(self, limit=100):
        """Get all analyses from database"""
        try:
            analyses = list(self.analyses_collection.find().sort("timestamp", -1).limit(limit))
            return analyses
        except Exception as e:
            print(f"    ❌ Error getting analyses: {e}")
            return []
    
    def compare_candidates_for_position(self, job_title, company, limit=10):
        """Compare candidates for a specific position"""
        try:
            candidates = list(
                self.analyses_collection.find({
                    "job_title": job_title,
                    "company": company
                }).sort("match_score", -1).limit(limit)
            )
            return candidates
        except Exception as e:
            print(f"    ❌ Error comparing candidates: {e}")
            return []


# DUAL STORAGE Schema Documentation
"""
DUAL RESUME STORAGE DATABASE STRUCTURE:

1. users collection (WITH resume data):
{
    "_id": ObjectId("auto-generated"),
    "name": "John Doe",
    "email": null,
    "password": null,
    "resume_data": {                    // ← Resume data stored HERE
        "skills": [...],
        "experience": [...],
        "education": [...]
    },
    "created_at": ISODate,
    "updated_at": ISODate
}

2. resumes collection (SEPARATE resume table):
{
    "_id": ObjectId("auto-generated"),
    "user_ref": ObjectId,               // Reference to users._id
    "candidate_name": "John Doe",       // For easy searching
    "resume_data": {                    // ← SAME resume data stored HERE TOO
        "skills": [...],
        "experience": [...],
        "education": [...]
    },
    "created_at": ISODate,
    "updated_at": ISODate
}

3. jobs collection:
{
    "_id": ObjectId("auto-generated"),
    "job_title": "Software Engineer", 
    "company": "Tech Corp",
    "job_requirements": {...},
    "created_at": ISODate
}

4. analyses collection:
{
    "_id": ObjectId("auto-generated"),
    "user_ref": ObjectId,               // Reference to users._id
    "resume_ref": ObjectId,             // Reference to resumes._id
    "job_ref": ObjectId,                // Reference to jobs._id
    "match_score": 85,
    "explanation": "...",
    "timestamp": ISODate,
    "name": "John Doe",                 // Legacy fields
    "job_title": "Software Engineer",
    "company": "Tech Corp",
    "resume_data": {...},               // Legacy - duplicated
    "job_requirements": {...}           // Legacy - duplicated
}

BENEFITS:
- Backward compatibility (resume data still in users)
- Dedicated resumes table for easier resume management
- Can query resumes independently
- Can search resumes by skills, experience, etc.
- References link everything together
"""