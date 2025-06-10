""" 
Author: Jonathan Hu
config.py
Stores the secret keys from the env file to allow the application to actually work
"""

import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = "resume_analyzer"