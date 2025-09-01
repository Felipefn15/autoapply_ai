"""
AngelList/Wellfound Job Scraper
"""
import asyncio
import aiohttp
import json
import re
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
            # Try multiple API endpoints and approaches
            endpoints_to_try = [
                # Direct API endpoint
                f"{self.api_url}?department={category}&remote=true&limit=20",
                # Alternative API structure
                f"{self.base_url}/api/jobs?department={category}&remote=true&limit=20",
                # GraphQL endpoint
                f"{self.base_url}/api/graphql",
                # Search endpoint
                f"{self.base_url}/api/search/jobs?q={category}&remote=true&limit=20"
            ]
            
            for endpoint in endpoints_to_try:
                try:
                    logger.info(f"Trying endpoint: {endpoint}")
                    
                    if "graphql" in endpoint:
                        # Try GraphQL query
                        query = {
                            "query": """
                            query GetJobs($department: String!, $remote: Boolean!, $limit: Int!) {
                                jobs(department: $department, remote: $remote, first: $limit) {
                                    edges {
                                        node {
                                            id
                                            title
                                            description
                                            location
                                            remote
                                            salaryMin
                                            salaryMax
                                            startup {
                                                name
                                            }
                                        }
                                    }
                                }
                            }
                            """,
                            "variables": {
                                "department": category,
                                "remote": True,
                                "limit": 20
                            }
                        }
                        
                        async with session.post(endpoint, json=query, headers=self.headers) as response:
                            if response.status == 200:
                                data = await response.json()
                                if 'data' in data and 'jobs' in data['data']:
                                    for edge in data['data']['jobs']['edges']:
                                        job_data = edge['node']
                                        job = self._parse_job_data(job_data)
                                        if job:
                                            jobs.append(job)
                                    logger.info(f"GraphQL API successful for {category}")
                                    break
                    else:
                        # Try REST API
                        async with session.get(endpoint, headers=self.headers, timeout=15) as response:
                            if response.status == 200:
                                try:
                                    data = await response.json()
                                    
                                    # Handle different response formats
                                    if 'jobs' in data:
                                        job_list = data['jobs']
                                    elif 'data' in data:
                                        job_list = data['data']
                                    elif 'results' in data:
                                        job_list = data['results']
                                    else:
                                        job_list = data if isinstance(data, list) else []
                                    
                                    for job_data in job_list[:20]:
                                        job = self._parse_job_data(job_data)
                                        if job:
                                            jobs.append(job)
                                    
                                    logger.info(f"REST API successful for {category}: {len(jobs)} jobs")
                                    break
                                    
                                except json.JSONDecodeError:
                                    logger.warning(f"Invalid JSON response from {endpoint}")
                                    continue
                            else:
                                logger.warning(f"Failed to fetch {endpoint}, status: {response.status}")
                                
                except Exception as e:
                    logger.warning(f"Error with endpoint {endpoint}: {str(e)}")
                    continue
            
            # If all APIs fail, try web scraping as fallback
            if not jobs:
                logger.info(f"All API endpoints failed for {category}, trying web scraping...")
                jobs = await self._scrape_web_fallback(session, category)
                
        except Exception as e:
            logger.error(f"Error scraping category {category}: {str(e)}")
        
        return jobs
    
    async def _scrape_web_fallback(self, session: aiohttp.ClientSession, category: str) -> List[JobPosting]:
        """Fallback to web scraping if API fails."""
        jobs = []
        
        try:
            # Try multiple web scraping approaches
            urls_to_try = [
                f"{self.base_url}/jobs?department={category}&remote=true",
                f"{self.base_url}/jobs?q={category}&remote=true",
                f"{self.base_url}/jobs?category={category}",
                f"{self.base_url}/jobs?search={category}"
            ]
            
            for url in urls_to_try:
                try:
                    logger.info(f"Trying web scraping: {url}")
                    
                    async with session.get(url, headers=self.headers, timeout=15) as response:
                        if response.status == 200:
                            html = await response.text()
                            
                            # Parse HTML for job listings
                            from bs4 import BeautifulSoup
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            # Look for job cards with multiple selectors
                            job_cards = soup.find_all('div', class_='job-card') or \
                                       soup.find_all('div', class_='job-item') or \
                                       soup.find_all('article', class_='job-card') or \
                                       soup.find_all('div', {'data-testid': 'job-card'}) or \
                                       soup.find_all('div', class_=re.compile(r'card|item|listing'))
                            
                            if not job_cards:
                                # Try alternative selectors
                                job_cards = soup.find_all('div', {'data-testid': re.compile(r'job|listing')})
                            
                            for card in job_cards[:15]:  # Increased limit
                                try:
                                    job = self._parse_job_card(card)
                                    if job:
                                        jobs.append(job)
                                except Exception as e:
                                    logger.warning(f"Error parsing job card: {str(e)}")
                                    continue
                            
                            # If we found jobs, break
                            if jobs:
                                logger.info(f"Web scraping found {len(jobs)} jobs for {category}")
                                break
                                
                except Exception as e:
                    logger.warning(f"Error scraping {url}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.warning(f"Web scraping fallback failed: {str(e)}")
        
        return jobs
    
    def _parse_job_card(self, card) -> Optional[JobPosting]:
        """Parse job information from a job card (web scraping fallback)."""
        try:
            # Extract job title
            title_elem = card.find('h3', class_='job-title') or \
                        card.find('h2', class_='job-title') or \
                        card.find('h3') or \
                        card.find('h2')
            title = title_elem.get_text(strip=True) if title_elem else "Unknown Position"
            
            # Extract company name
            company_elem = card.find('span', class_='company-name') or \
                          card.find('div', class_='company-name') or \
                          card.find('span', class_='startup-name')
            company = company_elem.get_text(strip=True) if company_elem else "Unknown Company"
            
            # Extract location
            location_elem = card.find('span', class_='location') or \
                           card.find('div', class_='location')
            location = location_elem.get_text(strip=True) if location_elem else "Remote"
            
            # Extract job URL
            link_elem = card.find('a', href=True)
            if link_elem:
                job_url = link_elem['href']
                if not job_url.startswith('http'):
                    job_url = self.base_url + job_url
            else:
                job_url = ""
            
            # Create job posting
            job = JobPosting(
                title=title,
                description=f"Company: {company}\nLocation: {location}\n\nVaga encontrada no AngelList/Wellfound",
                email=None,
                url=job_url
            )
            
            return job
            
        except Exception as e:
            logger.error(f"Error parsing job card: {str(e)}")
            return None
    
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
