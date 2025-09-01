"""
Remotive Job Scraper
"""
import asyncio
import aiohttp
import json
from typing import Dict, List, Optional
from loguru import logger

from ..models import JobPosting

class RemotiveScraper:
    """Remotive job scraper."""
    
    def __init__(self, config: Dict):
        """Initialize Remotive scraper."""
        self.config = config
        self.base_url = "https://remotive.com"
        self.api_url = "https://remotive.com/api/remote-jobs"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
        
    async def search(self) -> List[JobPosting]:
        """Search for jobs on Remotive."""
        try:
            logger.info("Searching Remotive jobs...")
            
            jobs = []
            
            # Remotive has different job categories
            categories = [
                "software-dev",
                "design",
                "customer-support",
                "copywriting",
                "devops-sysadmin",
                "business",
                "finance",
                "product",
                "sales",
                "all"
            ]
            
            # Focus on software development and related categories
            target_categories = ["software-dev", "devops-sysadmin", "product"]
            
            async with aiohttp.ClientSession(headers=self.headers) as session:
                for category in target_categories:
                    try:
                        category_jobs = await self._scrape_category(session, category)
                        jobs.extend(category_jobs)
                        logger.info(f"Found {len(category_jobs)} jobs in {category} category")
                        
                        # Add delay between requests
                        await asyncio.sleep(2)
                        
                    except Exception as e:
                        logger.error(f"Error scraping {category} category: {str(e)}")
                        continue
            
            logger.info(f"Found {len(jobs)} total jobs on Remotive")
            return jobs
            
        except Exception as e:
            logger.error(f"Error searching Remotive: {str(e)}")
            return []
    
    async def _scrape_category(self, session: aiohttp.ClientSession, category: str) -> List[JobPosting]:
        """Scrape jobs from a specific category."""
        jobs = []
        
        try:
            # Remotive uses a REST API
            url = f"{self.api_url}?category={category}&limit=20"
            logger.info(f"Scraping category: {url}")
            
            async with session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"Failed to fetch {url}, status: {response.status}")
                    return jobs
                
                data = await response.json()
                
                if 'jobs' in data:
                    for job_data in data['jobs'][:10]:  # Limit to 10 jobs per category
                        try:
                            job = self._parse_job_data(job_data)
                            if job:
                                jobs.append(job)
                                
                        except Exception as e:
                            logger.error(f"Error parsing job data: {str(e)}")
                            continue
                
        except Exception as e:
            logger.error(f"Error scraping category {category}: {str(e)}")
        
        return jobs
    
    def _parse_job_data(self, job_data: Dict) -> Optional[JobPosting]:
        """Parse job data from API response."""
        try:
            # Extract job information
            title = job_data.get('title', 'Unknown Position')
            company = job_data.get('company_name', 'Unknown Company')
            location = job_data.get('candidate_required_location', 'Remote')
            salary = job_data.get('salary', '')
            description = job_data.get('description', '')
            job_url = job_data.get('url', '')
            
            # Clean up description
            if description:
                # Remove HTML tags if present
                import re
                description = re.sub(r'<[^>]+>', '', description)
                description = description.strip()
            
            # Create job posting
            job = JobPosting(
                title=title,
                description=f"Company: {company}\nLocation: {location}\nSalary: {salary}\n\n{description}",
                email=None,  # Remotive doesn't show emails directly
                url=job_url
            )
            
            return job
            
        except Exception as e:
            logger.error(f"Error parsing job data: {str(e)}")
            return None
