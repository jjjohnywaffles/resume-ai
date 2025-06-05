import json
import openai
import config

class AIAnalyzer:
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
            print("🔍 MAKING OPENAI API CALL - Resume Analysis...")
            response = openai.ChatCompletion.create(
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
    
    def calculate_match_score(self, resume_data, job_requirements):
        """Calculate compatibility score between resume and job"""
        prompt = f"""
        Compare the following resume data with job requirements and provide a compatibility score from 1-100.
        
        Resume Data:
        {json.dumps(resume_data, indent=2)}
        
        Job Requirements:
        {json.dumps(job_requirements, indent=2)}
        
        Analyze the match based on:
        1. Skills alignment (40% weight)
        2. Experience relevance (30% weight)
        3. Education match (20% weight)
        4. Overall fit (10% weight)
        
        Return only a number between 1-100 representing the compatibility score.
        """
        
        try:
            print("🔍 MAKING OPENAI API CALL - Score Calculation...")
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a scoring assistant. Only respond with a single integer from 1 to 100. No explanation."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=10
            )
            
            print("RAW OPENAI RESPONSE (Score):")
            print("=" * 60)
            print(f"Full Response Object: {response}")
            print("=" * 60)
            
            content = response.choices[0].message.content.strip()
            print("EXTRACTED CONTENT:")
            print("=" * 60)
            print(f"'{content}'")
            print("=" * 60)
            
            score = int(content)
            final_score = max(1, min(100, score))
            print(f"FINAL SCORE: {final_score}")
            
            return final_score
            
        except ValueError as e:
            print(f"CORE PARSING FAILED: {e}")
            print(f"Raw content that failed to parse: '{content}'")
            return 0  # Default score if parsing fails
        except Exception as e:
            print(f"API CALL FAILED: {e}")
            return 0  # Default score if API call fails