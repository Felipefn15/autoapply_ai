"""LinkedIn job scraper implementation."""
import aiohttp
from bs4 import BeautifulSoup
from loguru import logger
from typing import List, Dict, Optional, Tuple
import asyncio
import time
import re
from ..models import JobPosting

class LinkedInScraper:
    """Scraper for LinkedIn jobs."""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the LinkedIn scraper.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {
            'search': {
                'keywords': ['software engineer', 'developer', 'python', 'typescript', 'react'],
                'location': 'Remote',
                'max_jobs': 100,
                'delay_between_requests': 2
            }
        }
        
        self.base_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.linkedin.com/jobs",
            "Connection": "keep-alive",
            "X-Li-Lang": "en_US"
        }
        self.rate_limiter = RateLimiter(calls_per_minute=30)  # 30 requests per minute
        self.retry_count = 3
        self.retry_delay = 5  # seconds

    async def search(self) -> List[JobPosting]:
        """
        Search for jobs on LinkedIn.
        
        Returns:
            List of JobPosting objects
        """
        try:
            # Use LinkedIn API
            api_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
            params = {
                "keywords": " ".join(self.config['search']['keywords']),
                "location": self.config['search']['location'],
                "start": 0
            }
            
            logger.info(f"Searching LinkedIn with params: {params}")
            
            jobs = []
            while len(jobs) < self.config['search']['max_jobs']:
                # Make API request
                async with aiohttp.ClientSession() as session:
                    logger.info(f"Making request to {api_url} with start={params['start']}")
                    async with session.get(api_url, params=params, headers=self.headers) as response:
                        if response.status != 200:
                            logger.error(f"LinkedIn API returned status {response.status}")
                            break
                            
                        html = await response.text()
                        if not html:
                            logger.error("LinkedIn API returned empty response")
                            break
                            
                        # Parse job cards
                        soup = BeautifulSoup(html, 'html.parser')
                        job_cards = soup.find_all('div', {'class': 'job-search-card'})
                        
                        if not job_cards:
                            logger.info("No more job cards found")
                            break
                            
                        logger.info(f"Found {len(job_cards)} job cards")
                        
                        # Process each job card
                        for card in job_cards:
                            if len(jobs) >= self.config['search']['max_jobs']:
                                break
                                
                            try:
                                # Extract job details
                                title = card.find('h3', {'class': 'base-search-card__title'}).text.strip()
                                company = card.find('h4', {'class': 'base-search-card__subtitle'}).text.strip()
                                location = card.find('span', {'class': 'job-search-card__location'}).text.strip()
                                link = card.find('a', {'class': 'base-card__full-link'})['href']
                                
                                logger.info(f"Processing job: {title} at {company}")
                                
                                # Create job posting
                                salary_range = await self._extract_salary(link)
                                job = JobPosting(
                                    title=title,
                                    company=company,
                                    location=location,
                                    url=link,
                                    platform='linkedin',
                                    description=await self._get_job_description(link),
                                    requirements=await self._extract_requirements(link),
                                    remote='remote' in location.lower(),
                                    salary_min=salary_range[0] if salary_range else None,
                                    salary_max=salary_range[1] if salary_range else None
                                )
                                jobs.append(job)
                                
                            except Exception as e:
                                logger.error(f"Error processing LinkedIn job card: {str(e)}")
                                continue
                                
                        # Update start parameter for next page
                        params['start'] += len(job_cards)
                        
                        # Add delay between requests
                        await asyncio.sleep(self.config['search']['delay_between_requests'])
            
            logger.info(f"Found {len(jobs)} jobs on LinkedIn")
            return jobs
            
        except Exception as e:
            logger.error(f"Error searching LinkedIn: {str(e)}")
            return []

    async def _get_job_details(self, session: aiohttp.ClientSession, url: str) -> Dict:
        """Get detailed job information from job page."""
        details = {
            'description': '',
            'requirements': [],
            'remote': False,
            'salary_range': None
        }
        
        try:
            async with session.get(url, headers=self.headers) as response:
                if response.status != 200:
                    return details
                    
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Get job description
                desc_elem = soup.find('div', {'class': 'description__text'})
                if desc_elem:
                    details['description'] = desc_elem.get_text(strip=True)
                    
                    # Extract requirements
                    text = desc_elem.get_text().lower()
                    requirements = []
                    
                    # Look for requirements section
                    req_keywords = ['requirements:', 'qualifications:', 'what you need:', 'what we need:']
                    for line in text.split('\n'):
                        line = line.strip()
                        if any(kw in line.lower() for kw in req_keywords):
                            requirements.extend([r.strip() for r in line.split('•') if r.strip()])
                            
                    details['requirements'] = requirements
                    
                    # Check for remote indicators
                    details['remote'] = any(kw in text for kw in ['remote', 'work from home', 'wfh'])
                    
                    # Try to find salary information
                    salary_keywords = ['salary', 'compensation', 'pay', '$', 'usd', 'eur']
                    for line in text.split('\n'):
                        if any(kw in line.lower() for kw in salary_keywords):
                            details['salary_range'] = line.strip()
                            break
                
                return details
                
        except Exception as e:
            logger.error(f"Error getting job details: {str(e)}")
            return details 

    async def _get_job_description(self, url: str) -> str:
        """Get job description from job page."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status != 200:
                        return ""
                        
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Get job description
                    desc_elem = soup.find('div', {'class': 'description__text'})
                    if desc_elem:
                        return desc_elem.get_text(strip=True)
                    
                    return ""
                    
        except Exception as e:
            logger.error(f"Error getting job description: {str(e)}")
            return ""

    async def _extract_requirements(self, url: str) -> List[str]:
        """Extract requirements from job page."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status != 200:
                        return []
                        
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Get job description
                    desc_elem = soup.find('div', {'class': 'description__text'})
                    if not desc_elem:
                        return []
                        
                    text = desc_elem.get_text().lower()
                    requirements = []
                    
                    # Look for requirements section
                    req_keywords = ['requirements:', 'qualifications:', 'what you need:', 'what we need:']
                    for line in text.split('\n'):
                        line = line.strip()
                        if any(kw in line.lower() for kw in req_keywords):
                            requirements.extend([r.strip() for r in line.split('•') if r.strip()])
                            
                    return requirements
                    
        except Exception as e:
            logger.error(f"Error extracting requirements: {str(e)}")
            return []

    async def _extract_salary(self, url: str) -> Optional[Tuple[float, float]]:
        """Extract salary information from job page."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status != 200:
                        return None
                        
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Get job description
                    desc_elem = soup.find('div', {'class': 'description__text'})
                    if not desc_elem:
                        return None
                        
                    text = desc_elem.get_text().lower()
                    
                    # Try to find salary information
                    patterns = [
                        r'(?:salary|compensation|pay).*?(?:\$|€|£)\s*(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:-|to|–)\s*(?:\$|€|£)\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
                        r'(?:\$|€|£)\s*(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:-|to|–)\s*(?:\$|€|£)\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
                        r'(?:salary|compensation|pay).*?(?:\$|€|£)\s*(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:k|K)',
                        r'(?:\$|€|£)\s*(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:k|K)'
                    ]
                    
                    for pattern in patterns:
                        match = re.search(pattern, text, re.IGNORECASE)
                        if match:
                            # If range found
                            if len(match.groups()) == 2:
                                min_salary = float(match.group(1).replace(',', ''))
                                max_salary = float(match.group(2).replace(',', ''))
                                
                                # Convert k to thousands
                                if 'k' in text[match.start():match.end()].lower():
                                    min_salary *= 1000
                                    max_salary *= 1000
                                    
                                return (min_salary, max_salary)
                            # If single value found
                            else:
                                salary = float(match.group(1).replace(',', ''))
                                if 'k' in text[match.start():match.end()].lower():
                                    salary *= 1000
                                # Use ±10% range
                                return (salary * 0.9, salary * 1.1)
                                
                    return None
                    
        except Exception as e:
            logger.error(f"Error extracting salary: {str(e)}")
            return None

class RateLimiter:
    """Simple rate limiter for API calls."""
    def __init__(self, calls_per_minute: int = 30):
        self.calls_per_minute = calls_per_minute
        self.calls = []
        
    def wait_if_needed(self):
        """Wait if we've exceeded our rate limit."""
        now = time.time()
        minute_ago = now - 60
        
        # Remove calls older than 1 minute
        self.calls = [call_time for call_time in self.calls if call_time > minute_ago]
        
        if len(self.calls) >= self.calls_per_minute:
            # Wait until we're under the limit
            sleep_time = 60 - (now - self.calls[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
            
        self.calls.append(now) 