#!/usr/bin/env python3
"""
Job Matching Script - Match jobs with user's profile
"""
import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

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

def extract_skills_from_text(text: str) -> List[str]:
    """Extract skills from text."""
    common_skills = [
        'python', 'javascript', 'typescript', 'react', 'node', 'aws',
        'docker', 'kubernetes', 'sql', 'nosql', 'mongodb', 'postgresql',
        'redis', 'kafka', 'elasticsearch', 'graphql', 'rest', 'api',
        'microservices', 'ci/cd', 'git', 'agile', 'scrum', 'java',
        'c++', 'go', 'rust', 'scala', 'ruby', 'php', 'html', 'css',
        'sass', 'less', 'webpack', 'babel', 'vue', 'angular', 'django',
        'flask', 'fastapi', 'spring', 'hibernate', 'junit', 'jest',
        'cypress', 'selenium', 'jenkins', 'terraform', 'ansible',
        'prometheus', 'grafana', 'datadog', 'newrelic', 'ai', 'ml',
        'machine learning', 'deep learning', 'nlp', 'computer vision',
        'data science', 'data engineering', 'etl', 'hadoop', 'spark',
        'airflow', 'dbt', 'tableau', 'power bi', 'looker', 'full stack',
        'frontend', 'backend', 'devops', 'sre', 'security'
    ]
    
    found_skills = set()
    text = text.lower()
    
    for skill in common_skills:
        if skill in text:
            found_skills.add(skill)
            
    return list(found_skills)

def match_jobs(jobs: List[Dict], profile: Dict) -> List[Dict]:
    """Match jobs with user profile."""
    matched_jobs = []
    
    try:
        # Get profile criteria
        required_skills = set(profile.get('skills', []))
        min_salary = profile.get('salary', {}).get('min', 0)
        max_salary = profile.get('salary', {}).get('max', float('inf'))
        preferred_remote = profile.get('preferences', {}).get('remote', True)
        
        logger.info("\nStarting job matching process:")
        logger.info("=" * 50)
        logger.info(f"Required skills: {', '.join(required_skills)}")
        logger.info(f"Salary range: ${min_salary:,} - {'∞' if max_salary == float('inf') else f'${max_salary:,}'}")
        logger.info(f"Remote preferred: {preferred_remote}")
        logger.info("-" * 50)
        
        for job in jobs:
            try:
                # Extract skills from job description and title
                job_skills = set()
                
                # From title
                if 'title' in job:
                    title_skills = extract_skills_from_text(job['title'])
                    job_skills.update(title_skills)
                
                # From description
                if 'description' in job:
                    desc_skills = extract_skills_from_text(job['description'])
                    job_skills.update(desc_skills)
                
                # From requirements
                if 'requirements' in job and isinstance(job['requirements'], list):
                    for req in job['requirements']:
                        req_skills = extract_skills_from_text(req)
                        job_skills.update(req_skills)
                
                # Calculate base match score from skills
                matched_skills = required_skills & job_skills
                match_score = len(matched_skills) / len(required_skills) if required_skills else 0
                
                # Boost score for remote jobs if preferred
                is_remote = False
                if 'remote' in job:
                    is_remote = job['remote']
                elif 'location' in job:
                    is_remote = 'remote' in job['location'].lower()
                
                if preferred_remote and is_remote:
                    match_score *= 1.2  # 20% boost for remote jobs
                
                # Check salary if available
                salary_match = False
                if 'salary_range' in job and job['salary_range']:
                    try:
                        # Try to extract salary from range string
                        salary_str = job['salary_range'].lower()
                        salary_str = ''.join(c for c in salary_str if c.isdigit() or c in '.-')
                        salary_parts = salary_str.split('-')
                        
                        if len(salary_parts) == 2:
                            job_min = float(salary_parts[0])
                            job_max = float(salary_parts[1])
                        else:
                            job_min = job_max = float(salary_parts[0])
                            
                        salary_match = (
                            min_salary <= job_max and
                            (max_salary == float('inf') or job_min <= max_salary)
                        )
                            
                    except Exception:
                        pass  # Skip salary matching if parsing fails
                
                # Add all jobs with their match information
                job['match_score'] = round(match_score * 100, 2)
                job['matched_skills'] = list(matched_skills)
                job['missing_skills'] = list(required_skills - job_skills)
                job['salary_match'] = salary_match
                job['remote_match'] = is_remote == preferred_remote
                job['application_status'] = 'pending'
                job['application_method'] = 'direct' if 'apply_url' in job else 'email'
                matched_jobs.append(job)
                
                # Log match details
                logger.info(f"\nAnalyzing job: {job.get('title', 'Unknown')}")
                logger.info(f"Match score: {job['match_score']}%")
                logger.info(f"Matched skills: {', '.join(matched_skills)}")
                logger.info(f"Missing skills: {', '.join(job['missing_skills'])}")
                logger.info(f"Remote match: {job['remote_match']}")
                logger.info(f"Salary match: {salary_match}")
                logger.info(f"Application method: {job['application_method']}")
                logger.info("-" * 50)
                    
            except Exception as e:
                logger.error(f"Error matching job {job.get('title', 'Unknown')}: {str(e)}")
                continue
                
        # Sort by match score
        matched_jobs.sort(key=lambda x: x['match_score'], reverse=True)
        
        # Log summary
        logger.info("\nMatching Summary:")
        logger.info("=" * 50)
        logger.info(f"Total jobs processed: {len(jobs)}")
        logger.info(f"Jobs matched: {len(matched_jobs)}")
        
        score_ranges = {
            "Excellent (80-100%)": 0,
            "Good (60-79%)": 0,
            "Fair (40-59%)": 0,
            "Poor (0-39%)": 0
        }
        
        for job in matched_jobs:
            if job['match_score'] >= 80:
                score_ranges["Excellent (80-100%)"] += 1
            elif job['match_score'] >= 60:
                score_ranges["Good (60-79%)"] += 1
            elif job['match_score'] >= 40:
                score_ranges["Fair (40-59%)"] += 1
            else:
                score_ranges["Poor (0-39%)"] += 1
                
        for range_name, count in score_ranges.items():
            logger.info(f"{range_name}: {count} jobs")
        
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
            report.append(f"Matched Skills: {', '.join(job['matched_skills'])}")
            if job['missing_skills']:
                report.append(f"Missing Skills: {', '.join(job['missing_skills'])}")
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