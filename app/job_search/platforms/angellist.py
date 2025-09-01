"""
AngelList/Wellfound Job Scraper
"""
import asyncio
import aiohttp
import json
from typing import Dict, List, Optional
from loguru import logger

from ..models import JobPosting

class AngelListScraper:
    """AngelList/Wellfound job scraper."""
    
    def __init__(self, config: Dict):
        """Initialize AngelList scraper."""
        self.config = config
        self.base_url = "https://wellfound.com"
        self.api_url = "https://wellfound.com/api/startup_jobs"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Referer": "https://wellfound.com/jobs",
        }
        
    async def search(self) -> List[JobPosting]:
        """Search for jobs on AngelList/Wellfound."""
        try:
            logger.info("Searching AngelList/Wellfound jobs...")
            
            jobs = []
            
            # AngelList has different job categories
            categories = [
                "engineering",
                "design",
                "marketing",
                "sales",
                "operations",
                "product",
                "data",
                "finance",
                "legal",
                "hr"
            ]
            
            # Focus on engineering and related categories
            target_categories = ["engineering", "product", "data"]
            
            async with aiohttp.ClientSession(headers=self.headers) as session:
                for category in target_categories:
                    try:
                        category_jobs = await self._scrape_category(session, category)
                        jobs.extend(category_jobs)
                        logger.info(f"Found {len(category_jobs)} jobs in {category} category")
                        
                        # Add delay between requests
                        await asyncio.sleep(3)
                        
                    except Exception as e:
                        logger.error(f"Error scraping {category} category: {str(e)}")
                        continue
            
            logger.info(f"Found {len(jobs)} total jobs on AngelList/Wellfound")
            return jobs
            
        except Exception as e:
            logger.error(f"Error searching AngelList/Wellfound: {str(e)}")
            return []
    
    async def _scrape_category(self, session: aiohttp.ClientSession, category: str) -> List[JobPosting]:
        """Scrape jobs from a specific category."""
        jobs = []
        
        try:
            # AngelList uses a GraphQL-like API
            url = f"{self.api_url}?department={category}&remote=true&limit=20"
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
            company = job_data.get('startup', {}).get('name', 'Unknown Company')
            location = job_data.get('location', 'Remote')
            salary_min = job_data.get('salary_min', '')
            salary_max = job_data.get('salary_max', '')
            description = job_data.get('description', '')
            job_url = f"{self.base_url}/job_posts/{job_data.get('id', '')}"
            
            # Format salary
            salary = ""
            if salary_min and salary_max:
                salary = f"${salary_min:,} - ${salary_max:,}"
            elif salary_min:
                salary = f"${salary_min:,}+"
            elif salary_max:
                salary = f"Up to ${salary_max:,}"
            
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
                email=None,  # AngelList doesn't show emails directly
                url=job_url
            )
            
            return job
            
        except Exception as e:
            logger.error(f"Error parsing job data: {str(e)}")
            return None
