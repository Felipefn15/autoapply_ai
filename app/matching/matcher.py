"""
Job Matcher Module - Matches resumes with job postings
"""
import logging
import os
import time
import json
import hashlib
from typing import Dict, List, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from pathlib import Path

from loguru import logger

from app.job_search.models import JobPosting

CACHE_DIR = Path("data/cache/matches")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def _generate_cache_key(resume_data: Dict, job: JobPosting) -> str:
    """Generate a unique cache key for a resume-job pair."""
    content = f"{json.dumps(resume_data, sort_keys=True)}_{job.title}_{job.description}"
    return hashlib.md5(content.encode()).hexdigest()

@dataclass
class MatchResult:
    """Result of matching a resume with a job posting."""
    score: float
    match_reasons: List[str]
    mismatch_reasons: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        """String representation of the match result."""
        result = f"Match Score: {self.score:.2f}\n"
        
        if self.match_reasons:
            result += "\nMatch Reasons:\n"
            for reason in self.match_reasons:
                result += f"✓ {reason}\n"
                
        if self.mismatch_reasons:
            result += "\nMismatch Reasons:\n"
            for reason in self.mismatch_reasons:
                result += f"✗ {reason}\n"
                
        return result

    def to_dict(self) -> Dict:
        """Convert to dictionary for caching."""
        return {
            'score': self.score,
            'match_reasons': self.match_reasons,
            'mismatch_reasons': self.mismatch_reasons
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'MatchResult':
        """Create from cached dictionary."""
        return cls(
            score=data['score'],
            match_reasons=data['match_reasons'],
            mismatch_reasons=data['mismatch_reasons']
        )

class JobMatcher:
    """Handles matching of resumes with job postings."""
    
    def __init__(self, config: Dict):
        """Initialize the job matcher."""
        self.config = config
        self.min_match_score = 0.3  # Lower threshold for testing
        self.logger = logger.bind(context="job_matcher")
        
        # Get user skills from config
        self.user_skills = set()
        if 'personal' in config:
            skills = config['personal'].get('skills', [])
            if isinstance(skills, list):
                self.user_skills = set(skill.lower() for skill in skills)
    
    def match_jobs(self, jobs: List[JobPosting]) -> List[Dict]:
        """
        Match jobs with user profile.
        
        Args:
            jobs: List of job postings to match against
            
        Returns:
            List of matched jobs with scores
        """
        results = []
        total_jobs = len(jobs)
        
        logger.info(f"Starting to match {total_jobs} jobs...")
        
        for job in jobs:
            try:
                match_result = self._evaluate_match_simple(job)
                
                if match_result.score >= self.min_match_score:
                    # Convert to dict format for compatibility
                    job_dict = job.to_dict()
                    job_dict['match_score'] = match_result.score
                    job_dict['match_reasons'] = match_result.match_reasons
                    job_dict['mismatch_reasons'] = match_result.mismatch_reasons
                    results.append(job_dict)
                
            except Exception as e:
                logger.error(f"Error matching job {job.title}: {str(e)}")
                continue
        
        # Sort by match score descending
        results.sort(key=lambda x: x.get('match_score', 0), reverse=True)
        logger.info(f"Completed matching. Found {len(results)} matches above threshold {self.min_match_score}")
        return results
    
    def _evaluate_match_simple(self, job: JobPosting) -> MatchResult:
        """Simple matching algorithm without external APIs."""
        score = 0.0
        match_reasons = []
        mismatch_reasons = []
        
        # Extract skills from job description
        job_skills = self._extract_skills_from_text(job.description.lower())
        
        # Calculate skill match
        if self.user_skills and job_skills:
            common_skills = self.user_skills.intersection(job_skills)
            if common_skills:
                skill_match_ratio = len(common_skills) / len(job_skills)
                score += skill_match_ratio * 0.6  # 60% weight for skills
                match_reasons.append(f"Skills match: {', '.join(common_skills)}")
            else:
                mismatch_reasons.append("No matching skills found")
        
        # Check for remote work
        remote_indicators = ['remote', 'work from home', 'wfh', 'virtual', 'distributed']
        if any(indicator in job.description.lower() for indicator in remote_indicators):
            score += 0.3  # 30% weight for remote
            match_reasons.append("Remote work available")
        else:
            mismatch_reasons.append("Not remote")
        
        # Check for experience level
        experience_indicators = ['senior', 'lead', 'principal', 'staff']
        if any(indicator in job.title.lower() for indicator in experience_indicators):
            score += 0.1  # 10% weight for senior positions
            match_reasons.append("Senior position")
        
        # Normalize score to 0-1 range
        score = min(score, 1.0)
        
        return MatchResult(
            score=score,
            match_reasons=match_reasons,
            mismatch_reasons=mismatch_reasons
        )
    
    def _extract_skills_from_text(self, text: str) -> set:
        """Extract skills from text."""
        # Common programming languages and technologies
        common_skills = {
            'python', 'javascript', 'typescript', 'react', 'node.js', 'java', 'c++', 'c#',
            'php', 'ruby', 'go', 'rust', 'swift', 'kotlin', 'scala', 'django', 'flask',
            'express', 'angular', 'vue', 'mongodb', 'postgresql', 'mysql', 'redis',
            'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'git', 'linux', 'unix',
            'html', 'css', 'sass', 'less', 'webpack', 'babel', 'jest', 'pytest',
            'selenium', 'playwright', 'cypress', 'jenkins', 'github actions', 'ci/cd'
        }
        
        found_skills = set()
        text_lower = text.lower()
        
        for skill in common_skills:
            if skill in text_lower:
                found_skills.add(skill)
        
        return found_skills 