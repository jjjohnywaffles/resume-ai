""" 
Author: Jonathan Hu
ai_analyzer.py
This file takes the user's input from both the name, resume and job description and sends it to an ai model.
The ai model then processes both the resume and job description to return json objects.
The json objects are then sent back to the ai model for a compatibility comparison.
The compatibility score is based on a specific criteria designed to return an accurate representation of a resume to the job description.
"""

import json
import openai
import config

# Analyzer class, extracts information and formats it into json. 
class AIAnalyzer:
    def __init__(self):
        if not config.OPENAI_API_KEY:
            raise ValueError("OpenAI API key not found. Please check your .env file.")
        openai.api_key = config.OPENAI_API_KEY
    
    # Format resume
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
            print("🔍 MAKING OPENAI API CALL - Resume Analysis...")
            response = openai.ChatCompletion.create(

                # USE MINI MODEL FOR TEST PLS
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1500
            )
            
            print("📥 RAW OPENAI RESPONSE (Resume):")
            print("=" * 60)
            print(f"Full Response Object: {response}")
            print("=" * 60)
            
            content = response.choices[0].message.content
            print("📄 EXTRACTED CONTENT:")
            print("=" * 60)
            print(content)
            print("=" * 60)
            
            parsed_json = json.loads(content)
            print("✅ JSON PARSING SUCCESSFUL")
            print("📊 PARSED JSON:")
            print("=" * 60)
            print(json.dumps(parsed_json, indent=2))
            print("=" * 60)
            
            return parsed_json
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON PARSING FAILED: {e}")
            print(f"📄 Raw content that failed to parse: {content}")
            return {"error": "Failed to parse resume data"}
        except Exception as e:
            print(f"❌ API CALL FAILED: {e}")
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
            print("🔍 MAKING OPENAI API CALL - Job Analysis...")
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1500
            )
            
            print("📥 RAW OPENAI RESPONSE (Job):")
            print("=" * 60)
            print(f"Full Response Object: {response}")
            print("=" * 60)
            
            content = response.choices[0].message.content
            print("📄 EXTRACTED CONTENT:")
            print("=" * 60)
            print(content)
            print("=" * 60)
            
            parsed_json = json.loads(content)
            print("✅ JSON PARSING SUCCESSFUL")
            print("📊 PARSED JSON:")
            print("=" * 60)
            print(json.dumps(parsed_json, indent=2))
            print("=" * 60)
            
            return parsed_json
            
        except json.JSONDecodeError as e:
            print(f"JSON PARSING FAILED: {e}")
            print(f"Raw content that failed to parse: {content}")
            return {"error": "Failed to parse job requirements"}
        except Exception as e:
            print(f"API CALL FAILED: {e}")
            return {"error": f"API call failed: {str(e)}"}
    
    def explain_match_score(self, resume_data, job_requirements):
        """Calculate compatibility score with detailed explanation - CONSISTENT SCORING VERSION"""
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
        
        CALCULATION REQUIREMENTS:
        - Show your math step by step
        - Count each deduction/bonus precisely
        - Apply the constraints at the end
        - Be consistent: same analysis = same score every time

        FORMAT YOUR RESPONSE EXACTLY AS:

        ## COMPATIBILITY ANALYSIS

        ### 1. BASE SCORE
        Starting score: 100 points

        ### 2. REQUIRED SKILLS ANALYSIS (Mathematical Breakdown)
        Required skills from job: [list each one]
        
        Skill-by-skill evaluation:
        [For each required skill, state: SKILL NAME - STATUS (Fully/Partially/Not Satisfied) - DEDUCTION]
        
        Skills calculation:
        - Fully satisfied: [count] × 0 = 0 points
        - Partially satisfied: [count] × -7 = -[total] points  
        - Not satisfied: [count] × -15 = -[total] points
        Total skills deduction: -[sum] points (capped at -45)

        ### 3. EXPERIENCE ANALYSIS (Mathematical Breakdown)
        Required: [state requirement]
        Candidate has: [state experience]
        Gap analysis: [percentage of requirement met]
        Relevance: [relevant/somewhat relevant/unrelated]
        
        Experience calculation:
        - Experience gap deduction: -[amount] points
        - Relevance deduction: -[amount] points  
        Total experience deduction: -[sum] points (capped at -45)

        ### 4. EDUCATION ANALYSIS (Mathematical Breakdown)
        Required: [state requirement]
        Candidate has: [state education]
        Match level: [exact/related/unrelated/missing]
        
        Education deduction: -[amount] points (capped at -20)

        ### 5. BONUS CALCULATION (Mathematical Breakdown)
        Preferred skills matched: [list] = [count] × 3 = +[total] points
        Experience bonus: [yes/no] = +[amount] points
        Education bonus: [yes/no] = +[amount] points
        Total bonus: +[sum] points (capped at +15)

        ### 6. FINAL CALCULATION
        Base score: 100
        Skills deduction: -[X]
        Experience deduction: -[Y]  
        Education deduction: -[Z]
        Bonus points: +[A]
        Raw total: [100-X-Y-Z+A]
        Applied constraints: [15-95 range]
        
        **FINAL COMPATIBILITY SCORE: [final_number]/100**

        ### CONSISTENCY CHECK
        Verify: Base(100) - Skills([X]) - Experience([Y]) - Education([Z]) + Bonus([A]) = [final_number]

        Resume Data:
        {json.dumps(resume_data, indent=2)}
        
        Job Requirements:
        {json.dumps(job_requirements, indent=2)}
        """
        
        try:
            print("🔍 MAKING OPENAI API CALL - Consistent Score Calculation...")
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a precise mathematical scoring system. Always follow the exact formula provided. Be consistent - identical inputs must produce identical outputs. Show all mathematical calculations step by step."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,  # CRITICAL: Set to 0 for maximum consistency
                max_tokens=2500,
                top_p=1.0,        # Use default top_p for consistency
                frequency_penalty=0.0,  # No penalties that could cause variation
                presence_penalty=0.0
            )
            
            print("📥 RAW OPENAI RESPONSE (Consistent Analysis):")
            print("=" * 60)
            print(f"Full Response Object: {response}")
            print("=" * 60)
            
            content = response.choices[0].message.content
            print("📄 EXTRACTED CONTENT:")
            print("=" * 60)
            print(content)
            print("=" * 60)
            
            # Extract the final score more reliably
            import re
            
            # Primary extraction method
            score_match = re.search(r'\*\*FINAL COMPATIBILITY SCORE: (\d+)/100\*\*', content)
            if score_match:
                final_score = int(score_match.group(1))
            else:
                # Fallback extraction methods
                score_patterns = [
                    r'FINAL COMPATIBILITY SCORE: (\d+)',
                    r'Final score: (\d+)',
                    r'Applied constraints: (\d+)',
                    r'(\d+)/100'
                ]
                
                final_score = None
                for pattern in score_patterns:
                    match = re.search(pattern, content)
                    if match:
                        final_score = int(match.group(1))
                        break
                
                if final_score is None:
                    print("⚠️ WARNING: Could not extract score, using fallback calculation")
                    # Emergency fallback: basic calculation from content
                    final_score = 50
            
            # Apply consistency constraints
            final_score = max(15, min(95, final_score))
            
            print(f"✅ EXTRACTED FINAL SCORE: {final_score}")
            
            return {
                "explanation": content,
                "score": final_score
            }
            
        except Exception as e:
            print(f"❌ API CALL FAILED: {e}")
            return {
                "explanation": "Failed to generate detailed explanation",
                "score": 0,
                "error": f"API call failed: {str(e)}"
            }
    def calculate_match_score(self, resume_data, job_requirements):
        """Calculate compatibility score between resume and job - WRAPPER FUNCTION"""
        print("🔍 CALCULATING MATCH SCORE (using detailed explanation method)...")
        
        # Call the detailed explanation function
        result = self.explain_match_score(resume_data, job_requirements)
        
        # Extract just the score
        score = result.get("score", 0)
        
        print(f"✅ FINAL SCORE: {score}")
        return score