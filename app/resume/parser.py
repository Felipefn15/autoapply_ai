"""
Resume Parser Module - Handles PDF and text resume processing
"""
import os
import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

import fitz  # PyMuPDF
import PyPDF2
import spacy
from pydantic import BaseModel
from loguru import logger

class ExperienceEntry(BaseModel):
    """Model for work experience entries."""
    company: str
    position: str
    start_date: Optional[str]
    end_date: Optional[str]
    duration: Optional[str]
    location: Optional[str]
    description: str
    skills: List[str]

class EducationEntry(BaseModel):
    """Model for education entries."""
    institution: str
    degree: str
    field: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    details: str

class ResumeData(BaseModel):
    """Data model for parsed resume information."""
    full_name: str
    email: Optional[str]
    phone: Optional[str]
    location: Optional[str]
    summary: Optional[str]
    skills: List[str]
    experience: List[ExperienceEntry]
    education: List[EducationEntry]
    languages: List[str]
    certifications: List[str]
    original_format: str  # 'pdf' or 'txt'
    text_content: str  # Stored text content for reuse

class ResumeParser:
    """Parses resume PDF and extracts structured information."""
    
    def __init__(self):
        """Initialize the resume parser."""
        # Load spaCy model for NER
        self.nlp = spacy.load("en_core_web_sm")
        
        # Regex patterns
        self.email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
        self.phone_pattern = r'\+?[\d\s-]{10,}'
        self.url_pattern = r'https?://(?:www\.)?[\w\.-]+\.\w+(?:/[\w\.-]*)*'
        
        # Skills keywords
        self.tech_skills = {
            'languages': ['python', 'javascript', 'typescript', 'java', 'c++', 'ruby', 'php'],
            'frameworks': ['react', 'angular', 'vue', 'django', 'flask', 'spring', 'express'],
            'databases': ['postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch'],
            'cloud': ['aws', 'gcp', 'azure', 'docker', 'kubernetes'],
            'tools': ['git', 'jenkins', 'jira', 'confluence', 'terraform']
        }
    
    def parse(self, pdf_path: str) -> Dict:
        """Parse resume PDF and extract information."""
        try:
            # Read PDF content
            text = self._extract_text(pdf_path)
            if not text:
                raise ValueError("Could not extract text from PDF")
            
            # Extract information
            contact_info = self._extract_contact_info(text)
            experience = self._extract_experience(text)
            education = self._extract_education(text)
            skills = self._extract_skills(text)
            achievements = self._extract_achievements(text)
            
            # Combine into structured data
            resume_data = {
                'name': contact_info.get('name', ''),
                'email': contact_info.get('email', ''),
                'phone': contact_info.get('phone', ''),
                'location': contact_info.get('location', ''),
                'linkedin_url': contact_info.get('linkedin_url', ''),
                'github_url': contact_info.get('github_url', ''),
                'portfolio_url': contact_info.get('portfolio_url', ''),
                'experience': experience,
                'education': education,
                'skills': skills,
                'achievements': achievements,
                'years_of_experience': self._calculate_years_experience(experience),
                'current_role': experience[0]['title'] if experience else ''
            }
            
            return resume_data
            
        except Exception as e:
            logger.error(f"Error parsing resume: {str(e)}")
            raise
    
    def _extract_text(self, pdf_path: str) -> str:
        """Extract text content from PDF."""
        try:
            text = ""
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            raise
    
    def _extract_contact_info(self, text: str) -> Dict:
        """Extract contact information."""
        info = {}
        
        # Extract email
        email_match = re.search(self.email_pattern, text)
        if email_match:
            info['email'] = email_match.group(0)
        
        # Extract phone
        phone_match = re.search(self.phone_pattern, text)
        if phone_match:
            info['phone'] = phone_match.group(0)
        
        # Extract URLs
        urls = re.findall(self.url_pattern, text)
        for url in urls:
            if 'linkedin.com' in url:
                info['linkedin_url'] = url
            elif 'github.com' in url:
                info['github_url'] = url
            elif not any(domain in url for domain in ['linkedin.com', 'github.com']):
                info['portfolio_url'] = url
        
        # Extract name and location using spaCy NER
        doc = self.nlp(text[:1000])  # Process first 1000 chars for efficiency
        for ent in doc.ents:
            if ent.label_ == 'PERSON' and 'name' not in info:
                info['name'] = ent.text
            elif ent.label_ == 'GPE' and 'location' not in info:
                info['location'] = ent.text
        
        return info
    
    def _extract_experience(self, text: str) -> List[Dict]:
        """Extract work experience entries."""
        experience = []
        
        # Split text into sections
        sections = text.split('\n\n')
        
        # Find experience section
        for i, section in enumerate(sections):
            if any(keyword in section.lower() for keyword in ['experience', 'work history', 'employment']):
                # Process next few sections as experience entries
                for j in range(i+1, min(i+6, len(sections))):
                    entry = sections[j]
                    if entry and not any(keyword in entry.lower() for keyword in ['education', 'skills', 'projects']):
                        # Parse entry
                        lines = entry.split('\n')
                        if len(lines) >= 2:
                            experience.append({
                                'title': lines[0],
                                'company': lines[1],
                                'period': self._extract_date_range(entry),
                                'description': '\n'.join(lines[2:])
                            })
        
        return experience
    
    def _extract_education(self, text: str) -> List[Dict]:
        """Extract education entries."""
        education = []
        
        # Split text into sections
        sections = text.split('\n\n')
        
        # Find education section
        for i, section in enumerate(sections):
            if 'education' in section.lower():
                # Process next few sections as education entries
                for j in range(i+1, min(i+4, len(sections))):
                    entry = sections[j]
                    if entry and not any(keyword in entry.lower() for keyword in ['experience', 'skills', 'projects']):
                        # Parse entry
                        lines = entry.split('\n')
                        if len(lines) >= 2:
                            education.append({
                                'degree': lines[0],
                                'institution': lines[1],
                                'period': self._extract_date_range(entry)
                            })
        
        return education
    
    def _extract_skills(self, text: str) -> Dict[str, List[str]]:
        """Extract skills by category."""
        skills = {category: [] for category in self.tech_skills}
        
        # Look for skills in each category
        for category, keywords in self.tech_skills.items():
            for keyword in keywords:
                if re.search(r'\b' + keyword + r'\b', text.lower()):
                    skills[category].append(keyword)
        
        return skills
    
    def _extract_achievements(self, text: str) -> List[str]:
        """Extract key achievements."""
        achievements = []
        
        # Look for achievement indicators
        indicators = ['achieved', 'developed', 'improved', 'increased', 'reduced', 'led', 'managed']
        
        # Split text into sentences
        sentences = text.split('.')
        
        # Find sentences with achievements
        for sentence in sentences:
            if any(indicator in sentence.lower() for indicator in indicators):
                achievements.append(sentence.strip())
        
        return achievements[:5]  # Return top 5 achievements
    
    def _extract_date_range(self, text: str) -> str:
        """Extract date range from text."""
        # Look for date patterns
        date_pattern = r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}'
        dates = re.findall(date_pattern, text)
        
        if len(dates) >= 2:
            return f"{dates[0]} - {dates[1]}"
        elif len(dates) == 1:
            return f"{dates[0]} - Present"
        return ""
    
    def _calculate_years_experience(self, experience: List[Dict]) -> int:
        """Calculate total years of experience."""
        total_years = 0
        current_year = datetime.now().year
        
        for entry in experience:
            period = entry.get('period', '')
            if period:
                dates = re.findall(r'\d{4}', period)
                if len(dates) >= 2:
                    total_years += int(dates[1]) - int(dates[0])
                elif len(dates) == 1:
                    total_years += current_year - int(dates[0])
        
        return total_years 