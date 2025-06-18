"""
File: analyzer.py
Author: Jonathan Hu
Date Created: 6/12/25
Last Modified: 6/17/25 (Added concurrent processing for speed optimization)
Description: AI analysis module that interfaces with OpenAI's GPT model to extract
             structured data from resumes and job descriptions, then calculates
             compatibility scores with detailed explanations. Now uses concurrent
             processing to analyze resume and job description simultaneously.
Classes:
    - ResumeAnalyzer: Main class for AI-powered resume and job analysis
Methods:
    - extract_resume_data(): Parse resume text into structured JSON
    - extract_job_requirements(): Parse job description into requirements
    - extract_data_concurrent(): Run both extractions simultaneously
    - explain_match_score(): Generate detailed compatibility analysis
    - calculate_match_score(): Calculate numerical compatibility score
    - get_detailed_analysis(): Get both score and explanation
"""

import json
import openai
import re
import concurrent.futures
from threading import Lock
from config import get_config

config = get_config()

class ResumeAnalyzer:
    """Main resume analysis class with concurrent processing"""
    
    def __init__(self):
        if not config.OPENAI_API_KEY:
            raise ValueError("OpenAI API key not found. Please check your .env file.")
        openai.api_key = config.OPENAI_API_KEY
        self._api_lock = Lock()  # Thread safety for API calls
    
    def extract_resume_data(self, resume_text):
        """Extract skills and experience from resume"""
        prompt = f"""
        Analyze the following resume text and extract key information in JSON format. Remove all markdown formatting.
        
        Resume text:
        {resume_text}
        
        Please return a JSON object with the following structure:
        {{
            "skills": ["skill1", "skill2", "skill3"],
            "experience": [
                {{
                    "role": "Job Title",
                    "company": "Company Name",
                    "duration": "Time period",
                    "description": "Brief description"
                }}
            ],
            "education": [
                {{
                    "degree": "Degree name",
                    "institution": "School name",
                    "year": "Graduation year"
                }}
            ]
        }}
        
        Only return the JSON object, no additional text, no markdown formatting.
        """
        
        try:
            print("MAKING OPENAI API CALL - Resume Analysis...")
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content
            parsed_json = json.loads(content)
            print("JSON PARSING SUCCESSFUL - Resume")
            
            return parsed_json
            
        except json.JSONDecodeError as e:
            print(f"JSON PARSING FAILED - Resume: {e}")
            return {"error": "Failed to parse resume data"}
        except Exception as e:
            print(f"API CALL FAILED - Resume: {e}")
            return {"error": f"API call failed: {str(e)}"}
    
    def extract_job_requirements(self, job_description):
        """Extract requirements from job description"""
        prompt = f"""
        Analyze the following job description and extract key requirements in JSON format. Remove all markdown formatting.
        
        Job description:
        {job_description}
        
        Please return a JSON object with the following structure:
        {{
            "required_skills": ["skill1", "skill2", "skill3"],
            "preferred_skills": ["skill1", "skill2"],
            "experience_required": "X years",
            "education_required": "Degree requirement",
            "responsibilities": ["responsibility1", "responsibility2"]
        }}
        
        Only return the JSON object, no additional text.
        """
        
        try:
            print("MAKING OPENAI API CALL - Job Analysis...")
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content
            parsed_json = json.loads(content)
            print("JSON PARSING SUCCESSFUL - Job")
            
            return parsed_json
            
        except json.JSONDecodeError as e:
            print(f"JSON PARSING FAILED - Job: {e}")
            return {"error": "Failed to parse job requirements"}
        except Exception as e:
            print(f"API CALL FAILED - Job: {e}")
            return {"error": f"API call failed: {str(e)}"}
    
    def extract_data_concurrent(self, resume_text, job_description):
        """
        Extract resume and job data concurrently for faster processing
        This is the main speed improvement - runs both API calls simultaneously
        """
        print("STARTING CONCURRENT DATA EXTRACTION...")
        
        try:
            # Use ThreadPoolExecutor to run both API calls concurrently
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                # Submit both tasks simultaneously
                resume_future = executor.submit(self.extract_resume_data, resume_text)
                job_future = executor.submit(self.extract_job_requirements, job_description)
                
                # Wait for both to complete
                resume_data = resume_future.result()
                job_requirements = job_future.result()
            
            print("CONCURRENT EXTRACTION COMPLETED")
            
            # Check for errors
            if "error" in resume_data:
                return {"error": "Failed to extract resume data", "details": resume_data}
            
            if "error" in job_requirements:
                return {"error": "Failed to extract job requirements", "details": job_requirements}
            
            return {
                "resume_data": resume_data,
                "job_requirements": job_requirements
            }
            
        except Exception as e:
            print(f"CONCURRENT EXTRACTION FAILED: {e}")
            return {"error": f"Concurrent extraction failed: {str(e)}"}
    
    def explain_match_score(self, resume_data, job_requirements):
        """Calculate compatibility score with detailed explanation"""
        prompt = f"""
        You are a precise HR scoring system. Calculate a compatibility score from 1-100 using EXACTLY the formula below.
        Be mathematically consistent - the same inputs should always produce the same score.

        MANDATORY SCORING FORMULA (follow exactly):
        
        1. BASE SCORE: Always start with 100 points
        
        2. REQUIRED SKILLS SCORING:
        For EACH required skill, evaluate if it's:
        - FULLY SATISFIED (0 deduction): Exact match OR equivalent (Python=Django/Flask, JavaScript=React/Node.js, Database=SQL/MySQL, Data Preprocessing=cleaning/quality)
        - PARTIALLY SATISFIED (-7 points): Related skill or transferable experience 
        - NOT SATISFIED (-15 points): No relevant skills or experience found
        
        Maximum deduction: -45 points (cap at 3 major missing skills)
        
        3. EXPERIENCE SCORING:
        Calculate experience gap:
        - Meets or exceeds requirement: 0 deduction
        - 75-99% of required: -10 points
        - 50-74% of required: -20 points  
        - Under 50% of required: -30 points
        - Experience completely unrelated to role: additional -15 points
        Maximum deduction: -45 points
        
        4. EDUCATION SCORING:
        - Meets requirement exactly: 0 deduction
        - Related field or higher degree: -5 points
        - Unrelated field: -10 points
        - Missing required degree entirely: -20 points
        Maximum deduction: -20 points
        
        5. BONUS POINTS:
        - Each preferred skill matched: +3 points
        - Exceeds experience requirement significantly: +5 points
        - Advanced degree when not required: +5 points
        Maximum bonus: +15 points

        FORMAT YOUR RESPONSE WITH DETAILED BREAKDOWN:

        **SCORING BREAKDOWN:**

        **BASE SCORE:** 100 points

        **REQUIRED SKILLS ANALYSIS:**
        [For each required skill, explain whether it's fully satisfied, partially satisfied, or not satisfied, and the points deducted]

        **EXPERIENCE ANALYSIS:**
        [Compare candidate's experience to requirements and explain deductions]

        **EDUCATION ANALYSIS:**
        [Compare candidate's education to requirements and explain deductions]

        **BONUS POINTS:**
        [List any bonus points earned and why]

        **CALCULATION:**
        Base Score: 100
        Skills Deductions: -X
        Experience Deductions: -Y
        Education Deductions: -Z
        Bonus Points: +A
        **FINAL COMPATIBILITY SCORE: [final_number]/100**

        IMPORTANT: Make sure the final score in "FINAL COMPATIBILITY SCORE" exactly matches your calculation above.

        Resume Data:
        {json.dumps(resume_data, indent=2)}
        
        Job Requirements:
        {json.dumps(job_requirements, indent=2)}
        """
        
        try:
            print("MAKING OPENAI API CALL - Detailed Score Calculation...")
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a precise mathematical scoring system. Always follow the exact formula provided. Be consistent - identical inputs must produce identical outputs. Provide detailed breakdowns showing your work. CRITICAL: Ensure your final score matches your calculation exactly."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=3000
            )
            
            content = response.choices[0].message.content
            print("RESPONSE CONTENT FOR DEBUGGING:")
            print("="*50)
            print(content)
            print("="*50)
            
            # IMPROVED SCORE EXTRACTION with multiple methods
            final_score = self._extract_score_from_response(content)
            
            # Apply consistency constraints
            final_score = max(15, min(95, final_score))
            
            print(f"EXTRACTED FINAL SCORE: {final_score}")
            
            return {
                "explanation": content,
                "score": final_score
            }
            
        except Exception as e:
            print(f"API CALL FAILED: {e}")
            return {
                "explanation": "Failed to generate detailed explanation",
                "score": 0,
                "error": f"API call failed: {str(e)}"
            }

    def _extract_score_from_response(self, content):
        """
        Improved score extraction with multiple fallback methods
        """
        print("ATTEMPTING SCORE EXTRACTION...")
        
        # Method 1: Look for calculation format (e.g., "= 50/100")
        calc_patterns = [
            r'=\s*(\d+)/100',                                    # = 50/100
            r'=\s*(\d+)\s*/\s*100',                             # = 50 / 100
            r'FINAL COMPATIBILITY SCORE:.*?=\s*(\d+)/100',      # Full calculation ending in = 50/100
            r'FINAL COMPATIBILITY SCORE:.*?=\s*(\d+)',          # Full calculation ending in = 50
        ]
        
        for i, pattern in enumerate(calc_patterns):
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                score = int(match.group(1))
                print(f"SCORE FOUND using calculation pattern {i+1}: {score}")
                return score
        
        # Method 2: Look for simple format (just the final number)
        simple_patterns = [
            r'FINAL COMPATIBILITY SCORE:\s*(\d+)/100',          # FINAL COMPATIBILITY SCORE: 50/100
            r'\*\*FINAL COMPATIBILITY SCORE:\s*(\d+)/100\*\*',  # **FINAL COMPATIBILITY SCORE: 50/100**
            r'FINAL COMPATIBILITY SCORE:\s*(\d+)',              # FINAL COMPATIBILITY SCORE: 50
        ]
        
        for i, pattern in enumerate(simple_patterns):
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                score = int(match.group(1))
                print(f"SCORE FOUND using simple pattern {i+1}: {score}")
                return score
        
        # Method 3: Extract from calculation section and verify
        calc_score = self._extract_from_calculation_section(content)
        if calc_score is not None:
            print(f"SCORE FOUND from calculation section: {calc_score}")
            return calc_score
        
        # Method 4: Last resort - look for any number/100 pattern (but be more careful)
        fallback_patterns = [
            r'(\d+)/100',
            r'Final score:\s*(\d+)',
            r'Score:\s*(\d+)',
        ]
        
        for i, pattern in enumerate(fallback_patterns):
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                # Take the last match (most likely to be the final score)
                score = int(matches[-1])
                print(f"FALLBACK SCORE FOUND using pattern {i+1}: {score}")
                return score
        
        print("WARNING: No score found in response, using default")
        return 50

    def _extract_from_calculation_section(self, content):
        """
        Extract score by parsing the calculation section
        """
        try:
            # Look for the calculation section
            calc_match = re.search(r'\*\*CALCULATION:\*\*(.*?)(?=\*\*FINAL|$)', content, re.DOTALL | re.IGNORECASE)
            if not calc_match:
                return None
            
            calc_section = calc_match.group(1)
            print("FOUND CALCULATION SECTION:")
            print(calc_section)
            
            # Extract base score, deductions, and bonuses
            base_score = 100
            total_deductions = 0
            total_bonuses = 0
            
            # Look for deduction patterns
            deduction_patterns = [
                r'Skills Deductions?:\s*-(\d+)',
                r'Experience Deductions?:\s*-(\d+)',
                r'Education Deductions?:\s*-(\d+)',
            ]
            
            for pattern in deduction_patterns:
                match = re.search(pattern, calc_section, re.IGNORECASE)
                if match:
                    total_deductions += int(match.group(1))
            
            # Look for bonus patterns
            bonus_match = re.search(r'Bonus Points?:\s*\+(\d+)', calc_section, re.IGNORECASE)
            if bonus_match:
                total_bonuses = int(bonus_match.group(1))
            
            calculated_score = base_score - total_deductions + total_bonuses
            print(f"CALCULATED: {base_score} - {total_deductions} + {total_bonuses} = {calculated_score}")
            
            return calculated_score
            
        except Exception as e:
            print(f"Error extracting from calculation: {e}")
            return None

    def calculate_match_score(self, resume_data, job_requirements):
        """Calculate compatibility score between resume and job (score only)"""
        print("CALCULATING MATCH SCORE (score only)...")
        
        result = self.explain_match_score(resume_data, job_requirements)
        score = result.get("score", 0)
        
        print(f"FINAL SCORE: {score}")
        return score
    
    def get_detailed_analysis(self, resume_data, job_requirements):
        """Get both compatibility score and detailed explanation"""
        print("GENERATING DETAILED ANALYSIS...")
        
        result = self.explain_match_score(resume_data, job_requirements)
        
        if "error" in result:
            print(f"ERROR: {result['error']}")
            return {
                "score": 0,
                "explanation": "Failed to generate analysis due to API error",
                "error": result["error"]
            }
        
        print(f"ANALYSIS COMPLETE - Score: {result['score']}")
        return {
            "score": result["score"],
            "explanation": result["explanation"],
            "breakdown": self._parse_explanation_breakdown(result["explanation"])
        }
    
    def _parse_explanation_breakdown(self, explanation):
        """Parse the explanation text to extract key components"""
        try:
            breakdown = {
                "base_score": 100,
                "skills_analysis": "",
                "experience_analysis": "",
                "education_analysis": "",
                "bonus_points": "",
                "final_calculation": ""
            }
            
            # Extract sections using regex
            sections = {
                "skills_analysis": r"REQUIRED SKILLS ANALYSIS:(.*?)(?=\*\*EXPERIENCE ANALYSIS:|$)",
                "experience_analysis": r"EXPERIENCE ANALYSIS:(.*?)(?=\*\*EDUCATION ANALYSIS:|$)",
                "education_analysis": r"EDUCATION ANALYSIS:(.*?)(?=\*\*BONUS POINTS:|$)",
                "bonus_points": r"BONUS POINTS:(.*?)(?=\*\*CALCULATION:|$)",
                "final_calculation": r"CALCULATION:(.*?)(?=\*\*FINAL COMPATIBILITY SCORE:|$)"
            }
            
            for key, pattern in sections.items():
                match = re.search(pattern, explanation, re.DOTALL | re.IGNORECASE)
                if match:
                    breakdown[key] = match.group(1).strip()
            
            return breakdown
            
        except Exception as e:
            print(f"Error parsing breakdown: {e}")
            return {"error": "Could not parse explanation breakdown"}
    
    

    # IMPROVED USAGE METHODS:
    
    def analyze_resume_job_match_fast(self, resume_text, job_description):
        """
        OPTIMIZED VERSION: Complete analysis workflow with concurrent processing
        This is the main method you should use for fastest performance
        """
        print("STARTING FAST ANALYSIS WORKFLOW...")
        
        # Extract data concurrently (NEW - this is the speed improvement)
        extraction_result = self.extract_data_concurrent(resume_text, job_description)
        
        if "error" in extraction_result:
            print("FAST ANALYSIS FAILED")
            return extraction_result
        
        resume_data = extraction_result["resume_data"]
        job_requirements = extraction_result["job_requirements"]
        
        # Get detailed analysis
        analysis = self.get_detailed_analysis(resume_data, job_requirements)
        
        print("FAST ANALYSIS WORKFLOW COMPLETED")
        
        return {
            "resume_data": resume_data,
            "job_requirements": job_requirements,
            "compatibility_score": analysis["score"],
            "detailed_explanation": analysis["explanation"],
            "breakdown": analysis.get("breakdown", {}),
            "error": analysis.get("error")
        }
    
    def analyze_resume_job_match(self, resume_text, job_description):
        """
        LEGACY VERSION: Complete analysis workflow - sequential processing
        Kept for backward compatibility, but use analyze_resume_job_match_fast() instead
        """
        print("STARTING COMPLETE ANALYSIS WORKFLOW (SEQUENTIAL)...")
        
        # Extract data sequentially (old way)
        resume_data = self.extract_resume_data(resume_text)
        if "error" in resume_data:
            print("SEQUENTIAL ANALYSIS FAILED")
            return {"error": "Failed to extract resume data", "details": resume_data}
        
        job_requirements = self.extract_job_requirements(job_description)
        if "error" in job_requirements:
            print("SEQUENTIAL ANALYSIS FAILED")
            return {"error": "Failed to extract job requirements", "details": job_requirements}
        
        # Get detailed analysis
        analysis = self.get_detailed_analysis(resume_data, job_requirements)
        
        print("SEQUENTIAL ANALYSIS WORKFLOW COMPLETED")
        
        return {
            "resume_data": resume_data,
            "job_requirements": job_requirements,
            "compatibility_score": analysis["score"],
            "detailed_explanation": analysis["explanation"],
            "breakdown": analysis.get("breakdown", {}),
            "error": analysis.get("error")
        }


# Example usage:
if __name__ == "__main__":
    analyzer = ResumeAnalyzer()
    
    pass