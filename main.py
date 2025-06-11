"""
Author: Jonathan Hu
main.py
The main application logic for the analyzer. Initializes all functions in order so it returns properly.
"""


from ai_analyzer import AIAnalyzer
from database import DatabaseManager
from pdf_reader import PDFReader
import json

class ResumeAnalyzer:
    def __init__(self):
        self.ai_analyzer = AIAnalyzer()
        self.db_manager = DatabaseManager()
        self.pdf_reader = PDFReader()
    
    def analyze_resume(self, name, resume_path, job_description_text, include_explanation=False, job_title=None, company=None):
        """Main function to analyze resume against job description"""
        print(f"Starting analysis for {name}...")
        if job_title and company:
            print(f"Position: {job_title} at {company}")
        
        # Step 1: Extract text from resume PDF
        print("Extracting text from resume...")
        resume_text = self.pdf_reader.extract_text_from_pdf(resume_path)
        
        if resume_text.startswith("Error"):
            return {"error": resume_text}
        
        # Step 2: Extract structured data from resume
        print("Analyzing resume content...")
        resume_data = self.ai_analyzer.extract_resume_data(resume_text)
        
        # Step 3: Extract job requirements
        print("Analyzing job description...")
        job_requirements = self.ai_analyzer.extract_job_requirements(job_description_text)
        
        # Step 4: Calculate match score (with or without explanation)
        if include_explanation:
            print("Calculating compatibility score with detailed explanation...")
            score_result = self.ai_analyzer.explain_match_score(resume_data, job_requirements)
            match_score = score_result["score"]
            explanation = score_result["explanation"]
        else:
            print("Calculating compatibility score...")
            # This now internally calls explain_match_score() but only returns the score
            match_score = self.ai_analyzer.calculate_match_score(resume_data, job_requirements)
            explanation = None
        
        # Step 5: Save to database with job title and company
        print("Saving to database...")
        self.db_manager.save_analysis(name, resume_data, job_requirements, match_score, explanation, job_title, company)
        
        # Return results
        result = {
            "name": name,
            "resume_data": resume_data,
            "job_requirements": job_requirements,
            "match_score": match_score
        }
        
        # Add job title and company if provided
        if job_title:
            result["job_title"] = job_title
        if company:
            result["company"] = company
        
        # Add explanation if requested
        if explanation:
            result["explanation"] = explanation
        
        print(f"Analysis complete! Match score: {match_score}/100")
        if job_title and company:
            print(f"Position: {job_title} at {company}")
        return result
    
    def get_analysis(self, name):
        """Get existing analysis by name"""
        return self.db_manager.get_analysis_by_name(name)
    
    def get_all_analyses(self):
        """Get all analyses"""
        return self.db_manager.get_all_analyses()
    
    def get_analyses_by_company(self, company_name):
        """Get all analyses for a specific company"""
        return self.db_manager.get_analyses_by_company(company_name)
    
    def get_analyses_by_job_title(self, job_title):
        """Get all analyses for a specific job title"""
        return self.db_manager.get_analyses_by_job_title(job_title)
    
    def compare_candidates_for_position(self, job_title=None, company=None, top_k=5):
        """Compare candidates for the same position"""
        return self.db_manager.compare_scores_by_position(job_title, company, top_k)
    
    def close(self):
        """Close database connection"""
        self.db_manager.close_connection()

def main():
    analyzer = ResumeAnalyzer()
    
    try:
        # Example usage
        print("Resume Analyzer Started")
        print("-" * 40)
        
        # Get user input
        name = input("Enter candidate name: ")
        job_title = input("Enter job title: ")
        company = input("Enter company name: ")
        resume_path = input("Enter path to resume PDF: ")
        
        print("\nEnter job description (press Enter twice when done):")
        job_description_lines = []
        while True:
            line = input()
            if line == "":
                break
            job_description_lines.append(line)
        
        job_description = "\n".join(job_description_lines)
        
        # Perform analysis with job title and company
        result = analyzer.analyze_resume(
            name, resume_path, job_description, 
            include_explanation=False, job_title=job_title, company=company
        )
        
        # Display results
        print("\n" + "="*50)
        print("ANALYSIS RESULTS")
        print("="*50)
        print(f"Candidate: {result['name']}")
        if 'job_title' in result and 'company' in result:
            print(f"Position: {result['job_title']} at {result['company']}")
        print(f"Match Score: {result['match_score']}/100")
        
        print("\nResume Skills:")
        for skill in result['resume_data'].get('skills', []):
            print(f"  • {skill}")
        
        print("\nJob Required Skills:")
        for skill in result['job_requirements'].get('required_skills', []):
            print(f"  • {skill}")
        
        print("\nFull analysis saved to database.")
        
        # Optional: Show other candidates for the same position
        if job_title and company:
            print(f"\nOther candidates for {job_title} at {company}:")
            other_candidates = analyzer.compare_candidates_for_position(job_title, company, 10)
            for i, candidate in enumerate(other_candidates, 1):
                print(f"  {i}. {candidate['name']} - {candidate['score']}/100")
        
    except KeyboardInterrupt:
        print("\nAnalysis cancelled.")
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        analyzer.close()

if __name__ == "__main__":
    main()