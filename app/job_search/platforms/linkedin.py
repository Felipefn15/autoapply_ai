"""LinkedIn job scraper implementation."""
import aiohttp
from bs4 import BeautifulSoup
from loguru import logger
from typing import List, Dict, Optional
import asyncio
import time
from ..models import JobPosting

class LinkedInScraper:
    """Scraper for LinkedIn jobs."""
    
    def __init__(self):
        """Initialize the LinkedIn scraper."""
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

    async def search(self, keywords: List[str], location: Optional[str] = None) -> List[JobPosting]:
        """
        Search for jobs on LinkedIn.
        
        Args:
            keywords: List of keywords to search for
            location: Optional location to filter by
            
        Returns:
            List of JobPosting objects
        """
        jobs = []
        
        try:
            # Build search query
            keywords_str = " ".join(keywords)
            location_str = location if location else "Remote"
            
            # Search parameters
            params = {
                "keywords": keywords_str,
                "location": location_str,
                "f_WT": "2",  # Remote jobs filter
                "f_TPR": "r86400",  # Last 24 hours
                "start": "0",
                "sortBy": "DD"  # Sort by date
            }
            
            async with aiohttp.ClientSession() as session:
                start = 0
                while True:
                    try:
                        # Update start position
                        params["start"] = str(start)
                        
                        # Apply rate limiting
                        self.rate_limiter.wait_if_needed()
                        
                        # Make request with retries
                        for attempt in range(self.retry_count):
                            try:
                                async with session.get(self.base_url, params=params, headers=self.headers) as response:
                                    if response.status == 200:
                                        html = await response.text()
                                        break
                                    elif response.status == 429:  # Too Many Requests
                                        logger.warning("Rate limit hit, waiting longer...")
                                        await asyncio.sleep(self.retry_delay * (attempt + 1))
                                        continue
                                    else:
                                        logger.error(f"LinkedIn API error: {response.status}")
                                        break
                            except aiohttp.ClientError as e:
                                if attempt < self.retry_count - 1:
                                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                                    continue
                                raise
                                
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Find all job cards
                        job_cards = soup.find_all('div', {'class': 'job-search-card'})
                        if not job_cards:
                            break
                            
                        for card in job_cards:
                            try:
                                # Extract job details
                                title_elem = card.find('h3', {'class': 'base-search-card__title'})
                                company_elem = card.find('h4', {'class': 'base-search-card__subtitle'})
                                location_elem = card.find('span', {'class': 'job-search-card__location'})
                                link_elem = card.find('a', {'class': 'base-card__full-link'})
                                
                                if not all([title_elem, company_elem, location_elem, link_elem]):
                                    continue
                                
                                title = title_elem.get_text(strip=True)
                                company = company_elem.get_text(strip=True)
                                location = location_elem.get_text(strip=True)
                                url = link_elem['href'].split('?')[0]  # Remove tracking parameters
                                
                                # Get detailed job info
                                details = await self._get_job_details(session, url)
                                
                                # Create JobPosting object
                                job = JobPosting(
                                    title=title,
                                    company=company,
                                    location=location,
                                    description=details.get('description', ''),
                                    url=url,
                                    source='LinkedIn',
                                    remote='remote' in location.lower() or details.get('remote', False),
                                    salary_min=details.get('salary_min'),
                                    salary_max=details.get('salary_max'),
                                    requirements=details.get('requirements', [])
                                )
                                
                                jobs.append(job)
                                
                            except Exception as e:
                                logger.error(f"Error processing job card: {str(e)}")
                                continue
                                
                        # Break if we have enough jobs
                        if len(jobs) >= 100:  # Limit to 100 jobs per search
                            break
                            
                        # Next page
                        start += len(job_cards)
                        
                        # Add delay between pages
                        await asyncio.sleep(2)
                        
                    except Exception as e:
                        logger.error(f"Error fetching LinkedIn jobs page: {str(e)}")
                        break
            
            logger.info(f"Found {len(jobs)} jobs on LinkedIn")
            return jobs
            
        except Exception as e:
            logger.error(f"Error searching LinkedIn jobs: {str(e)}")
            return jobs

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