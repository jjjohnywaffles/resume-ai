"""
File: analyzer.py
Author: Jonathan Hu
Date Created: 6/12/25
Last Modified: 6/19/25 (Updated for OpenAI v1.0+ with full async support and caching)
Description: AI analysis module that interfaces with OpenAI's GPT model to extract
             structured data from resumes and job descriptions, then calculates
             compatibility scores with detailed explanations. Now uses OpenAI v1.0+
             with async processing and caching for maximum performance.
Classes:
    - ResumeAnalyzer: Main class for AI-powered resume and job analysis
Methods:
    - extract_resume_data(): Parse resume text into structured JSON (async with caching)
    - extract_job_requirements(): Parse job description into requirements (async with caching)
    - extract_data_concurrent(): Run both extractions simultaneously (async)
    - explain_match_score(): Generate detailed compatibility analysis (async)
    - calculate_match_score(): Calculate numerical compatibility score
    - get_detailed_analysis(): Get both score and explanation
    - analyze_resume_job_match_fast(): Complete analysis workflow (optimized)
"""
import json
import asyncio
import openai
import re
import concurrent.futures
from threading import Lock
from typing import Dict, Any, Tuple
from config import get_config

config = get_config()

class ResumeAnalyzer:
    """Main resume analysis class with OpenAI v1.0+ async processing and caching"""
    
    def __init__(self):
        if not config.OPENAI_API_KEY:
            raise ValueError("OpenAI API key not found. Please check your .env file.")
        
        # Initialize both sync and async OpenAI clients for v1.0+
        self.client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
        self.async_client = openai.AsyncOpenAI(api_key=config.OPENAI_API_KEY)
        
        self._api_lock = Lock()  # Thread safety for sync API calls
        print("Using OpenAI v1.0+ with async support")
        
        # Simple in-memory cache for repeated analyses
        self._cache = {}
        self._cache_size_limit = 100
        
        # Add timeout for async operations
        self.async_timeout = 30  # 30 seconds timeout
    
    def _run_async_safely(self, coro):
        """
        Safely run async coroutine
        """
        try:
            # Use asyncio.run with timeout
            return asyncio.wait_for(asyncio.run(coro), timeout=self.async_timeout)
        except asyncio.TimeoutError:
            print("ASYNC OPERATION TIMED OUT - falling back to sync")
            raise Exception("Async timeout")
        except Exception as e:
            print(f"ASYNC OPERATION FAILED: {e} - falling back to sync")
            raise e
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key from text content"""
        return str(hash(text))
    
    def _cache_get(self, key: str) -> Dict[str, Any]:
        """Get from cache if exists"""
        return self._cache.get(key)
    
    def _cache_set(self, key: str, value: Dict[str, Any]):
        """Set cache with size limit"""
        if len(self._cache) >= self._cache_size_limit:
            # Remove oldest entry
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
        self._cache[key] = value
    
    async def extract_resume_data_async(self, resume_text):
        """Async version of extract_resume_data with caching for better performance"""
        cache_key = f"resume_{self._get_cache_key(resume_text)}"
        cached_result = self._cache_get(cache_key)
        
        if cached_result:
            print("CACHE HIT - Resume Analysis")
            return cached_result
        
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
            print("ASYNC API CALL - Resume Analysis...")
            response = await self.async_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content
            parsed_json = json.loads(content)
            
            # Cache the result
            self._cache_set(cache_key, parsed_json)
            print("JSON PARSING SUCCESSFUL - Resume (Cached)")
            
            return parsed_json
            
        except json.JSONDecodeError as e:
            print(f"JSON PARSING FAILED - Resume: {e}")
            return {"error": "Failed to parse resume data"}
        except Exception as e:
            print(f"ASYNC API CALL FAILED - Resume: {e}")
            return {"error": f"API call failed: {str(e)}"}
    
    def extract_resume_data(self, resume_text):
        """Extract skills and experience from resume - now forces async for better performance"""
        # Always try to use async for better performance
        try:
            return asyncio.run(self.extract_resume_data_async(resume_text))
        except Exception as e:
            print(f"Async failed, using sync fallback: {e}")
            return self._extract_resume_data_sync(resume_text)
    
    
    # IF ASYNC FAILS (it shouldn't tho)
    def _extract_resume_data_sync(self, resume_text):
        """Sync fallback version using OpenAI v1.0+ API"""
        cache_key = f"resume_{self._get_cache_key(resume_text)}"
        cached_result = self._cache_get(cache_key)
        
        if cached_result:
            print("CACHE HIT - Resume Analysis (Sync)")
            return cached_result
        
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
            print("SYNC API CALL - Resume Analysis...")
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content
            parsed_json = json.loads(content)
            
            # Cache the result
            self._cache_set(cache_key, parsed_json)
            print("JSON PARSING SUCCESSFUL - Resume")
            
            return parsed_json
            
        except json.JSONDecodeError as e:
            print(f"JSON PARSING FAILED - Resume: {e}")
            return {"error": "Failed to parse resume data"}
        except Exception as e:
            print(f"SYNC API CALL FAILED - Resume: {e}")
            return {"error": f"API call failed: {str(e)}"}
    
    async def extract_job_requirements_async(self, job_description):
        """Async version of extract_job_requirements with caching"""
        cache_key = f"job_{self._get_cache_key(job_description)}"
        cached_result = self._cache_get(cache_key)
        
        if cached_result:
            print("CACHE HIT - Job Analysis")
            return cached_result
        
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
            print("ASYNC API CALL - Job Analysis...")
            response = await self.async_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content
            parsed_json = json.loads(content)
            
            # Cache the result
            self._cache_set(cache_key, parsed_json)
            print("JSON PARSING SUCCESSFUL - Job (Cached)")
            
            return parsed_json
            
        except json.JSONDecodeError as e:
            print(f"JSON PARSING FAILED - Job: {e}")
            return {"error": "Failed to parse job requirements"}
        except Exception as e:
            print(f"ASYNC API CALL FAILED - Job: {e}")
            return {"error": f"API call failed: {str(e)}"}
    
    def extract_job_requirements(self, job_description):
        """Extract requirements from job description - now forces async for better performance"""
        # Always try to use async for better performance
        try:
            return asyncio.run(self.extract_job_requirements_async(job_description))
        except Exception as e:
            print(f"Async failed, using sync fallback: {e}")
            return self._extract_job_requirements_sync(job_description)
    
    def _extract_job_requirements_sync(self, job_description):
        """Sync fallback version using OpenAI v1.0+ API"""
        cache_key = f"job_{self._get_cache_key(job_description)}"
        cached_result = self._cache_get(cache_key)
        
        if cached_result:
            print("CACHE HIT - Job Analysis (Sync)")
            return cached_result
        
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
            print("SYNC API CALL - Job Analysis...")
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content
            parsed_json = json.loads(content)
            
            # Cache the result
            self._cache_set(cache_key, parsed_json)
            print("JSON PARSING SUCCESSFUL - Job")
            
            return parsed_json
            
        except json.JSONDecodeError as e:
            print(f"JSON PARSING FAILED - Job: {e}")
            return {"error": "Failed to parse job requirements"}
        except Exception as e:
            print(f"SYNC API CALL FAILED - Job: {e}")
            return {"error": f"API call failed: {str(e)}"}
    
    async def extract_data_concurrent_async(self, resume_text, job_description):
        """
        Extract resume and job data concurrently using asyncio
        """
        print("STARTING ASYNC CONCURRENT DATA EXTRACTION...")
        
        try:
            # Run both API calls concurrently with asyncio
            resume_task = self.extract_resume_data_async(resume_text)
            job_task = self.extract_job_requirements_async(job_description)
            
            # Wait for both to complete
            resume_data, job_requirements = await asyncio.gather(resume_task, job_task)
            
            print("ASYNC CONCURRENT EXTRACTION COMPLETED")
            
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
            print(f"ASYNC CONCURRENT EXTRACTION FAILED: {e}")
            return {"error": f"Concurrent extraction failed: {str(e)}"}
    
    def extract_data_concurrent(self, resume_text, job_description):
        """
        Extract resume and job data concurrently - with multiple fallback strategies
        """
        print("STARTING OPTIMIZED CONCURRENT DATA EXTRACTION...")
        
        # 1: Try async 
        try:
            print("ATTEMPTING ASYNC STRATEGY...")
            # Create a new event loop to avoid conflicts
            async def async_extraction():
                return await self.extract_data_concurrent_async(resume_text, job_description)
            
            # Run with timeout protection
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    asyncio.wait_for(async_extraction(), timeout=25)  # 25 second total timeout
                )
                print("ASYNC CONCURRENT EXTRACTION SUCCESSFUL!")
                return result
            finally:
                loop.close()
                
        except asyncio.TimeoutError:
            print("ASYNC EXTRACTION TIMED OUT - using threading fallback")
        except Exception as e:
            print(f"ASYNC EXTRACTION FAILED: {e} - using threading fallback")
        
        # 2: Use optimized threading with individual async calls
        try:
            print("ATTEMPTING THREADING + ASYNC STRATEGY...")
            
            def run_async_in_thread(coro):
                """Run async function in a separate thread with its own event loop"""
                import threading
                result = [None]
                exception = [None]
                
                def thread_target():
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        result[0] = loop.run_until_complete(coro)
                        loop.close()
                    except Exception as e:
                        exception[0] = e
                
                thread = threading.Thread(target=thread_target)
                thread.start()
                thread.join(timeout=15)  # 15 second timeout per thread
                
                if thread.is_alive():
                    raise TimeoutError("Thread timed out")
                if exception[0]:
                    raise exception[0]
                return result[0]
            
            # Run both extractions in parallel threads
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                resume_future = executor.submit(
                    run_async_in_thread, 
                    self.extract_resume_data_async(resume_text)
                )
                job_future = executor.submit(
                    run_async_in_thread, 
                    self.extract_job_requirements_async(job_description)
                )
                
                # Wait for both with timeout
                resume_data = resume_future.result(timeout=20)
                job_requirements = job_future.result(timeout=20)
            
            print("THREADING + ASYNC EXTRACTION SUCCESSFUL!")
            
            # Check for errors
            if isinstance(resume_data, dict) and "error" in resume_data:
                return {"error": "Failed to extract resume data", "details": resume_data}
            
            if isinstance(job_requirements, dict) and "error" in job_requirements:
                return {"error": "Failed to extract job requirements", "details": job_requirements}
            
            return {
                "resume_data": resume_data,
                "job_requirements": job_requirements
            }
            
        except Exception as e:
            print(f"THREADING + ASYNC FAILED: {e} - using pure sync fallback")
        
        # Strategy 3: Fall back to pure sync threading
        print("USING PURE SYNC THREADING FALLBACK...")
        return self._extract_data_concurrent_sync(resume_text, job_description)
    
    def _extract_data_concurrent_sync(self, resume_text, job_description):
        """Fallback threading version using sync methods"""
        print("STARTING SYNC CONCURRENT DATA EXTRACTION...")
        
        try:
            # Use ThreadPoolExecutor with sync methods
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                # Submit both tasks simultaneously
                resume_future = executor.submit(self._extract_resume_data_sync, resume_text)
                job_future = executor.submit(self._extract_job_requirements_sync, job_description)
                
                # Wait for both to complete
                resume_data = resume_future.result()
                job_requirements = job_future.result()
            
            print("SYNC CONCURRENT EXTRACTION COMPLETED")
            
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
            print(f"SYNC CONCURRENT EXTRACTION FAILED: {e}")
            return {"error": f"Concurrent extraction failed: {str(e)}"}
    
    async def explain_match_score_async(self, resume_data, job_requirements):
        """Async version of detailed score calculation"""
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
            print("ASYNC API CALL - Detailed Score Calculation...")
            response = await self.async_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a precise mathematical scoring system. Always follow the exact formula provided. Be consistent - identical inputs must produce identical outputs. Provide detailed breakdowns showing your work. CRITICAL: Ensure your final score matches your calculation exactly."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            print("ASYNC RESPONSE CONTENT FOR DEBUGGING:")
            print("="*50)
            print(content)
            print("="*50)
            
            final_score = self._extract_score_from_response(content)
            final_score = max(15, min(95, final_score))
            
            print(f"ASYNC EXTRACTED FINAL SCORE: {final_score}")
            
            return {
                "explanation": content,
                "score": final_score
            }
            
        except Exception as e:
            print(f"ASYNC API CALL FAILED: {e}")
            return {
                "explanation": "Failed to generate detailed explanation",
                "score": 0,
                "error": f"API call failed: {str(e)}"
            }
    
    def explain_match_score(self, resume_data, job_requirements):
        """Calculate compatibility score with detailed explanation - FORCES async"""
        try:
            # Always try async for better performance
            return asyncio.run(self.explain_match_score_async(resume_data, job_requirements))
        except Exception as e:
            print(f"Async explain_match_score failed: {e}")
            print("Falling back to sync version...")
            return self._explain_match_score_sync(resume_data, job_requirements)
    
    def _explain_match_score_sync(self, resume_data, job_requirements):
        """Sync fallback version using OpenAI v1.0+ API"""
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
            print("SYNC API CALL - Detailed Score Calculation...")
            response = self.client.chat.completions.create(
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
            print("SYNC RESPONSE CONTENT FOR DEBUGGING:")
            print("="*50)
            print(content)
            print("="*50)
            
            final_score = self._extract_score_from_response(content)
            final_score = max(15, min(95, final_score))
            
            print(f"SYNC EXTRACTED FINAL SCORE: {final_score}")
            
            return {
                "explanation": content,
                "score": final_score
            }
            
        except Exception as e:
            print(f"SYNC API CALL FAILED: {e}")
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
    
    # MAIN USAGE METHODS:
    
    async def analyze_resume_job_match_fast_async(self, resume_text, job_description):
        """
        ASYNC VERSION: Complete analysis workflow with full async processing
        This is the fastest possible version using OpenAI v1.0+ async capabilities
        """
        print("STARTING ULTRA-FAST ASYNC ANALYSIS WORKFLOW...")
        
        try:
            # Extract data concurrently
            extraction_result = await self.extract_data_concurrent_async(resume_text, job_description)
            
            if "error" in extraction_result:
                print("ASYNC ANALYSIS FAILED")
                return extraction_result
            
            resume_data = extraction_result["resume_data"]
            job_requirements = extraction_result["job_requirements"]
            
            # Get detailed analysis (async)
            analysis = await self.explain_match_score_async(resume_data, job_requirements)
            
            print("ULTRA-FAST ASYNC ANALYSIS WORKFLOW COMPLETED")
            
            return {
                "resume_data": resume_data,
                "job_requirements": job_requirements,
                "compatibility_score": analysis["score"],
                "detailed_explanation": analysis["explanation"],
                "breakdown": self._parse_explanation_breakdown(analysis["explanation"]),
                "error": analysis.get("error")
            }
            
        except Exception as e:
            print(f"ULTRA-FAST ASYNC ANALYSIS FAILED: {e}")
            return {"error": f"Analysis failed: {str(e)}"}
    
    def analyze_resume_job_match_fast(self, resume_text, job_description):
        """
        OPTIMIZED VERSION: Complete analysis workflow - FORCES async for maximum performance
        This is the main method you should use for fastest performance
        """
        print("STARTING ULTRA-FAST ASYNC ANALYSIS WORKFLOW...")
        
        try:
            # Force async version for processing speed
            return asyncio.run(self.analyze_resume_job_match_fast_async(resume_text, job_description))
        except Exception as e:
            print(f"Ultra-fast async analysis failed: {e}")
            print("Falling back to sync version...")
            return self._analyze_resume_job_match_fast_sync(resume_text, job_description)
    
    def _analyze_resume_job_match_fast_sync(self, resume_text, job_description):
        """Fallback sync version using threading"""
        print("STARTING FAST SYNC ANALYSIS WORKFLOW...")
        
        # Extract data concurrently (threading version)
        extraction_result = self.extract_data_concurrent(resume_text, job_description)
        
        if "error" in extraction_result:
            print("FAST SYNC ANALYSIS FAILED")
            return extraction_result
        
        resume_data = extraction_result["resume_data"]
        job_requirements = extraction_result["job_requirements"]
        
        # Get detailed analysis
        analysis = self.explain_match_score(resume_data, job_requirements)
        
        print("ANALYSIS WORKFLOW COMPLETED")
        
        return {
            "resume_data": resume_data,
            "job_requirements": job_requirements,
            "compatibility_score": analysis["score"],
            "detailed_explanation": analysis["explanation"],
            "breakdown": self._parse_explanation_breakdown(analysis["explanation"]),
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

    # BATCH PROCESSING METHODS (NOT NECESSARY FOR NOW):
    
    async def analyze_multiple_resumes_async(self, resumes_and_jobs):
        """
        Analyze multiple resume-job pairs concurrently for maximum efficiency
        resumes_and_jobs: [(resume_text1, job_desc1), (resume_text2, job_desc2), ...]
        """
        print(f"STARTING BATCH ASYNC ANALYSIS OF {len(resumes_and_jobs)} PAIRS...")
        
        # Create tasks for all analyses
        tasks = [
            self.analyze_resume_job_match_fast_async(resume, job) 
            for resume, job in resumes_and_jobs
        ]
        
        # Run all analyses concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        print("BATCH ASYNC ANALYSIS COMPLETED")
        return results
    
    def analyze_multiple_resumes(self, resumes_and_jobs):
        """
        Analyze multiple resume-job pairs using the fastest available method
        """
        try:
            # Force async batch processing for maximum speed
            return asyncio.run(self.analyze_multiple_resumes_async(resumes_and_jobs))
        except Exception as e:
            print(f"Batch async analysis failed: {e}")
            # Fallback to threading batch processing
            print(f"STARTING BATCH SYNC ANALYSIS OF {len(resumes_and_jobs)} PAIRS...")
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(4, len(resumes_and_jobs))) as executor:
                # Submit all analysis tasks
                futures = [
                    executor.submit(self._analyze_resume_job_match_fast_sync, resume, job)
                    for resume, job in resumes_and_jobs
                ]
                
                # Collect results
                results = []
                for future in concurrent.futures.as_completed(futures):
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        results.append({"error": f"Analysis failed: {str(e)}"})
            
            print("BATCH SYNC ANALYSIS COMPLETED")
            return results


# Example usage:
if __name__ == "__main__":
    analyzer = ResumeAnalyzer()

    pass