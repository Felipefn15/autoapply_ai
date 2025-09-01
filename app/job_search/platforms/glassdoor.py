import aiohttp
import asyncio
import logging
from typing import List, Dict, Any
from bs4 import BeautifulSoup
import re
from datetime import datetime

from ..models import JobPosting

logger = logging.getLogger(__name__)

class GlassdoorScraper:
    """Scraper for Glassdoor job postings."""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.base_url = "https://www.glassdoor.com"
        self.search_url = "https://www.glassdoor.com/Job"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Technology job categories
        self.categories = [
            "software-engineer",
            "developer",
            "data-scientist",
            "devops-engineer",
            "product-manager",
            "data-engineer",
            "machine-learning-engineer",
            "full-stack-developer",
            "backend-developer",
            "frontend-developer"
        ]
    
    async def search(self, keywords: List[str] = None) -> List[JobPosting]:
        """Search for jobs on Glassdoor."""
        if keywords is None:
            keywords = ["software engineer", "developer", "python", "react"]
        
        logger.info("Searching Glassdoor jobs...")
        all_jobs = []
        
        # Search in multiple categories
        for category in self.categories[:5]:  # Limit to 5 categories for performance
            try:
                jobs = await self._scrape_category(category)
                all_jobs.extend(jobs)
                logger.info(f"Found {len(jobs)} jobs in {category} category")
                
                # Add delay between categories
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error scraping category {category}: {str(e)}")
                continue
        
        # Remove duplicates based on URL
        unique_jobs = {}
        for job in all_jobs:
            if job.url not in unique_jobs:
                unique_jobs[job.url] = job
        
        logger.info(f"Found {len(unique_jobs)} total unique jobs on Glassdoor")
        return list(unique_jobs.values())
    
    async def _scrape_category(self, category: str) -> List[JobPosting]:
        """Scrape jobs from a specific category."""
        jobs = []
        
        try:
            # Glassdoor search URL structure
            search_url = f"{self.search_url}/{category}-jobs"
            logger.info(f"Scraping category: {search_url}")
            
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(search_url) as response:
                    if response.status != 200:
                        logger.warning(f"Failed to fetch {search_url}, status: {response.status}")
                        return jobs
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Find job listings
                    job_cards = soup.find_all('div', class_=re.compile(r'job-search-card|job-listing'))
                    
                    for card in job_cards[:20]:  # Limit to 20 jobs per category
                        try:
                            job = self._parse_job_card(card, category)
                            if job:
                                jobs.append(job)
                        except Exception as e:
                            logger.warning(f"Error parsing job card: {str(e)}")
                            continue
                    
        except Exception as e:
            logger.error(f"Error scraping Glassdoor category {category}: {str(e)}")
        
        return jobs
    
    def _parse_job_card(self, card, category: str) -> JobPosting:
        """Parse a job card to extract job information."""
        try:
            # Extract job title
            title_elem = card.find('a', class_=re.compile(r'title|job-title'))
            if not title_elem:
                title_elem = card.find('h2') or card.find('h3')
            
            title = title_elem.get_text(strip=True) if title_elem else "Unknown Position"
            
            # Extract company name
            company_elem = card.find('a', class_=re.compile(r'company|employer'))
            if not company_elem:
                company_elem = card.find('span', class_=re.compile(r'company|employer'))
            
            company = company_elem.get_text(strip=True) if company_elem else "Unknown Company"
            
            # Extract job URL
            url_elem = card.find('a', href=True)
            if url_elem and url_elem.get('href'):
                url = url_elem['href']
                if not url.startswith('http'):
                    url = self.base_url + url
            else:
                url = f"{self.base_url}/job/{category}"
            
            # Extract location
            location_elem = card.find('span', class_=re.compile(r'location|city'))
            location = location_elem.get_text(strip=True) if location_elem else "Remote"
            
            # Extract salary (if available)
            salary_elem = card.find('span', class_=re.compile(r'salary|compensation'))
            salary = salary_elem.get_text(strip=True) if salary_elem else ""
            
            # Create job posting
            job = JobPosting(
                title=title,
                company=company,
                location=location,
                url=url,
                platform="Glassdoor",
                category=category,
                salary=salary,
                posted_date=datetime.now().isoformat(),
                description="",
                requirements="",
                benefits=""
            )
            
            return job
            
        except Exception as e:
            logger.warning(f"Error parsing job card: {str(e)}")
            return None
