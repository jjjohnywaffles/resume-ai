"""
Author: Jonathan Hu
config.py
Stores the secret keys from the env file to allow the application to actually work
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration"""
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "resume_analyzer")
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this")

def get_config():
    """Get configuration instance"""
    return Config()
