"""
Job Search Module - Search for jobs across multiple platforms
"""
import asyncio
from typing import Dict, List, Optional

from loguru import logger

from .job_sources import (
    LinkedInJobSource,
    # IndeedJobSource,  # Temporarily disabled
    RemotiveJobSource,
    WeWorkRemotelyJobSource,
    AngelListJobSource,
    HackerNewsJobSource
)
from .models import JobPosting
from .platforms import LinkedInScraper, HackerNewsScraper

class JobSearcher:
    """Job searcher class."""
    
    def __init__(self):
        """Initialize the job searcher."""
        self.scrapers = [
            LinkedInScraper(),
            HackerNewsScraper()
        ]

    async def search(self, keywords: List[str], location: Optional[str] = None) -> List[JobPosting]:
        """
        Search for jobs across all platforms.
        
        Args:
            keywords: List of keywords to search for
            location: Optional location to filter by
            
        Returns:
            List of JobPosting objects
        """
        all_jobs = []
        
        try:
            # Create tasks for each scraper
            tasks = []
            for scraper in self.scrapers:
                task = asyncio.create_task(scraper.search(keywords, location))
                tasks.append(task)
            
            # Wait for all scrapers to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Scraper error: {str(result)}")
                    continue
                    
                if isinstance(result, list):
                    all_jobs.extend(result)
            
            logger.info(f"Found {len(all_jobs)} total jobs")
            return all_jobs
            
        except Exception as e:
            logger.error(f"Error searching jobs: {str(e)}")
            return []
    
    def filter_jobs(self, jobs: List[JobPosting]) -> List[JobPosting]:
        """Filter jobs based on preferences."""
        filtered = []
        
        try:
            preferences = self.config.get('preferences', {})
            excluded_companies = set(preferences.get('excluded_companies', []))
            min_salary = preferences.get('min_salary', 0)
            
            for job in jobs:
                # Skip if company is excluded
                if job.company.lower() in [c.lower() for c in excluded_companies]:
                    continue
                
                # Skip if salary is too low
                if job.salary_max and job.salary_max < min_salary:
                    continue
                
                # Add job to filtered list
                filtered.append(job)
            
            return filtered
            
        except Exception as e:
            logger.error(f"Error filtering jobs: {str(e)}")
            return jobs 