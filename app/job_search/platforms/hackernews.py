"""HackerNews job scraper implementation."""
import aiohttp
from bs4 import BeautifulSoup
from loguru import logger
from typing import List, Dict, Optional, Tuple
import asyncio
from datetime import datetime
import re
from ..models import JobPosting

class HackerNewsScraper:
    """Scraper for HackerNews jobs."""
    
    def __init__(self):
        """Initialize the HackerNews scraper."""
        self.base_url = "https://news.ycombinator.com"
        self.api_url = "https://hacker-news.firebaseio.com/v0"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }
        self.timeout = aiohttp.ClientTimeout(total=30)  # 30 seconds timeout
        self.retry_count = 3
        self.retry_delay = 5  # seconds

    async def get_latest_who_is_hiring_thread(self) -> Optional[str]:
        """Get the latest Who is Hiring thread ID."""
        try:
            # Get current month's thread
            current_month = datetime.now().strftime("%B %Y")
            search_title = f"Ask HN: Who is hiring? ({current_month})"
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                # Search for the thread using Algolia API
                search_url = "https://hn.algolia.com/api/v1/search"
                params = {
                    "query": search_title,
                    "tags": "story",
                    "numericFilters": "points>100"
                }
                
                async with session.get(search_url, params=params) as response:
                    if response.status != 200:
                        return None
                        
                    data = await response.json()
                    hits = data.get('hits', [])
                    
                    for hit in hits:
                        if hit.get('title', '').startswith('Ask HN: Who is hiring?'):
                            return hit.get('objectID')
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting latest Who is Hiring thread: {str(e)}")
            return None

    def _parse_salary(self, text: str) -> Optional[Tuple[float, float]]:
        """
        Parse salary information from text.
        
        Args:
            text: Text containing salary information
            
        Returns:
            Tuple of (min_salary, max_salary) in USD per year, or None if no valid salary found
        """
        try:
            # Remove HTML entities and normalize text
            text = text.lower().strip()
            text = re.sub(r'&[^;]+;', '', text)
            text = re.sub(r'[^\w\s\d$k\-–/,.]', '', text)
            
            # Common patterns for salary ranges
            patterns = [
                # Yearly ranges with k
                r'\$?(\d+(?:,\d{3})*(?:\.\d+)?k?)?\s*(?:[-–]|to)\s*\$?(\d+(?:,\d{3})*(?:\.\d+)?k)',
                # Monthly ranges
                r'\$?(\d+(?:,\d{3})*(?:\.\d+)?k?)/month\s*(?:[-–]|to)\s*\$?(\d+(?:,\d{3})*(?:\.\d+)?k?)/month',
                # Single value with k
                r'\$?(\d+(?:,\d{3})*(?:\.\d+)?k)',
                # Single value per month
                r'\$?(\d+(?:,\d{3})*(?:\.\d+)?k?)/month',
                # Euro ranges
                r'€(\d+(?:,\d{3})*(?:\.\d+)?k?)?\s*(?:[-–]|to)\s*€?(\d+(?:,\d{3})*(?:\.\d+)?k)',
                # Single Euro value
                r'€(\d+(?:,\d{3})*(?:\.\d+)?k)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    groups = match.groups()
                    
                    if len(groups) == 2 and groups[0] and groups[1]:  # Range found
                        min_val = float(groups[0].replace(',', '').replace('k', '000'))
                        max_val = float(groups[1].replace(',', '').replace('k', '000'))
                        
                        # Convert monthly to yearly if needed
                        if '/month' in text:
                            min_val *= 12
                            max_val *= 12
                            
                        # Convert Euro to USD (approximate)
                        if '€' in text:
                            min_val *= 1.1  # Approximate EUR to USD conversion
                            max_val *= 1.1
                            
                        # Validate reasonable salary ranges
                        if min_val < 1000:  # Likely in thousands
                            min_val *= 1000
                        if max_val < 1000:  # Likely in thousands
                            max_val *= 1000
                            
                        if min_val > 1000000 or max_val > 1000000:  # Likely parsing error
                            return None
                            
                        return min_val, max_val
                        
                    elif len(groups) == 1 and groups[0]:  # Single value found
                        val = float(groups[0].replace(',', '').replace('k', '000'))
                        
                        # Convert monthly to yearly if needed
                        if '/month' in text:
                            val *= 12
                            
                        # Convert Euro to USD (approximate)
                        if '€' in text:
                            val *= 1.1  # Approximate EUR to USD conversion
                            
                        # Validate reasonable salary range
                        if val < 1000:  # Likely in thousands
                            val *= 1000
                            
                        if val > 1000000:  # Likely parsing error
                            return None
                            
                        # Use ±10% range for single values
                        return val * 0.9, val * 1.1
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing salary: {str(e)}")
            return None

    def _parse_job_details(self, text: str) -> Dict:
        """Parse job details from comment text."""
        # Clean up HTML entities and tags
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'&[^;]+;', ' ', text)
        
        lines = text.split('\n')
        details = {
            'title': '',
            'company': 'Unknown',
            'location': 'Remote',
            'remote': False,
            'salary_min': None,
            'salary_max': None,
            'requirements': []
        }
        
        # Extract title and company from first line
        if lines:
            first_line = lines[0].strip()
            
            # Try to extract company name
            company_patterns = [
                r'([^|]+)\s*\|',  # Company | Position
                r'([^-]+)\s*-',   # Company - Position
                r'([^:]+)\s*:',   # Company: Position
                r'at\s+([^|]+)',  # Position at Company
                r'@\s+([^|]+)'    # Position @ Company
            ]
            
            for pattern in company_patterns:
                match = re.search(pattern, first_line)
                if match and match.group(1):
                    details['company'] = match.group(1).strip()
                    break
            
            # Extract title
            title_patterns = [
                r'\|\s*([^|]+?)(?=\||$)',  # After |
                r'-\s*([^-]+?)(?=-|$)',    # After -
                r':\s*([^:]+?)(?=:|$)',    # After :
                r'^([^@|]+?)(?=\s+at\s+|@)',   # Before at/@
                r'.*'                 # Entire line as fallback
            ]
            
            for pattern in title_patterns:
                match = re.search(pattern, first_line)
                if match and match.group(1):  # Check if group exists
                    details['title'] = match.group(1).strip()
                    if details['title']:
                        break
        
        # Look for location and other details
        location_found = False
        in_requirements = False
        requirements_buffer = []
        
        for line in lines:
            line = line.strip().lower()
            
            # Skip empty lines
            if not line:
                continue
            
            # Location patterns
            if not location_found:
                location_patterns = [
                    r'location:?\s*([^\.|\n]+)',
                    r'(?:^|\s)in\s+([^\.|\n]+)',
                    r'(?:^|\s)at\s+([^\.|\n]+)',
                    r'(?:^|\s)(?:office|headquarters)\s+(?:in|at)\s+([^\.|\n]+)',
                    r'(?:^|\s)based\s+(?:in|at)\s+([^\.|\n]+)'
                ]
                
                for pattern in location_patterns:
                    match = re.search(pattern, line)
                    if match and match.group(1):  # Check if group exists
                        location = match.group(1).strip()
                        if len(location) > 5:  # Avoid very short matches
                            details['location'] = location
                            location_found = True
                            break
            
            # Remote work patterns
            if any(x in line for x in ['remote', 'wfh', 'work from home', 'distributed team']):
                details['remote'] = True
                if not location_found:
                    details['location'] = 'Remote'
            
            # Salary patterns
            salary_info = self._parse_salary(line)
            if salary_info:
                details['salary_min'], details['salary_max'] = salary_info
            
            # Check for requirement section markers
            req_section_patterns = [
                r'^requirements?:?\s*$',
                r'^qualifications?:?\s*$',
                r'^must have:?\s*$',
                r'^skills:?\s*$',
                r'^tech stack:?\s*$',
                r'^stack:?\s*$',
                r'^what we\'?re looking for:?\s*$',
                r'^you have:?\s*$',
                r'^you should have:?\s*$',
                r'^you will have:?\s*$'
            ]
            
            if any(re.search(pattern, line, re.IGNORECASE) for pattern in req_section_patterns):
                in_requirements = True
                continue
            
            # Extract requirements
            if in_requirements:
                # Check if we've reached the end of the requirements section
                if line.startswith(('apply', 'to apply', 'what we offer', 'benefits', 'compensation')):
                    in_requirements = False
                else:
                    # Clean up the line
                    line = line.strip('•-* ')
                    if line and len(line) > 3:
                        requirements_buffer.append(line)
            
            # Look for inline requirements
            req_patterns = [
                r'requirements?:?\s*([^\.|\n]+)',
                r'qualifications?:?\s*([^\.|\n]+)',
                r'must have:?\s*([^\.|\n]+)',
                r'skills:?\s*([^\.|\n]+)',
                r'looking for:?\s*([^\.|\n]+)',
                r'you have:?\s*([^\.|\n]+)',
                r'tech stack:?\s*([^\.|\n]+)',
                r'stack:?\s*([^\.|\n]+)',
                r'technologies:?\s*([^\.|\n]+)',
                r'using:?\s*([^\.|\n]+)'
            ]
            
            for pattern in req_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match and match.group(1):  # Check if group exists
                    reqs = match.group(1).strip()
                    # Split requirements by common delimiters
                    for req in re.split(r'[,;•\n]', reqs):
                        req = req.strip()
                        if req and len(req) > 3:  # Avoid very short requirements
                            requirements_buffer.append(req)
                            
            # Look for tech stack in bullet points or lists
            if line.startswith(('•', '-', '*', '→', '▸', '›', '»')):
                tech = line.lstrip('•-*→▸›» ')
                if tech and len(tech) > 3:
                    requirements_buffer.append(tech)
                    
            # Look for technology mentions
            tech_patterns = [
                r'using\s+([^\.]+)',
                r'with\s+([^\.]+)',
                r'in\s+([^\.]+)',
                r'experience\s+(?:with|in)\s+([^\.]+)',
                r'knowledge\s+of\s+([^\.]+)',
                r'proficiency\s+in\s+([^\.]+)',
                r'expertise\s+in\s+([^\.]+)',
                r'familiarity\s+with\s+([^\.]+)',
                r'working\s+with\s+([^\.]+)',
                r'built\s+(?:with|using|in)\s+([^\.]+)',
                r'developing\s+(?:with|using|in)\s+([^\.]+)',
                r'programming\s+(?:with|using|in)\s+([^\.]+)',
                r'coding\s+(?:with|using|in)\s+([^\.]+)',
                r'tech:?\s*([^\.]+)',
                r'tools:?\s*([^\.]+)',
                r'frameworks:?\s*([^\.]+)',
                r'languages:?\s*([^\.]+)',
                r'platforms:?\s*([^\.]+)',
                r'environment:?\s*([^\.]+)'
            ]
            
            for pattern in tech_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match and match.group(1):
                    tech = match.group(1).strip()
                    if tech and len(tech) > 3:
                        requirements_buffer.append(tech)
                        
            # Look for specific technology mentions
            tech_keywords = [
                'javascript', 'typescript', 'python', 'java', 'c++', 'c#',
                'react', 'vue', 'angular', 'node', 'express', 'django',
                'flask', 'spring', 'rails', 'php', 'laravel', 'symfony',
                'aws', 'azure', 'gcp', 'kubernetes', 'docker', 'terraform',
                'mongodb', 'postgresql', 'mysql', 'redis', 'elasticsearch',
                'kafka', 'rabbitmq', 'graphql', 'rest', 'api', 'microservices',
                'ci/cd', 'git', 'linux', 'agile', 'scrum', 'jira',
                'react native', 'flutter', 'kotlin', 'swift', 'objective-c',
                'rust', 'go', 'scala', 'ruby', 'perl', 'haskell', 'erlang',
                'clojure', 'elixir', 'phoenix', 'next.js', 'nuxt.js', 'gatsby',
                'webpack', 'babel', 'sass', 'less', 'tailwind', 'bootstrap',
                'material-ui', 'storybook', 'jest', 'cypress', 'selenium',
                'jenkins', 'gitlab', 'github actions', 'circleci', 'travis',
                'ansible', 'puppet', 'chef', 'nginx', 'apache', 'websocket',
                'webrtc', 'socket.io', 'redux', 'mobx', 'vuex', 'rxjs',
                'numpy', 'pandas', 'scikit-learn', 'tensorflow', 'pytorch',
                'keras', 'opencv', 'unity', 'unreal engine', 'godot',
                'webgl', 'three.js', 'canvas', 'svg', 'd3.js', 'chart.js',
                'tableau', 'power bi', 'looker', 'metabase', 'airflow',
                'spark', 'hadoop', 'hive', 'presto', 'snowflake', 'bigquery'
            ]
            
            # Add any mentioned technologies
            for tech in tech_keywords:
                if tech in line:
                    requirements_buffer.append(tech)
        
        # Clean up and deduplicate requirements
        seen_reqs = set()
        for req in requirements_buffer:
            # Normalize requirement
            req = req.strip().lower()
            req = re.sub(r'\s+', ' ', req)  # Replace multiple spaces with single space
            
            # Skip if too short or already seen
            if len(req) <= 3 or req in seen_reqs:
                continue
                
            # Skip common non-requirement phrases
            skip_phrases = [
                'we are', 'you will', 'please', 'apply', 'http', 'www', 'click',
                'email', 'follow', 'find', 'check', 'visit', 'see', 'learn',
                'about', 'contact', 'join', 'work', 'help', 'team', 'company',
                'position', 'role', 'job', 'career', 'opportunity', 'looking',
                'hiring', 'seeking', 'wanted', 'needed', 'required', 'must',
                'should', 'ideal', 'preferred', 'plus', 'bonus', 'nice', 'great'
            ]
            if any(phrase in req for phrase in skip_phrases):
                continue
            
            seen_reqs.add(req)
            details['requirements'].append(req)
        
        return details

    async def _process_comment(self, session: aiohttp.ClientSession, comment_id: int, keywords: List[str]) -> Optional[JobPosting]:
        """Process a single comment."""
        try:
            # Add retries for comment fetching
            for attempt in range(self.retry_count):
                try:
                    async with session.get(f"{self.api_url}/item/{comment_id}.json") as response:
                        if response.status == 200:
                            comment = await response.json()
                            
                            # Skip if comment is deleted or doesn't exist
                            if not comment or not comment.get('text'):
                                return None
                            
                            text = comment['text'].lower()
                            
                            # Check if comment matches keywords
                            if not any(kw.lower() in text for kw in keywords):
                                return None
                            
                            # Parse job details
                            details = self._parse_job_details(comment['text'])
                            
                            # Create job posting
                            return JobPosting(
                                title=details['title'] or 'No Title',
                                company=details['company'],
                                location=details.get('location', 'Remote'),
                                description=comment['text'],
                                url=f"{self.base_url}/item?id={comment_id}",
                                source='HackerNews',
                                remote=details['remote'],
                                salary_min=details.get('salary_min'),
                                salary_max=details.get('salary_max'),
                                requirements=details.get('requirements', [])
                            )
                        elif response.status == 404:
                            # Comment doesn't exist
                            return None
                        elif response.status == 429:  # Too Many Requests
                            if attempt < self.retry_count - 1:
                                await asyncio.sleep(self.retry_delay * (attempt + 1))
                                continue
                            return None
                        else:
                            if attempt < self.retry_count - 1:
                                await asyncio.sleep(self.retry_delay)
                                continue
                            return None
                            
                except aiohttp.ClientError as e:
                    if attempt < self.retry_count - 1:
                        await asyncio.sleep(self.retry_delay)
                        continue
                    logger.error(f"Error fetching comment {comment_id}: {str(e)}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error processing comment {comment_id}: {str(e)}")
            return None

    async def search(self, keywords: List[str], location: Optional[str] = None) -> List[JobPosting]:
        """
        Search for jobs on HackerNews.
        
        Args:
            keywords: List of keywords to search for
            location: Optional location to filter by
            
        Returns:
            List of JobPosting objects
        """
        jobs = []
        
        try:
            # Get the latest thread ID
            thread_id = await self.get_latest_who_is_hiring_thread()
            if not thread_id:
                return jobs
            
            # Get thread comments using HN API
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                # Add retries for thread fetching
                for attempt in range(self.retry_count):
                    try:
                        async with session.get(f"{self.api_url}/item/{thread_id}.json") as response:
                            if response.status == 200:
                                thread = await response.json()
                                if not thread or 'kids' not in thread:
                                    return jobs
                                
                                # Process comments in parallel with semaphore to limit concurrency
                                semaphore = asyncio.Semaphore(10)  # Process 10 comments at a time
                                
                                async def process_with_semaphore(comment_id: int) -> Optional[JobPosting]:
                                    async with semaphore:
                                        return await self._process_comment(session, comment_id, keywords)
                                
                                # Create tasks for all comments
                                tasks = [process_with_semaphore(comment_id) for comment_id in thread['kids']]
                                
                                # Wait for all tasks to complete with timeout
                                try:
                                    results = await asyncio.gather(*tasks, return_exceptions=True)
                                    # Filter out None results and exceptions
                                    jobs = [job for job in results 
                                          if isinstance(job, JobPosting)]
                                except asyncio.TimeoutError:
                                    logger.error("Timeout processing HackerNews comments")
                                break
                            elif response.status == 429:  # Too Many Requests
                                if attempt < self.retry_count - 1:
                                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                                    continue
                                break
                            else:
                                if attempt < self.retry_count - 1:
                                    await asyncio.sleep(self.retry_delay)
                                    continue
                                break
                                
                    except aiohttp.ClientError as e:
                        if attempt < self.retry_count - 1:
                            await asyncio.sleep(self.retry_delay)
                            continue
                        logger.error(f"Error fetching thread: {str(e)}")
                        break
                    
            logger.info(f"Found {len(jobs)} jobs on HackerNews")
            return jobs
            
        except Exception as e:
            logger.error(f"Error searching HackerNews jobs: {str(e)}")
            return jobs 