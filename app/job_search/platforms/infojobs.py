"""
InfoJobs Job Scraper (Brazil)
"""
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from loguru import logger

from ..models import JobPosting

class InfoJobsScraper:
    """InfoJobs job scraper (Brazil)."""
    
    def __init__(self, config: Dict):
        """Initialize InfoJobs scraper."""
        self.config = config
        self.base_url = "https://www.infojobs.com.br"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        
    async def search(self) -> List[JobPosting]:
        """Search for jobs on InfoJobs."""
        try:
            logger.info("Searching InfoJobs jobs...")
            
            jobs = []
            
            # InfoJobs has different job categories
            categories = [
                "tecnologia-da-informacao",
                "desenvolvimento-de-software",
                "engenharia-de-software",
                "analise-de-sistemas",
                "devops",
                "dados",
                "produto"
            ]
            
            # Focus on technology categories
            target_categories = ["tecnologia-da-informacao", "desenvolvimento-de-software", "engenharia-de-software"]
            
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
            
            logger.info(f"Found {len(jobs)} total jobs on InfoJobs")
            return jobs
            
        except Exception as e:
            logger.error(f"Error searching InfoJobs: {str(e)}")
            return []
    
    async def _scrape_category(self, session: aiohttp.ClientSession, category: str) -> List[JobPosting]:
        """Scrape jobs from a specific category."""
        jobs = []
        
        try:
            # InfoJobs uses different URL structure
            if category == "tecnologia-da-informacao":
                url = f"{self.base_url}/vagas-de-emprego/tecnologia-da-informacao"
            elif category == "desenvolvimento-de-software":
                url = f"{self.base_url}/vagas-de-emprego/desenvolvimento"
            elif category == "engenharia-de-software":
                url = f"{self.base_url}/vagas-de-emprego/engenharia"
            else:
                url = f"{self.base_url}/vagas-de-emprego/{category}"
                
            logger.info(f"Scraping category: {url}")
            
            async with session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"Failed to fetch {url}, status: {response.status}")
                    # Try alternative URL structure
                    alt_url = f"{self.base_url}/vagas-de-emprego"
                    logger.info(f"Trying alternative URL: {alt_url}")
                    
                    async with session.get(alt_url) as alt_response:
                        if alt_response.status != 200:
                            logger.warning(f"Alternative URL also failed, status: {alt_response.status}")
                            return jobs
                        
                        html = await alt_response.text()
                else:
                    html = await response.text()
                
                soup = BeautifulSoup(html, 'html.parser')
                
                # Find job listings - try different selectors
                job_cards = soup.find_all('div', class_='job-card')
                if not job_cards:
                    job_cards = soup.find_all('div', class_='job-item')
                if not job_cards:
                    job_cards = soup.find_all('article', class_='job-card')
                if not job_cards:
                    job_cards = soup.find_all('div', {'data-testid': 'job-card'})
                
                logger.info(f"Found {len(job_cards)} job cards")
                
                for card in job_cards[:10]:  # Limit to 10 jobs per category
                    try:
                        job_data = self._parse_job_card(card)
                        if job_data:
                            jobs.append(job_data)
                            
                    except Exception as e:
                        logger.error(f"Error parsing job card: {str(e)}")
                        continue
                
        except Exception as e:
            logger.error(f"Error scraping category {category}: {str(e)}")
        
        return jobs
    
    def _parse_job_card(self, card) -> Optional[JobPosting]:
        """Parse job information from a job card."""
        try:
            # Extract job title
            title_elem = card.find('h2', class_='job-title')
            title = title_elem.get_text(strip=True) if title_elem else "Unknown Position"
            
            # Extract company name
            company_elem = card.find('span', class_='company-name')
            company = company_elem.get_text(strip=True) if company_elem else "Unknown Company"
            
            # Extract location
            location_elem = card.find('span', class_='location')
            location = location_elem.get_text(strip=True) if location_elem else "Remote"
            
            # Extract job URL
            link_elem = card.find('a', href=True)
            job_url = self.base_url + link_elem['href'] if link_elem else ""
            
            # Extract salary if available
            salary_elem = card.find('span', class_='salary')
            salary = salary_elem.get_text(strip=True) if salary_elem else ""
            
            # Create job posting
            job = JobPosting(
                title=title,
                description=f"Company: {company}\nLocation: {location}\nSalary: {salary}\n\nVaga encontrada no InfoJobs",
                email=None,  # InfoJobs doesn't show emails directly
                url=job_url
            )
            
            return job
            
        except Exception as e:
            logger.error(f"Error parsing job card: {str(e)}")
            return None
