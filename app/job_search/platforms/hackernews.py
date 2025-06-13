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
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the HackerNews scraper.
        
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

    async def _process_comment(self, session: aiohttp.ClientSession, comment_id: int) -> Optional[JobPosting]:
        """Process a single comment into a job posting."""
        try:
            # Get comment data
            comment_url = f"{self.api_url}/item/{comment_id}.json"
            async with session.get(comment_url) as response:
                if response.status != 200:
                    return None
                    
                comment = await response.json()
                if not comment or not comment.get('text'):
                    return None
                    
                text = comment['text']
                text_lower = text.lower()
                
                # Extract job details
                title = self._extract_title(text)
                company = self._extract_company(text)
                location = self._extract_location(text)
                description = text
                requirements = self._extract_requirements(text_lower)
                url = f"https://news.ycombinator.com/item?id={comment_id}"
                remote = self._is_remote(text_lower)
                salary_range = self._extract_salary(text_lower)
                
                # Create job posting
                job = JobPosting(
                    title=title,
                    company=company,
                    location=location,
                    description=description,
                    requirements=requirements,
                    url=url,
                    platform="hackernews",
                    remote=remote,
                    salary_min=salary_range[0] if salary_range else None,
                    salary_max=salary_range[1] if salary_range else None
                )
                
                return job
                
        except Exception as e:
            logger.error(f"Error processing comment {comment_id}: {str(e)}")
            return None
        
    def _extract_requirements(self, text: str) -> List[str]:
        """Extract requirements from job text."""
        requirements = set()
        
        # Look for common requirement patterns
        patterns = [
            r'required skills?:?\s*(.*?)(?:\.|$)',
            r'requirements?:?\s*(.*?)(?:\.|$)',
            r'qualifications?:?\s*(.*?)(?:\.|$)',
            r'tech stack:?\s*(.*?)(?:\.|$)',
            r'stack:?\s*(.*?)(?:\.|$)',
            r'using\s+([\w\s,/+]+)(?:\.|$)',
            r'experience (?:with|in)\s+([\w\s,/+]+)(?:\.|$)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Split by common delimiters and clean up
                skills = re.split(r'[,/&]|\sand\s', match.group(1))
                for skill in skills:
                    # Clean and validate skill
                    skill = skill.strip().strip('.')
                    if (len(skill) > 2 and  # Avoid single letters
                        not any(char.isdigit() for char in skill) and  # Avoid version numbers
                        not any(word in skill.lower() for word in ['years', 'month', 'week', 'day'])):  # Avoid time periods
                        requirements.add(skill)
        
        # Look for specific technologies
        tech_keywords = [
            'python', 'javascript', 'typescript', 'java', 'c++', 'c#', 'ruby', 'php',
            'go', 'rust', 'scala', 'kotlin', 'swift', 'react', 'vue', 'angular',
            'node', 'django', 'flask', 'spring', 'rails', 'postgresql', 'mysql',
            'mongodb', 'redis', 'aws', 'gcp', 'azure', 'docker', 'kubernetes'
        ]
        
        for keyword in tech_keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', text, re.IGNORECASE):
                requirements.add(keyword)
        
        return list(requirements)
        
    def _extract_salary(self, text: str) -> Optional[Tuple[float, float]]:
        """Extract salary range from job text."""
        try:
            # Look for salary patterns
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

    def _extract_title(self, text: str) -> str:
        """Extract job title from text."""
        try:
            # Look for common title patterns
            patterns = [
                r'(?:hiring|looking for|seeking)\s+(?:a\s+)?([^|.]+?)(?:\||$|\.|at\s)',
                r'(?:^|\n)([^|.]+?)\s+(?:position|role|opportunity)',
                r'(?:^|\n)([^|.]+?)\s+(?:\$|\d|remote|hybrid|onsite)',
                r'(?:^|\n)([^|.]+?)\s+(?:at|in|with)\s+',
                r'(?:^|\n)([^|.]+?)(?:\||$|\.|,)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    title = match.group(1).strip()
                    if len(title) > 3 and len(title) < 100:  # Reasonable title length
                        return title
            
            # Fallback: use first line
            first_line = text.split('\n')[0].strip()
            if '|' in first_line:
                title = first_line.split('|')[0].strip()
            else:
                title = first_line
                
            return title[:100]  # Limit length
            
        except Exception as e:
            logger.error(f"Error extracting title: {str(e)}")
            return "Software Engineer"  # Default title
            
    def _extract_company(self, text: str) -> str:
        """Extract company name from text."""
        try:
            # Look for common company patterns
            patterns = [
                r'(?:at|@)\s+([^|.]+?)(?:\||$|\.|,)',
                r'\|\s*([^|.]+?)\s*(?:\||$|\.|,)',
                r'(?:^|\n)([^|.]+?)\s+(?:is hiring|is looking)',
                r'(?:^|\n)([^|.]+?)\s+(?:\(|http)',
                r'(?:^|\n)([^|.]+?)(?:\||$|\.|,)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    company = match.group(1).strip()
                    if len(company) > 1 and len(company) < 50:  # Reasonable company name length
                        return company
            
            # Fallback: use first line
            first_line = text.split('\n')[0].strip()
            if '|' in first_line:
                company = first_line.split('|')[1].strip()
            else:
                company = first_line
                
            return company[:50]  # Limit length
            
        except Exception as e:
            logger.error(f"Error extracting company: {str(e)}")
            return "Unknown Company"  # Default company name
            
    def _extract_location(self, text: str) -> str:
        """Extract location from text."""
        try:
            # Look for common location patterns
            patterns = [
                r'(?:location|located in|based in|office in):\s*([^|.]+?)(?:\||$|\.|,)',
                r'(?:^|\n)(?:location|located|based):\s*([^|.]+?)(?:\||$|\.|,)',
                r'(?:^|\n)([^|.]+?)(?:\s+office|\s+area|\s+region)(?:\||$|\.|,)',
                r'(?:in|at)\s+([^|.]+?)(?:\s+(?:office|area|region))(?:\||$|\.|,)',
                r'\(([^|.]+?)\)(?:\||$|\.|,)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    location = match.group(1).strip()
                    if len(location) > 2 and len(location) < 100:  # Reasonable location length
                        return location
            
            # Check for remote indicators
            if any(kw in text.lower() for kw in ['remote', 'work from home', 'wfh', 'distributed team']):
                return 'Remote'
                
            return 'Remote'  # Default to remote
            
        except Exception as e:
            logger.error(f"Error extracting location: {str(e)}")
            return "Remote"  # Default location

    def _is_remote(self, text: str) -> bool:
        """Check if job is remote."""
        try:
            # Look for remote indicators
            remote_keywords = [
                'remote',
                'work from home',
                'wfh',
                'distributed team',
                'work from anywhere',
                'fully remote',
                'remote-first',
                'remote first',
                'remote-friendly',
                'remote friendly',
                'remote ok',
                'remote-ok',
                'remote possible',
                'remote position',
                'remote work',
                'remote role',
                'remote job',
                'remote opportunity',
                'remote based',
                'remote only'
            ]
            
            text = text.lower()
            
            # Check for explicit remote mentions
            for keyword in remote_keywords:
                if keyword in text:
                    return True
                    
            # Check for location patterns that indicate remote
            location_patterns = [
                r'location:\s*remote',
                r'location:\s*anywhere',
                r'location:\s*worldwide',
                r'location:\s*global',
                r'(?:^|\n)remote\s+(?:only|position|role|job)',
                r'(?:^|\n)(?:fully|100%)\s+remote',
                r'work\s+(?:from|remotely)\s+(?:home|anywhere)',
                r'distributed\s+team',
                r'remote\s+(?:ok|possible|friendly)',
                r'remote[- ]first'
            ]
            
            for pattern in location_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return True
                    
            # Check for negations
            negation_patterns = [
                r'not\s+remote',
                r'no\s+remote',
                r'remote\s+not\s+possible',
                r'remote\s+not\s+available',
                r'remote\s+not\s+an\s+option',
                r'(?:must|need\s+to)\s+(?:be|work)\s+(?:in|from)\s+office',
                r'in[- ]office\s+(?:only|required|mandatory)',
                r'on[- ]site\s+(?:only|required|mandatory)',
                r'local\s+(?:only|candidates)',
                r'no\s+remote\s+work'
            ]
            
            for pattern in negation_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return False
                    
            # Default to remote for HN jobs
            return True
            
        except Exception as e:
            logger.error(f"Error checking remote status: {str(e)}")
            return True  # Default to remote

    async def search(self) -> List[JobPosting]:
        """
        Search for jobs on HackerNews.
        
        Returns:
            List of JobPosting objects
        """
        try:
            # Get latest "Who is hiring?" thread
            logger.info("Getting latest Who is Hiring thread...")
            thread_id = await self.get_latest_who_is_hiring_thread()
            if not thread_id:
                logger.error("Could not find latest hiring thread")
                return []
                
            logger.info(f"Found thread ID: {thread_id}")
                
            # Get comments from thread
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                # Get thread details
                thread_url = f"{self.api_url}/item/{thread_id}.json"
                logger.info(f"Getting thread details from {thread_url}")
                
                async with session.get(thread_url) as response:
                    if response.status != 200:
                        logger.error("Could not get thread details")
                        return []
                        
                    thread_data = await response.json()
                    if not thread_data or 'kids' not in thread_data:
                        logger.error("Invalid thread data")
                        return []
                        
                    # Process each comment
                    jobs = []
                    comment_ids = thread_data['kids'][:20]  # Process only first 20 comments
                    logger.info(f"Found {len(comment_ids)} comments to process")
                    
                    # Create tasks for processing comments
                    tasks = []
                    for i, comment_id in enumerate(comment_ids):
                        task = asyncio.create_task(
                            self._process_comment(
                                session, 
                                comment_id
                            )
                        )
                        tasks.append(task)
                        logger.info(f"Processing comment {i+1}/{len(comment_ids)}")
                        
                        # Add delay between requests
                        await asyncio.sleep(self.config['search']['delay_between_requests'])
                        
                        # Break if we've reached max jobs
                        if len(tasks) >= self.config['search']['max_jobs']:
                            break
                    
                    logger.info(f"Processing {len(tasks)} comments...")
                    
                    # Wait for all tasks to complete
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Process results
                    for result in results:
                        if isinstance(result, Exception):
                            logger.error(f"Error processing comment: {str(result)}")
                            continue
                            
                        if result:  # Skip None results
                            jobs.append(result)
                    
                    logger.info(f"Found {len(jobs)} jobs on HackerNews")
                    return jobs
            
        except Exception as e:
            logger.error(f"Error searching HackerNews: {str(e)}")
            return [] 