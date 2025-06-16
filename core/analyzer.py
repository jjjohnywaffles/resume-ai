"""
File: ai_analyzer.py
Author: Jonathan Hu
Date Created: 6/12/25
Last Modified: 6/12/25
Description: AI analysis module that interfaces with OpenAI's GPT model to extract
             structured data from resumes and job descriptions, then calculates
             compatibility scores with detailed explanations.
Classes:
    - AIAnalyzer: Main class for AI-powered resume and job analysis
Methods:
    - extract_resume_data(): Parse resume text into structured JSON
    - extract_job_requirements(): Parse job description into requirements
    - explain_match_score(): Generate detailed compatibility analysis
    - calculate_match_score(): Calculate numerical compatibility score
"""

import json
import openai
import re
from config import get_config

config = get_config()

class ResumeAnalyzer:
    """Main resume analysis class"""
    
    def __init__(self):
        if not config.OPENAI_API_KEY:
            raise ValueError("OpenAI API key not found. Please check your .env file.")
        openai.api_key = config.OPENAI_API_KEY
    
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
            print("JSON PARSING SUCCESSFUL")
            
            return parsed_json
            
        except json.JSONDecodeError as e:
            print(f"JSON PARSING FAILED: {e}")
            return {"error": "Failed to parse resume data"}
        except Exception as e:
            print(f"API CALL FAILED: {e}")
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
            print("JSON PARSING SUCCESSFUL")
            
            return parsed_json
            
        except json.JSONDecodeError as e:
            print(f"JSON PARSING FAILED: {e}")
            return {"error": "Failed to parse job requirements"}
        except Exception as e:
            print(f"API CALL FAILED: {e}")
            return {"error": f"API call failed: {str(e)}"}
    
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

        FORMAT YOUR RESPONSE WITH:

        **FINAL COMPATIBILITY SCORE: [final_number]/100**

        Resume Data:
        {json.dumps(resume_data, indent=2)}
        
        Job Requirements:
        {json.dumps(job_requirements, indent=2)}
        """
        
        try:
            print("MAKING OPENAI API CALL - 'Consistent' Score Calculation lolxd...")
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a precise mathematical scoring system. Always follow the exact formula provided. Be consistent - identical inputs must produce identical outputs."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=2500
            )
            
            content = response.choices[0].message.content
            
            # Extract the final score
            score_match = re.search(r'FINAL COMPATIBILITY SCORE: (\d+)/100', content)
            if score_match:
                final_score = int(score_match.group(1))
            else:
                # Fallback patterns
                score_patterns = [
                    r'Final score: (\d+)',
                    r'Score: (\d+)',
                    r'(\d+)/100'
                ]
                
                final_score = None
                for pattern in score_patterns:
                    match = re.search(pattern, content)
                    if match:
                        final_score = int(match.group(1))
                        break
                
                if final_score is None:
                    print("WARNING: Could not extract score, using fallback calculation")
                    final_score = 50
            
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

    def calculate_match_score(self, resume_data, job_requirements):
        """Calculate compatibility score between resume and job"""
        print("CALCULATING MATCH SCORE (using detailed explanation method)...")
        
        result = self.explain_match_score(resume_data, job_requirements)
        score = result.get("score", 0)
        
        print(f"FINAL SCORE: {score}")
        return score
