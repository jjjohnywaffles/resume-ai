""" 
Author: Jonathan Hu
database.py
This file acts as the connection logic to the database. Also stores the database schema.
"""

from pymongo import MongoClient
from datetime import datetime
from typing import List, Dict  # Added missing import for type hints
import config

class DatabaseManager:
    def __init__(self):  # Fixed the __init__ method name
        # DB Connection
        self.client = MongoClient(config.MONGODB_URI)
        self.db = self.client[config.DATABASE_NAME]
        self.collection = self.db.resume_analyses
    
    def save_analysis(self, name, resume_data, job_description_data, match_score, explanation=None, job_title=None, company=None):
        """Save resume analysis to database with optional job title and company"""
        document = {
            "name": name,
            "resume_data": resume_data,
            "job_description_data": job_description_data,
            "match_score": match_score,
            "timestamp": datetime.utcnow()
        }
        
        # Add explanation if provided
        if explanation:
            document["explanation"] = explanation
        
        # Add job title if provided
        if job_title:
            document["job_title"] = job_title
        
        # Add company if provided
        if company:
            document["company"] = company
        
        # Update if name exists, otherwise insert new
        result = self.collection.update_one(
            {"name": name},
            {"$set": document},
            upsert=True
        )
        return result
    
    def get_analysis_by_name(self, name):
        """Get analysis by submitter name"""
        return self.collection.find_one({"name": name})
    
    def get_all_analyses(self):
        """Get all analyses"""
        return list(self.collection.find())
    
    def get_analysis_by(self, query={}, projection=None):
        """
        Pull data from the collection with optional query and projection
        Args:
            query (dict): MongoDB query to filter documents
            projection (dict): Fields to include/exclude in results
        Returns:
            list: Matching documents
        """
        if projection:
            return list(self.collection.find(query, projection))
        return list(self.collection.find(query))
    
    def get_analyses_by_company(self, company_name):
        """Get all analyses for a specific company"""
        return list(self.collection.find({"company": company_name}))
    
    def get_analyses_by_job_title(self, job_title):
        """Get all analyses for a specific job title"""
        return list(self.collection.find({"job_title": job_title}))
    
    def get_analyses_by_job_and_company(self, job_title, company_name):
        """Get all analyses for a specific job title and company combination"""
        return list(self.collection.find({
            "job_title": job_title,
            "company": company_name
        }))
    
    def compare_scores_by(self, job_description_query: dict = {}, k: int = 5) -> List[Dict]:
        """
        Compare match scores from analyses filtered by job description and return top k performers
        Args:
            job_description_query: Dictionary to filter job descriptions
                                  Example: {"position": "Software Engineer"}
            k: Number of top performers to return
        Returns:
            list: Sorted list of top k analyses with names, scores, and resume data
                  Empty list if no matches found
        """
        # Build the query to match job description criteria
        query = {}
        if job_description_query:
            query = {"job_description_data": {"$elemMatch": job_description_query}}
        
        # Pull data matching the job description criteria
        analyses = self.get_analysis_by(
            query=query,
            projection={
                "name": 1,
                "match_score": 1,
                "resume_data": 1,
                "job_title": 1,        # Include job title in projection
                "company": 1,          # Include company in projection
                "job_description_data": 0,
                "_id": 0
            }
        )
        if not analyses:
            return []
        
        # Sort analyses by match_score in descending order
        sorted_analyses = sorted(
            analyses,
            key=lambda x: x.get('match_score', 0),
            reverse=True
        )
        
        # Return top k analyses with relevant information
        top_k = []
        for analysis in sorted_analyses[:k]:
            top_k.append({
                'name': analysis.get('name', ''),
                'score': analysis.get('match_score', 0),
                'job_title': analysis.get('job_title', 'N/A'),      # Include job title
                'company': analysis.get('company', 'N/A'),          # Include company
                'resume_summary': analysis.get('resume_data', {}).get('summary', ''),
                'skills': analysis.get('resume_data', {}).get('skills', [])
            })
        
        return top_k
    
    def compare_scores_by_position(self, job_title: str = None, company: str = None, k: int = 5) -> List[Dict]:
        """
        Compare match scores for candidates applying to the same position/company
        Args:
            job_title: Filter by job title (optional)
            company: Filter by company (optional)
            k: Number of top performers to return
        Returns:
            list: Sorted list of top k analyses for the specified position/company
        """
        # Build query based on provided filters
        query = {}
        if job_title:
            query["job_title"] = job_title
        if company:
            query["company"] = company
        
        # If no filters provided, return empty list
        if not query:
            return []
        
        # Get analyses matching the criteria
        analyses = self.get_analysis_by(
            query=query,
            projection={
                "name": 1,
                "match_score": 1,
                "job_title": 1,
                "company": 1,
                "resume_data": 1,
                "_id": 0
            }
        )
        
        if not analyses:
            return []
        
        # Sort by match_score in descending order
        sorted_analyses = sorted(
            analyses,
            key=lambda x: x.get('match_score', 0),
            reverse=True
        )
        
        # Return top k analyses
        top_k = []
        for analysis in sorted_analyses[:k]:
            top_k.append({
                'name': analysis.get('name', ''),
                'score': analysis.get('match_score', 0),
                'job_title': analysis.get('job_title', 'N/A'),
                'company': analysis.get('company', 'N/A'),
                'skills': analysis.get('resume_data', {}).get('skills', [])
            })
        
        return top_k
    
    def close_connection(self):
        """Close database connection"""
        self.client.close()