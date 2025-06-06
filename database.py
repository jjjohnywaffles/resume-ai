""" 
Author: Jonathan Hu
database.py
This file acts as the connection logic to the database. Also stores the database schema.
"""

from pymongo import MongoClient
from datetime import datetime
import config

class DatabaseManager:
    def __init__(self):
        self.client = MongoClient(config.MONGODB_URI)
        self.db = self.client[config.DATABASE_NAME]
        self.collection = self.db.resume_analyses
    
    def save_analysis(self, name, resume_data, job_description_data, match_score):
        """Save resume analysis to database"""
        document = {
            "name": name,
            "resume_data": resume_data,
            "job_description_data": job_description_data,
            "match_score": match_score,
            "timestamp": datetime.utcnow()
        }
        
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
    
    def close_connection(self):
        """Close database connection"""
        self.client.close()