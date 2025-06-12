"""
Resume Parser Module - Handles PDF and text resume processing
"""
import os
import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

import fitz  # PyMuPDF
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
    """Handles parsing of resume documents in various formats."""
    
    def __init__(self):
        self.supported_formats = ['.pdf', '.txt']
        self.cache_dir = Path("data/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Common skill keywords
        self.skill_keywords = {
            'languages': ['python', 'javascript', 'typescript', 'java', 'c#', 'ruby', 'php', 'go', 'rust', 'swift'],
            'frontend': ['react', 'vue', 'angular', 'next.js', 'nuxt', 'svelte', 'html', 'css', 'sass', 'tailwind'],
            'backend': ['node.js', 'django', 'flask', 'express', 'fastapi', 'spring', 'rails', 'laravel'],
            'mobile': ['react native', 'flutter', 'ionic', 'swift', 'kotlin'],
            'database': ['postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch', 'dynamodb'],
            'cloud': ['aws', 'gcp', 'azure', 'docker', 'kubernetes', 'terraform'],
            'tools': ['git', 'github', 'gitlab', 'bitbucket', 'jira', 'confluence'],
            'testing': ['jest', 'pytest', 'cypress', 'selenium', 'playwright'],
            'concepts': ['ci/cd', 'tdd', 'agile', 'scrum', 'microservices', 'rest', 'graphql']
        }
    
    def parse(self, file_path: Path) -> Dict:
        """
        Parse resume file and extract structured information.
        
        Args:
            file_path: Path to the resume file
            
        Returns:
            Dictionary containing structured resume data
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Resume file not found: {file_path}")
            
        if file_path.suffix.lower() not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
        
        try:
            # Extract text and cache if needed
            text, original_format = self._extract_and_cache_text(file_path)
            
            # Process the text into structured data
            structured_data = self._process_text(text)
            
            # Add format information and text content
            structured_data.original_format = original_format
            structured_data.text_content = text
            
            return structured_data.model_dump()
            
        except Exception as e:
            logger.error(f"Error parsing resume {file_path}: {e}")
            raise
    
    def _extract_and_cache_text(self, file_path: Path) -> tuple[str, str]:
        """
        Extract text from file and cache the result.
        Returns tuple of (text_content, original_format)
        """
        # Generate cache path
        cache_path = self.cache_dir / f"{file_path.stem}_text.txt"
        
        # Check if cached version exists and is newer than the source file
        if cache_path.exists() and cache_path.stat().st_mtime > file_path.stat().st_mtime:
            logger.info(f"Using cached text version from {cache_path}")
            return cache_path.read_text(encoding='utf-8'), file_path.suffix.lower()[1:]
        
        # Extract text based on file format
        if file_path.suffix.lower() == '.pdf':
            text = self._extract_from_pdf(file_path)
            format_type = 'pdf'
        else:  # .txt
            text = file_path.read_text(encoding='utf-8')
            format_type = 'txt'
        
        # Cache the extracted text
        try:
            cache_path.write_text(text, encoding='utf-8')
            logger.info(f"Cached text version to {cache_path}")
        except Exception as e:
            logger.warning(f"Failed to cache text version: {e}")
        
        return text, format_type
    
    def _extract_from_pdf(self, file_path: Path) -> str:
        """
        Extract text from PDF file using PyMuPDF.
        Enhanced to better handle LinkedIn and modern resume formats.
        """
        text_blocks = []
        try:
            with fitz.open(file_path) as doc:
                for page in doc:
                    # Get the text blocks with their formatting
                    blocks = page.get_text("blocks")
                    
                    # Sort blocks by vertical position (top to bottom)
                    blocks.sort(key=lambda b: (b[1], b[0]))  # Sort by y, then x
                    
                    for block in blocks:
                        block_text = block[4].strip()
                        if block_text:
                            # Clean up common PDF artifacts
                            block_text = re.sub(r'\s+', ' ', block_text)
                            block_text = block_text.replace('• ', '\n• ')
                            
                            text_blocks.append(block_text)
                            
                            # Add extra newline for better section separation
                            if len(block_text) < 50 and any(marker in block_text.upper() for marker in ['EXPERIENCE', 'EDUCATION', 'SKILLS', 'LANGUAGES']):
                                text_blocks.append("")
                
            return "\n".join(text_blocks)
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise
    
    def _process_text(self, text: str) -> ResumeData:
        """
        Process extracted text to structure resume information.
        Enhanced with better section detection and information extraction.
        """
        sections = self._split_into_sections(text)
        
        # Extract all skills from the entire text
        all_skills = self._extract_all_skills(text)
        
        # Process experience entries with skill detection
        experience_entries = []
        for exp in self._extract_experience(sections.get('experience', '')):
            # Extract skills mentioned in this experience
            exp_skills = [skill for skill in all_skills if skill.lower() in exp['description'].lower()]
            
            # Parse dates and duration
            start_date, end_date, duration = self._parse_date_range(exp['description'])
            
            # Create experience entry
            experience_entries.append(ExperienceEntry(
                company=exp['company'],
                position=exp['position'],
                start_date=start_date,
                end_date=end_date,
                duration=duration,
                location=self._extract_location_from_text(exp['description']),
                description=exp['description'],
                skills=exp_skills
            ))
        
        # Process education entries
        education_entries = []
        for edu in self._extract_education(sections.get('education', '')):
            start_date, end_date, _ = self._parse_date_range(edu['details'])
            field = self._extract_field_of_study(edu['degree'])
            
            education_entries.append(EducationEntry(
                institution=edu['institution'],
                degree=edu['degree'],
                field=field,
                start_date=start_date,
                end_date=end_date,
                details=edu['details']
            ))
        
        return ResumeData(
            full_name=self._extract_name(sections.get('header', '')),
            email=self._extract_email(sections.get('header', '')),
            phone=self._extract_phone(sections.get('header', '')),
            location=self._extract_location(sections.get('header', '')),
            summary=sections.get('summary', ''),
            skills=all_skills,
            experience=experience_entries,
            education=education_entries,
            languages=self._extract_languages(text),
            certifications=self._extract_certifications(text),
            original_format='',  # Will be set in parse()
            text_content=''  # Will be set in parse()
        )
    
    def _split_into_sections(self, text: str) -> Dict[str, str]:
        """
        Split resume text into logical sections.
        Enhanced to better handle various resume formats.
        """
        sections = {
            'header': '',
            'summary': '',
            'experience': '',
            'education': '',
            'skills': '',
            'languages': '',
            'certifications': ''
        }
        
        current_section = 'header'
        lines = text.split('\n')
        
        section_markers = {
            'EXPERIENCE': 'experience',
            'EMPLOYMENT': 'experience',
            'WORK': 'experience',
            'EDUCATION': 'education',
            'ACADEMIC': 'education',
            'SKILLS': 'skills',
            'TECHNICAL SKILLS': 'skills',
            'LANGUAGES': 'languages',
            'CERTIFICATIONS': 'certifications',
            'CERTIFICATES': 'certifications',
            'SUMMARY': 'summary',
            'PROFILE': 'summary',
            'ABOUT': 'summary'
        }
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for section headers
            upper_line = line.upper()
            section_found = False
            
            for marker, section in section_markers.items():
                if marker in upper_line and len(line) < 50:  # Avoid matching long lines
                    current_section = section
                    section_found = True
                    break
            
            if not section_found:
                sections[current_section] += line + '\n'
        
        return sections
    
    def _extract_name(self, text: str) -> str:
        """Extract full name from header section."""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if not lines:
            return "Unknown"
        
        # Usually the first line that's not an email/phone/location
        for line in lines:
            if '@' not in line and not any(c.isdigit() for c in line):
                return line
        
        return lines[0]
    
    def _extract_email(self, text: str) -> Optional[str]:
        """Extract email from text."""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        matches = re.findall(email_pattern, text)
        return matches[0] if matches else None
    
    def _extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number from text."""
        # Match various phone number formats
        phone_pattern = r'(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        matches = re.findall(phone_pattern, text)
        return matches[0] if matches else None
    
    def _extract_location(self, text: str) -> Optional[str]:
        """Extract location from text."""
        # Match city, state/country format
        location_pattern = r'([A-Za-z\s]+,\s*[A-Za-z\s]+(?:\s*,\s*[A-Za-z\s]+)?)'
        matches = re.findall(location_pattern, text)
        return matches[0] if matches else None
    
    def _extract_location_from_text(self, text: str) -> Optional[str]:
        """Extract location from experience text."""
        location_patterns = [
            r'(?:in|at)\s+([A-Za-z\s]+,\s*[A-Za-z\s]+(?:\s*,\s*[A-Za-z\s]+)?)',
            r'(?:Remote|Hybrid|On-site)\s+in\s+([A-Za-z\s]+(?:,\s*[A-Za-z\s]+)*)',
            r'\(([A-Za-z\s]+,\s*[A-Za-z\s]+(?:\s*,\s*[A-Za-z\s]+)?)\)'
        ]
        
        for pattern in location_patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0].strip()
        return None
    
    def _extract_all_skills(self, text: str) -> List[str]:
        """
        Extract all skills mentioned in the text.
        Uses predefined skill categories and pattern matching.
        """
        found_skills = set()
        
        # Look for skills in all categories
        for category, skills in self.skill_keywords.items():
            for skill in skills:
                # Create pattern that matches whole words only
                pattern = r'\b' + re.escape(skill) + r'\b'
                if re.search(pattern, text.lower()):
                    found_skills.add(skill)
        
        # Look for additional skills in Skills section
        skills_section = self._split_into_sections(text).get('skills', '')
        if skills_section:
            # Split by common separators and clean
            for line in skills_section.split('\n'):
                # Remove common prefixes
                line = re.sub(r'^(Skills|Technologies|Tools|Languages):\s*', '', line, flags=re.IGNORECASE)
                
                # Split by common separators and clean
                parts = re.split(r'[,|•]|\band\b', line)
                found_skills.update(part.strip() for part in parts if part.strip())
        
        return sorted(list(found_skills))
    
    def _extract_languages(self, text: str) -> List[str]:
        """Extract language proficiencies."""
        languages = []
        language_pattern = r'(?:Languages?|Idiomas?)(?:\s*:\s*|\n)((?:[A-Za-z]+\s*(?:\([^)]+\))?\s*(?:,|\n|$)\s*)+)'
        
        matches = re.findall(language_pattern, text, re.IGNORECASE)
        if matches:
            # Split languages and clean up
            for lang_group in matches:
                langs = re.split(r',|\n', lang_group)
                languages.extend(lang.strip() for lang in langs if lang.strip())
        
        return languages
    
    def _extract_certifications(self, text: str) -> List[str]:
        """Extract certifications and licenses."""
        certifications = []
        cert_section = self._split_into_sections(text).get('certifications', '')
        
        if cert_section:
            # Split by bullet points or newlines
            for line in re.split(r'•|\n', cert_section):
                line = line.strip()
                if line and not line.lower().startswith(('certifications', 'certificates')):
                    certifications.append(line)
        
        return certifications
    
    def _parse_date_range(self, text: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Extract start date, end date, and duration from text.
        Returns (start_date, end_date, duration)
        """
        # Common date patterns
        date_pattern = r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}'
        duration_pattern = r'\(([^)]+)\)'
        
        # Find all dates
        dates = re.findall(date_pattern, text)
        
        # Find duration
        duration_match = re.search(duration_pattern, text)
        duration = duration_match.group(1) if duration_match else None
        
        if len(dates) >= 2:
            return dates[0], dates[1], duration
        elif len(dates) == 1:
            if 'Present' in text:
                return dates[0], 'Present', duration
            return dates[0], None, duration
        
        return None, None, duration
    
    def _extract_field_of_study(self, degree_text: str) -> Optional[str]:
        """Extract field of study from degree text."""
        field_pattern = r'(?:in|of|,)\s+([^,]+)(?:$|,)'
        match = re.search(field_pattern, degree_text)
        return match.group(1).strip() if match else None
    
    def _extract_experience(self, text: str) -> List[Dict[str, str]]:
        """
        Extract work experience entries.
        Enhanced to better handle LinkedIn and modern resume formats.
        """
        experiences = []
        
        # Split text into potential experience blocks
        blocks = re.split(r'\n\s*\n', text)
        
        for block in blocks:
            lines = block.strip().split('\n')
            if not lines:
                continue
            
            # Look for title line (usually contains position and company)
            title_line = lines[0]
            
            # Try to identify position and company
            if ' at ' in title_line:
                position, company = title_line.split(' at ', 1)
            else:
                # Try other common patterns
                match = re.match(r'^(.*?(?:Developer|Engineer|Architect|Manager|Lead|Consultant|Analyst))\s*[-|,]?\s*(.+)$', title_line)
                if match:
                    position, company = match.groups()
                else:
                    position = company = title_line
            
            # Join remaining lines as description
            description = '\n'.join(lines[1:]) if len(lines) > 1 else ''
            
            experiences.append({
                'company': company.strip(),
                'position': position.strip(),
                'description': description.strip()
            })
        
        return experiences
    
    def _extract_education(self, text: str) -> List[Dict[str, str]]:
        """
        Extract education entries.
        Enhanced to better handle various formats.
        """
        education = []
        
        # Split text into potential education blocks
        blocks = re.split(r'\n\s*\n', text)
        
        for block in blocks:
            lines = block.strip().split('\n')
            if not lines:
                continue
            
            # Look for degree line
            degree_line = lines[0]
            
            # Try to split degree and institution
            if ' from ' in degree_line:
                degree, institution = degree_line.split(' from ', 1)
            else:
                # Try other common patterns
                match = re.match(r'^(.*?(?:Bachelor|Master|PhD|BSc|MSc|MBA|Diploma).*?),\s*(.+)$', degree_line)
                if match:
                    degree, institution = match.groups()
                else:
                    degree = institution = degree_line
            
            # Join remaining lines as details
            details = '\n'.join(lines[1:]) if len(lines) > 1 else ''
            
            education.append({
                'degree': degree.strip(),
                'institution': institution.strip(),
                'details': details.strip()
            })
        
        return education 