#!/usr/bin/env python3
"""
Job Matching Script - Match jobs with user's profile
"""
import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
import re

import yaml
from loguru import logger

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
    """Load jobs from JSON files."""
    jobs = []
    jobs_dir = Path(jobs_dir)
    
    try:
        for job_file in jobs_dir.glob("*.json"):
            try:
                with open(job_file, 'r') as f:
                    file_jobs = json.load(f)
                    if isinstance(file_jobs, list):
                        jobs.extend(file_jobs)
                    logger.debug(f"Loaded jobs from {job_file}")
            except Exception as e:
                logger.error(f"Error loading {job_file}: {str(e)}")
                continue
                
        logger.info(f"Loaded {len(jobs)} total jobs")
        return jobs
    except Exception as e:
        logger.error(f"Error loading jobs: {str(e)}")
        raise

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

def normalize_salary(salary_str: str) -> Tuple[float, float]:
    """Normalize salary string to monthly USD values."""
    try:
        # Remove non-numeric characters except digits, dots, and hyphens
        salary_str = ''.join(c for c in salary_str.lower() if c.isdigit() or c in '.-k')
        
        # Handle k notation (e.g. 150k)
        if 'k' in salary_str:
            salary_str = salary_str.replace('k', '000')
        
        # Split range
        if '-' in salary_str:
            min_str, max_str = salary_str.split('-')
            min_salary = float(min_str)
            max_salary = float(max_str)
        else:
            min_salary = max_salary = float(salary_str)
            
        # If values look like yearly salaries (>20000), convert to monthly
        if min_salary > 20000:
            min_salary /= 12
        if max_salary > 20000:
            max_salary /= 12
            
        return min_salary, max_salary
        
    except Exception:
        return 0, float('inf')

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

def match_jobs(jobs: List[Dict], profile: Dict) -> List[Dict]:
    """Match jobs with user profile based on core skills."""
    matched_jobs = []
    
    try:
        # Get profile preferences
        core_skills_config = profile.get('matching', {}).get('core_skills', [
            "react", "react native", "javascript", "node.js"
        ])
        
        logger.info("\nStarting job matching process:")
        logger.info("=" * 50)
        logger.info(f"Looking for jobs with any of these skills: {', '.join(core_skills_config)}")
        logger.info("Remote only: True")
        logger.info("-" * 50)
        
        for job in jobs:
            try:
                # Check if job is remote first - if not, skip it
                is_remote = detect_remote(job)
                if not is_remote:
                    continue
                
                # Extract skills from job description and title
                job_skills = set()
                
                # From title
                if 'title' in job:
                    title_skills = extract_core_skills_from_text(job['title'], core_skills_config)
                    job_skills.update(title_skills)
                
                # From description
                if 'description' in job:
                    desc_skills = extract_core_skills_from_text(job['description'], core_skills_config)
                    job_skills.update(desc_skills)
                    
                    # Extract email from description
                    if 'email' not in job or not job['email']:
                        job['email'] = extract_email_from_text(job['description'])
                
                # Calculate match score based on skills
                if job_skills:
                    # Base score is percentage of core skills found
                    score = len(job_skills) / len(core_skills_config)
                    
                    # Store match details
                    job['match_score'] = score * 100  # Convert to percentage
                    job['found_skills'] = list(job_skills)
                    job['remote'] = is_remote
                    
                    # Log job details
                    logger.info("\nAnalyzing job: {}".format(job.get('title', 'Unknown')))
                    logger.info("Match score: {:.1f}%".format(job['match_score']))
                    logger.info("Found skills: {}".format(', '.join(job['found_skills'])))
                    logger.info("Remote match: {}".format(job['remote']))
                    
                    # Add salary info if available
                    if 'salary' in job:
                        min_salary, max_salary = normalize_salary(job['salary'])
                        job['salary_min'] = min_salary
                        job['salary_max'] = max_salary
                        logger.info("Salary match: {}".format(bool(min_salary)))
                    else:
                        logger.info("Salary match: False")
                    
                    # Determine application method
                    if job.get('email'):
                        job['application_method'] = 'email'
                    elif 'linkedin.com' in job.get('url', '').lower():
                        job['application_method'] = 'linkedin'
                    else:
                        job['application_method'] = 'unknown'
                    logger.info("Application method: {}".format(job['application_method']))
                    
                    logger.info("-" * 50)
                    
                    # Add to matched jobs if score is high enough
                    if score >= 0.3:  # 30% match threshold
                        matched_jobs.append(job)
                        
            except Exception as e:
                logger.error(f"Error processing job: {str(e)}")
                continue
                
        logger.info(f"\nFound {len(matched_jobs)} matching jobs")
        return matched_jobs
        
    except Exception as e:
        logger.error(f"Error matching jobs: {str(e)}")
        raise

def save_matches(matched_jobs: List[Dict], output_dir: str):
    """Save matched jobs to file."""
    try:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save matches
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        matches_file = output_dir / f"matches_{timestamp}.json"
        
        with open(matches_file, 'w') as f:
            json.dump(matched_jobs, f, indent=2)
            
        logger.info(f"Saved {len(matched_jobs)} matches to {matches_file}")
        
        # Generate report
        report = []
        report.append("Job Matching Report")
        report.append("=" * 30)
        report.append(f"\nTotal Matches: {len(matched_jobs)}")
        
        # Group by match score ranges
        score_ranges = {
            "Excellent (80-100%)": [],
            "Good (60-79%)": [],
            "Fair (40-59%)": [],
            "Poor (0-39%)": []
        }
        
        for job in matched_jobs:
            if job['match_score'] >= 80:
                score_ranges["Excellent (80-100%)"].append(job)
            elif job['match_score'] >= 60:
                score_ranges["Good (60-79%)"].append(job)
            elif job['match_score'] >= 40:
                score_ranges["Fair (40-59%)"].append(job)
            else:
                score_ranges["Poor (0-39%)"].append(job)
        
        report.append("\nMatches by Score Range:")
        for range_name, jobs in score_ranges.items():
            report.append(f"\n{range_name}: {len(jobs)} jobs")
            
        report.append("\nDetailed Job Matches:")
        for job in matched_jobs:
            report.append(f"\n{job['title']} at {job['company']}")
            report.append(f"Match Score: {job['match_score']}%")
            report.append(f"Location: {job['location']}")
            if job.get('salary_range'):
                report.append(f"Salary Range: {job['salary_range']}")
            report.append(f"Remote: {'Yes' if job.get('remote') else 'No'}")
            report.append(f"Matched Skills: {', '.join(job['found_skills'])}")
            report.append(f"Application Method: {job['application_method']}")
            report.append(f"URL: {job['url']}\n")
            
        report_file = output_dir / f"matches_report_{timestamp}.txt"
        with open(report_file, 'w') as f:
            f.write('\n'.join(report))
            
        logger.info(f"Saved matching report to {report_file}")
        
    except Exception as e:
        logger.error(f"Error saving matches: {str(e)}")
        raise

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Match jobs with user profile")
    
    parser.add_argument(
        "--profile",
        help="Path to user profile YAML file",
        default="config/profile.yaml"
    )
    
    parser.add_argument(
        "--jobs-dir",
        help="Directory containing job JSON files",
        default="data/jobs"
    )
    
    parser.add_argument(
        "--output-dir",
        help="Output directory for matched jobs",
        default="data/matches"
    )
    
    args = parser.parse_args()
    
    try:
        # Load profile and jobs
        profile = load_profile(args.profile)
        jobs = load_jobs(args.jobs_dir)
        
        # Match jobs with profile
        matched_jobs = match_jobs(jobs, profile)
        
        # Save results
        save_matches(matched_jobs, args.output_dir)
        
    except KeyboardInterrupt:
        logger.info("Matching stopped by user")
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    main() 