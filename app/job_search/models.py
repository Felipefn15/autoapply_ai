"""
Job Search Models
"""
from dataclasses import dataclass, asdict
from typing import List, Optional, Set, Dict, Any
from datetime import datetime
import re

from app.utils.text_extractor import extract_emails_from_text

def normalize_location(location: str) -> str:
    """Normalize location string."""
    # Common location prefixes to remove
    prefixes = [
        'location:', 'location', 'based in:', 'based in', 
        'position location:', 'position location'
    ]
    
    # Common location suffixes to remove
    suffixes = [
        'area', 'region', 'timezone', 'time zone', 'based',
        'preferred', 'required', 'only'
    ]
    
    # Clean the location string
    location = location.lower().strip()
    
    # Remove prefixes
    for prefix in prefixes:
        if location.startswith(prefix.lower()):
            location = location[len(prefix):].strip()
            
    # Remove suffixes
    for suffix in suffixes:
        if location.endswith(suffix.lower()):
            location = location[:-len(suffix)].strip()
    
    # Handle special cases
    if any(keyword in location.lower() for keyword in ['remote', 'anywhere', 'worldwide']):
        return 'Remote'
        
    # Remove parenthetical clarifications
    location = re.sub(r'\([^)]*\)', '', location)
    
    # Clean up remaining text
    location = location.strip(' ,:;.-')
    
    # Capitalize properly
    location = ' '.join(word.capitalize() for word in location.split())
    
    return location

@dataclass
class Job:
    """Job posting model."""
    title: str
    company: str
    location: str
    description: str
    url: str
    platform: str
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: str = "USD"
    application_method: str = "unknown"
    remote: bool = False
    skills: Set[str] = None
    
    def __post_init__(self):
        """Post initialization processing."""
        # Decode HTML entities
        self.title = html.unescape(self.title)
        self.company = html.unescape(self.company)
        self.description = html.unescape(self.description)
        
        # Normalize location
        self.location = normalize_location(self.location)
        
        # Initialize skills set
        if self.skills is None:
            self.skills = set()
            
        # Extract salary information
        self._extract_salary_info()
            
    def _extract_salary_info(self):
        """Extract salary information from description."""
        # Common salary patterns
        patterns = [
            # Range with K suffix: $100K-150K
            r'\$(\d+)K\s*[-–]\s*\$?(\d+)K',
            # Range with thousand: $100,000-150,000
            r'\$(\d{1,3}(?:,\d{3})*)\s*[-–]\s*\$?(\d{1,3}(?:,\d{3})*)',
            # Single value with K suffix: $100K
            r'\$(\d+)K',
            # Single value with thousand: $100,000
            r'\$(\d{1,3}(?:,\d{3})*)',
        ]
        
        desc_lower = self.description.lower()
        
        for pattern in patterns:
            matches = re.finditer(pattern, self.description)
            for match in matches:
                if len(match.groups()) == 2:  # Range
                    min_val = float(match.group(1).replace(',', ''))
                    max_val = float(match.group(2).replace(',', ''))
                    if 'k' in pattern.lower():
                        min_val *= 1000
                        max_val *= 1000
                    self.salary_min = min_val
                    self.salary_max = max_val
                    break
                else:  # Single value
                    val = float(match.group(1).replace(',', ''))
                    if 'k' in pattern.lower():
                        val *= 1000
                    self.salary_min = val
                    self.salary_max = val
                    break
                    
        # Try to determine currency
        currency_patterns = {
            'USD': [r'\$', r'USD', r'US\s*dollars?'],
            'EUR': [r'€', r'EUR', r'euros?'],
            'GBP': [r'£', r'GBP', r'pounds?'],
        }
        
        for currency, patterns in currency_patterns.items():
            if any(re.search(pattern, desc_lower) for pattern in patterns):
                self.salary_currency = currency
                break
        
    def calculate_match_score(self, required_skills: Set[str], 
                            preferred_skills: Set[str],
                            min_salary: Optional[float] = None,
                            max_salary: Optional[float] = None) -> float:
        """Calculate how well this job matches the requirements."""
        score = 0.0
        total_weight = 0.0
        
        # Skills match (50% weight)
        if required_skills:
            required_match = len(self.skills.intersection(required_skills)) / len(required_skills)
            score += required_match * 50
            total_weight += 50
            
        if preferred_skills:
            preferred_match = len(self.skills.intersection(preferred_skills)) / len(preferred_skills)
            score += preferred_match * 25
            total_weight += 25
            
        # Salary match (25% weight)
        if min_salary and self.salary_min:
            if self.salary_min >= min_salary:
                score += 25
            total_weight += 25
            
        # Remote match (25% weight if remote is required)
        if self.remote:
            score += 25
            total_weight += 25
            
        # Normalize score
        return (score / total_weight * 100) if total_weight > 0 else 0.0
        
    def extract_application_method(self) -> str:
        """Extract the application method from the job description."""
        desc_lower = self.description.lower()
        
        # Check for email application
        if any(phrase in desc_lower for phrase in [
            "apply via email",
            "send your resume to",
            "email us at",
            "apply by email",
            "@",
            "[at]",
            "(at)"
        ]):
            return "email"
            
        # Check for LinkedIn
        if any(phrase in desc_lower for phrase in [
            "apply on linkedin",
            "linkedin.com/jobs",
            "linkedin profile"
        ]):
            return "linkedin"
            
        # Check for company website
        if any(phrase in desc_lower for phrase in [
            "apply on our website",
            "apply through our website",
            "apply at our website",
            "apply here:",
            "apply at:"
        ]):
            return "website"
            
        return "unknown"

@dataclass
class JobPosting:
    """Job posting model."""
    
    title: str
    description: str
    email: Optional[str] = None
    url: Optional[str] = None  # mantido para referência
    extracted_emails: List[str] = None

    def __post_init__(self):
        """Post initialization processing."""
        # Normalize fields
        self.title = self.title.strip()
        self.description = self.description.strip()
        if self.email:
            self.email = self.email.strip()
            
        # Extract emails from title and description
        self.extracted_emails = []
        if self.title:
            self.extracted_emails.extend(extract_emails_from_text(self.title))
        if self.description:
            self.extracted_emails.extend(extract_emails_from_text(self.description))
        self.extracted_emails = list(set(self.extracted_emails))  # Remove duplicates
        
        # If no email was provided but we found one, use it
        if not self.email and self.extracted_emails:
            self.email = self.extracted_emails[0]

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'JobPosting':
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in ['title', 'description', 'email', 'url', 'extracted_emails']}) 