"""Post analyzer module for extracting job information from social media posts."""
import re
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from datetime import datetime

from loguru import logger

@dataclass
class JobPostInfo:
    """Structured information extracted from a job post."""
    title: str
    company: str
    location: str
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: str = "USD"
    salary_period: str = "year"
    skills_required: Set[str] = None
    skills_preferred: Set[str] = None
    experience_years: Optional[int] = None
    seniority_level: str = "not_specified"
    employment_type: str = "full_time"
    remote_type: str = "not_specified"
    contact_email: Optional[str] = None
    contact_linkedin: Optional[str] = None
    application_url: Optional[str] = None
    hashtags: Set[str] = None
    
    def __post_init__(self):
        """Initialize default sets."""
        if self.skills_required is None:
            self.skills_required = set()
        if self.skills_preferred is None:
            self.skills_preferred = set()
        if self.hashtags is None:
            self.hashtags = set()

class PostAnalyzer:
    """Analyzes social media posts to extract job information."""
    
    def __init__(self):
        """Initialize the analyzer with common patterns."""
        # Location patterns
        self.location_patterns = [
            # City, State/Country format
            r'(?:in|at|location|based in|position in|remote in)\s+([A-Z][a-z]+(?:\s*,\s*[A-Z]{2,3})?)',
            # Remote patterns
            r'((?:100%\s+)?remote|fully remote|remote(?:\s+(?:friendly|ok|possible|only))?)',
            # Hybrid patterns
            r'(hybrid(?:\s+in\s+[A-Z][a-z]+(?:\s*,\s*[A-Z]{2,3})?)?)',
            # Multiple locations
            r'(?:locations?|offices?)\s+in\s+([A-Z][a-z]+(?:\s*[,&]\s*[A-Z][a-z]+)*)',
        ]
        
        # Salary patterns
        self.salary_patterns = [
            # Ranges with K suffix
            r'\$(\d+)k\s*[-–]\s*\$?(\d+)k',
            r'(\d+)k\s*[-–]\s*(\d+)k\s*(?:usd|eur|gbp)',
            # Ranges with full numbers
            r'\$(\d{2,3}(?:,\d{3})*)\s*[-–]\s*\$?(\d{2,3}(?:,\d{3})*)',
            # Single values
            r'\$(\d+)k\+?',
            r'(\d+)k\+?\s*(?:usd|eur|gbp)',
            # Annual/monthly indicators
            r'(?:annual|yearly|per year)',
            r'(?:monthly|per month)',
        ]
        
        # Experience patterns
        self.experience_patterns = [
            r'(\d+)\+?\s*(?:years?|yrs?)(?:\s+of)?\s+(?:experience|exp)',
            r'(?:minimum|min|at least)\s+(\d+)\s*(?:years?|yrs?)',
            r'(\d+)[-–](\d+)\s*(?:years?|yrs?)',
        ]
        
        # Seniority patterns
        self.seniority_levels = {
            'junior': ['junior', 'entry level', 'entry-level', 'jr'],
            'mid': ['mid level', 'mid-level', 'intermediate'],
            'senior': ['senior', 'sr', 'lead'],
            'staff': ['staff', 'principal'],
            'manager': ['manager', 'head of', 'director'],
        }
        
        # Employment type patterns
        self.employment_types = {
            'full_time': ['full time', 'full-time', 'permanent'],
            'part_time': ['part time', 'part-time'],
            'contract': ['contract', 'contractor', 'freelance'],
            'internship': ['intern', 'internship', 'trainee'],
        }
        
        # Common tech skills
        self.tech_skills = {
            'languages': {'python', 'javascript', 'typescript', 'java', 'c++', 'ruby', 'go', 'rust'},
            'frontend': {'react', 'vue', 'angular', 'svelte', 'next.js', 'gatsby'},
            'backend': {'node.js', 'django', 'flask', 'fastapi', 'spring', 'rails'},
            'database': {'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch'},
            'cloud': {'aws', 'gcp', 'azure', 'kubernetes', 'docker'},
            'tools': {'git', 'jenkins', 'terraform', 'ansible', 'prometheus'},
        }
        
    def analyze_post(self, post: Dict) -> JobPostInfo:
        """Analyze a post and extract job information."""
        text = post['text'].lower()
        
        # Extract basic info
        title = self._extract_title(post)
        company = post['author']
        location = self._extract_location(text)
        
        # Extract salary info
        salary_min, salary_max, salary_currency, salary_period = self._extract_salary(text)
        
        # Extract skills
        skills_required, skills_preferred = self._extract_skills(text)
        
        # Extract experience and seniority
        experience_years = self._extract_experience(text)
        seniority_level = self._extract_seniority(text)
        
        # Extract employment type
        employment_type = self._extract_employment_type(text)
        
        # Extract remote type
        remote_type = self._extract_remote_type(text)
        
        # Extract contact info
        contact_email = self._extract_email(text)
        contact_linkedin = post.get('author_profile')
        
        # Extract hashtags
        hashtags = self._extract_hashtags(text)
        
        return JobPostInfo(
            title=title,
            company=company,
            location=location,
            salary_min=salary_min,
            salary_max=salary_max,
            salary_currency=salary_currency,
            salary_period=salary_period,
            skills_required=skills_required,
            skills_preferred=skills_preferred,
            experience_years=experience_years,
            seniority_level=seniority_level,
            employment_type=employment_type,
            remote_type=remote_type,
            contact_email=contact_email,
            contact_linkedin=contact_linkedin,
            application_url=post.get('url'),
            hashtags=hashtags
        )
        
    def _extract_title(self, post: Dict) -> str:
        """Extract job title from post."""
        text = post['text'].lower()
        
        # Common title patterns
        patterns = [
            r'hiring (?:a\s+)?([^.!?\n]+(?:engineer|developer|architect|designer)[^.!?\n]+)',
            r'looking for (?:a\s+)?([^.!?\n]+(?:engineer|developer|architect|designer)[^.!?\n]+)',
            r'open position:?\s*([^.!?\n]+)',
            r'job opening:?\s*([^.!?\n]+)',
            r'role:?\s*([^.!?\n]+)',
            r'position:?\s*([^.!?\n]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                title = match.group(1).strip()
                return title.capitalize()
                
        # Fallback to post title if available
        return post.get('title', 'Unknown Position')
        
    def _extract_location(self, text: str) -> str:
        """Extract location from text."""
        for pattern in self.location_patterns:
            match = re.search(pattern, text)
            if match:
                location = match.group(1).strip()
                if any(remote in location.lower() for remote in ['remote', 'anywhere', 'worldwide']):
                    return 'Remote'
                return location.capitalize()
        return 'Not specified'
        
    def _extract_salary(self, text: str) -> tuple:
        """Extract salary information from text."""
        for pattern in self.salary_patterns:
            match = re.search(pattern, text)
            if match:
                if len(match.groups()) == 2:  # Range
                    min_val = float(match.group(1).replace(',', ''))
                    max_val = float(match.group(2).replace(',', ''))
                    if 'k' in pattern.lower():
                        min_val *= 1000
                        max_val *= 1000
                else:  # Single value
                    val = float(match.group(1).replace(',', ''))
                    if 'k' in pattern.lower():
                        val *= 1000
                    min_val = max_val = val
                    
                # Determine currency
                currency = 'USD'
                if 'eur' in text:
                    currency = 'EUR'
                elif 'gbp' in text:
                    currency = 'GBP'
                    
                # Determine period
                period = 'year'
                if 'month' in text:
                    period = 'month'
                    
                return min_val, max_val, currency, period
                
        return None, None, 'USD', 'year'
        
    def _extract_skills(self, text: str) -> tuple:
        """Extract required and preferred skills from text."""
        required = set()
        preferred = set()
        
        # Check each skill category
        for category, skills in self.tech_skills.items():
            for skill in skills:
                if skill.lower() in text:
                    # Check if skill is required or preferred
                    skill_context = re.findall(f'.{{50}}{skill}.{{50}}', text)
                    for context in skill_context:
                        if any(word in context for word in ['required', 'must', 'need', 'essential']):
                            required.add(skill)
                        elif any(word in context for word in ['preferred', 'nice to have', 'plus']):
                            preferred.add(skill)
                        else:
                            required.add(skill)  # Default to required if not specified
                            
        return required, preferred
        
    def _extract_experience(self, text: str) -> Optional[int]:
        """Extract years of experience requirement."""
        for pattern in self.experience_patterns:
            match = re.search(pattern, text)
            if match:
                if len(match.groups()) == 2:  # Range
                    return (int(match.group(1)) + int(match.group(2))) // 2  # Average
                return int(match.group(1))
        return None
        
    def _extract_seniority(self, text: str) -> str:
        """Extract seniority level from text."""
        for level, keywords in self.seniority_levels.items():
            if any(keyword in text for keyword in keywords):
                return level
        return 'not_specified'
        
    def _extract_employment_type(self, text: str) -> str:
        """Extract employment type from text."""
        for type_, keywords in self.employment_types.items():
            if any(keyword in text for keyword in keywords):
                return type_
        return 'full_time'  # Default to full-time
        
    def _extract_remote_type(self, text: str) -> str:
        """Extract remote work type from text."""
        if 'hybrid' in text:
            return 'hybrid'
        elif any(pattern in text for pattern in ['100% remote', 'fully remote', 'remote only']):
            return 'remote'
        elif 'remote' in text:
            return 'remote_flexible'
        elif 'office' in text or 'onsite' in text:
            return 'office'
        return 'not_specified'
        
    def _extract_email(self, text: str) -> Optional[str]:
        """Extract email address from text.
        
        Args:
            text: Text to extract email from
            
        Returns:
            str: Email address if found, None otherwise
        """
        # Common email patterns
        patterns = [
            # Basic email pattern
            r'[\w\.-]+@[\w\.-]+\.\w+',
            # Email with "mailto:" prefix
            r'mailto:[\w\.-]+@[\w\.-]+\.\w+',
            # Email with surrounding text
            r'(?:email|contact|apply|send|at).{0,30}?([\w\.-]+@[\w\.-]+\.\w+)',
            # Email with HTML entities
            r'[\w\.-]+(?:\s*(?:at|@|\[at\]|\(at\))\s*)[\w\.-]+(?:\s*(?:dot|\.|,|\[dot\]|\(dot\))\s*)\w+',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Get the email from the match
                email = match.group(1) if len(match.groups()) > 0 else match.group(0)
                
                # Clean up email
                email = email.lower()
                email = re.sub(r'mailto:', '', email)
                email = re.sub(r'(?:^.*?:|>|<)', '', email)
                email = re.sub(r'\s+(?:at|\[at\]|\(at\))\s+', '@', email)
                email = re.sub(r'\s+(?:dot|\[dot\]|\(dot\))\s+', '.', email)
                email = email.strip()
                
                # Validate email format
                if re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
                    return email
                    
        return None
        
    def _extract_hashtags(self, text: str) -> Set[str]:
        """Extract hashtags from text."""
        return set(re.findall(r'#(\w+)', text))

    def analyze(self, post: Dict) -> Dict:
        """Analyze a job post and extract relevant information.
        
        Args:
            post: Dictionary containing job post information
            
        Returns:
            Dict: Extracted information
        """
        # Extract application method and contact info
        application_info = self._extract_application_info(post)
        
        # Extract salary range
        salary_range = self._extract_salary_range(post.get('description', ''))
        
        # Extract location and remote info
        location, is_remote = self._extract_location_info(post)
        
        # Return combined info
        return {
            **post,
            **application_info,
            'salary_min': salary_range[0] if salary_range else None,
            'salary_max': salary_range[1] if salary_range else None,
            'location': location,
            'remote': is_remote
        }
        
    def _extract_application_info(self, post: Dict) -> Dict:
        """Extract application method and contact information.
        
        Args:
            post: Dictionary containing job post information
            
        Returns:
            Dict: Application method and contact info
        """
        info = {
            'application_method': 'unknown',
            'apply_url': None,
            'contact_email': None
        }
        
        # Check for direct application URL
        apply_url = post.get('apply_url') or post.get('url')
        if apply_url:
            if any(domain in apply_url.lower() for domain in [
                'linkedin.com/jobs',
                'greenhouse.io',
                'lever.co',
                'workday.com',
                'recruitee.com',
                'jobs.ashbyhq.com'
            ]):
                info['application_method'] = 'direct'
                info['apply_url'] = apply_url
                return info
        
        # Check for email application
        description = post.get('description', '')
        email = self._extract_email(description)
        if email:
            info['application_method'] = 'email'
            info['contact_email'] = email
            return info
            
        return info
        
    def _extract_salary_range(self, text: str) -> Optional[Tuple[float, float]]:
        """Extract salary range from text.
        
        Args:
            text: Text to extract salary from
            
        Returns:
            Tuple[float, float]: Minimum and maximum salary if found, None otherwise
        """
        # Common salary patterns
        patterns = [
            # $X0-90k, $X0k-90k
            r'\$(\d+)(?:k)?(?:\s*-\s*|\s+to\s+)\$?(\d+)k',
            # $X0,000-90,000
            r'\$(\d+,\d+)(?:\s*-\s*|\s+to\s+)\$?(\d+,\d+)',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                min_salary = float(match.group(1).replace(',', ''))
                max_salary = float(match.group(2).replace(',', ''))
                
                # Convert to annual if needed
                if min_salary < 1000:  # Assuming k format
                    min_salary *= 1000
                if max_salary < 1000:  # Assuming k format
                    max_salary *= 1000
                    
                return (min_salary, max_salary)
                
        return None
        
    def _extract_location_info(self, post: Dict) -> Tuple[Optional[str], bool]:
        """Extract location and remote work information.
        
        Args:
            post: Dictionary containing job post information
            
        Returns:
            Tuple[str, bool]: Location and whether job is remote
        """
        location = post.get('location', '')
        description = post.get('description', '')
        title = post.get('title', '')
        
        # Check for remote indicators
        remote_patterns = [
            r'\bremote\b',
            r'\bwork from home\b',
            r'\bwfh\b',
            r'\bvirtual\b',
            r'\btelework\b',
        ]
        
        is_remote = any(
            re.search(pattern, text, re.IGNORECASE)
            for pattern in remote_patterns
            for text in [location, description, title]
        )
        
        return location, is_remote 