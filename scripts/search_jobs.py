#!/usr/bin/env python3
"""
Job Search Script - Search for jobs across multiple platforms
"""
import argparse
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import os
from dotenv import load_dotenv
import yaml

from loguru import logger

from app.job_search import JobSearcher
from app.job_search.models import JobPosting

def load_config(config_dir: str) -> Dict:
    """Load configuration from YAML and .env files."""
    try:
        # Load .env file
        load_dotenv()
        
        # Load YAML config
        config_file = Path(config_dir) / "config.yaml"
        if not config_file.exists():
            logger.error(f"Configuration file not found: {config_file}")
            return None
            
        with open(config_file) as f:
            config = yaml.safe_load(f)
            
        # Add environment variables to config
        config.update({
            'primary_skills': os.getenv('PRIMARY_SKILLS', '').split(','),
            'secondary_skills': os.getenv('SECONDARY_SKILLS', '').split(','),
            'location': {
                'country': os.getenv('COUNTRY'),
                'city': os.getenv('CITY'),
                'timezone': os.getenv('TIMEZONE')
            },
            'remote_only': os.getenv('REMOTE_ONLY', 'true').lower() == 'true'
        })
            
        return config
            
    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
        return None

def get_search_terms(profile: Dict) -> List[str]:
    """Get search terms from profile."""
    keywords = []
    
    # Add primary skills
    if 'primary_skills' in profile:
        keywords.extend(profile['primary_skills'])
    
    # Add secondary skills
    if 'secondary_skills' in profile:
        keywords.extend(profile['secondary_skills'])
            
    # Add default keywords if none found
    if not keywords:
        keywords = ["software engineer", "developer", "python", "typescript", "react"]
            
    return keywords

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

def print_job_summary(jobs: List[JobPosting]):
    """Print a summary of the jobs found."""
    print("\nJobs found:")
    print("=" * 80)
    
    for i, job in enumerate(jobs, 1):
        print(f"\n{i}. {job.title}")
        print(f"   URL: {job.url}")
        if job.email:
            print(f"   Contact: {job.email}")
        print("-" * 80)

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
        default=os.getenv('OUTPUT_PATH', 'data/jobs')
    )
    
    args = parser.parse_args()
    
    try:
        # Load configuration
        profile = load_config(args.config_dir)
        if not profile:
            return
            
        # Get search terms
        keywords = get_search_terms(profile)
        
        # Initialize job searcher
        searcher = JobSearcher()
        
        # Search for jobs
        jobs = await searcher.search(keywords=keywords)
        
        # Print job summary
        print_job_summary(jobs)
        
        # Save results
        save_jobs(jobs, args.output_dir)
        
    except KeyboardInterrupt:
        logger.info("Search stopped by user")
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 