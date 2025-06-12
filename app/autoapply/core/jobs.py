"""
Jobs Module - Handles job searching and management
"""
from typing import Dict, List, Optional
from datetime import datetime
import json
from pathlib import Path
import re

import requests
from pydantic import BaseModel
from loguru import logger

from ..config.settings import config
from ..utils.logging import setup_logger

# Setup module logger
logger = setup_logger("jobs")

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
    platform: str  # source platform (Remotive, WeWorkRemotely, etc.)
    requirements: List[str]
    posted_date: Optional[str] = None
    timezone: Optional[str] = None
    salary_currency: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    languages: List[str] = []
    visa_sponsorship: Optional[bool] = None
    benefits: List[str] = []

class JobManager:
    """Handles job searching across multiple platforms."""
    
    def __init__(self):
        """Initialize the job manager."""
        self.platforms = {
            'remotive': self._search_remotive,
            'weworkremotely': self._search_weworkremotely
        }
        
        # Common headers for requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Setup directories
        self.raw_jobs_dir = Path("data/jobs/raw")
        self.processed_jobs_dir = Path("data/jobs/processed")
        
        # Ensure directories exist
        for directory in [self.raw_jobs_dir, self.processed_jobs_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def search(self, platform: str = None) -> List[JobPosting]:
        """
        Search for jobs on specified platform or all platforms if none specified.
        
        Args:
            platform: Platform to search on ('remotive', 'weworkremotely', etc.) or None for all
            
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
            'title': f"{config.technical.seniority_level} {config.technical.role_type}",
            'skills': config.technical.primary_skills,
            'location': 'Remote' if config.work_preferences.remote_only else config.location.city,
            'experience_level': config.technical.seniority_level
        }
        
        # Search each platform
        for platform_name in platforms_to_search:
            try:
                logger.info(f"Searching {platform_name}...")
                search_func = self.platforms[platform_name]
                
                # Search for jobs
                platform_jobs = search_func(search_terms)
                
                # Save raw jobs
                self._save_raw_jobs(platform_name, platform_jobs)
                
                # Process and filter jobs
                processed_jobs = self._process_jobs(platform_jobs)
                
                # Save processed jobs
                self._save_processed_jobs(platform_name, processed_jobs)
                
                # Add platform jobs to all jobs
                all_jobs.extend(processed_jobs)
                logger.info(f"Found {len(processed_jobs)} jobs on {platform_name}")
                
            except Exception as e:
                logger.error(f"Error searching {platform_name}: {str(e)}")
        
        logger.info(f"Found {len(all_jobs)} total jobs")
        return all_jobs
    
    def _save_raw_jobs(self, platform: str, jobs: List[JobPosting]) -> None:
        """Save raw job data to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.raw_jobs_dir / f"{platform}_{timestamp}.json"
        
        try:
            with output_file.open('w') as f:
                json.dump([job.dict() for job in jobs], f, indent=2)
            logger.debug(f"Saved {len(jobs)} raw jobs to {output_file}")
        except Exception as e:
            logger.error(f"Error saving raw jobs: {str(e)}")
    
    def _save_processed_jobs(self, platform: str, jobs: List[JobPosting]) -> None:
        """Save processed job data to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.processed_jobs_dir / f"{platform}_{timestamp}.json"
        
        try:
            with output_file.open('w') as f:
                json.dump([job.dict() for job in jobs], f, indent=2)
            logger.debug(f"Saved {len(jobs)} processed jobs to {output_file}")
        except Exception as e:
            logger.error(f"Error saving processed jobs: {str(e)}")
    
    def _process_jobs(self, jobs: List[JobPosting]) -> List[JobPosting]:
        """Process and filter jobs based on preferences."""
        processed = []
        
        for job in jobs:
            # Check remote/hybrid preferences
            if config.work_preferences.remote_only and not job.remote:
                continue
            if not config.work_preferences.accept_hybrid and job.location != "Remote":
                continue
            
            # Check job type preferences
            if job.job_type:
                job_type_lower = job.job_type.lower()
                if "contract" in job_type_lower and not config.work_preferences.accept_contract:
                    continue
                if "full-time" in job_type_lower and not config.work_preferences.accept_fulltime:
                    continue
                if "part-time" in job_type_lower and not config.work_preferences.accept_parttime:
                    continue
            
            # Check salary range if available
            if job.salary_min and job.salary_max:
                if job.salary_currency != config.salary.preferred_currency:
                    # TODO: Implement currency conversion
                    pass
                if job.salary_max < config.salary.min_salary_usd:
                    continue
            
            # Check company blacklist/preferences
            if job.company in config.application.blacklisted_companies:
                continue
            
            # Check language requirements
            if job.languages:
                if not any(lang in config.work_preferences.preferred_languages for lang in job.languages):
                    continue
            
            processed.append(job)
        
        return processed
    
    def _search_remotive(self, search_terms: Dict) -> List[JobPosting]:
        """Search for jobs on Remotive."""
        jobs = []
        
        try:
            # Remotive API endpoint
            url = "https://remotive.com/api/remote-jobs"
            
            # Build query parameters based on search terms
            params = {
                "search": f"{search_terms['title']} {' '.join(search_terms['skills'][:3])}",
                "limit": 100  # Maximum results
            }
            
            # Make API request
            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            
            for job_data in data.get('jobs', []):
                try:
                    # Extract salary information if available
                    salary_text = job_data.get('salary', '')
                    salary_min = None
                    salary_max = None
                    salary_currency = "USD"
                    
                    if salary_text:
                        # Try to parse salary range
                        try:
                            salary_parts = salary_text.replace('$', '').replace(',', '').split('-')
                            if len(salary_parts) == 2:
                                salary_min = int(salary_parts[0].strip())
                                salary_max = int(salary_parts[1].strip())
                        except:
                            pass
                    
                    # Extract requirements from description
                    description = job_data.get('description', '')
                    requirements = self._extract_requirements(description)
                    benefits = self._extract_benefits(description)
                    
                    # Create job posting
                    job = JobPosting(
                        title=job_data.get('title', ''),
                        company=job_data.get('company_name', ''),
                        location=job_data.get('candidate_required_location', 'Remote'),
                        description=description,
                        url=job_data.get('url', ''),
                        platform="remotive",
                        requirements=requirements,
                        remote=True,  # Remotive is remote-only
                        job_type=job_data.get('job_type', 'Full-time'),
                        salary_range=salary_text if salary_text else None,
                        salary_currency=salary_currency,
                        salary_min=salary_min,
                        salary_max=salary_max,
                        posted_date=job_data.get('publication_date', ''),
                        languages=["English"],  # Default to English
                        benefits=benefits
                    )
                    jobs.append(job)
                    
                except Exception as e:
                    logger.error(f"Error processing Remotive job: {str(e)}")
                    continue
            
        except Exception as e:
            logger.error(f"Remotive search error: {str(e)}")
        
        return jobs
    
    def _search_weworkremotely(self, search_terms: Dict) -> List[JobPosting]:
        """Search for jobs on WeWorkRemotely."""
        jobs = []
        
        try:
            # WeWorkRemotely API endpoint
            base_url = "https://weworkremotely.com"
            categories = [
                "remote-programming-jobs",
                "remote-back-end-programming-jobs",
                "remote-front-end-programming-jobs",
                "remote-full-stack-programming-jobs"
            ]
            
            for category in categories:
                try:
                    # Make API request for each category
                    url = f"{base_url}/{category}.json"
                    response = requests.get(url, headers=self.headers)
                    response.raise_for_status()
                    
                    data = response.json()
                    
                    for listing in data.get('jobs', []):
                        try:
                            # Extract salary information if available
                            description = listing.get('description', '')
                            salary_match = re.search(r'\$(\d+,?\d*)\s*-\s*\$?(\d+,?\d*)', description)
                            salary_min = None
                            salary_max = None
                            salary_text = None
                            
                            if salary_match:
                                try:
                                    salary_min = int(salary_match.group(1).replace(',', ''))
                                    salary_max = int(salary_match.group(2).replace(',', ''))
                                    salary_text = f"${salary_min:,} - ${salary_max:,}"
                                except:
                                    pass
                            
                            # Extract requirements and benefits
                            requirements = self._extract_requirements(description)
                            benefits = self._extract_benefits(description)
                            
                            # Create job posting
                            job = JobPosting(
                                title=listing.get('title', ''),
                                company=listing.get('company_name', ''),
                                location="Remote",  # WWR is remote-only
                                description=description,
                                url=f"{base_url}{listing.get('url', '')}",
                                platform="weworkremotely",
                                requirements=requirements,
                                remote=True,
                                job_type=listing.get('job_type', 'Full-time'),
                                salary_range=salary_text,
                                salary_currency="USD",
                                salary_min=salary_min,
                                salary_max=salary_max,
                                posted_date=listing.get('published_at', ''),
                                languages=["English"],  # Default to English
                                benefits=benefits
                            )
                            jobs.append(job)
                            
                        except Exception as e:
                            logger.error(f"Error processing WWR job: {str(e)}")
                            continue
                            
                except Exception as e:
                    logger.error(f"Error fetching WWR category {category}: {str(e)}")
                    continue
            
        except Exception as e:
            logger.error(f"WeWorkRemotely search error: {str(e)}")
        
        return jobs
    
    def _extract_requirements(self, description: str) -> List[str]:
        """Extract requirements from job description."""
        requirements = []
        
        # Common requirement indicators
        indicators = [
            r"requirements?:",
            r"qualifications?:",
            r"what you'll need:",
            r"what we're looking for:",
            r"must have:",
            r"required skills?:"
        ]
        
        # Try to find requirements section
        pattern = "|".join(indicators)
        match = re.search(pattern, description.lower())
        
        if match:
            # Get text after the indicator
            req_text = description[match.end():].strip()
            
            # Split into bullet points or sentences
            points = re.split(r'[•\-\*\n]', req_text)
            
            # Clean up points
            for point in points:
                point = point.strip()
                if point and len(point) > 10:  # Ignore very short points
                    requirements.append(point)
        
        return requirements[:10]  # Return top 10 requirements
    
    def _extract_benefits(self, description: str) -> List[str]:
        """Extract benefits from job description."""
        benefits = []
        
        # Common benefit indicators
        indicators = [
            r"benefits?:",
            r"perks?:",
            r"what we offer:",
            r"we provide:",
            r"compensation:",
            r"package includes?:"
        ]
        
        # Try to find benefits section
        pattern = "|".join(indicators)
        match = re.search(pattern, description.lower())
        
        if match:
            # Get text after the indicator
            benefits_text = description[match.end():].strip()
            
            # Split into bullet points or sentences
            points = re.split(r'[•\-\*\n]', benefits_text)
            
            # Clean up points
            for point in points:
                point = point.strip()
                if point and len(point) > 10:  # Ignore very short points
                    benefits.append(point)
        
        return benefits[:10]  # Return top 10 benefits 