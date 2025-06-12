"""
Job Search Module - Handles searching for jobs across different platforms
"""
import logging
from typing import Dict, List, Optional
from urllib.parse import urljoin
from datetime import datetime
import pytz
import re

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel

from app.config import config

logger = logging.getLogger(__name__)

class JobPosting(BaseModel):
    """Data model for job postings."""
    title: str
    company: str
    location: str
    description: str
    url: str
    salary_range: Optional[str] = None
    job_type: Optional[str] = None  # full-time, part-time, contract, etc.
    remote: Optional[bool] = None
    platform: str  # source platform (LinkedIn, Indeed, etc.)
    requirements: List[str]
    posted_date: Optional[str] = None
    timezone: Optional[str] = None
    salary_currency: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    languages: List[str] = []
    visa_sponsorship: Optional[bool] = None
    benefits: List[str] = []

class JobSearcher:
    """Handles job searching across multiple platforms."""
    
    def __init__(self):
        """Initialize the job searcher."""
        self.platforms = {
            'remotive': self._search_remotive,
            'weworkremotely': self._search_weworkremotely
        }
        
        # Common headers for requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Load configuration
        self.config = config
        
        # Setup timezone
        self.local_tz = pytz.timezone(self.config.location.timezone)
    
    def search(self, platform: str = None) -> List[JobPosting]:
        """
        Search for jobs on specified platform or all platforms if none specified.
        
        Args:
            platform: Platform to search on ('linkedin', 'indeed', etc.) or None for all
            
        Returns:
            List of JobPosting objects
        """
        all_jobs = []
        
        # Determine which platforms to search
        platforms_to_search = [platform] if platform else list(self.platforms.keys())
        
        # Validate platform if specified
        if platform and platform not in self.platforms:
            raise ValueError(f"Unsupported platform: {platform}")
        
        # Generate search terms based on technical preferences
        search_terms = {
            'title': f"{self.config.technical.seniority_level} {self.config.technical.role_type}",
            'skills': self.config.technical.primary_skills,
            'location': 'Remote' if self.config.work_preferences.remote_only else self.config.location.city,
            'experience_level': self.config.technical.seniority_level
        }
        
        # Search each platform
        for platform_name in platforms_to_search:
            try:
                logger.info(f"Searching {platform_name}...")
                search_func = self.platforms[platform_name]
                
                # Search for jobs
                platform_jobs = search_func(search_terms)
                
                # Add platform jobs to all jobs
                all_jobs.extend(platform_jobs)
                logger.info(f"Found {len(platform_jobs)} jobs on {platform_name}")
                
            except Exception as e:
                logger.error(f"Error searching {platform_name}: {str(e)}")
        
        # Filter all jobs based on preferences
        filtered_jobs = self._filter_jobs(all_jobs)
        logger.info(f"Found {len(filtered_jobs)} matching jobs after filtering")
        
        return filtered_jobs
    
    def _filter_jobs(self, jobs: List[JobPosting]) -> List[JobPosting]:
        """Filter jobs based on preferences."""
        filtered = []
        
        for job in jobs:
            # Check remote/hybrid preferences
            if self.config.work_preferences.remote_only and not job.remote:
                continue
            if not self.config.work_preferences.accept_hybrid and job.location != "Remote":
                continue
            
            # Check job type preferences
            if job.job_type:
                job_type_lower = job.job_type.lower()
                if "contract" in job_type_lower and not self.config.work_preferences.accept_contract:
                    continue
                if "full-time" in job_type_lower and not self.config.work_preferences.accept_fulltime:
                    continue
                if "part-time" in job_type_lower and not self.config.work_preferences.accept_parttime:
                    continue
            
            # Check salary range if available
            if job.salary_min and job.salary_max:
                if job.salary_currency != self.config.salary.preferred_currency:
                    # TODO: Implement currency conversion
                    pass
                if job.salary_max < self.config.salary.min_salary_usd:
                    continue
            
            # Check company blacklist/preferences
            if job.company in self.config.application.blacklisted_companies:
                continue
            
            # Check language requirements
            if job.languages:
                if not any(lang in self.config.work_preferences.preferred_languages for lang in job.languages):
                    continue
            
            filtered.append(job)
        
        return filtered
    
    def _generate_search_terms(self, resume_data: Dict) -> Dict[str, str]:
        """Generate search terms from resume data."""
        # Extract relevant information from resume
        skills = resume_data.get('skills', [])
        experience = resume_data.get('experience', [])
        
        # Get most recent job title
        recent_title = ""
        if experience:
            recent_title = experience[0].get('position', '')
        
        # Get primary skills (first 5)
        primary_skills = skills[:5] if skills else []
        
        return {
            'title': recent_title,
            'skills': primary_skills,
            'location': 'Remote' if self.config.work_preferences.remote_only else self.config.location.city,
            'experience_level': self.config.technical.seniority_level
        }
    
    def _search_remotive(self, search_terms: Dict) -> List[JobPosting]:
        """Search for jobs on Remotive."""
        jobs = []
        
        try:
            # Remotive has a public API we can use
            api_url = "https://remotive.com/api/remote-jobs"
            params = {
                'search': search_terms['title'],
                'limit': 50  # Increased limit to find more matches
            }
            
            response = requests.get(api_url, params=params, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            for job_data in data.get('jobs', []):
                try:
                    # Extract and clean up data
                    title = job_data.get('title', '').strip()
                    company = job_data.get('company_name', '').strip()
                    description = job_data.get('description', '').strip()
                    
                    if not (title and company and description):
                        continue
                    
                    # Extract salary information
                    salary_str = job_data.get('salary', '')
                    salary_min = None
                    salary_max = None
                    salary_currency = "USD"  # Default assumption
                    
                    if salary_str:
                        # TODO: Implement better salary parsing
                        try:
                            if '-' in salary_str:
                                parts = salary_str.replace('$', '').replace(',', '').split('-')
                                salary_min = int(parts[0].strip())
                                salary_max = int(parts[1].strip())
                        except:
                            pass
                    
                    # Extract languages from description
                    languages = []
                    for lang in self.config.work_preferences.preferred_languages:
                        if lang.lower() in description.lower():
                            languages.append(lang)
                    
                    job = JobPosting(
                        title=title,
                        company=company,
                        location='Remote',
                        description=description,
                        url=job_data.get('url', ''),
                        platform='remotive',
                        requirements=self._extract_requirements(description),
                        remote=True,
                        salary_range=salary_str,
                        salary_currency=salary_currency,
                        salary_min=salary_min,
                        salary_max=salary_max,
                        job_type=job_data.get('job_type', None),
                        posted_date=job_data.get('publication_date', None),
                        languages=languages,
                        benefits=self._extract_benefits(description)
                    )
                    jobs.append(job)
                except Exception as e:
                    logger.warning(f"Error parsing Remotive job: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Remotive search error: {str(e)}")
        
        return jobs
    
    def _search_weworkremotely(self, search_terms: Dict) -> List[JobPosting]:
        """Search for jobs on We Work Remotely."""
        # TODO: Implement We Work Remotely search
        return []
    
    def _extract_requirements(self, description: str) -> List[str]:
        """Extract requirements from job description."""
        # This would use more sophisticated NLP in production
        # For MVP, we'll do simple keyword matching
        common_requirements = [
            "python", "javascript", "java", "c++", "react",
            "angular", "vue", "node", "aws", "docker",
            "kubernetes", "sql", "nosql", "git"
        ]
        
        found_requirements = []
        description_lower = description.lower()
        
        for req in common_requirements:
            if req in description_lower:
                found_requirements.append(req)
        
        return found_requirements
    
    def _extract_benefits(self, description: str) -> List[str]:
        """Extract benefits from job description."""
        common_benefits = [
            "health insurance", "dental", "vision",
            "401k", "stock options", "equity",
            "unlimited pto", "paid time off",
            "remote work", "flexible hours",
            "home office stipend", "education"
        ]
        
        found_benefits = []
        description_lower = description.lower()
        
        for benefit in common_benefits:
            if benefit in description_lower:
                found_benefits.append(benefit.title())
        
        return found_benefits 