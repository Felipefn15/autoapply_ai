"""Job matcher module for matching candidates with job posts."""
import re
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from datetime import datetime

from loguru import logger

from .post_analyzer import JobPostInfo
from .resume_analyzer import ResumeInfo

@dataclass
class MatchScore:
    """Detailed matching score between a candidate and a job post."""
    total_score: float  # 0-100
    skill_match: float  # 0-100
    experience_match: float  # 0-100
    location_match: float  # 0-100
    seniority_match: float  # 0-100
    salary_match: float  # 0-100
    education_match: float  # 0-100
    language_match: float  # 0-100
    missing_required_skills: Set[str]
    matching_preferred_skills: Set[str]
    reasons: List[str]

class JobMatcher:
    """Matches candidates with job posts based on various criteria."""
    
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """Initialize the matcher with scoring weights."""
        self.weights = weights or {
            'skills': 0.30,  # 30% weight for skills match
            'experience': 0.20,  # 20% weight for experience match
            'location': 0.15,  # 15% weight for location match
            'seniority': 0.10,  # 10% weight for seniority match
            'salary': 0.10,  # 10% weight for salary match
            'education': 0.10,  # 10% weight for education match
            'language': 0.05,  # 5% weight for language match
        }
        
        # Minimum scores for recommendation
        self.min_total_score = 60.0  # Minimum total score to recommend
        self.min_skill_score = 50.0  # Minimum skill match score
        self.min_experience_score = 40.0  # Minimum experience match score
        
        # Seniority level mapping
        self.seniority_levels = {
            'junior': 0,
            'mid': 1,
            'senior': 2,
            'staff': 3,
            'manager': 4
        }
        
        # Experience years mapping
        self.experience_ranges = {
            'junior': (0, 3),
            'mid': (2, 5),
            'senior': (4, 8),
            'staff': (6, 12),
            'manager': (5, 15)
        }
        
    def match_job(self, job: JobPostInfo, candidate: ResumeInfo) -> MatchScore:
        """Match a candidate against a job post."""
        # First check if job is remote - if not, return 0
        if not self._is_remote_job(job):
            return MatchScore(
                total_score=0.0,
                skill_match=0.0,
                experience_match=0.0,
                location_match=0.0,
                seniority_match=0.0,
                salary_match=0.0,
                education_match=0.0,
                language_match=0.0,
                missing_required_skills=set(),
                matching_preferred_skills=set(),
                reasons=["Job is not remote."]
            )
            
        # Calculate individual match scores
        skill_score, missing_required, matching_preferred = self._calculate_skill_match(job, candidate)
        experience_score = self._calculate_experience_match(job, candidate)
        location_score = self._calculate_location_match(job, candidate)
        seniority_score = self._calculate_seniority_match(job, candidate)
        salary_score = self._calculate_salary_match(job, candidate)
        education_score = self._calculate_education_match(job, candidate)
        language_score = self._calculate_language_match(job, candidate)
        
        # Calculate weighted total score
        total_score = (
            skill_score * self.weights['skills'] +
            experience_score * self.weights['experience'] +
            location_score * self.weights['location'] +
            seniority_score * self.weights['seniority'] +
            salary_score * self.weights['salary'] +
            education_score * self.weights['education'] +
            language_score * self.weights['language']
        ) * 100
        
        # Generate reasons for the match score
        reasons = self._generate_match_reasons(
            job, candidate,
            skill_score, experience_score, location_score,
            seniority_score, salary_score, education_score,
            language_score, missing_required, matching_preferred
        )
        
        return MatchScore(
            total_score=total_score,
            skill_match=skill_score * 100,
            experience_match=experience_score * 100,
            location_match=location_score * 100,
            seniority_match=seniority_score * 100,
            salary_match=salary_score * 100,
            education_match=education_score * 100,
            language_match=language_score * 100,
            missing_required_skills=missing_required,
            matching_preferred_skills=matching_preferred,
            reasons=reasons
        )
        
    def is_recommended_match(self, score: MatchScore) -> bool:
        """Determine if a match score meets minimum criteria for recommendation."""
        return (
            score.total_score >= self.min_total_score and
            score.skill_match >= self.min_skill_score and
            score.experience_match >= self.min_experience_score
        )
        
    def _is_remote_job(self, job: JobPostInfo) -> bool:
        """Check if job is remote."""
        # Check location field
        location = job.location.lower()
        remote_indicators = [
            'remote',
            'work from home',
            'wfh',
            'virtual',
            'distributed team',
            'anywhere',
            'worldwide'
        ]
        
        non_remote_indicators = [
            'on-site',
            'onsite',
            'in office',
            'hybrid',
            'local only',
            'must be in',
            'must work from'
        ]
        
        # If any non-remote indicators are found, job is not remote
        if any(indicator in location for indicator in non_remote_indicators):
            return False
            
        # Check description for remote indicators
        description = job.description.lower()
        if any(indicator in description for indicator in non_remote_indicators):
            return False
            
        # Must have at least one remote indicator in location or description
        return any(
            indicator in location or indicator in description 
            for indicator in remote_indicators
        )
        
    def _calculate_skill_match(self, job: JobPostInfo, candidate: ResumeInfo) -> Tuple[float, Set[str], Set[str]]:
        """Calculate skill match score and identify missing/matching skills."""
        if not job.skills_required and not job.skills_preferred:
            return 1.0, set(), set()
            
        # Check required skills
        missing_required = job.skills_required - candidate.skills
        matching_required = job.skills_required & candidate.skills
        
        # Check preferred skills
        matching_preferred = job.skills_preferred & candidate.skills
        
        # Calculate scores
        required_score = len(matching_required) / len(job.skills_required) if job.skills_required else 1.0
        preferred_score = len(matching_preferred) / len(job.skills_preferred) if job.skills_preferred else 1.0
        
        # Weight required skills more heavily (70-30 split)
        total_score = (required_score * 0.7) + (preferred_score * 0.3)
        
        return total_score, missing_required, matching_preferred
        
    def _calculate_experience_match(self, job: JobPostInfo, candidate: ResumeInfo) -> float:
        """Calculate experience match score."""
        if not job.experience_years:
            return 1.0
            
        # Calculate total years of experience from resume
        total_experience = 0
        for exp in candidate.experience:
            if exp.get('start_date') and exp.get('end_date'):
                try:
                    start = datetime.strptime(exp['start_date'], '%B %Y')
                    end = datetime.strptime(exp['end_date'], '%B %Y') if exp['end_date'] != 'Present' else datetime.now()
                    years = (end - start).days / 365.25
                    total_experience += years
                except ValueError:
                    continue
                    
        # Calculate match score based on required experience
        if total_experience >= job.experience_years:
            return 1.0
        elif total_experience >= job.experience_years * 0.7:  # Allow some flexibility
            return 0.8
        elif total_experience >= job.experience_years * 0.5:
            return 0.5
        else:
            return 0.2
            
    def _calculate_location_match(self, job: JobPostInfo, candidate: ResumeInfo) -> float:
        """Calculate location match score."""
        if job.remote_type in ['remote', 'remote_flexible']:
            return 1.0
            
        if job.location.lower() == 'not specified' or candidate.location.lower() == 'not specified':
            return 0.5
            
        # Clean and normalize locations
        job_location = job.location.lower().replace(',', '').strip()
        candidate_location = candidate.location.lower().replace(',', '').strip()
        
        if job_location == candidate_location:
            return 1.0
        
        # Check if locations are in the same region/area
        job_parts = set(job_location.split())
        candidate_parts = set(candidate_location.split())
        common_parts = job_parts & candidate_parts
        
        if common_parts:
            return 0.8
            
        return 0.3
        
    def _calculate_seniority_match(self, job: JobPostInfo, candidate: ResumeInfo) -> float:
        """Calculate seniority level match score."""
        if job.seniority_level == 'not_specified':
            return 1.0
            
        # Determine candidate's seniority from experience
        total_experience = 0
        for exp in candidate.experience:
            if exp.get('start_date') and exp.get('end_date'):
                try:
                    start = datetime.strptime(exp['start_date'], '%B %Y')
                    end = datetime.strptime(exp['end_date'], '%B %Y') if exp['end_date'] != 'Present' else datetime.now()
                    years = (end - start).days / 365.25
                    total_experience += years
                except ValueError:
                    continue
                    
        # Map experience to seniority level
        candidate_level = 'junior'
        for level, (min_years, max_years) in self.experience_ranges.items():
            if min_years <= total_experience <= max_years:
                candidate_level = level
                break
                
        # Calculate match score based on seniority difference
        job_level_value = self.seniority_levels.get(job.seniority_level, 0)
        candidate_level_value = self.seniority_levels.get(candidate_level, 0)
        
        difference = abs(job_level_value - candidate_level_value)
        
        if difference == 0:
            return 1.0
        elif difference == 1:
            return 0.7
        else:
            return 0.3
            
    def _calculate_salary_match(self, job: JobPostInfo, candidate: ResumeInfo) -> float:
        """Calculate salary match score."""
        # If no salary information is provided, assume a match
        if not job.salary_min and not job.salary_max:
            return 1.0
            
        # TODO: Implement salary expectations extraction from resume
        # For now, return neutral score
        return 0.5
        
    def _calculate_education_match(self, job: JobPostInfo, candidate: ResumeInfo) -> float:
        """Calculate education match score."""
        if not candidate.education:
            return 0.5
            
        # Define education level hierarchy
        education_levels = {
            'phd': 4,
            'master': 3,
            'bachelor': 2,
            'associate': 1
        }
        
        # Get highest education level from candidate
        highest_level = 0
        relevant_major = False
        
        for edu in candidate.education:
            degree = edu.get('degree', '').lower()
            major = edu.get('major', '').lower()
            
            # Check education level
            for level, value in education_levels.items():
                if level in degree:
                    highest_level = max(highest_level, value)
                    
            # Check if major is relevant (tech/CS related)
            if any(term in major for term in ['computer', 'software', 'information', 'data']):
                relevant_major = True
                
        # Calculate score based on level and relevance
        base_score = min(highest_level / 3, 1.0)  # Normalize to 0-1
        relevance_bonus = 0.2 if relevant_major else 0
        
        return min(base_score + relevance_bonus, 1.0)
        
    def _calculate_language_match(self, job: JobPostInfo, candidate: ResumeInfo) -> float:
        """Calculate language match score."""
        if not candidate.languages:
            return 0.5  # Neutral score if no language information
            
        # Assume English is required if not specified
        required_languages = {'English'}
        
        # Check if candidate knows required languages
        matching_languages = required_languages & candidate.languages
        
        if matching_languages:
            return 1.0
        return 0.3
        
    def _generate_match_reasons(
        self,
        job: JobPostInfo,
        candidate: ResumeInfo,
        skill_score: float,
        experience_score: float,
        location_score: float,
        seniority_score: float,
        salary_score: float,
        education_score: float,
        language_score: float,
        missing_required: Set[str],
        matching_preferred: Set[str]
    ) -> List[str]:
        """Generate human-readable reasons for the match score."""
        reasons = []
        
        # Skills assessment
        if skill_score >= 0.8:
            reasons.append("Strong skill match with the required qualifications.")
            if matching_preferred:
                reasons.append(f"Bonus: Matches preferred skills: {', '.join(matching_preferred)}")
        elif skill_score >= 0.5:
            reasons.append("Partial skill match, but some key skills are missing.")
            if missing_required:
                reasons.append(f"Missing required skills: {', '.join(missing_required)}")
        else:
            reasons.append("Significant skill gap with the requirements.")
            reasons.append(f"Missing critical skills: {', '.join(missing_required)}")
            
        # Experience assessment
        if experience_score >= 0.8:
            reasons.append("Experience level exceeds the requirements.")
        elif experience_score >= 0.5:
            reasons.append("Experience level meets the minimum requirements.")
        else:
            reasons.append("May need more experience for this role.")
            
        # Location assessment
        if location_score >= 0.8:
            reasons.append("Location is ideal for this position.")
        elif location_score >= 0.5:
            reasons.append("Location is workable but may require relocation or remote work arrangement.")
        else:
            reasons.append("Location mismatch might be a challenge.")
            
        # Seniority assessment
        if seniority_score >= 0.8:
            reasons.append("Seniority level is a great match.")
        elif seniority_score >= 0.5:
            reasons.append("Seniority level is acceptable but not ideal.")
        else:
            reasons.append("Seniority level mismatch.")
            
        # Education assessment
        if education_score >= 0.8:
            reasons.append("Educational background is highly relevant.")
        elif education_score >= 0.5:
            reasons.append("Educational background is adequate.")
        else:
            reasons.append("May need additional education or certifications.")
            
        # Language assessment
        if language_score >= 0.8:
            reasons.append("Meets all language requirements.")
        elif language_score >= 0.5:
            reasons.append("Basic language requirements are met.")
        else:
            reasons.append("May need to improve language skills.")
            
        return reasons 