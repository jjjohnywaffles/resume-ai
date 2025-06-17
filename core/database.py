"""
File: database.py
Author: Jonathan Hu
Date Created: 6/12/25
Last Modified: 6/15/25
Description: Database management module for MongoDB operations. Handles all
             database connections, queries, and data persistence for resume analyses.
Classes:
    - DatabaseManager: MongoDB interface for storing and retrieving analyses
Methods:
    - save_analysis(): Store analysis results with metadata
    - get_analysis_by_name(): Retrieve analysis by candidate name
    - get_all_analyses(): Fetch all stored analyses
    - compare_scores_by_position(): Compare candidates for same position
    - Various query methods for filtering by company, job title, etc.
    
"""

from pymongo import MongoClient
from datetime import datetime
from typing import List, Dict
from config import get_config

config = get_config()

class DatabaseManager:
    """MongoDB interface for storing and retrieving analyses"""
    
    def __init__(self):
        # DB Connection
        self.client = MongoClient(config.MONGODB_URI)
        self.db = self.client[config.DATABASE_NAME]
        self.collection = self.db.resume_analyses
    
    def save_analysis(self, name, resume_data, job_description_data, match_score, explanation=None, job_title=None, company=None):
        """Save resume analysis to database - SAME as original"""
        document = {
            "name": name,
            "resume_data": resume_data,
            "job_description_data": job_description_data,
            "match_score": match_score,
            "timestamp": datetime.utcnow()
        }
        
        if explanation:
            document["explanation"] = explanation
        if job_title:
            document["job_title"] = job_title
        if company:
            document["company"] = company
        
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
        """Pull data from collection with optional query and projection"""
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
        """Get analyses for specific job and company"""
        return list(self.collection.find({
            "job_title": job_title,
            "company": company_name
        }))
    
    def compare_scores_by(self, job_description_query: dict = {}, k: int = 5) -> List[Dict]:
        """Compare match scores - SAME as original"""
        query = {}
        if job_description_query:
            query = {"job_description_data": {"$elemMatch": job_description_query}}
        
        analyses = self.get_analysis_by(
            query=query,
            projection={
                "name": 1,
                "match_score": 1,
                "resume_data": 1,
                "job_title": 1,
                "company": 1,
                "job_description_data": 0,
                "_id": 0
            }
        )
        if not analyses:
            return []
        
        sorted_analyses = sorted(
            analyses,
            key=lambda x: x.get('match_score', 0),
            reverse=True
        )
        
        top_k = []
        for analysis in sorted_analyses[:k]:
            top_k.append({
                'name': analysis.get('name', ''),
                'score': analysis.get('match_score', 0),
                'job_title': analysis.get('job_title', 'N/A'),
                'company': analysis.get('company', 'N/A'),
                'resume_summary': analysis.get('resume_data', {}).get('summary', ''),
                'skills': analysis.get('resume_data', {}).get('skills', [])
            })
        
        return top_k
    
    def compare_scores_by_position(self, job_title: str = None, company: str = None, k: int = 5) -> List[Dict]:
        """Compare candidates for same position"""
        query = {}
        if job_title:
            query["job_title"] = job_title
        if company:
            query["company"] = company
        
        if not query:
            return []
        
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
        
        sorted_analyses = sorted(
            analyses,
            key=lambda x: x.get('match_score', 0),
            reverse=True
        )
        
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
    
    def compare_candidates_for_position(self, job_title, company, top_k=10):
        """Alias for compare_scores_by_position - for compatibility"""
        return self.compare_scores_by_position(job_title, company, top_k)
    
    def close_connection(self):
        """Close database connection"""
        self.client.close()
