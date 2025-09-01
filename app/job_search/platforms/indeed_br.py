import aiohttp
import asyncio
import logging
from typing import List, Dict, Any
from bs4 import BeautifulSoup
import re
from datetime import datetime
import urllib.parse

from ..models import JobPosting

logger = logging.getLogger(__name__)

class IndeedBrasilScraper:
    """Scraper for Indeed Brasil job postings."""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.base_url = "https://br.indeed.com"
        self.search_url = "https://br.indeed.com/empregos"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Technology job categories in Portuguese
        self.categories = [
            "desenvolvedor",
            "engenheiro-de-software",
            "programador",
            "analista-de-sistemas",
            "cientista-de-dados",
            "engenheiro-de-dados",
            "devops",
            "analista-de-qualidade",
            "gerente-de-produto",
            "arquiteto-de-software"
        ]
    
    async def search(self, keywords: List[str] = None) -> List[JobPosting]:
        """Search for jobs on Indeed Brasil."""
        if keywords is None:
            keywords = ["desenvolvedor", "engenheiro", "programador", "python", "react"]
        
        logger.info("Searching Indeed Brasil jobs...")
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
        
        logger.info(f"Found {len(unique_jobs)} total unique jobs on Indeed Brasil")
        return list(unique_jobs.values())
    
    async def _scrape_category(self, category: str) -> List[JobPosting]:
        """Scrape jobs from a specific category."""
        jobs = []
        
        try:
            # Indeed Brasil search URL structure
            search_params = {
                'q': category,
                'l': 'Brasil',
                'sort': 'date',
                'limit': '20'
            }
            search_url = f"{self.search_url}?{urllib.parse.urlencode(search_params)}"
            logger.info(f"Scraping category: {search_url}")
            
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(search_url) as response:
                    if response.status != 200:
                        logger.warning(f"Failed to fetch {search_url}, status: {response.status}")
                        return jobs
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Find job listings - Indeed uses various class names
                    job_cards = soup.find_all('div', class_=re.compile(r'job_seen_beacon|jobsearch-ResultsList|job_seen_beacon'))
                    
                    if not job_cards:
                        # Try alternative selectors
                        job_cards = soup.find_all('div', {'data-jk': True})
                    
                    for card in job_cards[:20]:  # Limit to 20 jobs per category
                        try:
                            job = self._parse_job_card(card, category)
                            if job:
                                jobs.append(job)
                        except Exception as e:
                            logger.warning(f"Error parsing job card: {str(e)}")
                            continue
                    
        except Exception as e:
            logger.error(f"Error scraping Indeed Brasil category {category}: {str(e)}")
        
        return jobs
    
    def _parse_job_card(self, card, category: str) -> JobPosting:
        """Parse a job card to extract job information."""
        try:
            # Extract job title
            title_elem = card.find('h2', class_=re.compile(r'title|jobTitle'))
            if not title_elem:
                title_elem = card.find('a', class_=re.compile(r'title|jobTitle'))
            
            title = title_elem.get_text(strip=True) if title_elem else "Unknown Position"
            
            # Extract company name
            company_elem = card.find('span', class_=re.compile(r'company|companyName'))
            if not company_elem:
                company_elem = card.find('div', class_=re.compile(r'company|companyName'))
            
            company = company_elem.get_text(strip=True) if company_elem else "Unknown Company"
            
            # Extract job URL
            url_elem = card.find('a', href=True)
            if url_elem and url_elem.get('href'):
                url = url_elem['href']
                if not url.startswith('http'):
                    url = self.base_url + url
            else:
                url = f"{self.base_url}/empregos?q={category}"
            
            # Extract location
            location_elem = card.find('div', class_=re.compile(r'location|companyLocation'))
            if not location_elem:
                location_elem = card.find('span', class_=re.compile(r'location|companyLocation'))
            
            location = location_elem.get_text(strip=True) if location_elem else "Brasil"
            
            # Extract salary (if available)
            salary_elem = card.find('div', class_=re.compile(r'salary|metadata'))
            if not salary_elem:
                salary_elem = card.find('span', class_=re.compile(r'salary|metadata'))
            
            salary = salary_elem.get_text(strip=True) if salary_elem else ""
            
            # Create job posting
            job = JobPosting(
                title=title,
                company=company,
                location=location,
                url=url,
                platform="Indeed Brasil",
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
