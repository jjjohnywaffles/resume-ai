"""
File: database.py
Author: Jonathan Hu
Date Created: 6/12/25
Last Modified: 6/25/25
Description: Database management module for MongoDB operations with 
            three collection schema. Handles database connections, queries, 
            and data persistence for resume analyses. Stores resumes in 
            original uploaded format.
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
    """Database manager with single resume storage in users collection"""
    
    def __init__(self):
        try:
            # Use your existing configuration
            connection_string = getattr(config, 'MONGODB_URI', 'mongodb://localhost:27017/')
            db_name = getattr(config, 'DATABASE_NAME', 'resume_analyzer')
            
            self.client = MongoClient(connection_string)
            self.db = self.client[db_name]
            
            # THREE collections (removed resumes collection)
            self.users_collection = self.db.users           # User info + resume data
            self.jobs_collection = self.db.jobs             # Job descriptions
            self.analyses_collection = self.db.analyses     # Analysis results
            
            print("DatabaseManager initialized - single resume storage (users table only)")
            
        except Exception as e:
            print(f"Error initializing database: {e}")
            raise
    
    def save_analysis(self, name, resume_data, job_requirements, match_score, 
                 explanation, job_title, company, original_resume=None, user_id=None):
        """
        Save analysis with resume in original uploaded format
        
        Args:
            original_resume: The resume in its original uploaded format (text, binary, etc.)
            resume_data: Parsed/processed resume data for analysis
            user_id: Optional user ID for authenticated users
        """
        try:
            print(f"    💾 Saving analysis for: {name}")
            
            # Save user WITH resume data (both original and processed)
            user_mongodb_id = self._save_user_resume(name, resume_data, original_resume, user_id)
            if user_mongodb_id is None:
                print(f"    ❌ User save failed - cannot continue")
                return None
            print(f"    ✅ User saved with _id: {user_mongodb_id}")
            
            # Save job data  
            job_mongodb_id = self._save_job(job_title, company, job_requirements)
            if job_mongodb_id is None:
                print(f"    ❌ Job save failed - cannot continue")
                return None
            print(f"    ✅ Job saved with _id: {job_mongodb_id}")
            
            # Save analysis with references
            analysis_doc = {
                "user_ref": user_mongodb_id,        # Reference to users._id
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
    
    def _save_user_resume(self, name, resume_data, original_resume=None, user_id=None):
        """Save user WITH resume data in users collection"""
        try:
            print(f"      👤 Processing user with resume: {name}")
            
            # If user_id is provided, use it to find the user
            if user_id:
                existing_user = self.users_collection.find_one({"_id": ObjectId(user_id)})
            else:
                # Check if user already exists by name
                existing_user = self.users_collection.find_one({"name": name})
            
            # Prepare resume storage with both formats
            resume_storage = {
                "processed_data": resume_data,  # Parsed data for analysis
                "original_format": original_resume,  # Original uploaded format
                "upload_timestamp": datetime.utcnow()
            }
            
            if existing_user:
                # Update existing user's resume data
                self.users_collection.update_one(
                    {"_id": existing_user["_id"]},
                    {
                        "$set": {
                            "resume_data": resume_storage,
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
                    "resume_data": resume_storage,    # Resume data stored here
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
    def get_user_with_resume(self, user_id):
        """Get user with resume data from users table"""
        try:
            return self.users_collection.find_one({"_id": ObjectId(user_id)})
        except Exception as e:
            print(f"Error getting user with resume: {e}")
            return None
    
    def get_all_users_with_resumes(self, limit=100):
        """Get all users with resume data"""
        try:
            users = list(self.users_collection.find({"resume_data": {"$exists": True}}).sort("created_at", -1).limit(limit))
            print(f"    👤 Found {len(users)} users with resume data")
            return users
        except Exception as e:
            print(f"Error getting users with resumes: {e}")
            return []
    
    def search_users_by_skills(self, skills):
        """Search users by skills in their processed resume data"""
        try:
            query = {"resume_data.processed_data.skills": {"$in": skills}}
            users = list(self.users_collection.find(query))
            return users
        except Exception as e:
            print(f"Error searching users by skills: {e}")
            return []
    
    def get_original_resume(self, user_id):
        """Get the original uploaded resume format for a user"""
        try:
            user = self.users_collection.find_one({"_id": ObjectId(user_id)})
            if user and "resume_data" in user and "original_format" in user["resume_data"]:
                return user["resume_data"]["original_format"]
            return None
        except Exception as e:
            print(f"Error getting original resume: {e}")
            return None
    
    def get_processed_resume(self, user_id):
        """Get the processed resume data for a user"""
        try:
            user = self.users_collection.find_one({"_id": ObjectId(user_id)})
            if user and "resume_data" in user and "processed_data" in user["resume_data"]:
                return user["resume_data"]["processed_data"]
            return None
        except Exception as e:
            print(f"Error getting processed resume: {e}")
            return None
    
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
    
    def get_user_analyses(self, user_id, limit=50):
        """Get all analyses for a specific user"""
        try:
            # Find analyses where the user_ref matches the user_id
            analyses = list(self.analyses_collection.find({
                "user_ref": ObjectId(user_id)
            }).sort("timestamp", -1).limit(limit))
            
            # Format the analyses for display
            formatted_analyses = []
            for analysis in analyses:
                formatted_analyses.append({
                    "job_title": analysis.get("job_title", "Unknown"),
                    "company": analysis.get("company", "Unknown"),
                    "match_score": analysis.get("match_score", 0),
                    "timestamp": analysis.get("timestamp", datetime.utcnow()).strftime("%Y-%m-%d %H:%M"),
                    "explanation": analysis.get("explanation", "")
                })
            
            return formatted_analyses
        except Exception as e:
            print(f"    ❌ Error getting user analyses: {e}")
            return []
    
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
    
    def get_all_jobs(self):
        try:
            jobs_cursor = self.jobs_collection.find()
            jobs = []

            for job_doc in jobs_cursor:
                jobs.append({
                    "id": str(job_doc.get("_id")),
                    "title": job_doc.get("job_title", ""),
                    "company": job_doc.get("company", ""),
                    #"description": self._format_job_requirements(job_doc.get("job_requirements", {}))
                    "created":job_doc.get("created_at", "")
                })

            return jobs

        except Exception as e:
            print(f"Error fetching jobs: {e}")
            return []
    
    def _format_job_requirements(self, reqs):
        try:
            if isinstance(reqs, dict):
                lines = []
                for key, value in reqs.items():
                    lines.append(f"{key}: {value}")
                return "\n".join(lines)
            return str(reqs)
        except Exception as e:
            print("Error formatting job requirements:", e)
            return "N/A"


# Schema Documentation
"""
DATABASE STRUCTURE:

1. users collection (added both original and processed resume data):
{
    "_id": ObjectId("auto-generated"),
    "name": "John Doe",
    "email": null,
    "password": null,
    "resume_data": {
        "processed_data": {             // ← Parsed data for analysis
            "skills": [...],
            "experience": [...],
            "education": [...]
        },
        "original_format": "...",       // ← Original uploaded format (text/binary)
        "upload_timestamp": ISODate
    },
    "created_at": ISODate,
    "updated_at": ISODate
}

2. jobs collection:
{
    "_id": ObjectId("auto-generated"),
    "job_title": "Software Engineer", 
    "company": "Tech Corp",
    "job_requirements": {...},
    "created_at": ISODate
}

3. analyses collection:
{
    "_id": ObjectId("auto-generated"),
    "user_ref": ObjectId,               // Reference to users._id
    "job_ref": ObjectId,                // Reference to jobs._id
    "match_score": 85,
    "explanation": "...",
    "timestamp": ISODate,
    "name": "John Doe",                 // Legacy fields
    "job_title": "Software Engineer",
    "company": "Tech Corp",
    "resume_data": {...},               // Legacy - duplicated processed data
    "job_requirements": {...}           // Legacy - duplicated
}
"""