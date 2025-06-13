#!/usr/bin/env python3
"""
Job Search Script - Search for jobs across multiple platforms
"""
import argparse
import asyncio
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import yaml
from loguru import logger

from app.job_search import JobSearcher
from app.job_search.models import JobPosting

def load_config(config_dir: str) -> Dict:
    """Load configuration from YAML file."""
    config_path = os.path.join(config_dir, "profile.yaml")
    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error loading config: {str(e)}")
        return {}

def get_search_terms(profile: Dict) -> Dict:
    """Extract search terms from profile."""
    search_terms = {
        "keywords": ["software engineer", "developer", "python", "typescript", "react", "full stack"],
        "location": profile.get("location", "Remote"),
        "min_salary_monthly": None,
        "max_salary_monthly": None,
        "core_technologies": []
    }
    
    # Add skills to keywords
    if "skills" in profile:
        search_terms["keywords"].extend(profile["skills"])
        
    # Add salary preferences
    if "salary" in profile:
        salary = profile["salary"]
        if isinstance(salary, dict):
            search_terms["min_salary_monthly"] = salary.get("min_monthly")
            search_terms["max_salary_monthly"] = salary.get("max_monthly")
        elif isinstance(salary, (int, float)):
            # If single value, use as minimum
            search_terms["min_salary_monthly"] = salary
            
    # Add core technologies
    if "core_technologies" in profile:
        search_terms["core_technologies"] = profile["core_technologies"]
            
    return search_terms

def filter_jobs_by_salary(jobs: List[JobPosting], min_monthly: float = None, max_monthly: float = None) -> List[JobPosting]:
    """Filter jobs by salary range."""
    if not min_monthly and not max_monthly:
        return jobs
        
    filtered_jobs = []
    for job in jobs:
        # Get job salary range
        job_min = job.salary_min
        job_max = job.salary_max
        
        if not job_min or not job_max:
            continue
            
        # Convert yearly to monthly
        job_min_monthly = job_min / 12
        job_max_monthly = job_max / 12
        
        # Check if job salary range overlaps with desired range
        if min_monthly and job_max_monthly < min_monthly:
            continue
        if max_monthly and job_min_monthly > max_monthly:
            continue
            
        filtered_jobs.append(job)
        
    return filtered_jobs

def filter_jobs_by_core_technologies(jobs: List[JobPosting], core_technologies: List[str]) -> List[JobPosting]:
    """Filter jobs that contain at least one core technology."""
    if not core_technologies:
        return jobs
        
    filtered_jobs = []
    for job in jobs:
        description = job.description.lower()
        title = job.title.lower()
        requirements = [req.lower() for req in job.requirements]
        
        # Check if any core technology is mentioned in description, title or requirements
        for tech in core_technologies:
            tech = tech.lower()
            if (tech in description or 
                tech in title or 
                any(tech in req for req in requirements)):
                filtered_jobs.append(job)
                break
                
    return filtered_jobs

def save_jobs(jobs: List[JobPosting], output_dir: str):
    """Save jobs to file."""
    try:
        # Create output directory if it doesn't exist
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save jobs
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        jobs_file = output_dir / f"jobs_{timestamp}.json"
        
        with open(jobs_file, "w") as f:
            json.dump([job.to_dict() for job in jobs], f, indent=2)
            
        logger.info(f"Saved {len(jobs)} jobs to {jobs_file}")
        
    except Exception as e:
        logger.error(f"Error saving jobs: {str(e)}")
        raise

async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Search for jobs")
    
    parser.add_argument(
        "--config-dir",
        help="Configuration directory",
        default="config"
    )
    
    parser.add_argument(
        "--output-dir",
        help="Output directory for job results",
        default="data/jobs"
    )
    
    args = parser.parse_args()
    
    try:
        # Load configuration
        profile = load_config(args.config_dir)
        if not profile:
            return
            
        # Get search terms
        search_terms = get_search_terms(profile)
        
        # Initialize job searcher
        searcher = JobSearcher()
        
        # Search for jobs
        jobs = await searcher.search(
            keywords=search_terms["keywords"],
            location=search_terms["location"]
        )
        
        # Filter jobs by salary
        if search_terms["min_salary_monthly"] or search_terms["max_salary_monthly"]:
            jobs = filter_jobs_by_salary(
                jobs,
                min_monthly=search_terms["min_salary_monthly"],
                max_monthly=search_terms["max_salary_monthly"]
            )
            logger.info(f"Filtered to {len(jobs)} jobs within salary range")
            
        # Filter jobs by core technologies
        if search_terms["core_technologies"]:
            jobs = filter_jobs_by_core_technologies(
                jobs,
                core_technologies=search_terms["core_technologies"]
            )
            logger.info(f"Filtered to {len(jobs)} jobs with core technologies")
        
        # Save results
        save_jobs(jobs, args.output_dir)
        
    except KeyboardInterrupt:
        logger.info("Search stopped by user")
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 