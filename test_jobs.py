from core.database import DatabaseManager

db = DatabaseManager()
if db.jobs_collection.count_documents({}) == 0:
    db._save_job("Test Engineer", "TestCorp", {"skills": ["Python", "Testing"]})

jobs = db.get_all_jobs()
for job in jobs:
    print(job)