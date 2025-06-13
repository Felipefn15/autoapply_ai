"""
Job Sources Module - Implementations for different job platforms
"""
from typing import Dict, List, Optional
import aiohttp
from bs4 import BeautifulSoup
from abc import ABC, abstractmethod
from datetime import datetime
import json
import re

from loguru import logger

class JobSource(ABC):
    """Abstract base class for job sources."""
    
    def __init__(self, config: Dict):
        """Initialize the job source with configuration."""
        self.config = config
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
    
    async def _fetch_json(self, url: str) -> Dict:
        """Fetch JSON from URL with error handling."""
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Error fetching {url}: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error fetching JSON from {url}: {str(e)}")
            return None
            
    async def _fetch_html(self, url: str) -> str:
        """Fetch HTML from URL with error handling."""
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        logger.error(f"Error fetching {url}: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error fetching HTML from {url}: {str(e)}")
            return None
    
    @abstractmethod
    async def search(self, keywords: List[str], location: str, max_jobs: int = 50) -> List[Dict]:
        """Search for jobs with given keywords and location."""
        pass
        
    async def _fetch_page(self, url: str, params: Optional[Dict] = None) -> Optional[str]:
        """Fetch a page content."""
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.text()
            return None
        except Exception as e:
            logger.error(f"Error fetching page {url}: {str(e)}")
            return None
            
    async def _fetch_json(self, url: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Fetch JSON data."""
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
            return None
        except Exception as e:
            logger.error(f"Error fetching JSON from {url}: {str(e)}")
            return None

class LinkedInJobSource(JobSource):
    """LinkedIn job source implementation."""
    
    async def search(self, keywords: List[str], location: str, max_jobs: int = 50) -> List[Dict]:
        """Search LinkedIn jobs."""
        jobs = []
        try:
            # Use LinkedIn API
            api_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
            params = {
                "keywords": " ".join(keywords),
                "location": location,
                "start": 0
            }
            
            while len(jobs) < max_jobs:
                html = await self._fetch_html(f"{api_url}?{'&'.join(f'{k}={v}' for k,v in params.items())}")
                if not html:
                    break
                    
                soup = BeautifulSoup(html, 'html.parser')
                job_cards = soup.find_all('div', {'class': 'job-search-card'})
                
                if not job_cards:
                    break
                    
                for card in job_cards:
                    if len(jobs) >= max_jobs:
                        break
                        
                    try:
                        title = card.find('h3', {'class': 'base-search-card__title'}).text.strip()
                        company = card.find('h4', {'class': 'base-search-card__subtitle'}).text.strip()
                        location = card.find('span', {'class': 'job-search-card__location'}).text.strip()
                        link = card.find('a', {'class': 'base-card__full-link'})['href']
                        
                        jobs.append({
                            'title': title,
                            'company': company,
                            'location': location,
                            'url': link,
                            'platform': 'linkedin'
                        })
                    except:
                        continue
                        
                params['start'] += len(job_cards)
                
        except Exception as e:
            logger.error(f"Error searching LinkedIn: {str(e)}")
            
        return jobs

class IndeedJobSource(JobSource):
    """Indeed job source implementation."""
    
    async def search(self, keywords: List[str], location: str, max_jobs: int = 50) -> List[Dict]:
        """Search Indeed jobs."""
        jobs = []
        try:
            # Use Indeed RSS feed instead of web scraping
            # RSS feeds are more stable and less likely to be blocked
            base_url = "https://www.indeed.com/rss"
            params = {
                'q': " ".join(keywords),
                'l': location,
                'sort': 'date',
                'fromage': '30',  # Last 30 days
                'limit': max_jobs
            }
            
            url = f"{base_url}?{'&'.join(f'{k}={v}' for k,v in params.items())}"
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        xml = await response.text()
                        soup = BeautifulSoup(xml, 'xml')
                        
                        for item in soup.find_all('item'):
                            if len(jobs) >= max_jobs:
                                break
                                
                            try:
                                title = item.title.text
                                company = item.source.text
                                location = item.find('georss:point').text if item.find('georss:point') else 'Remote'
                                link = item.link.text
                                
                                jobs.append({
                                    'title': title,
                                    'company': company,
                                    'location': location,
                                    'url': link,
                                    'platform': 'indeed'
                                })
                            except:
                                continue
                                
        except Exception as e:
            logger.error(f"Error searching Indeed: {str(e)}")
            
        return jobs

class RemotiveJobSource(JobSource):
    """Remotive job source implementation."""
    
    async def search(self, keywords: List[str], location: str, max_jobs: int = 50) -> List[Dict]:
        """Search Remotive jobs."""
        jobs = []
        try:
            url = "https://remotive.com/api/remote-jobs"
            params = {
                'search': " ".join(keywords),
                'limit': max_jobs
            }
            
            data = await self._fetch_json(f"{url}?{'&'.join(f'{k}={v}' for k,v in params.items())}")
            if data and 'jobs' in data:
                for job in data['jobs'][:max_jobs]:
                    jobs.append({
                        'title': job.get('title'),
                        'company': job.get('company_name'),
                        'location': 'Remote',
                        'url': job.get('url'),
                        'platform': 'remotive'
                    })
                    
        except Exception as e:
            logger.error(f"Error searching Remotive: {str(e)}")
            
        return jobs

class WeWorkRemotelyJobSource(JobSource):
    """WeWorkRemotely job source implementation."""
    
    async def search(self, keywords: List[str], location: str, max_jobs: int = 50) -> List[Dict]:
        """Search WeWorkRemotely jobs."""
        jobs = []
        try:
            categories = ['remote-jobs-programming', 'remote-jobs-devops-sysadmin', 
                         'remote-jobs-full-stack-programming', 'remote-jobs-back-end-programming',
                         'remote-jobs-front-end-programming']
                         
            for category in categories:
                if len(jobs) >= max_jobs:
                    break
                    
                html = await self._fetch_html(f"https://weworkremotely.com/{category}")
                if not html:
                    continue
                    
                soup = BeautifulSoup(html, 'html.parser')
                job_sections = soup.find_all('section', {'class': 'jobs'})
                
                for section in job_sections:
                    job_items = section.find_all('li', {'class': 'feature'})
                    for item in job_items:
                        if len(jobs) >= max_jobs:
                            break
                            
                        try:
                            title = item.find('span', {'class': 'title'}).text.strip()
                            company = item.find('span', {'class': 'company'}).text.strip()
                            link = item.find('a', href=True)['href']
                            
                            # Check if job matches keywords
                            if any(kw.lower() in title.lower() for kw in keywords):
                                jobs.append({
                                    'title': title,
                                    'company': company,
                                    'location': 'Remote',
                                    'url': f"https://weworkremotely.com{link}",
                                    'platform': 'weworkremotely'
                                })
                        except:
                            continue
                            
        except Exception as e:
            logger.error(f"Error searching WeWorkRemotely: {str(e)}")
            
        return jobs

class StackOverflowJobSource(JobSource):
    """StackOverflow job source implementation."""
    
    async def search(self, keywords: List[str], location: str, max_jobs: int = 50) -> List[Dict]:
        """Search StackOverflow jobs."""
        jobs = []
        try:
            url = "https://stackoverflow.com/jobs"
            params = {
                'q': " ".join(keywords),
                'l': location,
                'pg': 1
            }
            
            while len(jobs) < max_jobs:
                html = await self._fetch_html(f"{url}?{'&'.join(f'{k}={v}' for k,v in params.items())}")
                if not html:
                    break
                    
                soup = BeautifulSoup(html, 'html.parser')
                job_cards = soup.find_all('div', {'class': '-job'})
                
                if not job_cards:
                    break
                    
                for card in job_cards:
                    if len(jobs) >= max_jobs:
                        break
                        
                    try:
                        title = card.find('h2').find('a').text.strip()
                        company = card.find('h3').find('span').text.strip()
                        location = card.find('span', {'class': 'fc-black-500'}).text.strip()
                        link = card.find('h2').find('a')['href']
                        
                        jobs.append({
                            'title': title,
                            'company': company,
                            'location': location,
                            'url': f"https://stackoverflow.com{link}",
                            'platform': 'stackoverflow'
                        })
                    except:
                        continue
                        
                params['pg'] += 1
                
        except Exception as e:
            logger.error(f"Error searching StackOverflow: {str(e)}")
            
        return jobs

class GithubJobsSource(JobSource):
    """GitHub Jobs source implementation."""
    
    async def search(self, keywords: List[str], location: str, max_jobs: int = 50) -> List[Dict]:
        """Search GitHub jobs."""
        jobs = []
        try:
            base_url = "https://jobs.github.com/positions.json"
            params = {
                'description': ' '.join(keywords),
                'location': location or '',
                'full_time': 'true'
            }
            
            data = await self._fetch_json(base_url, params)
            if data:
                for job in data:
                    try:
                        jobs.append({
                            'title': job['title'],
                            'company': job['company'],
                            'location': job['location'],
                            'url': job['url'],
                            'platform': 'github',
                            'type': job['type'],
                            'company_url': job.get('company_url', '')
                        })
                    except Exception as e:
                        logger.error(f"Error parsing GitHub job: {str(e)}")
                        continue
                        
        except Exception as e:
            logger.error(f"Error in GitHub Jobs search: {str(e)}")
            
        return jobs

class AngelListJobSource(JobSource):
    """AngelList job source implementation."""
    
    async def search(self, keywords: List[str], location: str, max_jobs: int = 50) -> List[Dict]:
        """Search AngelList jobs."""
        # Note: AngelList's API requires authentication
        # This is a placeholder for future implementation
        return []

class HackerNewsJobSource(JobSource):
    """HackerNews job source implementation."""
    
    async def search(self, keywords: List[str], location: str, max_jobs: int = 50) -> List[Dict]:
        """Search HackerNews jobs."""
        jobs = []
        try:
            # Search in the monthly "Who is hiring?" threads
            url = "https://hn.algolia.com/api/v1/search_by_date"
            params = {
                'query': 'who is hiring',
                'tags': 'story',
                'numericFilters': 'points>50'
            }
            
            data = await self._fetch_json(f"{url}?{'&'.join(f'{k}={v}' for k,v in params.items())}")
            if not data or 'hits' not in data:
                return jobs
                
            # Get the most recent "Who is hiring?" thread
            hiring_threads = [hit for hit in data['hits'] 
                            if hit.get('title', '').lower().startswith('ask hn: who is hiring?')]
            if not hiring_threads:
                return jobs
                
            thread_id = hiring_threads[0]['objectID']
            
            # Get comments (job posts) from the thread
            comments_url = f"https://hn.algolia.com/api/v1/items/{thread_id}"
            thread_data = await self._fetch_json(comments_url)
            
            if thread_data and 'children' in thread_data:
                for comment in thread_data['children']:
                    if len(jobs) >= max_jobs:
                        break
                        
                    text = comment.get('text', '').lower()
                    if any(kw.lower() in text for kw in keywords):
                        jobs.append({
                            'title': text.split('\n')[0][:100] + '...',
                            'company': 'From HN: Who is Hiring?',
                            'location': 'See description',
                            'url': f"https://news.ycombinator.com/item?id={comment.get('id')}",
                            'platform': 'hackernews'
                        })
                        
        except Exception as e:
            logger.error(f"Error searching HackerNews: {str(e)}")
            
        return jobs 