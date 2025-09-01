"""
Job Search Module - Search for jobs across multiple platforms
"""
import asyncio
import os
import time
from typing import Dict, List, Optional
from dotenv import load_dotenv

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
from .platforms import (
    LinkedInScraper, 
    HackerNewsScraper,
    WeWorkRemotelyScraper,
    RemotiveScraper,
    AngelListScraper,
    InfoJobsScraper,
    CathoScraper
)

class JobSearcher:
    """Job searcher class."""
    
    def __init__(self, config: Optional[Dict] = None, logger_instance=None):
        """
        Initialize the job searcher.
        
        Args:
            config: Optional configuration dictionary
            logger_instance: Optional ApplicationLogger instance for detailed logging
        """
        # Load environment variables
        load_dotenv()
        
        self.config = config or {
            'search': {
                'keywords': os.getenv('PRIMARY_SKILLS', 'software engineer,developer,python').split(','),
                'max_jobs': int(os.getenv('MAX_APPLICATIONS_PER_DAY', '20')),
                'delay_between_requests': 5,
                'remote_only': os.getenv('REMOTE_ONLY', 'true').lower() == 'true'
            },
            'credentials': {
                'linkedin': {
                    'email': os.getenv('LINKEDIN_EMAIL'),
                    'password': os.getenv('LINKEDIN_PASSWORD')
                }
            }
        }
        
        # Store logger instance
        self.logger_instance = logger_instance
        
        # Initialize scrapers with configuration
        self.scrapers = [
            # International platforms
            WeWorkRemotelyScraper(self.config),
            RemotiveScraper(self.config),
            AngelListScraper(self.config),
            HackerNewsScraper(self.config),
            
            # Brazilian platforms
            InfoJobsScraper(self.config),
            CathoScraper(self.config),
            
            # LinkedIn (requires credentials)
            LinkedInScraper(self.config),
        ]

    async def search(self, keywords: Optional[List[str]] = None) -> List[JobPosting]:
        """
        Search for jobs across all platforms.
        
        Args:
            keywords: Optional list of keywords to search for. If not provided, uses config keywords.
            
        Returns:
            List of JobPosting objects with only title, description and email
        """
        # Get keywords from config or use defaults
        if keywords:
            search_keywords = keywords
        else:
            # Try to get keywords from config
            if 'personal' in self.config and 'skills' in self.config['personal']:
                search_keywords = self.config['personal']['skills']
            else:
                search_keywords = ['software engineer', 'developer', 'python', 'react']
            
        all_jobs = []
        
        try:
            logger.info(f"Starting job search with keywords: {', '.join(search_keywords)}")
            
            # Create tasks for each scraper
            tasks = []
            for scraper in self.scrapers:
                logger.info(f"Initializing search on {scraper.__class__.__name__}")
                task = asyncio.create_task(self._search_with_logging(scraper, search_keywords))
                tasks.append(task)
            
            # Wait for all scrapers to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for scraper, result in zip(self.scrapers, results):
                platform = scraper.__class__.__name__
                if isinstance(result, Exception):
                    logger.error(f"Error in {platform}: {str(result)}")
                    # Log the error to the application logger
                    if self.logger_instance:
                        self.logger_instance.log_job_search(
                            platform=platform,
                            keywords=search_keywords,
                            jobs_found=0,
                            search_duration=0.0,
                            errors=[str(result)]
                        )
                    continue
                    
                if isinstance(result, list):
                    logger.info(f"\nResults from {platform}:")
                    logger.info("=" * 50)
                    
                    # Convert each job to simplified format
                    for job in result:
                        simplified_job = JobPosting(
                            title=job.title,
                            description=job.description,
                            email=job.email,
                            url=job.url
                        )
                        all_jobs.append(simplified_job)
                        
                        # Log job details
                        logger.info(f"Title: {job.title}")
                        logger.info(f"URL: {job.url}")
                        logger.info("-" * 50)
            
            logger.info(f"\nSearch Summary:")
            logger.info("=" * 50)
            logger.info(f"Total jobs found: {len(all_jobs)}")
            for scraper in self.scrapers:
                platform = scraper.__class__.__name__
                platform_jobs = [j for j in all_jobs if platform.lower() in j.url.lower()]
                logger.info(f"{platform}: {len(platform_jobs)} jobs")
            
            return all_jobs
            
        except Exception as e:
            logger.error(f"Error searching jobs: {str(e)}")
            return []
    
    async def _search_with_logging(self, scraper, keywords: List[str]) -> List[JobPosting]:
        """Search with a specific scraper and log the results."""
        platform = scraper.__class__.__name__
        start_time = time.time()
        errors = []
        
        try:
            # Perform the search
            jobs = await scraper.search()
            search_duration = time.time() - start_time
            
            # Log the search results
            if self.logger_instance:
                self.logger_instance.log_job_search(
                    platform=platform,
                    keywords=keywords,
                    jobs_found=len(jobs),
                    search_duration=search_duration,
                    errors=errors
                )
            
            return jobs
            
        except Exception as e:
            search_duration = time.time() - start_time
            errors.append(str(e))
            
            # Log the error
            if self.logger_instance:
                self.logger_instance.log_job_search(
                    platform=platform,
                    keywords=keywords,
                    jobs_found=0,
                    search_duration=search_duration,
                    errors=errors
                )
            
            raise e
    
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