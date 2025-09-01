"""
WeWorkRemotely Job Scraper
"""
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from loguru import logger

from ..models import JobPosting

class WeWorkRemotelyScraper:
    """WeWorkRemotely job scraper."""
    
    def __init__(self, config: Dict):
        """Initialize WeWorkRemotely scraper."""
        self.config = config
        self.base_url = "https://weworkremotely.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        
    async def search(self) -> List[JobPosting]:
        """Search for jobs on WeWorkRemotely."""
        try:
            logger.info("Searching WeWorkRemotely jobs...")
            
            jobs = []
            
            # WeWorkRemotely has different categories
            categories = [
                "programming",
                "design", 
                "customer-support",
                "copywriting",
                "devops-sysadmin",
                "business",
                "finance",
                "all",
                "product",
                "sales",
                "management"
            ]
            
            # Focus on programming and related categories
            target_categories = ["programming", "devops-sysadmin", "product"]
            
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
            
            logger.info(f"Found {len(jobs)} total jobs on WeWorkRemotely")
            return jobs
            
        except Exception as e:
            logger.error(f"Error searching WeWorkRemotely: {str(e)}")
            return []
    
    async def _scrape_category(self, session: aiohttp.ClientSession, category: str) -> List[JobPosting]:
        """Scrape jobs from a specific category."""
        jobs = []
        
        try:
            url = f"{self.base_url}/categories/remote-{category}-jobs"
            logger.info(f"Scraping category: {url}")
            
            async with session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"Failed to fetch {url}, status: {response.status}")
                    return jobs
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Find job listings
                job_sections = soup.find_all('section', class_='jobs')
                
                for section in job_sections:
                    job_links = section.find_all('a', href=True)
                    
                    for link in job_links[:10]:  # Limit to 10 jobs per category
                        try:
                            job_url = self.base_url + link['href']
                            job_data = await self._scrape_job_details(session, job_url)
                            
                            if job_data:
                                jobs.append(job_data)
                                
                        except Exception as e:
                            logger.error(f"Error scraping job details: {str(e)}")
                            continue
                
        except Exception as e:
            logger.error(f"Error scraping category {category}: {str(e)}")
        
        return jobs
    
    async def _scrape_job_details(self, session: aiohttp.ClientSession, job_url: str) -> Optional[JobPosting]:
        """Scrape detailed job information."""
        try:
            async with session.get(job_url) as response:
                if response.status != 200:
                    return None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract job title
                title_elem = soup.find('h1')
                title = title_elem.get_text(strip=True) if title_elem else "Unknown Position"
                
                # Extract company name
                company_elem = soup.find('span', class_='company')
                company = company_elem.get_text(strip=True) if company_elem else "Unknown Company"
                
                # Extract job description
                description_elem = soup.find('div', class_='listing-container')
                description = description_elem.get_text(strip=True) if description_elem else ""
                
                # Extract location
                location_elem = soup.find('span', class_='location')
                location = location_elem.get_text(strip=True) if location_elem else "Remote"
                
                # Extract salary if available
                salary_elem = soup.find('span', class_='salary')
                salary = salary_elem.get_text(strip=True) if salary_elem else ""
                
                # Create job posting
                job = JobPosting(
                    title=title,
                    description=f"Company: {company}\nLocation: {location}\nSalary: {salary}\n\n{description}",
                    email=None,  # WeWorkRemotely doesn't show emails directly
                    url=job_url
                )
                
                return job
                
        except Exception as e:
            logger.error(f"Error scraping job details from {job_url}: {str(e)}")
            return None
