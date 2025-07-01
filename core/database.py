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
import re

config = get_config()

class User(UserMixin):
    """Enhanced User class for Flask-Login integration with better error handling"""
    
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.email = user_data.get('email', '')
        self.name = user_data.get('name', '')
        self.created_at = user_data.get('created_at', datetime.utcnow())
        self.updated_at = user_data.get('updated_at', datetime.utcnow())
        self.has_resume = bool(user_data.get('resume_data'))
    
    def get_id(self):
        """Return user ID as string for Flask-Login"""
        return self.id
    
    @staticmethod
    def get(user_id):
        """Get user by ID for Flask-Login user loader"""
        try:
            if not user_id:
                return None
                
            # Handle both string and ObjectId
            if isinstance(user_id, str):
                if not ObjectId.is_valid(user_id):
                    return None
                user_id = ObjectId(user_id)
            
            db_manager = DatabaseManager()
            user_data = db_manager.get_user_by_id(user_id)
            
            if user_data:
                return User(user_data)
            return None
            
        except Exception as e:
            print(f"Error in User.get: {e}")
            return None
    
    def __repr__(self):
        return f'<User {self.email}>'


class DatabaseManager:
    """Enhanced Database manager with improved authentication and error handling"""
    
    def __init__(self):
        try:
            # Use existing configuration
            connection_string = getattr(config, 'MONGODB_URI', 'mongodb://localhost:27017/')
            db_name = getattr(config, 'DATABASE_NAME', 'resume_analyzer')
            
            self.client = MongoClient(connection_string)
            self.db = self.client[db_name]
            
            # Collection references
            self.users_collection = self.db.users
            self.jobs_collection = self.db.jobs
            self.analyses_collection = self.db.analyses
            
            # Create indexes for better performance
            self._create_indexes()
            
            print("Enhanced DatabaseManager initialized successfully")
            
        except Exception as e:
            print(f"Error initializing database: {e}")
            raise
    
    def _create_indexes(self):
        """Create database indexes for optimal performance"""
        try:
            # User collection indexes
            self.users_collection.create_index("email", unique=True)
            self.users_collection.create_index("created_at")
            
            # Job collection indexes
            self.jobs_collection.create_index([("job_title", 1), ("company", 1)])
            self.jobs_collection.create_index("created_at")
            
            # Analysis collection indexes
            self.analyses_collection.create_index("timestamp")
            self.analyses_collection.create_index("match_score")
            
        except Exception as e:
            # Indexes may already exist - this is normal
            pass
    
    def validate_email(self, email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def create_user(self, name, email, password):
        """Create new user with encrypted password and validation"""
        try:
            # Validate inputs
            if not name or len(name.strip()) < 2:
                print("Invalid name provided")
                return None
            
            if not email or not self.validate_email(email):
                print("Invalid email provided")
                return None
            
            if not password or len(password) < 8:
                print("Invalid password provided")
                return None
            
            # Normalize data
            name = name.strip()
            email = email.strip().lower()
            
            # Check if user already exists
            if self.get_user_by_email(email):
                print(f"User with email {email} already exists")
                return None
            
            # Create user document with encrypted password
            hashed_password = generate_password_hash(password)
            
            user_doc = {
                "name": name,
                "email": email,
                "password": hashed_password,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "resume_data": None,  # Will be populated when user uploads resume
                "is_active": True
            }
            
            result = self.users_collection.insert_one(user_doc)
            
            if result.inserted_id:
                print(f"User created successfully: {email}")
                return str(result.inserted_id)
            else:
                print("Failed to create user")
                return None
                
        except Exception as e:
            print(f"Error creating user: {e}")
            return None
    
    def verify_user(self, email, password):
        """Verify user credentials with encrypted password"""
        try:
            if not email or not password:
                return None
            
            email = email.strip().lower()
            
            # Find user by email
            user = self.users_collection.find_one({"email": email, "is_active": True})
            
            if user and user.get('password'):
                # Check password against hash
                if check_password_hash(user['password'], password):
                    # Update last login time
                    self.users_collection.update_one(
                        {"_id": user["_id"]},
                        {"$set": {"last_login": datetime.utcnow()}}
                    )
                    return user
            
            return None
            
        except Exception as e:
            print(f"Error verifying user: {e}")
            return None
    
    def get_user_by_email(self, email):
        """Find user by email"""
        try:
            if not email:
                return None
            
            email = email.strip().lower()
            return self.users_collection.find_one({"email": email, "is_active": True})
            
        except Exception as e:
            print(f"Error getting user by email: {e}")
            return None
    
    def get_user_by_id(self, user_id):
        """Find user by MongoDB _id"""
        try:
            if not user_id:
                return None
            
            # Handle both string and ObjectId
            if isinstance(user_id, str):
                if not ObjectId.is_valid(user_id):
                    return None
                user_id = ObjectId(user_id)
            
            return self.users_collection.find_one({"_id": user_id, "is_active": True})
            
        except Exception as e:
            print(f"Error getting user by ID: {e}")
            return None
    
    def update_user_password(self, user_id, new_password):
        """Update user password with encryption"""
        try:
            if not user_id or not new_password:
                return False
            
            if isinstance(user_id, str):
                user_id = ObjectId(user_id)
            
            hashed_password = generate_password_hash(new_password)
            
            result = self.users_collection.update_one(
                {"_id": user_id},
                {"$set": {
                    "password": hashed_password,
                    "updated_at": datetime.utcnow()
                }}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            print(f"Error updating password: {e}")
            return False
    
    def update_user_profile(self, user_id, name=None, email=None):
        """Update user profile information"""
        try:
            if not user_id:
                return False
            
            if isinstance(user_id, str):
                user_id = ObjectId(user_id)
            
            update_data = {"updated_at": datetime.utcnow()}
            
            if name and len(name.strip()) >= 2:
                update_data["name"] = name.strip()
            
            if email and self.validate_email(email):
                email = email.strip().lower()
                # Check if email is already taken by another user
                existing_user = self.users_collection.find_one({
                    "email": email,
                    "_id": {"$ne": user_id},
                    "is_active": True
                })
                if existing_user:
                    print("Email already taken by another user")
                    return False
                update_data["email"] = email
            
            if len(update_data) > 1:  # More than just updated_at
                result = self.users_collection.update_one(
                    {"_id": user_id},
                    {"$set": update_data}
                )
                return result.modified_count > 0
            
            return False
            
        except Exception as e:
            print(f"Error updating user profile: {e}")
            return False
    
    def deactivate_user(self, user_id):
        """Deactivate user account (soft delete)"""
        try:
            if not user_id:
                return False
            
            if isinstance(user_id, str):
                user_id = ObjectId(user_id)
            
            result = self.users_collection.update_one(
                {"_id": user_id},
                {"$set": {
                    "is_active": False,
                    "deactivated_at": datetime.utcnow()
                }}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            print(f"Error deactivating user: {e}")
            return False
    
    def get_user_stats(self, user_id):
        """Get statistics for a specific user"""
        try:
            if not user_id:
                return None
            
            if isinstance(user_id, str):
                user_id = ObjectId(user_id)
            
            # Get user info
            user = self.get_user_by_id(user_id)
            if not user:
                return None
            
            # Get user's analyses (by name matching for now)
            user_name = user.get('name', '')
            analyses = list(self.analyses_collection.find({"name": user_name}))
            
            if not analyses:
                return {
                    "total_analyses": 0,
                    "average_score": 0,
                    "best_score": 0,
                    "recent_analyses": []
                }
            
            # Calculate statistics
            scores = [a.get('match_score', 0) for a in analyses]
            total_analyses = len(analyses)
            average_score = sum(scores) / total_analyses if scores else 0
            best_score = max(scores) if scores else 0
            
            # Get recent analyses (last 5)
            recent_analyses = sorted(
                analyses,
                key=lambda x: x.get('timestamp', datetime.min),
                reverse=True
            )[:5]
            
            return {
                "total_analyses": total_analyses,
                "average_score": round(average_score, 1),
                "best_score": best_score,
                "recent_analyses": recent_analyses
            }
            
        except Exception as e:
            print(f"Error getting user stats: {e}")
            return None
    
    # Resume-related methods (existing functionality)
    def save_analysis(self, name, resume_data, job_requirements, match_score, 
                     explanation, job_title, company, original_resume=None):
        """Save analysis with resume in original uploaded format"""
        try:
            print(f"💾 Saving analysis for: {name}")
            
            # Save user WITH resume data (both original and processed)
            user_mongodb_id = self._save_user_resume(name, resume_data, original_resume)
            if user_mongodb_id is None:
                print(f"❌ User save failed - cannot continue")
                return None
            print(f"✅ User saved with _id: {user_mongodb_id}")
            
            # Save job data  
            job_mongodb_id = self._save_job(job_title, company, job_requirements)
            if job_mongodb_id is None:
                print(f"❌ Job save failed - cannot continue")
                return None
            print(f"✅ Job saved with _id: {job_mongodb_id}")
            
            # Save analysis with references
            analysis_doc = {
                "user_ref": user_mongodb_id,
                "job_ref": job_mongodb_id,
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
            print(f"✅ Analysis saved successfully with _id: {result.inserted_id}")
            return result.inserted_id
            
        except Exception as e:
            print(f"❌ Error saving analysis: {e}")
            return None
    
    def _save_user_resume(self, name, resume_data, original_resume=None):
        """Save user WITH resume data in users collection"""
        try:
            print(f"👤 Processing user with resume: {name}")
            
            # Check if user already exists by name
            existing_user = self.users_collection.find_one({
                "name": name,
                "is_active": True
            })
            
            # Prepare resume storage with both formats
            resume_storage = {
                "processed_data": resume_data,
                "original_format": original_resume,
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
                print(f"🔄 Updated existing user with resume: {name}")
                return existing_user["_id"]
            else:
                # Create new user WITH resume data (guest user)
                user_doc = {
                    "name": name,
                    "email": None,  # Guest user
                    "password": None,
                    "resume_data": resume_storage,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "is_active": True
                }
                
                result = self.users_collection.insert_one(user_doc)
                print(f"➕ Created new guest user with resume: {name} with _id: {result.inserted_id}")
                return result.inserted_id
                
        except Exception as e:
            print(f"❌ Error saving user with resume: {e}")
            return None
    
    def _save_job(self, job_title, company, job_requirements):
        """Save job description data"""
        try:
            print(f"💼 Processing job: {job_title} at {company}")
            
            # Check if job already exists
            existing_job = self.jobs_collection.find_one({
                "job_title": job_title,
                "company": company,
                "job_requirements": job_requirements
            })
            
            if existing_job:
                print(f"🔄 Job already exists with _id: {existing_job['_id']}")
                return existing_job["_id"]
            
            # Create new job
            job_doc = {
                "job_title": job_title,
                "company": company,
                "job_requirements": job_requirements,
                "created_at": datetime.utcnow()
            }
            
            result = self.jobs_collection.insert_one(job_doc)
            print(f"➕ Created new job with _id: {result.inserted_id}")
            return result.inserted_id
            
        except Exception as e:
            print(f"❌ Error saving job: {e}")
            return None
    
    # Existing methods for backward compatibility
    def get_all_analyses(self, limit=100):
        """Get all analyses from database"""
        try:
            analyses = list(self.analyses_collection.find().sort("timestamp", -1).limit(limit))
            return analyses
        except Exception as e:
            print(f"❌ Error getting analyses: {e}")
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
            print(f"❌ Error comparing candidates: {e}")
            return []
    
    def get_all_jobs(self):
        """Get all jobs for display"""
        try:
            jobs_cursor = self.jobs_collection.find()
            jobs = []

            for job_doc in jobs_cursor:
                jobs.append({
                    "id": str(job_doc.get("_id")),
                    "title": job_doc.get("job_title", ""),
                    "company": job_doc.get("company", ""),
                    "created": job_doc.get("created_at", "")
                })

            return jobs

        except Exception as e:
            print(f"Error fetching jobs: {e}")
            return []
    
    def get_user_with_resume(self, user_id):
        """Get user with resume data from users table"""
        try:
            if isinstance(user_id, str):
                user_id = ObjectId(user_id)
            return self.users_collection.find_one({"_id": user_id})
        except Exception as e:
            print(f"Error getting user with resume: {e}")
            return None
    
    def get_all_users_with_resumes(self, limit=100):
        """Get all users with resume data"""
        try:
            users = list(self.users_collection.find({
                "resume_data": {"$exists": True}
            }).sort("created_at", -1).limit(limit))
            print(f"👤 Found {len(users)} users with resume data")
            return users
        except Exception as e:
            print(f"Error getting users with resumes: {e}")
            return []
    
    def get_original_resume(self, user_id):
        """Get the original uploaded resume format for a user"""
        try:
            if isinstance(user_id, str):
                user_id = ObjectId(user_id)
            user = self.users_collection.find_one({"_id": user_id})
            if user and "resume_data" in user and "original_format" in user["resume_data"]:
                return user["resume_data"]["original_format"]
            return None
        except Exception as e:
            print(f"Error getting original resume: {e}")
            return None
    
    def get_processed_resume(self, user_id):
        """Get the processed resume data for a user"""
        try:
            if isinstance(user_id, str):
                user_id = ObjectId(user_id)
            user = self.users_collection.find_one({"_id": user_id})
            if user and "resume_data" in user and "processed_data" in user["resume_data"]:
                return user["resume_data"]["processed_data"]
            return None
        except Exception as e:
            print(f"Error getting processed resume: {e}")
            return None
    
    def close_connection(self):
        """Close database connection"""
        try:
            if hasattr(self, 'client'):
                self.client.close()
                print("Database connection closed")
        except Exception as e:
            print(f"Error closing database connection: {e}")
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.close_connection()