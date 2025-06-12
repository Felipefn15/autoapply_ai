"""
Matching Module - Matches resumes with job postings using GROQ
"""
import json
import hashlib
from typing import Dict, List, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from pathlib import Path

import groq
from loguru import logger

from .jobs import JobPosting
from ..config.settings import config
from ..utils.logging import setup_logger

# Setup module logger
logger = setup_logger("matching")

@dataclass
class MatchResult:
    """Result of a match evaluation."""
    match_score: float
    match_reasons: List[str]
    mismatch_reasons: List[str]
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a value by key with a default."""
        return getattr(self, key, default)
    
    def __str__(self) -> str:
        """String representation of the match result."""
        return f"""Match Score: {self.match_score:.2f}
Reasons:
{chr(10).join(f'- {r}' for r in self.match_reasons)}

Potential Concerns:
{chr(10).join(f'- {r}' for r in self.mismatch_reasons)}"""

    def to_dict(self) -> Dict:
        """Convert to dictionary for caching."""
        return {
            'match_score': self.match_score,
            'match_reasons': self.match_reasons,
            'mismatch_reasons': self.mismatch_reasons
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'MatchResult':
        """Create from cached dictionary."""
        return cls(
            match_score=data['match_score'],
            match_reasons=data['match_reasons'],
            mismatch_reasons=data['mismatch_reasons']
        )

class RateLimiter:
    """Simple rate limiter for API calls."""
    def __init__(self, calls_per_minute: int = 10):
        self.calls_per_minute = calls_per_minute
        self.calls = []
        self.total_calls = 0
    
    def wait_if_needed(self):
        """Wait if we've exceeded our rate limit."""
        now = datetime.now()
        # Remove calls older than 1 minute
        self.calls = [call_time for call_time in self.calls 
                     if now - call_time < timedelta(minutes=1)]
        
        if len(self.calls) >= self.calls_per_minute:
            # Wait until the oldest call is more than 1 minute old
            sleep_time = 60 - (now - self.calls[0]).total_seconds()
            if sleep_time > 0:
                logger.info(f"Rate limit reached. Waiting {sleep_time:.1f} seconds...")
                time.sleep(sleep_time)
        elif len(self.calls) > 0:
            # Add a small delay between calls anyway
            time.sleep(1.0)
        
        self.calls.append(now)
        self.total_calls += 1
        
        # Log progress every 10 calls
        if self.total_calls % 10 == 0:
            logger.info(f"Processed {self.total_calls} API calls")

class JobMatcher:
    """Handles matching of resumes with job postings using AI."""
    
    def __init__(self, api_key: str):
        """Initialize the job matcher."""
        self.client = groq.Groq(api_key=api_key)
        self.rate_limiter = RateLimiter()
        self.min_match_score = 0.5
        
        # Setup directories
        self.cache_dir = Path("storage/cache/api/matches")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def match(self, resume_data: Dict, jobs: List[JobPosting]) -> List[Tuple[JobPosting, MatchResult]]:
        """
        Match resume with job postings.
        
        Args:
            resume_data: Dictionary containing parsed resume information
            jobs: List of job postings to match against
            
        Returns:
            List of tuples (job, MatchResult) sorted by match score
        """
        results = []
        total_jobs = len(jobs)
        processed_jobs = 0
        
        logger.info(f"Starting to match {total_jobs} jobs...")
        
        for job in jobs:
            try:
                # Check cache first
                cache_key = self._generate_cache_key(resume_data, job)
                cache_file = self.cache_dir / f"{cache_key}.json"
                
                if cache_file.exists():
                    try:
                        with cache_file.open('r') as f:
                            cached_data = json.load(f)
                        match_result = MatchResult.from_dict(cached_data)
                        if match_result.match_score >= self.min_match_score:
                            results.append((job, match_result))
                        processed_jobs += 1
                        if processed_jobs % 5 == 0:
                            logger.info(f"Processed {processed_jobs}/{total_jobs} jobs ({processed_jobs/total_jobs*100:.1f}%)")
                        continue
                    except Exception as e:
                        logger.warning(f"Error reading cache: {str(e)}")
                
                # If not in cache or cache error, evaluate match
                self.rate_limiter.wait_if_needed()
                match_result = self._evaluate_match(resume_data, job)
                
                if match_result.match_score >= self.min_match_score:
                    results.append((job, match_result))
                
                processed_jobs += 1
                if processed_jobs % 5 == 0:
                    logger.info(f"Processed {processed_jobs}/{total_jobs} jobs ({processed_jobs/total_jobs*100:.1f}%)")
                
            except Exception as e:
                logger.error(f"Error matching job {job.title} at {job.company}: {str(e)}")
                continue
        
        # Sort by match score descending
        results.sort(key=lambda x: x[1].match_score, reverse=True)
        logger.info(f"Completed matching. Found {len(results)} matches above threshold {self.min_match_score}")
        return results
    
    def _generate_cache_key(self, resume_data: Dict, job: JobPosting) -> str:
        """Generate a unique cache key for a resume-job pair."""
        content = f"{json.dumps(resume_data, sort_keys=True)}_{job.title}_{job.company}_{job.description}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _evaluate_match(self, resume_data: Dict, job: JobPosting) -> MatchResult:
        """Evaluate match between resume and job posting using GROQ."""
        try:
            prompt = self._prepare_match_prompt(resume_data, job)
            response = self._make_api_call_with_retry(prompt)
            
            if "error" in response:
                logger.error(f"Error in API response: {response['error']}")
                return MatchResult(
                    match_score=0.0,
                    match_reasons=["Error in evaluation"],
                    mismatch_reasons=["Could not evaluate match due to API error"]
                )
            
            match_data = self._parse_match_response(response)
            
            # Validate match data
            if not isinstance(match_data.get('score'), (int, float)):
                logger.error("Invalid match score type")
                return MatchResult(
                    match_score=0.0,
                    match_reasons=["Error: Invalid match score"],
                    mismatch_reasons=["Could not evaluate match due to invalid score"]
                )
            
            if not isinstance(match_data.get('match_reasons'), list):
                logger.error("Invalid match reasons type")
                match_data['match_reasons'] = ["Error: Could not determine match reasons"]
            
            if not isinstance(match_data.get('mismatch_reasons'), list):
                logger.error("Invalid mismatch reasons type")
                match_data['mismatch_reasons'] = ["Error: Could not determine mismatch reasons"]
            
            # Create result
            result = MatchResult(
                match_score=float(match_data['score']),
                match_reasons=match_data['match_reasons'],
                mismatch_reasons=match_data['mismatch_reasons']
            )
            
            # Cache the result
            try:
                cache_key = self._generate_cache_key(resume_data, job)
                cache_file = self.cache_dir / f"{cache_key}.json"
                with cache_file.open('w') as f:
                    json.dump(result.to_dict(), f)
            except Exception as e:
                logger.warning(f"Error writing cache: {str(e)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in match evaluation: {str(e)}")
            return MatchResult(
                match_score=0.0,
                match_reasons=[f"Error in evaluation: {str(e)}"],
                mismatch_reasons=["Could not evaluate match due to error"]
            )
    
    def _make_api_call_with_retry(self, prompt: str, max_retries: int = 3) -> Dict:
        """Make API call with retries and exponential backoff."""
        retry_count = 0
        base_wait = 5  # seconds
        
        while retry_count < max_retries:
            try:
                completion = self.client.chat.completions.create(
                    model="llama3-70b-8192",
                    messages=[
                        {"role": "system", "content": "You are an expert job matcher. Analyze the match between a resume and job posting."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1000
                )
                try:
                    return json.loads(completion.choices[0].message.content)
                except json.JSONDecodeError:
                    logger.error("Failed to parse API response as JSON")
                    if retry_count < max_retries - 1:
                        retry_count += 1
                        wait_time = base_wait * (2 ** (retry_count - 1))
                        logger.warning(f"Retrying in {wait_time} seconds... ({retry_count}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                    return {"error": "Failed to parse response as JSON"}
                
            except groq.error.RateLimitError as e:
                retry_count += 1
                if retry_count == max_retries:
                    raise e
                
                # For rate limit errors, wait longer
                wait_time = base_wait * (4 ** (retry_count - 1))  # Use 4 instead of 2 for longer waits
                logger.warning(f"Rate limit exceeded. Retrying in {wait_time} seconds... ({retry_count}/{max_retries})")
                time.sleep(wait_time)
                
            except Exception as e:
                retry_count += 1
                if retry_count == max_retries:
                    raise e
                
                wait_time = base_wait * (2 ** (retry_count - 1))
                logger.warning(f"API call failed: {str(e)}. Retrying in {wait_time} seconds... ({retry_count}/{max_retries})")
                time.sleep(wait_time)
    
    def _prepare_match_prompt(self, resume_data: Dict, job: JobPosting) -> str:
        """Prepare prompt for match evaluation."""
        prompt = f"""Analyze the match between this resume and job posting. Return a JSON response with three keys:
1. 'score': A float between 0 and 1 indicating match quality
2. 'match_reasons': A list of strings explaining why this is a good match
3. 'mismatch_reasons': A list of strings explaining potential concerns or mismatches

Resume Information:
- Experience: {resume_data.get('experience_years', 'Not specified')} years
- Skills: {', '.join(resume_data.get('skills', []))}
- Recent Role: {resume_data.get('current_role', 'Not specified')}
- Languages: {', '.join(resume_data.get('languages', []))}
- Education: {resume_data.get('education', 'Not specified')}
- Location: {resume_data.get('location', 'Not specified')}

Job Requirements:
- Title: {job.title}
- Company: {job.company}
- Location: {job.location}
- Remote: {job.remote}
- Type: {job.job_type}
- Requirements: {', '.join(job.requirements)}
- Salary Range: {job.salary_range if job.salary_range else 'Not specified'}

Consider these factors in your evaluation:
1. Skills match
2. Experience level match
3. Location/remote work compatibility
4. Language requirements
5. Salary expectations (if specified)
6. Job type match
7. Industry relevance

Format your response as a JSON object with exactly these fields:
{{
    "score": 0.85,  # Example score
    "match_reasons": [
        "Strong match in required technical skills",
        "Experience level aligns well"
    ],
    "mismatch_reasons": [
        "Missing experience with specific technology X",
        "Location may require relocation"
    ]
}}"""
        return prompt
    
    def _parse_match_response(self, response: Dict) -> Dict:
        """Parse and validate the match response."""
        try:
            # Ensure we have all required fields
            if not all(k in response for k in ['score', 'match_reasons', 'mismatch_reasons']):
                logger.error("Missing required fields in response")
                return {
                    'score': 0.0,
                    'match_reasons': ['Error: Invalid response format'],
                    'mismatch_reasons': ['Could not process match evaluation']
                }
            
            # Validate and clean score
            try:
                score = float(response['score'])
                score = max(0.0, min(1.0, score))  # Clamp between 0 and 1
            except (ValueError, TypeError):
                logger.error("Invalid score value")
                score = 0.0
            
            # Validate and clean match reasons
            match_reasons = response.get('match_reasons', [])
            if not isinstance(match_reasons, list):
                logger.error("Invalid match reasons format")
                match_reasons = ['Error: Invalid match reasons format']
            match_reasons = [str(r).strip() for r in match_reasons if r]  # Convert to strings and remove empty
            if not match_reasons:
                match_reasons = ['No specific match reasons provided']
            
            # Validate and clean mismatch reasons
            mismatch_reasons = response.get('mismatch_reasons', [])
            if not isinstance(mismatch_reasons, list):
                logger.error("Invalid mismatch reasons format")
                mismatch_reasons = ['Error: Invalid mismatch reasons format']
            mismatch_reasons = [str(s).strip() for s in mismatch_reasons if s]  # Convert to strings and remove empty
            if not mismatch_reasons:
                mismatch_reasons = ['No specific mismatch reasons provided']
            
            return {
                'score': score,
                'match_reasons': match_reasons[:5],  # Limit to top 5 reasons
                'mismatch_reasons': mismatch_reasons[:3]  # Limit to top 3 reasons
            }
            
        except Exception as e:
            logger.error(f"Error parsing match response: {str(e)}")
            return {
                'score': 0.0,
                'match_reasons': [f'Error parsing response: {str(e)}'],
                'mismatch_reasons': ['Could not process match evaluation']
            } 