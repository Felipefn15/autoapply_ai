"""
Job Matcher Module - Matches resumes with job postings using GROQ
"""
import logging
import os
import time
import json
import hashlib
from typing import Dict, List, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from pathlib import Path

import groq
from pydantic import BaseModel
from loguru import logger

from app.job_search.searcher import JobPosting
from app.config import config

CACHE_DIR = Path("data/cache/matches")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def _generate_cache_key(resume_data: Dict, job: JobPosting) -> str:
    """Generate a unique cache key for a resume-job pair."""
    content = f"{json.dumps(resume_data, sort_keys=True)}_{job.title}_{job.company}_{job.description}"
    return hashlib.md5(content.encode()).hexdigest()

class RateLimiter:
    """Simple rate limiter for API calls."""
    def __init__(self, calls_per_minute: int = 25):
        self.calls_per_minute = calls_per_minute
        self.calls = []
    
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
        
        self.calls.append(now)

@dataclass
class MatchResult:
    """Result of a match evaluation."""
    match_score: float
    match_reasons: List[str]
    suggested_improvements: List[str]
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a value by key with a default."""
        return getattr(self, key, default)
    
    def __str__(self) -> str:
        """String representation of the match result."""
        return f"""Match Score: {self.match_score:.2f}
Reasons:
{chr(10).join(f'- {r}' for r in self.match_reasons)}

Suggested Improvements:
{chr(10).join(f'- {i}' for i in self.suggested_improvements)}"""

    def to_dict(self) -> Dict:
        """Convert to dictionary for caching."""
        return {
            'match_score': self.match_score,
            'match_reasons': self.match_reasons,
            'suggested_improvements': self.suggested_improvements
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'MatchResult':
        """Create from cached dictionary."""
        return cls(
            match_score=data['match_score'],
            match_reasons=data['match_reasons'],
            suggested_improvements=data['suggested_improvements']
        )

class JobMatcher:
    """Handles matching of resumes with job postings using AI."""
    
    def __init__(self, api_key: str):
        """Initialize the job matcher."""
        self.client = groq.Groq(api_key=api_key)
        self.rate_limiter = RateLimiter()
        self.min_match_score = 0.7
        self.logger = logger.bind(context="job_matcher")
    
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
        
        for job in jobs:
            try:
                self.rate_limiter.wait_if_needed()
                match_result = self._evaluate_match(resume_data, job)
                if match_result.match_score >= self.min_match_score:
                    results.append((job, match_result))
            except Exception as e:
                logger.error(f"Error matching job {job.title} at {job.company}: {str(e)}")
                continue
        
        # Sort by match score descending
        results.sort(key=lambda x: x[1].match_score, reverse=True)
        return results
    
    def _evaluate_match(self, resume_data: Dict, job: JobPosting) -> MatchResult:
        """Evaluate match between resume and job posting using GROQ."""
        # Check cache first
        cache_key = _generate_cache_key(resume_data, job)
        cache_file = CACHE_DIR / f"{cache_key}.json"
        
        if cache_file.exists():
            try:
                with cache_file.open('r') as f:
                    cached_data = json.load(f)
                return MatchResult.from_dict(cached_data)
            except Exception as e:
                logger.warning(f"Error reading cache: {str(e)}")
        
        # If not in cache, evaluate match
        try:
            prompt = self._prepare_match_prompt(resume_data, job)
            response = self._make_api_call_with_retry(prompt)
            match_data = self._parse_match_response(response)
            
            # Cache the result
            result = MatchResult(
                match_score=match_data['score'],
                match_reasons=match_data['reasons'],
                suggested_improvements=match_data['suggestions']
            )
            
            try:
                with cache_file.open('w') as f:
                    json.dump(result.to_dict(), f)
            except Exception as e:
                logger.warning(f"Error writing cache: {str(e)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in match evaluation: {str(e)}")
            # Return a low score match in case of error
            return MatchResult(
                match_score=0.0,
                match_reasons=["Error in evaluation"],
                suggested_improvements=["Could not evaluate match"]
            )
    
    def _make_api_call_with_retry(self, prompt: str, max_retries: int = 3) -> Dict:
        """Make API call with retries and exponential backoff."""
        retry_count = 0
        base_wait = 3
        
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
                    return {"error": "Failed to parse response as JSON"}
                
            except Exception as e:
                retry_count += 1
                if retry_count == max_retries:
                    raise e
                
                wait_time = base_wait * (2 ** (retry_count - 1))  # Exponential backoff
                logger.warning(f"API call failed. Retrying in {wait_time} seconds... ({retry_count}/{max_retries})")
                time.sleep(wait_time)
    
    def _prepare_match_prompt(self, resume_data: Dict, job: JobPosting) -> str:
        """Prepare prompt for match evaluation."""
        return f"""Please evaluate the match between this resume and job posting. Return a JSON object with the following fields:
- score: A float between 0.0 and 1.0 indicating the match score
- reasons: A list of strings explaining the key reasons for the match score
- suggestions: A list of strings with suggested improvements for the candidate

Resume:
- Name: {resume_data.get('full_name', 'Not provided')}
- Skills: {', '.join(resume_data.get('skills', []))}
- Experience: {len(resume_data.get('experience', []))} years
- Recent Position: {resume_data.get('experience', [{}])[0].get('position', 'Not provided') if resume_data.get('experience') else 'Not provided'}
- Languages: {', '.join(resume_data.get('languages', []))}

Job Posting:
- Title: {job.title}
- Company: {job.company}
- Location: {job.location}
- Remote: {job.remote}
- Description: {job.description}
- Requirements: {', '.join(job.requirements)}

Return ONLY a valid JSON object with the specified fields. Do not include any additional text or explanation."""
    
    def _parse_match_response(self, response: Dict) -> Dict:
        """Parse the match response from GROQ."""
        try:
            if "error" in response:
                return {
                    "score": 0.0,
                    "reasons": ["Error in evaluation"],
                    "suggestions": ["Could not evaluate match"]
                }
            
            return {
                "score": float(response.get("score", 0.0)),
                "reasons": response.get("reasons", ["No reasons provided"]),
                "suggestions": response.get("suggestions", ["No suggestions available"])
            }
            
        except Exception as e:
            self.logger.error(f"Error parsing match response: {str(e)}")
            return {
                "score": 0.0,
                "reasons": ["Error parsing response"],
                "suggestions": ["Could not parse match response"]
            } 