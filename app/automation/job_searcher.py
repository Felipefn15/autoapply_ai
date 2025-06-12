"""
Job Searcher Module

Handles searching for jobs across multiple platforms:
- LinkedIn
- Indeed
- Remotive
- WeWorkRemotely
- Greenhouse
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import aiohttp
from bs4 import BeautifulSoup
from loguru import logger

class JobSearcher:
    """Searches for jobs across multiple platforms."""
    
    def __init__(self, platform_config: Dict):
        """Initialize the job searcher."""
        self.config = platform_config
        self.last_search = {}  # Track last search time per platform
        
    def search(self) -> List[Dict]:
        """Search for jobs across all enabled platforms."""
        all_jobs = []
        
        # Create event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Run searches for all enabled platforms
            tasks = []
            for platform, config in self.config.items():
                if config['enabled'] and self._should_search(platform, config['search_interval']):
                    tasks.append(self._search_platform(platform))
            
            # Wait for all searches to complete
            if tasks:
                results = loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
                
                # Process results
                for result in results:
                    if isinstance(result, Exception):
                        logger.error(f"Error in job search: {str(result)}")
                    elif result:
                        all_jobs.extend(result)
                        
            return all_jobs
            
        except Exception as e:
            logger.error(f"Error searching for jobs: {str(e)}")
            return []
            
        finally:
            loop.close()
            
    def _should_search(self, platform: str, interval: int) -> bool:
        """Check if we should search this platform based on interval."""
        now = datetime.now()
        last = self.last_search.get(platform)
        
        if not last or (now - last).total_seconds() >= interval:
            self.last_search[platform] = now
            return True
        return False
        
    async def _search_platform(self, platform: str) -> List[Dict]:
        """Search a specific platform for jobs."""
        try:
            if platform == 'linkedin':
                return await self._search_linkedin()
            elif platform == 'indeed':
                return await self._search_indeed()
            elif platform == 'remotive':
                return await self._search_remotive()
            elif platform == 'weworkremotely':
                return await self._search_weworkremotely()
            elif platform == 'greenhouse':
                return await self._search_greenhouse()
            else:
                logger.warning(f"Unknown platform: {platform}")
                return []
        except Exception as e:
            logger.error(f"Error searching {platform}: {str(e)}")
            return []
            
    async def _search_linkedin(self) -> List[Dict]:
        """Search LinkedIn for jobs."""
        jobs = []
        config = self.config['linkedin']
        
        try:
            # Build search URL
            base_url = "https://www.linkedin.com/jobs/search"
            params = {
                'keywords': ' '.join(config['keywords']) if config['keywords'] else '',
                'location': ' '.join(config['locations']) if config['locations'] else '',
                'f_WT': '2' if config['remote_only'] else '',
                'sortBy': 'DD',  # Most recent first
                'position': '1',
                'pageNum': '0'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(base_url, params=params) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Parse job listings
                        for job in soup.find_all('div', class_='job-search-card'):
                            try:
                                # Extract job details
                                title = job.find('h3', class_='base-search-card__title').text.strip()
                                company = job.find('h4', class_='base-search-card__subtitle').text.strip()
                                location = job.find('span', class_='job-search-card__location').text.strip()
                                url = job.find('a', class_='base-card__full-link')['href']
                                job_id = url.split('/')[-1]
                                
                                jobs.append({
                                    'platform': 'linkedin',
                                    'id': job_id,
                                    'title': title,
                                    'company': company,
                                    'location': location,
                                    'url': url,
                                    'description': await self._fetch_job_description(url, session)
                                })
                            except Exception as e:
                                logger.error(f"Error parsing LinkedIn job: {str(e)}")
                                continue
                                
        except Exception as e:
            logger.error(f"Error searching LinkedIn: {str(e)}")
            
        return jobs
        
    async def _search_indeed(self) -> List[Dict]:
        """Search Indeed for jobs."""
        jobs = []
        config = self.config['indeed']
        
        try:
            # Build search URL
            base_url = "https://www.indeed.com/jobs"
            params = {
                'q': ' '.join(config['keywords']) if config['keywords'] else '',
                'l': ' '.join(config['locations']) if config['locations'] else '',
                'remotejob': 'true' if config['remote_only'] else '',
                'sort': 'date',
                'fromage': '1'  # Last 24 hours
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(base_url, params=params) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Parse job listings
                        for job in soup.find_all('div', class_='job_seen_beacon'):
                            try:
                                # Extract job details
                                title = job.find('h2', class_='jobTitle').text.strip()
                                company = job.find('span', class_='companyName').text.strip()
                                location = job.find('div', class_='companyLocation').text.strip()
                                url = 'https://www.indeed.com' + job.find('a', class_='jcs-JobTitle')['href']
                                job_id = url.split('jk=')[-1].split('&')[0]
                                
                                jobs.append({
                                    'platform': 'indeed',
                                    'id': job_id,
                                    'title': title,
                                    'company': company,
                                    'location': location,
                                    'url': url,
                                    'description': await self._fetch_job_description(url, session)
                                })
                            except Exception as e:
                                logger.error(f"Error parsing Indeed job: {str(e)}")
                                continue
                                
        except Exception as e:
            logger.error(f"Error searching Indeed: {str(e)}")
            
        return jobs
        
    async def _search_remotive(self) -> List[Dict]:
        """Search Remotive for jobs."""
        jobs = []
        config = self.config['remotive']
        
        try:
            # Build search URL
            base_url = "https://remotive.com/api/remote-jobs"
            params = {
                'search': ' '.join(config['keywords']) if config['keywords'] else ''
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for job in data['jobs']:
                            try:
                                jobs.append({
                                    'platform': 'remotive',
                                    'id': str(job['id']),
                                    'title': job['title'],
                                    'company': job['company_name'],
                                    'location': 'Remote',
                                    'url': job['url'],
                                    'description': job['description']
                                })
                            except Exception as e:
                                logger.error(f"Error parsing Remotive job: {str(e)}")
                                continue
                                
        except Exception as e:
            logger.error(f"Error searching Remotive: {str(e)}")
            
        return jobs
        
    async def _search_weworkremotely(self) -> List[Dict]:
        """Search WeWorkRemotely for jobs."""
        jobs = []
        config = self.config['weworkremotely']
        
        try:
            # Build search URL
            base_url = "https://weworkremotely.com/remote-jobs.rss"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(base_url) as response:
                    if response.status == 200:
                        xml = await response.text()
                        soup = BeautifulSoup(xml, 'xml')
                        
                        for item in soup.find_all('item'):
                            try:
                                # Extract job details
                                title = item.title.text
                                company = item.find('dc:creator').text
                                url = item.link.text
                                job_id = url.split('/')[-1]
                                description = item.description.text
                                
                                # Filter by keywords if specified
                                if config['keywords'] and not any(kw.lower() in title.lower() for kw in config['keywords']):
                                    continue
                                
                                jobs.append({
                                    'platform': 'weworkremotely',
                                    'id': job_id,
                                    'title': title,
                                    'company': company,
                                    'location': 'Remote',
                                    'url': url,
                                    'description': description
                                })
                            except Exception as e:
                                logger.error(f"Error parsing WeWorkRemotely job: {str(e)}")
                                continue
                                
        except Exception as e:
            logger.error(f"Error searching WeWorkRemotely: {str(e)}")
            
        return jobs
        
    async def _search_greenhouse(self) -> List[Dict]:
        """Search Greenhouse for jobs."""
        jobs = []
        config = self.config['greenhouse']
        
        try:
            # Build search URL
            base_url = "https://api.greenhouse.io/v1/boards/recently_published_jobs"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(base_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for job in data['jobs']:
                            try:
                                # Filter by keywords if specified
                                if config['keywords'] and not any(kw.lower() in job['title'].lower() for kw in config['keywords']):
                                    continue
                                
                                jobs.append({
                                    'platform': 'greenhouse',
                                    'id': str(job['id']),
                                    'title': job['title'],
                                    'company': job['company']['name'],
                                    'location': job['location']['name'],
                                    'url': job['absolute_url'],
                                    'description': await self._fetch_job_description(job['absolute_url'], session)
                                })
                            except Exception as e:
                                logger.error(f"Error parsing Greenhouse job: {str(e)}")
                                continue
                                
        except Exception as e:
            logger.error(f"Error searching Greenhouse: {str(e)}")
            
        return jobs
        
    async def _fetch_job_description(self, url: str, session: aiohttp.ClientSession) -> Optional[str]:
        """Fetch full job description from URL."""
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Try common job description selectors
                    selectors = [
                        'div.job-description',
                        'div.description',
                        'div#job-description',
                        'div.jobDescriptionText',
                        'div[data-automation="jobDescription"]'
                    ]
                    
                    for selector in selectors:
                        description = soup.select_one(selector)
                        if description:
                            return description.get_text(strip=True)
                            
                    # If no specific selector works, try to find the largest text block
                    text_blocks = soup.find_all(['p', 'div', 'section'])
                    if text_blocks:
                        largest_block = max(text_blocks, key=lambda x: len(x.get_text()))
                        return largest_block.get_text(strip=True)
                        
            return None
            
        except Exception as e:
            logger.error(f"Error fetching job description: {str(e)}")
            return None 