"""
File: data_access.py
Author: Jonathan Hu
Date Created: 6/20/25
Last Modified: 7/5/25
Description: Data Access Layer for ResumeMatchAI Platform

This module provides a high-level interface for accessing and analyzing
data from the database. It turns complex MongoDB operations into methods 
while providing advanced analytics and reporting capabilities.

Key Features:
- High-level data access methods for all collections
- Automatic database indexing for optimal performance
- JSON-serializable responses for API integration
- Advanced search and filtering capabilities
- Comprehensive analytics and reporting functions
- Error handling and data validation
- Pagination support for large datasets
- ObjectId conversion for API compatibility

Core Collections:
- users: User profiles, authentication data, and resume information
- jobs: Job descriptions, requirements, and company information
- analyses: Analysis results linking users to jobs with scores and explanations

Performance Optimizations:
- Strategic database indexing on frequently queried fields
- Efficient query patterns with proper sorting and limiting
- Connection pooling and resource management
- Caching-friendly data structures
- Optimized aggregation pipelines for analytics

Data Access Methods:
- User Management: CRUD operations, search, and profile management
- Job Management: Job listings, company searches, skill-based filtering
- Analysis Management: Score-based queries, candidate comparisons, trend analysis
- Analytics: Statistical summaries, skill demand analysis, talent pipeline insights

Search Capabilities:
- Full-text search across multiple collections
- Skill-based user and job matching
- Company and experience-based filtering
- Score range and date-based queries
- Advanced multi-criteria search with filters
- (More to come)

API Integration Features:
- Automatic ObjectId to string conversion
- JSON-serializable response formatting
- Consistent error handling and logging
- Pagination support for large result sets
- Optional ID conversion for flexibility

Database Schema Support:
- User profiles with resume data and skills
- Job postings with requirements and company info
- Analysis results with scores and explanations
- Timestamp tracking for all operations
- Relationship mapping between entities

Error Handling:
- Comprehensive exception catching and logging
- Degradation for database failures
- Input validation and sanitization
- Safe default values for failed operations
- Detailed error messages for debugging

Usage Examples:
# Basic data access
dal = DataAccessLayer()
users = dal.get_all_users(limit=50)
jobs = dal.get_jobs_by_company("Google")

# Advanced search
python_devs = dal.get_users_by_skill("Python")
top_candidates = dal.get_high_scoring_analyses(min_score=85)

# Analytics and reporting
stats = dal.get_database_stats()
skill_demand = dal.get_skill_demand_analysis()
user_report = dal.generate_user_report("user@example.com")

# Quick utility functions
user = quick_user_lookup("user@example.com")
candidates = quick_top_candidates(min_score=80)

Dependencies:
- PyMongo for MongoDB operations
- BSON for ObjectId handling
- Config module for database configuration
- Regular expressions for pattern matching
- Datetime for temporal queries

"""

from pymongo import MongoClient, ASCENDING, DESCENDING
from datetime import datetime, timedelta
from bson import ObjectId
from typing import List, Dict, Optional, Union, Any
import re
from config import get_config

config = get_config()


class DataAccessLayer:
    """
    Data access layer for resume analyzer database operations.
    Provides high-level, simple methods for data retrieval and analysis.
    """
    
    def __init__(self):
        """Initialize database connection and create performance indexes"""
        try:
            # Use existing configuration
            connection_string = getattr(config, 'MONGODB_URI', 'mongodb://localhost:27017/')
            db_name = getattr(config, 'DATABASE_NAME', 'resume_analyzer')
            
            self.client = MongoClient(connection_string)
            self.db = self.client[db_name]
            
            # Collection references
            self.users = self.db.users
            self.jobs = self.db.jobs
            self.analyses = self.db.analyses
            
            # Create performance indexes
            self._create_indexes()
            
            print("DataAccessLayer initialized successfully")
            
        except Exception as e:
            print(f"Error initializing DataAccessLayer: {e}")
            raise
    
    def _create_indexes(self):
        """Create database indexes for optimal query performance"""
        try:
            # User collection indexes
            self.users.create_index("email", unique=True)
            self.users.create_index("created_at")
            self.users.create_index("resume_data.skills")
            self.users.create_index("resume_data.experience.company")
            
            # Job collection indexes
            self.jobs.create_index([("job_title", 1), ("company", 1)])
            self.jobs.create_index("company")
            self.jobs.create_index("job_requirements.required_skills")
            self.jobs.create_index("created_at")
            
            # Analysis collection indexes
            self.analyses.create_index("user_id")
            self.analyses.create_index("job_id")
            self.analyses.create_index("match_score")
            self.analyses.create_index("timestamp")
            self.analyses.create_index([("job_title", 1), ("company", 1)])
            self.analyses.create_index([("company", 1), ("match_score", -1)])
            
        except Exception as e:
            # Indexes may already exist - this is normal
            pass

    def _convert_objectids(self, document: Dict) -> Dict:
        """Convert ObjectId fields to strings for JSON serialization"""
        if isinstance(document, dict):
            for key, value in document.items():
                if isinstance(value, ObjectId):
                    document[key] = str(value)
                elif isinstance(value, dict):
                    document[key] = self._convert_objectids(value)
                elif isinstance(value, list):
                    document[key] = [self._convert_objectids(item) if isinstance(item, dict) 
                                   else str(item) if isinstance(item, ObjectId) else item 
                                   for item in value]
        return document

    def _convert_objectids_list(self, documents: List[Dict]) -> List[Dict]:
        """Convert ObjectIds in a list of documents"""
        return [self._convert_objectids(doc.copy()) for doc in documents]

    # =================================================================
    # USER RETRIEVAL METHODS
    # =================================================================
    
    def get_user_by_email(self, email: str, convert_ids: bool = True) -> Optional[Dict]:
        """
        Get user by email address
        
        Args:
            email: User's email address
            convert_ids: Whether to convert ObjectIds to strings
            
        Returns:
            User document or None if not found
        """
        try:
            user = self.users.find_one({"email": email})
            if user and convert_ids:
                user = self._convert_objectids(user)
            return user
        except Exception as e:
            print(f"Error getting user by email: {e}")
            return None

    def get_user_by_id(self, user_id: Union[str, ObjectId], convert_ids: bool = True) -> Optional[Dict]:
        """
        Get user by ID
        
        Args:
            user_id: User's ObjectId (string or ObjectId)
            convert_ids: Whether to convert ObjectIds to strings
            
        Returns:
            User document or None if not found
        """
        try:
            if isinstance(user_id, str):
                user_id = ObjectId(user_id)
            user = self.users.find_one({"_id": user_id})
            if user and convert_ids:
                user = self._convert_objectids(user)
            return user
        except Exception as e:
            print(f"Error getting user by ID: {e}")
            return None
    
    def get_all_users(self, limit: int = 100, skip: int = 0, convert_ids: bool = True) -> List[Dict]:
        """
        Get all users with pagination
        
        Args:
            limit: Maximum number of users to return
            skip: Number of users to skip (for pagination)
            convert_ids: Whether to convert ObjectIds to strings
            
        Returns:
            List of user documents
        """
        try:
            users = list(self.users.find()
                        .sort("created_at", DESCENDING)
                        .skip(skip)
                        .limit(limit))
            return self._convert_objectids_list(users) if convert_ids else users
        except Exception as e:
            print(f"Error getting all users: {e}")
            return []
    
    def search_users_by_name(self, name_pattern: str, limit: int = 50, convert_ids: bool = True) -> List[Dict]:
        """
        Search users by name (case-insensitive partial match)
        
        Args:
            name_pattern: Name pattern to search for
            limit: Maximum number of results
            convert_ids: Whether to convert ObjectIds to strings
            
        Returns:
            List of matching users
        """
        try:
            regex = re.compile(name_pattern, re.IGNORECASE)
            users = list(self.users.find({"name": regex})
                        .sort("name", ASCENDING)
                        .limit(limit))
            return self._convert_objectids_list(users) if convert_ids else users
        except Exception as e:
            print(f"Error searching users by name: {e}")
            return []
    
    def get_users_by_skill(self, skill: str, limit: int = 50, convert_ids: bool = True) -> List[Dict]:
        """
        Find users who have a specific skill
        
        Args:
            skill: Skill to search for (case-insensitive)
            limit: Maximum number of results
            convert_ids: Whether to convert ObjectIds to strings
            
        Returns:
            List of users with the specified skill
        """
        try:
            regex = re.compile(skill, re.IGNORECASE)
            users = list(self.users.find({"resume_data.skills": regex})
                        .sort("updated_at", DESCENDING)
                        .limit(limit))
            return self._convert_objectids_list(users) if convert_ids else users
        except Exception as e:
            print(f"Error getting users by skill: {e}")
            return []
    
    def get_users_by_company_experience(self, company: str, limit: int = 50, convert_ids: bool = True) -> List[Dict]:
        """
        Find users who worked at a specific company
        
        Args:
            company: Company name to search for (case-insensitive)
            limit: Maximum number of results
            convert_ids: Whether to convert ObjectIds to strings
            
        Returns:
            List of users who worked at the company
        """
        try:
            regex = re.compile(company, re.IGNORECASE)
            users = list(self.users.find({"resume_data.experience.company": regex})
                        .sort("updated_at", DESCENDING)
                        .limit(limit))
            return self._convert_objectids_list(users) if convert_ids else users
        except Exception as e:
            print(f"Error getting users by company experience: {e}")
            return []
    
    def get_users_by_education(self, degree_or_institution: str, limit: int = 50, convert_ids: bool = True) -> List[Dict]:
        """
        Find users by degree or educational institution
        
        Args:
            degree_or_institution: Degree or institution name (case-insensitive)
            limit: Maximum number of results
            convert_ids: Whether to convert ObjectIds to strings
            
        Returns:
            List of users matching education criteria
        """
        try:
            regex = re.compile(degree_or_institution, re.IGNORECASE)
            users = list(self.users.find({
                "$or": [
                    {"resume_data.education.degree": regex},
                    {"resume_data.education.institution": regex}
                ]
            }).sort("updated_at", DESCENDING).limit(limit))
            return self._convert_objectids_list(users) if convert_ids else users
        except Exception as e:
            print(f"Error getting users by education: {e}")
            return []
    
    def get_recent_users(self, days: int = 30, limit: int = 100, convert_ids: bool = True) -> List[Dict]:
        """
        Get users created in the last N days
        
        Args:
            days: Number of days to look back
            limit: Maximum number of results
            convert_ids: Whether to convert ObjectIds to strings
            
        Returns:
            List of recently created users
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            users = list(self.users.find({"created_at": {"$gte": cutoff_date}})
                        .sort("created_at", DESCENDING)
                        .limit(limit))
            return self._convert_objectids_list(users) if convert_ids else users
        except Exception as e:
            print(f"Error getting recent users: {e}")
            return []

    # =================================================================
    # JOB RETRIEVAL METHODS
    # =================================================================
    
    def get_job_by_id(self, job_id: Union[str, ObjectId], convert_ids: bool = True) -> Optional[Dict]:
        """
        Get job by ID
        
        Args:
            job_id: Job's ObjectId (string or ObjectId)
            convert_ids: Whether to convert ObjectIds to strings
            
        Returns:
            Job document or None if not found
        """
        try:
            if isinstance(job_id, str):
                job_id = ObjectId(job_id)
            job = self.jobs.find_one({"_id": job_id})
            if job and convert_ids:
                job = self._convert_objectids(job)
            return job
        except Exception as e:
            print(f"Error getting job by ID: {e}")
            return None
    
    def get_all_jobs(self, limit: int = 100, skip: int = 0, convert_ids: bool = True) -> List[Dict]:
        """
        Get all jobs with pagination
        
        Args:
            limit: Maximum number of jobs to return
            skip: Number of jobs to skip (for pagination)
            convert_ids: Whether to convert ObjectIds to strings
            
        Returns:
            List of job documents
        """
        try:
            jobs = list(self.jobs.find()
                       .sort("created_at", DESCENDING)
                       .skip(skip)
                       .limit(limit))
            return self._convert_objectids_list(jobs) if convert_ids else jobs
        except Exception as e:
            print(f"Error getting all jobs: {e}")
            return []
    
    def get_jobs_by_company(self, company: str, limit: int = 50, convert_ids: bool = True) -> List[Dict]:
        """
        Find jobs by company (case-insensitive partial match)
        
        Args:
            company: Company name to search for
            limit: Maximum number of results
            convert_ids: Whether to convert ObjectIds to strings
            
        Returns:
            List of jobs at the specified company
        """
        try:
            regex = re.compile(company, re.IGNORECASE)
            jobs = list(self.jobs.find({"company": regex})
                       .sort("created_at", DESCENDING)
                       .limit(limit))
            return self._convert_objectids_list(jobs) if convert_ids else jobs
        except Exception as e:
            print(f"Error getting jobs by company: {e}")
            return []
    
    def get_jobs_by_title(self, title: str, limit: int = 50, convert_ids: bool = True) -> List[Dict]:
        """
        Find jobs by title (case-insensitive partial match)
        
        Args:
            title: Job title to search for
            limit: Maximum number of results
            convert_ids: Whether to convert ObjectIds to strings
            
        Returns:
            List of jobs with matching titles
        """
        try:
            regex = re.compile(title, re.IGNORECASE)
            jobs = list(self.jobs.find({"job_title": regex})
                       .sort("created_at", DESCENDING)
                       .limit(limit))
            return self._convert_objectids_list(jobs) if convert_ids else jobs
        except Exception as e:
            print(f"Error getting jobs by title: {e}")
            return []
    
    def search_jobs(self, search_term: str, limit: int = 50, convert_ids: bool = True) -> List[Dict]:
        """
        Search jobs by company OR title
        
        Args:
            search_term: Term to search for in company or title
            limit: Maximum number of results
            convert_ids: Whether to convert ObjectIds to strings
            
        Returns:
            List of matching jobs
        """
        try:
            regex = re.compile(search_term, re.IGNORECASE)
            jobs = list(self.jobs.find({
                "$or": [
                    {"company": regex},
                    {"job_title": regex}
                ]
            }).sort("created_at", DESCENDING).limit(limit))
            return self._convert_objectids_list(jobs) if convert_ids else jobs
        except Exception as e:
            print(f"Error searching jobs: {e}")
            return []
    
    def get_jobs_requiring_skill(self, skill: str, limit: int = 50, convert_ids: bool = True) -> List[Dict]:
        """
        Find jobs that require a specific skill
        
        Args:
            skill: Skill to search for
            limit: Maximum number of results
            convert_ids: Whether to convert ObjectIds to strings
            
        Returns:
            List of jobs requiring the skill
        """
        try:
            regex = re.compile(skill, re.IGNORECASE)
            jobs = list(self.jobs.find({
                "$or": [
                    {"job_requirements.required_skills": regex},
                    {"job_requirements.preferred_skills": regex}
                ]
            }).sort("created_at", DESCENDING).limit(limit))
            return self._convert_objectids_list(jobs) if convert_ids else jobs
        except Exception as e:
            print(f"Error getting jobs by skill requirement: {e}")
            return []
    
    def get_recent_jobs(self, days: int = 30, limit: int = 100, convert_ids: bool = True) -> List[Dict]:
        """
        Get jobs posted in the last N days
        
        Args:
            days: Number of days to look back
            limit: Maximum number of results
            convert_ids: Whether to convert ObjectIds to strings
            
        Returns:
            List of recently posted jobs
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            jobs = list(self.jobs.find({"created_at": {"$gte": cutoff_date}})
                       .sort("created_at", DESCENDING)
                       .limit(limit))
            return self._convert_objectids_list(jobs) if convert_ids else jobs
        except Exception as e:
            print(f"Error getting recent jobs: {e}")
            return []
    
    def get_unique_companies(self, limit: int = 100) -> List[str]:
        """
        Get list of unique companies
        
        Args:
            limit: Maximum number of companies to return
            
        Returns:
            List of unique company names
        """
        try:
            return self.jobs.distinct("company")[:limit]
        except Exception as e:
            print(f"Error getting unique companies: {e}")
            return []
    
    def get_unique_job_titles(self, limit: int = 100) -> List[str]:
        """
        Get list of unique job titles
        
        Args:
            limit: Maximum number of titles to return
            
        Returns:
            List of unique job titles
        """
        try:
            return self.jobs.distinct("job_title")[:limit]
        except Exception as e:
            print(f"Error getting unique job titles: {e}")
            return []

    # =================================================================
    # ANALYSIS RETRIEVAL METHODS
    # =================================================================
    
    def get_analysis_by_id(self, analysis_id: Union[str, ObjectId], convert_ids: bool = True) -> Optional[Dict]:
        """
        Get analysis by ID
        
        Args:
            analysis_id: Analysis ObjectId (string or ObjectId)
            convert_ids: Whether to convert ObjectIds to strings
            
        Returns:
            Analysis document or None if not found
        """
        try:
            if isinstance(analysis_id, str):
                analysis_id = ObjectId(analysis_id)
            analysis = self.analyses.find_one({"_id": analysis_id})
            if analysis and convert_ids:
                analysis = self._convert_objectids(analysis)
            return analysis
        except Exception as e:
            print(f"Error getting analysis by ID: {e}")
            return None
    
    def get_all_analyses(self, limit: int = 100, skip: int = 0, convert_ids: bool = True) -> List[Dict]:
        """
        Get all analyses with pagination
        
        Args:
            limit: Maximum number of analyses to return
            skip: Number of analyses to skip (for pagination)
            convert_ids: Whether to convert ObjectIds to strings
            
        Returns:
            List of analysis documents
        """
        try:
            analyses = list(self.analyses.find()
                           .sort("timestamp", DESCENDING)
                           .skip(skip)
                           .limit(limit))
            return self._convert_objectids_list(analyses) if convert_ids else analyses
        except Exception as e:
            print(f"Error getting all analyses: {e}")
            return []
    
    def get_analyses_by_user_id(self, user_id: Union[str, ObjectId], limit: int = 50, convert_ids: bool = True) -> List[Dict]:
        """
        Get all analyses for a specific user
        
        Args:
            user_id: User's ObjectId (string or ObjectId)
            limit: Maximum number of results
            convert_ids: Whether to convert ObjectIds to strings
            
        Returns:
            List of user's analyses
        """
        try:
            if isinstance(user_id, str):
                user_id = ObjectId(user_id)
            analyses = list(self.analyses.find({"user_id": user_id})
                           .sort("timestamp", DESCENDING)
                           .limit(limit))
            return self._convert_objectids_list(analyses) if convert_ids else analyses
        except Exception as e:
            print(f"Error getting analyses by user ID: {e}")
            return []
    
    def get_analyses_by_user_email(self, email: str, limit: int = 50, convert_ids: bool = True) -> List[Dict]:
        """
        Get all analyses for a user by email
        
        Args:
            email: User's email address
            limit: Maximum number of results
            convert_ids: Whether to convert ObjectIds to strings
            
        Returns:
            List of user's analyses
        """
        try:
            user = self.get_user_by_email(email, convert_ids=False)
            if user:
                return self.get_analyses_by_user_id(user["_id"], limit, convert_ids)
            return []
        except Exception as e:
            print(f"Error getting analyses by user email: {e}")
            return []
    
    def get_analyses_by_job_id(self, job_id: Union[str, ObjectId], limit: int = 50, convert_ids: bool = True) -> List[Dict]:
        """
        Get all analyses for a specific job
        
        Args:
            job_id: Job's ObjectId (string or ObjectId)
            limit: Maximum number of results
            convert_ids: Whether to convert ObjectIds to strings
            
        Returns:
            List of analyses for the job
        """
        try:
            if isinstance(job_id, str):
                job_id = ObjectId(job_id)
            analyses = list(self.analyses.find({"job_id": job_id})
                           .sort("match_score", DESCENDING)
                           .limit(limit))
            return self._convert_objectids_list(analyses) if convert_ids else analyses
        except Exception as e:
            print(f"Error getting analyses by job ID: {e}")
            return []
    
    def get_analyses_by_company(self, company: str, limit: int = 100, convert_ids: bool = True) -> List[Dict]:
        """
        Get all analyses for jobs at a specific company
        
        Args:
            company: Company name to search for
            limit: Maximum number of results
            convert_ids: Whether to convert ObjectIds to strings
            
        Returns:
            List of analyses for company jobs
        """
        try:
            regex = re.compile(company, re.IGNORECASE)
            analyses = list(self.analyses.find({"company": regex})
                           .sort("match_score", DESCENDING)
                           .limit(limit))
            return self._convert_objectids_list(analyses) if convert_ids else analyses
        except Exception as e:
            print(f"Error getting analyses by company: {e}")
            return []
    
    def get_analyses_by_job_title(self, job_title: str, limit: int = 100, convert_ids: bool = True) -> List[Dict]:
        """
        Get all analyses for a specific job title
        
        Args:
            job_title: Job title to search for
            limit: Maximum number of results
            convert_ids: Whether to convert ObjectIds to strings
            
        Returns:
            List of analyses for the job title
        """
        try:
            regex = re.compile(job_title, re.IGNORECASE)
            analyses = list(self.analyses.find({"job_title": regex})
                           .sort("match_score", DESCENDING)
                           .limit(limit))
            return self._convert_objectids_list(analyses) if convert_ids else analyses
        except Exception as e:
            print(f"Error getting analyses by job title: {e}")
            return []
    
    def get_high_scoring_analyses(self, min_score: int = 80, limit: int = 100, convert_ids: bool = True) -> List[Dict]:
        """
        Get analyses with match score above threshold
        
        Args:
            min_score: Minimum match score
            limit: Maximum number of results
            convert_ids: Whether to convert ObjectIds to strings
            
        Returns:
            List of high-scoring analyses
        """
        try:
            analyses = list(self.analyses.find({"match_score": {"$gte": min_score}})
                           .sort("match_score", DESCENDING)
                           .limit(limit))
            return self._convert_objectids_list(analyses) if convert_ids else analyses
        except Exception as e:
            print(f"Error getting high scoring analyses: {e}")
            return []
    
    def get_analyses_by_score_range(self, min_score: int, max_score: int, limit: int = 100, convert_ids: bool = True) -> List[Dict]:
        """
        Get analyses within a specific score range
        
        Args:
            min_score: Minimum match score
            max_score: Maximum match score
            limit: Maximum number of results
            convert_ids: Whether to convert ObjectIds to strings
            
        Returns:
            List of analyses within score range
        """
        try:
            analyses = list(self.analyses.find({
                "match_score": {"$gte": min_score, "$lte": max_score}
            }).sort("match_score", DESCENDING).limit(limit))
            return self._convert_objectids_list(analyses) if convert_ids else analyses
        except Exception as e:
            print(f"Error getting analyses by score range: {e}")
            return []
    
    def get_recent_analyses(self, days: int = 30, limit: int = 100, convert_ids: bool = True) -> List[Dict]:
        """
        Get analyses from the last N days
        
        Args:
            days: Number of days to look back
            limit: Maximum number of results
            convert_ids: Whether to convert ObjectIds to strings
            
        Returns:
            List of recent analyses
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            analyses = list(self.analyses.find({"timestamp": {"$gte": cutoff_date}})
                           .sort("timestamp", DESCENDING)
                           .limit(limit))
            return self._convert_objectids_list(analyses) if convert_ids else analyses
        except Exception as e:
            print(f"Error getting recent analyses: {e}")
            return []
    
    def compare_candidates_for_position(self, job_title: str, company: str, limit: int = 10, convert_ids: bool = True) -> List[Dict]:
        """
        Compare candidates for the same position (ranked by score)
        
        Args:
            job_title: Job title to search for
            company: Company name
            limit: Maximum number of candidates
            convert_ids: Whether to convert ObjectIds to strings
            
        Returns:
            List of candidates ranked by match score
        """
        try:
            candidates = list(self.analyses.find({
                "job_title": job_title,
                "company": company
            }).sort("match_score", DESCENDING).limit(limit))
            return self._convert_objectids_list(candidates) if convert_ids else candidates
        except Exception as e:
            print(f"Error comparing candidates: {e}")
            return []

    # =================================================================
    # ADVANCED ANALYTICS AND STATISTICS
    # =================================================================
    
    def get_user_analysis_summary(self, user_id: Union[str, ObjectId]) -> Dict[str, Any]:
        """
        Get summary statistics for a user's analyses
        
        Args:
            user_id: User's ObjectId (string or ObjectId)
            
        Returns:
            Dictionary with user's analysis statistics
        """
        try:
            if isinstance(user_id, str):
                user_id = ObjectId(user_id)
            
            pipeline = [
                {"$match": {"user_id": user_id}},
                {"$group": {
                    "_id": None,
                    "total_analyses": {"$sum": 1},
                    "avg_score": {"$avg": "$match_score"},
                    "max_score": {"$max": "$match_score"},
                    "min_score": {"$min": "$match_score"},
                    "job_titles": {"$addToSet": "$job_title"},
                    "high_quality_candidates": {
                        "$sum": {"$cond": [{"$gte": ["$match_score", 80]}, 1, 0]}
                    },
                    "excellent_candidates": {
                        "$sum": {"$cond": [{"$gte": ["$match_score", 90]}, 1, 0]}
                    }
                }}
            ]
            
            result = list(self.analyses.aggregate(pipeline))
            if result:
                stats = result[0]
                stats["num_positions"] = len(stats["job_titles"])
                stats["avg_score"] = round(stats["avg_score"], 2) if stats["avg_score"] else 0
                stats["high_quality_percentage"] = (
                    round((stats["high_quality_candidates"] / stats["total_applications"]) * 100, 2)
                    if stats["total_applications"] > 0 else 0
                )
                stats["excellent_percentage"] = (
                    round((stats["excellent_candidates"] / stats["total_applications"]) * 100, 2)
                    if stats["total_applications"] > 0 else 0
                )
                return stats
            return {
                "total_applications": 0,
                "avg_score": 0,
                "max_score": 0,
                "min_score": 0,
                "num_positions": 0,
                "high_quality_candidates": 0,
                "excellent_candidates": 0,
                "high_quality_percentage": 0,
                "excellent_percentage": 0,
                "job_titles": []
            }
            
        except Exception as e:
            print(f"Error getting company hiring stats: {e}")
            return {}
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get overall database statistics
        
        Returns:
            Dictionary with comprehensive database statistics
        """
        try:
            # Basic counts
            total_users = self.users.count_documents({})
            total_jobs = self.jobs.count_documents({})
            total_analyses = self.analyses.count_documents({})
            
            # Advanced stats
            unique_companies = len(self.get_unique_companies())
            unique_job_titles = len(self.get_unique_job_titles())
            avg_match_score = self._get_average_match_score()
            
            # Recent activity (last 30 days)
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            recent_users = self.users.count_documents({"created_at": {"$gte": cutoff_date}})
            recent_jobs = self.jobs.count_documents({"created_at": {"$gte": cutoff_date}})
            recent_analyses = self.analyses.count_documents({"timestamp": {"$gte": cutoff_date}})
            
            return {
                "total_users": total_users,
                "total_jobs": total_jobs,
                "total_analyses": total_analyses,
                "unique_companies": unique_companies,
                "unique_job_titles": unique_job_titles,
                "avg_match_score": avg_match_score,
                "recent_activity": {
                    "new_users_30d": recent_users,
                    "new_jobs_30d": recent_jobs,
                    "new_analyses_30d": recent_analyses
                },
                "last_updated": datetime.utcnow()
            }
        except Exception as e:
            print(f"Error getting database stats: {e}")
            return {}
    
    def _get_average_match_score(self) -> float:
        """Calculate average match score across all analyses"""
        try:
            pipeline = [
                {"$group": {"_id": None, "avg_score": {"$avg": "$match_score"}}}
            ]
            result = list(self.analyses.aggregate(pipeline))
            return round(result[0]["avg_score"], 2) if result else 0.0
        except:
            return 0.0

    # =================================================================
    # ADVANCED SEARCH AND FILTERING
    # =================================================================
    
    def advanced_search_analyses(self, filters: Dict[str, Any], limit: int = 100, convert_ids: bool = True) -> List[Dict]:
        """
        Advanced search with multiple filters
        
        Args:
            filters: Dictionary of search criteria
            limit: Maximum number of results
            convert_ids: Whether to convert ObjectIds to strings
            
        Example filters:
            {
                "min_score": 70,
                "max_score": 95,
                "company": "Google",
                "job_title": "Engineer",
                "days_ago": 30,
                "user_email": "john@example.com"
            }
            
        Returns:
            List of matching analyses
        """
        try:
            query = {}
            
            # Score range filters
            if "min_score" in filters or "max_score" in filters:
                score_filter = {}
                if "min_score" in filters:
                    score_filter["$gte"] = filters["min_score"]
                if "max_score" in filters:
                    score_filter["$lte"] = filters["max_score"]
                query["match_score"] = score_filter
            
            # Company filter
            if "company" in filters:
                query["company"] = re.compile(filters["company"], re.IGNORECASE)
            
            # Job title filter
            if "job_title" in filters:
                query["job_title"] = re.compile(filters["job_title"], re.IGNORECASE)
            
            # Date filter
            if "days_ago" in filters:
                cutoff_date = datetime.utcnow() - timedelta(days=filters["days_ago"])
                query["timestamp"] = {"$gte": cutoff_date}
            
            # User email filter
            if "user_email" in filters:
                user = self.get_user_by_email(filters["user_email"], convert_ids=False)
                if user:
                    query["user_id"] = user["_id"]
                else:
                    return []  # User not found
            
            # User ID filter
            if "user_id" in filters:
                if isinstance(filters["user_id"], str):
                    query["user_id"] = ObjectId(filters["user_id"])
                else:
                    query["user_id"] = filters["user_id"]
            
            # Job ID filter
            if "job_id" in filters:
                if isinstance(filters["job_id"], str):
                    query["job_id"] = ObjectId(filters["job_id"])
                else:
                    query["job_id"] = filters["job_id"]
            
            analyses = list(self.analyses.find(query)
                           .sort("match_score", DESCENDING)
                           .limit(limit))
            return self._convert_objectids_list(analyses) if convert_ids else analyses
            
        except Exception as e:
            print(f"Error in advanced search: {e}")
            return []
    
    def search_everything(self, query: str, limit_per_type: int = 10, convert_ids: bool = True) -> Dict[str, Any]:
        """
        Universal search across users, jobs, and analyses
        
        Args:
            query: Search term
            limit_per_type: Maximum results per category
            convert_ids: Whether to convert ObjectIds to strings
            
        Returns:
            Dictionary with search results for each category
        """
        try:
            results = {}
            
            # Search users by name
            results["users"] = self.search_users_by_name(query, limit_per_type, convert_ids)
            
            # Search jobs by company or title
            results["jobs"] = self.search_jobs(query, limit_per_type, convert_ids)
            
            # Search analyses by company or job title
            results["analyses"] = self.advanced_search_analyses({
                "$or": [
                    {"company": query},
                    {"job_title": query}
                ]
            }, limit_per_type, convert_ids)
            
            return {
                "query": query,
                "results": results,
                "total_found": len(results["users"]) + len(results["jobs"]) + len(results["analyses"]),
                "success": True
            }
            
        except Exception as e:
            print(f"Universal search failed: {e}")
            return {"error": f"Search failed: {e}", "success": False}

    # =================================================================
    # SPECIALIZED QUERY METHODS
    # =================================================================
    
    def get_top_candidates_across_companies(self, limit: int = 50, convert_ids: bool = True) -> List[Dict]:
        """
        Get top-scoring candidates across all companies
        
        Args:
            limit: Maximum number of candidates
            convert_ids: Whether to convert ObjectIds to strings
            
        Returns:
            List of top candidates sorted by match score
        """
        try:
            candidates = list(self.analyses.find()
                             .sort("match_score", DESCENDING)
                             .limit(limit))
            return self._convert_objectids_list(candidates) if convert_ids else candidates
        except Exception as e:
            print(f"Error getting top candidates: {e}")
            return []
    
    def get_skill_demand_analysis(self, limit: int = 20) -> List[Dict]:
        """
        Analyze which skills are most in demand by jobs
        
        Args:
            limit: Maximum number of skills to return
            
        Returns:
            List of skills with demand counts
        """
        try:
            pipeline = [
                {"$unwind": "$job_requirements.required_skills"},
                {"$group": {
                    "_id": {"$toLower": "$job_requirements.required_skills"},
                    "demand_count": {"$sum": 1},
                    "companies": {"$addToSet": "$company"}
                }},
                {"$project": {
                    "skill": "$_id",
                    "demand_count": 1,
                    "company_count": {"$size": "$companies"},
                    "_id": 0
                }},
                {"$sort": {"demand_count": -1}},
                {"$limit": limit}
            ]
            
            return list(self.jobs.aggregate(pipeline))
        except Exception as e:
            print(f"Error getting skill demand analysis: {e}")
            return []
    
    def get_user_skill_gaps(self, user_id: Union[str, ObjectId], limit: int = 10) -> List[Dict]:
        """
        Identify skill gaps for a user based on their applications
        
        Args:
            user_id: User's ObjectId (string or ObjectId)
            limit: Maximum number of gaps to return
            
        Returns:
            List of missing skills with frequency
        """
        try:
            if isinstance(user_id, str):
                user_id = ObjectId(user_id)
            
            # Get user's current skills
            user = self.get_user_by_id(user_id, convert_ids=False)
            if not user or not user.get("resume_data", {}).get("skills"):
                return []
            
            user_skills = [skill.lower() for skill in user["resume_data"]["skills"]]
            
            # Get jobs the user applied to
            user_analyses = self.get_analyses_by_user_id(user_id, limit=100, convert_ids=False)
            
            # Collect required skills from all jobs applied to
            missing_skills = {}
            for analysis in user_analyses:
                job_skills = analysis.get("job_requirements", {}).get("required_skills", [])
                for skill in job_skills:
                    skill_lower = skill.lower()
                    if skill_lower not in user_skills:
                        missing_skills[skill] = missing_skills.get(skill, 0) + 1
            
            # Sort by frequency
            skill_gaps = [
                {"skill": skill, "frequency": count}
                for skill, count in sorted(missing_skills.items(), key=lambda x: x[1], reverse=True)
            ]
            
            return skill_gaps[:limit]
            
        except Exception as e:
            print(f"Error getting user skill gaps: {e}")
            return []
    
    def get_company_talent_pipeline(self, company: str, min_score: int = 70, limit: int = 50, convert_ids: bool = True) -> List[Dict]:
        """
        Get potential talent pipeline for a company (qualified candidates)
        
        Args:
            company: Company name
            min_score: Minimum match score threshold
            limit: Maximum number of candidates
            convert_ids: Whether to convert ObjectIds to strings
            
        Returns:
            List of qualified candidates for the company
        """
        try:
            pipeline = [
                {"$match": {
                    "company": re.compile(company, re.IGNORECASE),
                    "match_score": {"$gte": min_score}
                }},
                {"$group": {
                    "_id": "$user_id",
                    "best_score": {"$max": "$match_score"},
                    "applications_count": {"$sum": 1},
                    "positions_applied": {"$addToSet": "$job_title"},
                    "latest_application": {"$max": "$timestamp"}
                }},
                {"$sort": {"best_score": -1}},
                {"$limit": limit}
            ]
            
            talent_pipeline = list(self.analyses.aggregate(pipeline))
            
            # Enrich with user details
            enriched_pipeline = []
            for candidate in talent_pipeline:
                user = self.get_user_by_id(candidate["_id"], convert_ids=convert_ids)
                if user:
                    candidate["user_details"] = user
                    candidate["_id"] = str(candidate["_id"]) if convert_ids else candidate["_id"]
                    enriched_pipeline.append(candidate)
            
            return enriched_pipeline
            
        except Exception as e:
            print(f"Error getting company talent pipeline: {e}")
            return []

    # =================================================================
    # REPORTING AND ANALYTICS METHODS
    # =================================================================
    
    def generate_user_report(self, user_email: str) -> Dict[str, Any]:
        """
        Generate comprehensive report for a user
        
        Args:
            user_email: User's email address
            
        Returns:
            Complete user report with profile, analyses, and insights
        """
        try:
            user = self.get_user_by_email(user_email)
            if not user:
                return {"error": "User not found", "success": False}
            
            # Get user's analyses
            analyses = self.get_analyses_by_user_email(user_email, limit=100)
            summary = self.get_user_analysis_summary(user["_id"])
            skill_gaps = self.get_user_skill_gaps(user["_id"])
            
            # Calculate additional insights
            insights = {
                "most_applied_company": self._get_most_frequent_value(analyses, "company"),
                "most_applied_role": self._get_most_frequent_value(analyses, "job_title"),
                "score_trend": self._calculate_score_trend(analyses),
                "application_frequency": len(analyses) / max((datetime.utcnow() - user["created_at"]).days, 1)
            }
            
            return {
                "user_profile": user,
                "analysis_summary": summary,
                "recent_analyses": analyses[:10],
                "skill_gaps": skill_gaps,
                "insights": insights,
                "success": True
            }
            
        except Exception as e:
            print(f"Error generating user report: {e}")
            return {"error": f"Report generation failed: {e}", "success": False}
    
    def generate_company_report(self, company: str) -> Dict[str, Any]:
        """
        Generate comprehensive report for a company
        
        Args:
            company: Company name
            
        Returns:
            Complete company report with jobs, candidates, and analytics
        """
        try:
            # Get company data
            jobs = self.get_jobs_by_company(company, limit=100)
            analyses = self.get_analyses_by_company(company, limit=500)
            stats = self.get_company_hiring_stats(company)
            talent_pipeline = self.get_company_talent_pipeline(company)
            
            # Calculate insights
            insights = {
                "most_popular_role": self._get_most_frequent_value(analyses, "job_title"),
                "average_applications_per_job": len(analyses) / max(len(jobs), 1),
                "hiring_difficulty": self._calculate_hiring_difficulty(analyses),
                "top_skills_needed": self._get_top_required_skills(jobs)
            }
            
            return {
                "company_name": company,
                "jobs": jobs,
                "hiring_stats": stats,
                "talent_pipeline": talent_pipeline[:20],
                "recent_analyses": analyses[:20],
                "insights": insights,
                "success": True
            }
            
        except Exception as e:
            print(f"Error generating company report: {e}")
            return {"error": f"Report generation failed: {e}", "success": False}
    
    def _get_most_frequent_value(self, items: List[Dict], field: str) -> str:
        """Get the most frequently occurring value for a field"""
        if not items:
            return "N/A"
        
        frequency = {}
        for item in items:
            value = item.get(field, "Unknown")
            frequency[value] = frequency.get(value, 0) + 1
        
        return max(frequency, key=frequency.get) if frequency else "N/A"
    
    def _calculate_score_trend(self, analyses: List[Dict]) -> str:
        """Calculate if user's scores are improving, declining, or stable"""
        if len(analyses) < 2:
            return "Insufficient data"
        
        # Sort by timestamp (newest first due to our query)
        recent_scores = [a["match_score"] for a in analyses[:5]]
        older_scores = [a["match_score"] for a in analyses[-5:]]
        
        recent_avg = sum(recent_scores) / len(recent_scores)
        older_avg = sum(older_scores) / len(older_scores)
        
        if recent_avg > older_avg + 5:
            return "Improving"
        elif recent_avg < older_avg - 5:
            return "Declining"
        else:
            return "Stable"
    
    def _calculate_hiring_difficulty(self, analyses: List[Dict]) -> str:
        """Calculate hiring difficulty based on application scores"""
        if not analyses:
            return "Unknown"
        
        scores = [a["match_score"] for a in analyses]
        avg_score = sum(scores) / len(scores)
        high_scores = len([s for s in scores if s >= 80])
        high_score_percentage = (high_scores / len(scores)) * 100
        
        if avg_score >= 75 and high_score_percentage >= 30:
            return "Easy (Many qualified candidates)"
        elif avg_score >= 60 and high_score_percentage >= 15:
            return "Moderate (Some qualified candidates)"
        else:
            return "Difficult (Few qualified candidates)"
    
    def _get_top_required_skills(self, jobs: List[Dict], limit: int = 5) -> List[str]:
        """Get the most frequently required skills across jobs"""
        skill_count = {}
        
        for job in jobs:
            required_skills = job.get("job_requirements", {}).get("required_skills", [])
            for skill in required_skills:
                skill_lower = skill.lower()
                skill_count[skill_lower] = skill_count.get(skill_lower, 0) + 1
        
        # Sort by frequency and return top skills
        top_skills = sorted(skill_count.items(), key=lambda x: x[1], reverse=True)
        return [skill for skill, count in top_skills[:limit]]


# =================================================================
# CONVENIENCE FUNCTIONS FOR COMMON USE CASES
# =================================================================

def quick_user_lookup(email: str) -> Optional[Dict]:
    """Quick function to look up a user by email"""
    dal = DataAccessLayer()
    return dal.get_user_by_email(email)

def quick_job_search(search_term: str) -> List[Dict]:
    """Quick function to search for jobs"""
    dal = DataAccessLayer()
    return dal.search_jobs(search_term, limit=20)

def quick_top_candidates(min_score: int = 80) -> List[Dict]:
    """Quick function to get top-scoring candidates"""
    dal = DataAccessLayer()
    return dal.get_high_scoring_analyses(min_score, limit=20)

def quick_company_overview(company: str) -> Dict[str, Any]:
    """Quick function to get company overview"""
    dal = DataAccessLayer()
    return dal.generate_company_report(company)



