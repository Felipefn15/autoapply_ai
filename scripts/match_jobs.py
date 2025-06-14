#!/usr/bin/env python3
"""
Job Matching Script - Match jobs with user's profile
"""
import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import re

import yaml
from loguru import logger

from app.db.database import Database
from app.job_search.post_analyzer import PostAnalyzer

def load_profile(profile_path: str) -> Dict:
    """Load user profile from YAML file."""
    try:
        with open(profile_path, 'r') as f:
            profile = yaml.safe_load(f)
        logger.info("Loaded user profile")
        return profile
    except Exception as e:
        logger.error(f"Error loading profile: {str(e)}")
        raise

def load_jobs(jobs_dir: str) -> List[Dict]:
    """Load jobs from JSON files in directory."""
    jobs = []
    try:
        jobs_path = Path(jobs_dir)
        if not jobs_path.exists():
            logger.warning(f"Jobs directory not found: {jobs_dir}")
            return []
            
        for file in jobs_path.glob('*.json'):
            try:
                logger.debug(f"Loaded jobs from {file}")
                with open(file) as f:
                    jobs.extend(json.load(f))
            except Exception as e:
                logger.error(f"Error loading jobs from {file}: {str(e)}")
                continue
                
        return jobs
        
    except Exception as e:
        logger.error(f"Error loading jobs: {str(e)}")
        return []

def extract_core_skills_from_text(text: str, core_skills_config: Dict) -> List[str]:
    """Extract core skills from text based on configuration."""
    # Convert text to lowercase for case-insensitive matching
    text = text.lower()
    
    # Core skills and their variations from config
    core_skills = {}
    for skill in core_skills_config:
        skill_lower = skill.lower()
        variations = []
        
        # Add base skill
        variations.append(skill_lower)
        
        # Add common variations
        if skill_lower == "react":
            variations.extend(["react.js", "reactjs"])
        elif skill_lower == "react native":
            variations.extend(["react-native", "reactnative"])
        elif skill_lower == "javascript":
            variations.extend(["js", "ecmascript"])
        elif skill_lower == "node.js":
            variations.extend(["nodejs", "node"])
            
        core_skills[skill_lower] = variations
    
    found_skills = set()
    
    # Check for each skill and its variations
    for skill, variations in core_skills.items():
        for variation in variations:
            if variation in text:
                found_skills.add(skill)
                break
                
    return list(found_skills)

def detect_remote(job: Dict) -> bool:
    """Detect if a job is remote friendly."""
    remote_indicators = [
        'remote',
        'work from home',
        'wfh',
        'virtual',
        'telecommute',
        'anywhere',
        'flexible location',
        'home office',
        'distributed team'
    ]
    
    # Check explicit remote flag
    if 'remote' in job:
        return bool(job['remote'])
        
    # Check location field
    if 'location' in job:
        location = job['location'].lower()
        for indicator in remote_indicators:
            if indicator in location:
                return True
                
    # Check title
    if 'title' in job:
        title = job['title'].lower()
        for indicator in remote_indicators:
            if indicator in title:
                return True
                
    # Check description
    if 'description' in job:
        desc = job['description'].lower()
        for indicator in remote_indicators:
            if indicator in desc:
                return True
                
    return False

def extract_email_from_text(text: str) -> str:
    """Extract email address from text."""
    if not text:
        return ''
        
    # Handle obfuscated email formats
    text = text.replace(' [at] ', '@')
    text = text.replace(' (at) ', '@')
    text = text.replace('[at]', '@')
    text = text.replace('(at)', '@')
    text = text.replace(' [dot] ', '.')
    text = text.replace(' (dot) ', '.')
    text = text.replace('[dot]', '.')
    text = text.replace('(dot)', '.')
    
    # Look for email patterns
    email_pattern = r'[\w\.-]+(?:\s*(?:@|\[at\]|\(at\))\s*[\w\.-]+(?:\s*(?:\.|\[dot\]|\(dot\))\s*[\w\.-]+)+|\w+(?:\s*[.@]\s*|\s+(?:at|dot)\s+)\w+(?:\s*\.\s*\w+)*)'
    matches = re.findall(email_pattern, text.lower())
    
    if matches:
        # Clean up the found email
        email = matches[0]
        email = email.replace(' ', '')
        email = email.replace('at', '@')
        email = email.replace('dot', '.')
        return email
        
    return ''

def match_jobs(jobs: List[Dict], profile: Dict, db: Database) -> List[Dict]:
    """Match jobs with user profile based on core skills."""
    matched_jobs = []
    analyzer = PostAnalyzer()
    
    try:
        # Get profile preferences
        core_skills = profile.get('matching', {}).get('core_skills', [
            "react", "react native", "javascript", "node.js"
        ])
        min_match_score = profile.get('matching', {}).get('min_match_score', 25)
        remote_only = profile.get('matching', {}).get('remote_only', True)
        
        logger.info("\nStarting job matching process:")
        logger.info("=" * 50)
        logger.info(f"Looking for jobs with any of these skills: {', '.join(core_skills)}")
        logger.info(f"Remote only: {remote_only}")
        logger.info("-" * 50)
        
        for job in jobs:
            # Skip if no title or description
            if not job.get('title') or not job.get('description'):
                continue
                
            # Analyze job post
            job = analyzer.analyze(job)
            
            # Calculate match score
            match_score = 0
            found_skills = []
            
            # Check skills match
            description = job.get('description', '').lower()
            title = job.get('title', '').lower()
            
            for skill in core_skills:
                if skill.lower() in description or skill.lower() in title:
                    match_score += 25
                    found_skills.append(skill)
                    
            # Check remote match
            is_remote = job.get('remote', False)
            remote_match = not remote_only or is_remote
            if remote_match:
                match_score += 25
                
            # Check salary match (if provided)
            salary_min = job.get('salary_min')
            salary_max = job.get('salary_max')
            target_salary = profile.get('target_salary')
            
            salary_match = False
            if target_salary and salary_min and salary_max:
                target_min, target_max = map(float, target_salary.split('-'))
                if salary_min <= target_max and salary_max >= target_min:
                    match_score += 25
                    salary_match = True
                    
            # Add to matched jobs if score meets minimum
            if match_score >= min_match_score:
                # Log match details
                logger.info(f"\nAnalyzing job: {job.get('title')}")
                logger.info(f"Match score: {match_score}%")
                logger.info(f"Found skills: {', '.join(found_skills)}")
                logger.info(f"Remote match: {remote_match}")
                logger.info(f"Salary match: {salary_match}")
                
                # Add to database
                job_id = db.add_job(job)
                if job_id:
                    db.add_application(
                        job_id=job_id,
                        match_score=match_score,
                        method=job.get('application_method', 'unknown'),
                        status='pending'
                    )
                    matched_jobs.append(job)
                    
                logger.info(f"Application method: {job.get('application_method', 'unknown')}")
                logger.info("-" * 50)
                
        return matched_jobs
        
    except Exception as e:
        logger.error(f"Error matching jobs: {str(e)}")
        return []

def save_matches(matches: List[Dict], output_dir: str):
    """Save matched jobs to JSON file."""
    try:
        # Create output directory if it doesn't exist
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"matches_{timestamp}.json"
        filepath = output_path / filename
        
        # Save matches
        with open(filepath, 'w') as f:
            json.dump(matches, f, indent=2)
            
        logger.info(f"\nSaved {len(matches)} matches to {filepath}")
        
    except Exception as e:
        logger.error(f"Error saving matches: {str(e)}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Match jobs with user profile')
    parser.add_argument('--profile', default='config/profile.yaml', help='Path to profile YAML')
    parser.add_argument('--jobs-dir', default='data/jobs', help='Path to jobs directory')
    parser.add_argument('--output-dir', default='data/matches', help='Path to output directory')
    args = parser.parse_args()
    
    try:
        # Load profile and jobs
        profile = load_profile(args.profile)
        jobs = load_jobs(args.jobs_dir)
        
        if not jobs:
            logger.warning("No jobs found to process")
            return
            
        # Initialize database
        db = Database()
        
        # Match jobs
        matches = match_jobs(jobs, profile, db)
        
        # Save matches
        if matches:
            save_matches(matches, args.output_dir)
        else:
            logger.warning("No matches found")
            
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        raise

if __name__ == '__main__':
    main() 