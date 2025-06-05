from ai_analyzer import AIAnalyzer
from database import DatabaseManager
from pdf_reader import PDFReader
import json

class ResumeAnalyzer:
    def __init__(self):
        self.ai_analyzer = AIAnalyzer()
        self.db_manager = DatabaseManager()
        self.pdf_reader = PDFReader()
    
    def analyze_resume(self, name, resume_path, job_description_text):
        """Main function to analyze resume against job description"""
        print(f"Starting analysis for {name}...")
        
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
        
        # Step 4: Calculate match score
        print("Calculating compatibility score...")
        match_score = self.ai_analyzer.calculate_match_score(resume_data, job_requirements)
        
        # Step 5: Save to database
        print("Saving to database...")
        self.db_manager.save_analysis(name, resume_data, job_requirements, match_score)
        
        # Return results
        result = {
            "name": name,
            "resume_data": resume_data,
            "job_requirements": job_requirements,
            "match_score": match_score
        }
        
        print(f"Analysis complete! Match score: {match_score}/100")
        return result
    
    def get_analysis(self, name):
        """Get existing analysis by name"""
        return self.db_manager.get_analysis_by_name(name)
    
    def get_all_analyses(self):
        """Get all analyses"""
        return self.db_manager.get_all_analyses()
    
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
        resume_path = input("Enter path to resume PDF: ")
        
        print("\nEnter job description (press Enter twice when done):")
        job_description_lines = []
        while True:
            line = input()
            if line == "":
                break
            job_description_lines.append(line)
        
        job_description = "\n".join(job_description_lines)
        
        # Perform analysis
        result = analyzer.analyze_resume(name, resume_path, job_description)
        
        # Display results
        print("\n" + "="*50)
        print("ANALYSIS RESULTS")
        print("="*50)
        print(f"Candidate: {result['name']}")
        print(f"Match Score: {result['match_score']}/100")
        
        print("\nResume Skills:")
        for skill in result['resume_data'].get('skills', []):
            print(f"  • {skill}")
        
        print("\nJob Required Skills:")
        for skill in result['job_requirements'].get('required_skills', []):
            print(f"  • {skill}")
        
        print("\nFull analysis saved to database.")
        
    except KeyboardInterrupt:
        print("\nAnalysis cancelled.")
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        analyzer.close()

if __name__ == "__main__":
    main()