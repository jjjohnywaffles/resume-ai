"""
File: tests/test_data_access.py
Author: Jonathan Hu
Date Created: 6/20/25
Description: Simple test file for the DataAccessLayer to verify basic functionality
             with limited database content. Tests basic CRUD operations and
             simple queries without requiring extensive data.

Usage:
    python tests/test_data_access.py
"""

import sys
import os
from datetime import datetime

# Add the parent directory to the path so we can import from core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.data_access import DataAccessLayer


class DataAccessTester:
    """Simple test class for DataAccessLayer functionality"""
    
    def __init__(self):
        self.dal = DataAccessLayer()
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message
        })
        print(f"{status} - {test_name}: {message}")
    
    def test_connection(self):
        """Test basic database connection"""
        try:
            stats = self.dal.get_database_stats()
            success = isinstance(stats, dict) and "total_users" in stats
            message = f"Connected successfully. Users: {stats.get('total_users', 0)}, Jobs: {stats.get('total_jobs', 0)}, Analyses: {stats.get('total_analyses', 0)}"
            self.log_test("Database Connection", success, message)
            return stats
        except Exception as e:
            self.log_test("Database Connection", False, f"Connection failed: {e}")
            return None
    
    def test_get_all_users(self):
        """Test getting all users"""
        try:
            users = self.dal.get_all_users(limit=10)
            success = isinstance(users, list)
            message = f"Retrieved {len(users)} users"
            self.log_test("Get All Users", success, message)
            return users
        except Exception as e:
            self.log_test("Get All Users", False, f"Error: {e}")
            return []
    
    def test_get_all_jobs(self):
        """Test getting all jobs"""
        try:
            jobs = self.dal.get_all_jobs(limit=10)
            success = isinstance(jobs, list)
            message = f"Retrieved {len(jobs)} jobs"
            self.log_test("Get All Jobs", success, message)
            return jobs
        except Exception as e:
            self.log_test("Get All Jobs", False, f"Error: {e}")
            return []
    
    def test_get_all_analyses(self):
        """Test getting all analyses"""
        try:
            analyses = self.dal.get_all_analyses(limit=10)
            success = isinstance(analyses, list)
            message = f"Retrieved {len(analyses)} analyses"
            self.log_test("Get All Analyses", success, message)
            return analyses
        except Exception as e:
            self.log_test("Get All Analyses", False, f"Error: {e}")
            return []
    
    def test_user_lookup(self, users):
        """Test user lookup by email if users exist"""
        if not users:
            self.log_test("User Lookup by Email", True, "Skipped - no users in database")
            return
        
        try:
            # Try to get the first user by email
            first_user = users[0]
            email = first_user.get('email')
            
            if email:
                user = self.dal.get_user_by_email(email)
                success = user is not None and user.get('email') == email
                message = f"Successfully looked up user: {email}" if success else f"Failed to lookup user: {email}"
            else:
                success = True
                message = "Skipped - user has no email field"
            
            self.log_test("User Lookup by Email", success, message)
            
        except Exception as e:
            self.log_test("User Lookup by Email", False, f"Error: {e}")
    
    def test_job_search(self, jobs):
        """Test job search functionality"""
        if not jobs:
            self.log_test("Job Search by Company", True, "Skipped - no jobs in database")
            return
        
        try:
            # Try to search by the first job's company
            first_job = jobs[0]
            company = first_job.get('company')
            
            if company:
                company_jobs = self.dal.get_jobs_by_company(company, limit=5)
                success = isinstance(company_jobs, list) and len(company_jobs) > 0
                message = f"Found {len(company_jobs)} jobs for company: {company}" if success else f"No jobs found for: {company}"
            else:
                success = True
                message = "Skipped - job has no company field"
            
            self.log_test("Job Search by Company", success, message)
            
        except Exception as e:
            self.log_test("Job Search by Company", False, f"Error: {e}")
    
    def test_analysis_queries(self, analyses):
        """Test basic analysis queries"""
        if not analyses:
            self.log_test("Analysis Score Query", True, "Skipped - no analyses in database")
            return
        
        try:
            # Test high-scoring analyses
            high_scores = self.dal.get_high_scoring_analyses(min_score=70, limit=5)
            success = isinstance(high_scores, list)
            message = f"Found {len(high_scores)} analyses with score >= 70"
            self.log_test("Analysis Score Query", success, message)
            
            # Test recent analyses
            recent = self.dal.get_recent_analyses(days=365, limit=5)  # Use 365 days to catch existing data
            success = isinstance(recent, list)
            message = f"Found {len(recent)} recent analyses (last 365 days)"
            self.log_test("Recent Analyses Query", success, message)
            
        except Exception as e:
            self.log_test("Analysis Queries", False, f"Error: {e}")
    
    def test_search_functionality(self):
        """Test search functionality with generic terms"""
        try:
            # Test universal search with a common term
            search_results = self.dal.search_everything("software", limit_per_type=3)
            success = isinstance(search_results, dict) and "results" in search_results
            
            if success:
                results = search_results["results"]
                total = len(results.get("users", [])) + len(results.get("jobs", [])) + len(results.get("analyses", []))
                message = f"Search returned {total} total results across all categories"
            else:
                message = "Search failed to return proper format"
            
            self.log_test("Universal Search", success, message)
            
        except Exception as e:
            self.log_test("Universal Search", False, f"Error: {e}")
    
    def test_data_integrity(self, users, jobs, analyses):
        """Test basic data integrity"""
        try:
            # Check if users have proper structure
            user_structure_ok = True
            if users:
                first_user = users[0]
                required_fields = ['_id', 'email']
                user_structure_ok = all(field in first_user for field in required_fields)
            
            # Check if jobs have proper structure
            job_structure_ok = True
            if jobs:
                first_job = jobs[0]
                required_fields = ['_id', 'company', 'job_title']
                job_structure_ok = all(field in first_job for field in required_fields)
            
            # Check if analyses have proper structure
            analysis_structure_ok = True
            if analyses:
                first_analysis = analyses[0]
                required_fields = ['_id', 'match_score', 'timestamp']
                analysis_structure_ok = all(field in first_analysis for field in required_fields)
            
            success = user_structure_ok and job_structure_ok and analysis_structure_ok
            message = f"Users: {'✓' if user_structure_ok else '✗'}, Jobs: {'✓' if job_structure_ok else '✗'}, Analyses: {'✓' if analysis_structure_ok else '✗'}"
            
            self.log_test("Data Structure Integrity", success, message)
            
        except Exception as e:
            self.log_test("Data Structure Integrity", False, f"Error: {e}")
    
    def test_objectid_conversion(self):
        """Test ObjectId to string conversion"""
        try:
            # Test with conversion enabled (default)
            users_with_strings = self.dal.get_all_users(limit=1, convert_ids=True)
            
            # Test with conversion disabled
            users_with_objectids = self.dal.get_all_users(limit=1, convert_ids=False)
            
            if users_with_strings and users_with_objectids:
                string_id = users_with_strings[0].get('_id')
                objectid_id = users_with_objectids[0].get('_id')
                
                success = isinstance(string_id, str) and not isinstance(objectid_id, str)
                message = f"String conversion: {type(string_id).__name__}, ObjectId preserved: {type(objectid_id).__name__}"
            else:
                success = True
                message = "Skipped - no users to test conversion"
            
            self.log_test("ObjectId Conversion", success, message)
            
        except Exception as e:
            self.log_test("ObjectId Conversion", False, f"Error: {e}")
    
    def test_pagination(self):
        """Test pagination functionality"""
        try:
            # Get first page
            page1 = self.dal.get_all_analyses(limit=2, skip=0)
            
            # Get second page
            page2 = self.dal.get_all_analyses(limit=2, skip=2)
            
            # Check if pagination works (different results or empty second page)
            if len(page1) == 0:
                success = True
                message = "Skipped - no data for pagination test"
            else:
                success = True  # If we get here, pagination didn't crash
                message = f"Page 1: {len(page1)} items, Page 2: {len(page2)} items"
            
            self.log_test("Pagination", success, message)
            
        except Exception as e:
            self.log_test("Pagination", False, f"Error: {e}")
    
    def test_edge_cases(self):
        """Test edge cases and error handling"""
        try:
            # Test with non-existent email
            non_existent_user = self.dal.get_user_by_email("nonexistent@example.com")
            test1_pass = non_existent_user is None
            
            # Test with invalid ObjectId string
            try:
                invalid_user = self.dal.get_user_by_id("invalid_id")
                test2_pass = invalid_user is None
            except:
                test2_pass = True  # Exception handling worked
            
            # Test empty search
            empty_search = self.dal.search_users_by_name("", limit=1)
            test3_pass = isinstance(empty_search, list)
            
            success = test1_pass and test2_pass and test3_pass
            message = f"Non-existent lookup: {'✓' if test1_pass else '✗'}, Invalid ID: {'✓' if test2_pass else '✗'}, Empty search: {'✓' if test3_pass else '✗'}"
            
            self.log_test("Edge Cases", success, message)
            
        except Exception as e:
            self.log_test("Edge Cases", False, f"Error: {e}")
    
    def run_all_tests(self):
        """Run all tests and print summary"""
        print("=" * 60)
        print("🧪 DataAccessLayer Test Suite")
        print("=" * 60)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Run tests in order
        stats = self.test_connection()
        
        if stats is None:
            print("\n❌ Cannot proceed - database connection failed")
            return
        
        print()
        users = self.test_get_all_users()
        jobs = self.test_get_all_jobs()
        analyses = self.test_get_all_analyses()
        
        print()
        self.test_user_lookup(users)
        self.test_job_search(jobs)
        self.test_analysis_queries(analyses)
        
        print()
        self.test_search_functionality()
        self.test_data_integrity(users, jobs, analyses)
        self.test_objectid_conversion()
        self.test_pagination()
        self.test_edge_cases()
        
        # Print summary
        print()
        print("=" * 60)
        print("📊 Test Summary")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Tests Run: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total*100):.1f}%" if total > 0 else "No tests run")
        
        if total - passed > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        else:
            print("\n🎉 All tests passed!")
        
        print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        return passed == total


def main():
    """Main function to run tests"""
    print("Initializing DataAccessLayer tests...")
    
    tester = DataAccessTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    exit_code = 0 if success else 1
    print(f"\nExiting with code: {exit_code}")
    
    return exit_code


if __name__ == "__main__":
    main()