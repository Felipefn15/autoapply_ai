"""
Job Matcher Module

Matches job postings against resume data using:
- Required skills matching
- Experience level matching
- Keyword matching
- Semantic similarity
"""
from typing import Dict, List, Set
import re
import spacy
from loguru import logger
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class JobMatcher:
    """Matches jobs against resume data."""
    
    def __init__(self, min_score: float = 0.5, required_skills: List[str] = None,
                 preferred_skills: List[str] = None, excluded_keywords: List[str] = None):
        """Initialize the job matcher."""
        self.min_score = min_score
        self.required_skills = set(s.lower() for s in (required_skills or []))
        self.preferred_skills = set(s.lower() for s in (preferred_skills or []))
        self.excluded_keywords = set(k.lower() for k in (excluded_keywords or []))
        
        # Initialize NLP components
        self.nlp = spacy.load('en_core_web_sm')
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            ngram_range=(1, 2),
            max_features=10000
        )
        
        # Initialize resume data
        self.resume_data = None
        self.resume_skills = set()
        self.resume_vector = None
        
    def update_resume_data(self, resume_data: Dict):
        """Update resume data and precompute features."""
        self.resume_data = resume_data
        
        # Extract skills from resume
        self.resume_skills = set()
        for category, skills in resume_data.get('skills', {}).items():
            self.resume_skills.update(s.lower() for s in skills)
            
        # Create resume text for vectorization
        resume_text = self._create_resume_text()
        
        # Vectorize resume text
        try:
            self.resume_vector = self.vectorizer.fit_transform([resume_text])
        except Exception as e:
            logger.error(f"Error vectorizing resume: {str(e)}")
            self.resume_vector = None
            
    def calculate_match(self, job: Dict) -> float:
        """Calculate match score between resume and job."""
        try:
            if not self.resume_data or not self.resume_vector:
                logger.warning("Resume data not initialized")
                return 0.0
                
            # Check for excluded keywords
            if self._has_excluded_keywords(job):
                return 0.0
                
            # Calculate various match components
            required_score = self._calculate_required_skills_match(job)
            if required_score == 0:  # Missing required skills
                return 0.0
                
            preferred_score = self._calculate_preferred_skills_match(job)
            experience_score = self._calculate_experience_match(job)
            semantic_score = self._calculate_semantic_match(job)
            
            # Combine scores with weights
            weights = {
                'required': 0.3,
                'preferred': 0.2,
                'experience': 0.2,
                'semantic': 0.3
            }
            
            total_score = (
                required_score * weights['required'] +
                preferred_score * weights['preferred'] +
                experience_score * weights['experience'] +
                semantic_score * weights['semantic']
            )
            
            return round(total_score, 2)
            
        except Exception as e:
            logger.error(f"Error calculating match score: {str(e)}")
            return 0.0
            
    def _has_excluded_keywords(self, job: Dict) -> bool:
        """Check if job contains any excluded keywords."""
        job_text = f"{job['title']} {job['description']}".lower()
        return any(kw in job_text for kw in self.excluded_keywords)
        
    def _calculate_required_skills_match(self, job: Dict) -> float:
        """Calculate match score for required skills."""
        if not self.required_skills:
            return 1.0  # No required skills specified
            
        # Extract skills from job posting
        job_skills = self._extract_skills_from_job(job)
        
        # Calculate match
        matched_skills = self.required_skills.intersection(job_skills)
        return len(matched_skills) / len(self.required_skills)
        
    def _calculate_preferred_skills_match(self, job: Dict) -> float:
        """Calculate match score for preferred skills."""
        if not self.preferred_skills:
            return 1.0  # No preferred skills specified
            
        # Extract skills from job posting
        job_skills = self._extract_skills_from_job(job)
        
        # Calculate match
        matched_skills = self.preferred_skills.intersection(job_skills)
        return len(matched_skills) / len(self.preferred_skills)
        
    def _calculate_experience_match(self, job: Dict) -> float:
        """Calculate match score for experience level."""
        try:
            # Extract years of experience from job posting
            job_years = self._extract_years_required(job)
            if job_years is None:
                return 1.0  # No experience requirement specified
                
            # Get candidate's years of experience
            candidate_years = self.resume_data.get('years_of_experience', 0)
            
            # Calculate match
            if candidate_years >= job_years:
                return 1.0
            elif candidate_years >= job_years * 0.8:  # Allow some flexibility
                return 0.8
            elif candidate_years >= job_years * 0.6:
                return 0.5
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"Error calculating experience match: {str(e)}")
            return 1.0  # Default to full match on error
            
    def _calculate_semantic_match(self, job: Dict) -> float:
        """Calculate semantic similarity between resume and job."""
        try:
            # Create job text
            job_text = self._create_job_text(job)
            
            # Vectorize job text
            job_vector = self.vectorizer.transform([job_text])
            
            # Calculate cosine similarity
            similarity = cosine_similarity(self.resume_vector, job_vector)[0][0]
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating semantic match: {str(e)}")
            return 0.0
            
    def _extract_skills_from_job(self, job: Dict) -> Set[str]:
        """Extract skills mentioned in job posting."""
        skills = set()
        
        # Combine title and description
        job_text = f"{job['title']} {job['description']}".lower()
        
        # Look for resume skills in job text
        for skill in self.resume_skills:
            if re.search(r'\b' + re.escape(skill) + r'\b', job_text):
                skills.add(skill)
                
        return skills
        
    def _extract_years_required(self, job: Dict) -> float:
        """Extract years of experience required from job posting."""
        try:
            # Common patterns for years of experience
            patterns = [
                r'(\d+)[\+]?\s*(?:years|yrs|yr)(?:\s+of)?\s+experience',
                r'(\d+)[\+]?\s*(?:years|yrs|yr)(?:\s+of)?\s+work\s+experience',
                r'experience\s*(?:of|:)?\s*(\d+)[\+]?\s*(?:years|yrs|yr)',
                r'(\d+)[\+]?\s*(?:years|yrs|yr)\s+(?:of\s+)?(?:relevant|related)\s+experience'
            ]
            
            job_text = f"{job['title']} {job['description']}".lower()
            
            for pattern in patterns:
                match = re.search(pattern, job_text)
                if match:
                    years = int(match.group(1))
                    return years
                    
            return None
            
        except Exception as e:
            logger.error(f"Error extracting years required: {str(e)}")
            return None
            
    def _create_resume_text(self) -> str:
        """Create text representation of resume for vectorization."""
        sections = []
        
        # Add current role
        if self.resume_data.get('current_role'):
            sections.append(self.resume_data['current_role'])
            
        # Add experience descriptions
        for exp in self.resume_data.get('experience', []):
            sections.append(f"{exp['title']} {exp['description']}")
            
        # Add skills
        sections.extend(self.resume_skills)
        
        # Add achievements
        sections.extend(self.resume_data.get('achievements', []))
        
        return ' '.join(sections)
        
    def _create_job_text(self, job: Dict) -> str:
        """Create text representation of job for vectorization."""
        sections = [
            job['title'],
            job['description']
        ]
        return ' '.join(sections) 