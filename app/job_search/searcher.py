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
        
        # Load credentials
        self.credentials = self._load_credentials()
        
        self.config = config or {
            'search': {
                'keywords': self.credentials.get('skills', ['software engineer', 'developer', 'python']),
                'max_jobs': self.credentials.get('search', {}).get('max_jobs_per_platform', 100),
                'delay_between_requests': self.credentials.get('search', {}).get('search_delay', 2),
                'remote_only': self.credentials.get('search', {}).get('remote_only', True),
                'max_applications_per_day': self.credentials.get('search', {}).get('max_applications_per_day', 50),
                'max_concurrent_applications': self.credentials.get('search', {}).get('max_concurrent_applications', 10)
            },
            'credentials': {
                'linkedin': {
                    'email': self.credentials.get('linkedin', {}).get('email'),
                    'password': self.credentials.get('linkedin', {}).get('password'),
                    'enabled': self.credentials.get('linkedin', {}).get('enabled', False)
                }
            }
        }
        
        # Store logger instance
        self.logger_instance = logger_instance
        
        # Initialize scrapers with configuration
        self.scrapers = []
        
        # Add scrapers based on configuration
        if (self.credentials.get('linkedin', {}).get('enabled') and 
            self.credentials.get('linkedin', {}).get('email')):
            self.scrapers.append(LinkedInScraper(self.config))
            logger.info("✅ LinkedIn scraper enabled with credentials")
        else:
            logger.warning("⚠️ LinkedIn scraper disabled - missing credentials")
        
        # Always add these scrapers (they don't need credentials)
        self.scrapers.extend([
            WeWorkRemotelyScraper(self.config),
            RemotiveScraper(self.config),
            AngelListScraper(self.config),
            HackerNewsScraper(self.config),
            InfoJobsScraper(self.config),
            CathoScraper(self.config),
        ])
        
        logger.info(f"🚀 Initialized {len(self.scrapers)} scrapers for maximum job discovery")

    def _load_credentials(self) -> Dict:
        """Load credentials from credentials.yaml file."""
        try:
            import yaml
            credentials_path = "config/credentials.yaml"
            if os.path.exists(credentials_path):
                with open(credentials_path, 'r') as f:
                    return yaml.safe_load(f)
            else:
                logger.warning(f"Credentials file not found: {credentials_path}")
                return {}
        except Exception as e:
            logger.error(f"Error loading credentials: {e}")
            return {}
    
    async def search(self, keywords: Optional[List[str]] = None) -> List[JobPosting]:
        """
        Search for jobs across all platforms with maximum efficiency.
        
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
            elif 'search' in self.config and 'keywords' in self.config['search']:
                search_keywords = self.config['search']['keywords']
            else:
                search_keywords = ['software engineer', 'developer', 'python', 'react']
            
        all_jobs = []
        
        try:
            logger.info(f"🚀 Starting MAXIMUM job search with keywords: {', '.join(search_keywords)}")
            logger.info(f"📊 Target: {self.config.get('search', {}).get('max_jobs', 100)} jobs per platform")
            logger.info(f"⚡ Max concurrent applications: {self.config.get('search', {}).get('max_concurrent_applications', 10)}")
            
            # Create tasks for each scraper with optimized concurrency
            tasks = []
            for scraper in self.scrapers:
                logger.info(f"🔄 Initializing search on {scraper.__class__.__name__}")
                task = asyncio.create_task(self._search_with_logging(scraper, search_keywords))
                tasks.append(task)
            
            # Wait for all scrapers to complete with timeout
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results and optimize job list
            for scraper, result in zip(self.scrapers, results):
                platform = scraper.__class__.__name__
                if isinstance(result, Exception):
                    logger.error(f"❌ Error in {platform}: {str(result)}")
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
                    logger.info(f"\n✅ Results from {platform}:")
                    logger.info("=" * 50)
                    
                    # Convert each job to simplified format and limit per platform
                    platform_jobs = []
                    max_jobs = self.config.get('search', {}).get('max_jobs', 100)
                    for job in result[:max_jobs]:
                        simplified_job = JobPosting(
                            title=job.title,
                            description=job.description,
                            email=job.email,
                            url=job.url
                        )
                        platform_jobs.append(simplified_job)
                        
                        # Log job details (only first 5 for brevity)
                        if len(platform_jobs) <= 5:
                            logger.info(f"📋 {job.title}")
                            logger.info(f"🔗 {job.url}")
                    
                    all_jobs.extend(platform_jobs)
                    logger.info(f"📊 {platform}: {len(platform_jobs)} jobs (limited to {max_jobs})")
            
            # Remove duplicates based on URL
            unique_jobs = []
            seen_urls = set()
            for job in all_jobs:
                if job.url not in seen_urls:
                    unique_jobs.append(job)
                    seen_urls.add(job.url)
            
            logger.info(f"\n🎯 SEARCH SUMMARY:")
            logger.info("=" * 60)
            logger.info(f"📊 Total unique jobs found: {len(unique_jobs)}")
            logger.info(f"🎯 Target applications per day: {self.config.get('search', {}).get('max_applications_per_day', 50)}")
            logger.info(f"⚡ Max concurrent applications: {self.config.get('search', {}).get('max_concurrent_applications', 10)}")
            
            # Platform breakdown
            for scraper in self.scrapers:
                platform = scraper.__class__.__name__
                platform_jobs = [j for j in unique_jobs if platform.lower() in j.url.lower()]
                if platform_jobs:
                    logger.info(f"   {platform}: {len(platform_jobs)} jobs")
            
            return unique_jobs
            
        except Exception as e:
            logger.error(f"❌ Error searching jobs: {str(e)}")
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