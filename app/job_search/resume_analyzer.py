"""Resume analyzer module for extracting information from resumes."""
import re
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime

from loguru import logger

@dataclass
class ResumeInfo:
    """Structured information extracted from a resume."""
    name: str
    email: str
    phone: Optional[str] = None
    location: str = "Not specified"
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    skills: Set[str] = None
    languages: Set[str] = None
    education: List[Dict] = None
    experience: List[Dict] = None
    projects: List[Dict] = None
    certifications: List[Dict] = None
    summary: Optional[str] = None
    
    def __post_init__(self):
        """Initialize default collections."""
        if self.skills is None:
            self.skills = set()
        if self.languages is None:
            self.languages = set()
        if self.education is None:
            self.education = []
        if self.experience is None:
            self.experience = []
        if self.projects is None:
            self.projects = []
        if self.certifications is None:
            self.certifications = []

class ResumeAnalyzer:
    """Analyzes resumes to extract structured information."""
    
    def __init__(self):
        """Initialize the analyzer with common patterns."""
        # Contact patterns
        self.email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
        self.phone_pattern = r'(?:\+\d{1,3}[-\.\s]?)?\(?\d{3}\)?[-\.\s]?\d{3}[-\.\s]?\d{4}'
        self.url_pattern = r'https?://(?:www\.)?([^\s<>"]+|(?:[^\s<>"]*?))'
        
        # Common tech skills
        self.tech_skills = {
            'languages': {'python', 'javascript', 'typescript', 'java', 'c++', 'ruby', 'go', 'rust'},
            'frontend': {'react', 'vue', 'angular', 'svelte', 'next.js', 'gatsby'},
            'backend': {'node.js', 'django', 'flask', 'fastapi', 'spring', 'rails'},
            'database': {'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch'},
            'cloud': {'aws', 'gcp', 'azure', 'kubernetes', 'docker'},
            'tools': {'git', 'jenkins', 'terraform', 'ansible', 'prometheus'},
        }
        
        # Common human languages
        self.human_languages = {
            'english', 'spanish', 'portuguese', 'french', 'german', 'italian', 'chinese', 'japanese',
            'korean', 'russian', 'arabic', 'hindi'
        }
        
        # Education keywords
        self.education_keywords = {
            'degree': {'phd', 'master', 'bachelor', 'bs', 'ba', 'msc', 'bsc'},
            'major': {'computer science', 'software engineering', 'information technology', 'data science'},
            'institution': {'university', 'college', 'institute', 'school'}
        }
        
    def analyze_resume(self, text: str) -> ResumeInfo:
        """Analyze resume text and extract structured information."""
        # Extract basic info
        name = self._extract_name(text)
        email = self._extract_email(text)
        phone = self._extract_phone(text)
        location = self._extract_location(text)
        
        # Extract URLs
        linkedin_url = self._extract_linkedin_url(text)
        github_url = self._extract_github_url(text)
        portfolio_url = self._extract_portfolio_url(text)
        
        # Extract skills and languages
        skills = self._extract_skills(text)
        languages = self._extract_languages(text)
        
        # Extract sections
        education = self._extract_education(text)
        experience = self._extract_experience(text)
        projects = self._extract_projects(text)
        certifications = self._extract_certifications(text)
        summary = self._extract_summary(text)
        
        return ResumeInfo(
            name=name,
            email=email,
            phone=phone,
            location=location,
            linkedin_url=linkedin_url,
            github_url=github_url,
            portfolio_url=portfolio_url,
            skills=skills,
            languages=languages,
            education=education,
            experience=experience,
            projects=projects,
            certifications=certifications,
            summary=summary
        )
    
    def _extract_name(self, text: str) -> str:
        """Extract name from resume text."""
        # Look for name at the beginning of the resume
        lines = text.split('\n')
        for line in lines[:5]:  # Check first 5 lines
            # Remove common resume headers
            line = re.sub(r'(resume|cv|curriculum vitae)', '', line, flags=re.IGNORECASE).strip()
            if line and not re.search(self.email_pattern, line) and not re.search(self.phone_pattern, line):
                return line
        return "Unknown"
    
    def _extract_email(self, text: str) -> str:
        """Extract email from resume text."""
        match = re.search(self.email_pattern, text)
        return match.group(0) if match else ""
    
    def _extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number from resume text."""
        match = re.search(self.phone_pattern, text)
        return match.group(0) if match else None
    
    def _extract_location(self, text: str) -> str:
        """Extract location from resume text."""
        # Common location patterns
        patterns = [
            r'(?:location|address|based in):\s*([^\n]+)',
            r'([A-Z][a-z]+(?:\s*,\s*[A-Z]{2})?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        return "Not specified"
    
    def _extract_linkedin_url(self, text: str) -> Optional[str]:
        """Extract LinkedIn URL from resume text."""
        pattern = r'(?:linkedin\.com/in/|linkedin:)\s*([\w-]+)'
        match = re.search(pattern, text.lower())
        if match:
            username = match.group(1)
            return f"https://linkedin.com/in/{username}"
        return None
    
    def _extract_github_url(self, text: str) -> Optional[str]:
        """Extract GitHub URL from resume text."""
        pattern = r'(?:github\.com/|github:)\s*([\w-]+)'
        match = re.search(pattern, text.lower())
        if match:
            username = match.group(1)
            return f"https://github.com/{username}"
        return None
    
    def _extract_portfolio_url(self, text: str) -> Optional[str]:
        """Extract portfolio URL from resume text."""
        pattern = r'(?:portfolio|website|blog):\s*(https?://[^\s<>"]+)'
        match = re.search(pattern, text.lower())
        return match.group(1) if match else None
    
    def _extract_skills(self, text: str) -> Set[str]:
        """Extract technical skills from resume text."""
        skills = set()
        
        # Look for skills section
        skills_text = self._extract_section(text, ['skills', 'technical skills', 'technologies'])
        
        # Extract skills from all categories
        for category, category_skills in self.tech_skills.items():
            for skill in category_skills:
                if skill.lower() in text.lower():
                    skills.add(skill)
                    
        return skills
    
    def _extract_languages(self, text: str) -> Set[str]:
        """Extract human languages from resume text."""
        languages = set()
        
        # Look for languages section
        languages_text = self._extract_section(text, ['languages', 'spoken languages'])
        
        # Extract known languages
        for language in self.human_languages:
            if language.lower() in text.lower():
                languages.add(language.capitalize())
                
        return languages
    
    def _extract_education(self, text: str) -> List[Dict]:
        """Extract education information from resume text."""
        education = []
        
        # Look for education section
        education_text = self._extract_section(text, ['education', 'academic background'])
        if not education_text:
            return education
            
        # Split into entries
        entries = re.split(r'\n\s*\n', education_text)
        
        for entry in entries:
            if not entry.strip():
                continue
                
            edu_entry = {
                'degree': None,
                'major': None,
                'institution': None,
                'graduation_date': None,
                'gpa': None
            }
            
            # Extract degree and major
            for degree in self.education_keywords['degree']:
                if degree in entry.lower():
                    edu_entry['degree'] = degree.upper()
                    break
                    
            for major in self.education_keywords['major']:
                if major in entry.lower():
                    edu_entry['major'] = major.title()
                    break
                    
            # Extract institution
            for keyword in self.education_keywords['institution']:
                pattern = fr'{keyword}\s+of\s+([^,\n]+)'
                match = re.search(pattern, entry, re.IGNORECASE)
                if match:
                    edu_entry['institution'] = match.group(1).strip()
                    break
                    
            # Extract graduation date
            date_pattern = r'(?:graduated|completion|expected):\s*([A-Za-z]+\s+\d{4})'
            match = re.search(date_pattern, entry, re.IGNORECASE)
            if match:
                edu_entry['graduation_date'] = match.group(1)
                
            # Extract GPA if present
            gpa_pattern = r'gpa:\s*(\d+\.\d+)'
            match = re.search(gpa_pattern, entry, re.IGNORECASE)
            if match:
                edu_entry['gpa'] = float(match.group(1))
                
            if any(edu_entry.values()):  # Add entry if any field was populated
                education.append(edu_entry)
                
        return education
    
    def _extract_experience(self, text: str) -> List[Dict]:
        """Extract work experience information from resume text."""
        experience = []
        
        # Look for experience section
        experience_text = self._extract_section(text, ['experience', 'work experience', 'employment'])
        if not experience_text:
            return experience
            
        # Split into entries
        entries = re.split(r'\n\s*\n', experience_text)
        
        for entry in entries:
            if not entry.strip():
                continue
                
            exp_entry = {
                'title': None,
                'company': None,
                'location': None,
                'start_date': None,
                'end_date': None,
                'responsibilities': []
            }
            
            lines = entry.split('\n')
            
            # First line usually contains title and company
            if lines:
                header = lines[0]
                title_match = re.search(r'^([^|@]+)(?:[|@]\s*(.+))?', header)
                if title_match:
                    exp_entry['title'] = title_match.group(1).strip()
                    if title_match.group(2):
                        exp_entry['company'] = title_match.group(2).strip()
                        
            # Look for dates
            date_pattern = r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})\s*-\s*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}|Present)'
            match = re.search(date_pattern, entry)
            if match:
                exp_entry['start_date'] = match.group(1)
                exp_entry['end_date'] = match.group(2)
                
            # Extract responsibilities (bullet points)
            for line in lines[1:]:
                line = line.strip()
                if line.startswith(('•', '-', '*')) and len(line) > 1:
                    exp_entry['responsibilities'].append(line[1:].strip())
                    
            if any(exp_entry.values()):  # Add entry if any field was populated
                experience.append(exp_entry)
                
        return experience
    
    def _extract_projects(self, text: str) -> List[Dict]:
        """Extract project information from resume text."""
        projects = []
        
        # Look for projects section
        projects_text = self._extract_section(text, ['projects', 'personal projects'])
        if not projects_text:
            return projects
            
        # Split into entries
        entries = re.split(r'\n\s*\n', projects_text)
        
        for entry in entries:
            if not entry.strip():
                continue
                
            project_entry = {
                'name': None,
                'description': None,
                'technologies': set(),
                'url': None
            }
            
            lines = entry.split('\n')
            
            # First line is usually the project name
            if lines:
                project_entry['name'] = lines[0].strip()
                
            # Look for URL
            url_match = re.search(self.url_pattern, entry)
            if url_match:
                project_entry['url'] = url_match.group(0)
                
            # Extract technologies used
            for category, skills in self.tech_skills.items():
                for skill in skills:
                    if skill.lower() in entry.lower():
                        project_entry['technologies'].add(skill)
                        
            # Remaining lines form the description
            description_lines = []
            for line in lines[1:]:
                line = line.strip()
                if line and not line.startswith(('•', '-', '*')):
                    description_lines.append(line)
            if description_lines:
                project_entry['description'] = ' '.join(description_lines)
                
            if any(project_entry.values()):  # Add entry if any field was populated
                projects.append(project_entry)
                
        return projects
    
    def _extract_certifications(self, text: str) -> List[Dict]:
        """Extract certification information from resume text."""
        certifications = []
        
        # Look for certifications section
        cert_text = self._extract_section(text, ['certifications', 'certificates', 'qualifications'])
        if not cert_text:
            return certifications
            
        # Split into entries
        entries = re.split(r'\n\s*\n', cert_text)
        
        for entry in entries:
            if not entry.strip():
                continue
                
            cert_entry = {
                'name': None,
                'issuer': None,
                'date': None,
                'url': None
            }
            
            lines = entry.split('\n')
            
            # First line usually contains certification name
            if lines:
                cert_entry['name'] = lines[0].strip()
                
            # Look for issuer
            issuer_pattern = r'(?:issued by|from):\s*([^\n]+)'
            match = re.search(issuer_pattern, entry, re.IGNORECASE)
            if match:
                cert_entry['issuer'] = match.group(1).strip()
                
            # Look for date
            date_pattern = r'(?:issued|completed|earned):\s*([A-Za-z]+\s+\d{4})'
            match = re.search(date_pattern, entry, re.IGNORECASE)
            if match:
                cert_entry['date'] = match.group(1)
                
            # Look for URL
            url_match = re.search(self.url_pattern, entry)
            if url_match:
                cert_entry['url'] = url_match.group(0)
                
            if any(cert_entry.values()):  # Add entry if any field was populated
                certifications.append(cert_entry)
                
        return certifications
    
    def _extract_summary(self, text: str) -> Optional[str]:
        """Extract professional summary from resume text."""
        # Look for summary section
        summary_text = self._extract_section(text, ['summary', 'objective', 'profile'])
        if summary_text:
            # Clean up the summary
            summary = re.sub(r'\s+', ' ', summary_text).strip()
            return summary if summary else None
        return None
    
    def _extract_section(self, text: str, section_names: List[str]) -> Optional[str]:
        """Extract a section from the resume text based on common section headers."""
        text = text.lower()
        
        for name in section_names:
            # Look for section header
            pattern = fr'(?:^|\n){name}:?\s*\n+(.*?)(?:\n\n|\Z)'
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
                
        return None 