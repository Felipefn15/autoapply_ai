#!/usr/bin/env python3
"""
Job Application Script - Apply to matched jobs or send emails
"""
import argparse
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from loguru import logger

from app.automation.applicator_manager import ApplicatorManager
from app.automation.application_logger import ApplicationLogger
from app.db.database import Database

def load_config() -> Dict:
    """Load configuration from config file."""
    try:
        config_path = Path("config/config.yaml")
        if not config_path.exists():
            logger.error("Configuration file not found")
            return {}
            
        with open(config_path) as f:
            config = yaml.safe_load(f)
            
        # Add personal info from profile
        profile_path = Path("config/profile.yaml")
        if profile_path.exists():
            with open(profile_path) as f:
                profile = yaml.safe_load(f)
                config['personal'] = profile.get('personal', {})
                
        return config
    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
        return {}

def load_jobs() -> List[Dict]:
    """Load matched jobs from the matches directory."""
    try:
        # Get matches directory from command line arguments
        parser = argparse.ArgumentParser()
        parser.add_argument('--matches-dir', type=str, required=True, help='Directory containing matched jobs')
        parser.add_argument('--resume', type=str, required=True, help='Path to resume PDF')
        args = parser.parse_args()
        
        matches_dir = Path(args.matches_dir)
        if not matches_dir.exists():
            logger.error(f"Matches directory not found: {matches_dir}")
            return []
            
        # Find the most recent matches file
        matches_files = list(matches_dir.glob("matches_*.json"))
        if not matches_files:
            logger.error("No matches files found")
            return []
            
        latest_matches_file = max(matches_files, key=lambda x: x.stat().st_mtime)
        logger.info(f"Loading matches from: {latest_matches_file}")
        
        # Load matches
        with open(latest_matches_file) as f:
            matches = json.load(f)
            
        if not matches:
            logger.warning("No matches found in file")
            return []
            
        # Update config with resume path
        config = load_config()
        config['resume_path'] = args.resume
        
        return matches
        
    except Exception as e:
        logger.error(f"Error loading matches: {str(e)}")
        return []

async def apply_to_jobs(matches: List[Dict], config: Dict, resume_path: str) -> None:
    """Apply to matched jobs."""
    if not matches:
        logger.warning("No matches to apply to")
        return
        
    # Initialize database
    db = Database()
    
    # Initialize applicator manager
    manager = ApplicatorManager(config)
    
    # Initialize logger
    app_logger = ApplicationLogger()
    
    logger.info("\nStarting application process")
    logger.info("=" * 50)
    logger.info(f"Processing {len(matches)} matches...")
    
    try:
        # Process each job
        for i, job in enumerate(matches, 1):
            logger.info(f"\nProcessing job {i}/{len(matches)}")
            logger.info(f"Title: {job.get('title', 'Unknown Position')}")
            logger.info(f"Company: {job.get('company', 'Unknown Company')}")
            logger.info(f"URL: {job.get('url', 'No URL')}")
            logger.info("-" * 50)
            
            try:
                # Apply to job
                result = await manager.apply(job)
                
                # Log result
                app_logger.log_application_attempt(job, result)
                
                # Update database
                if result.status == 'success':
                    db.update_application_status(job["url"], "applied")
                    logger.success(f"✅ Successfully applied to {job.get('title')} at {job.get('company')}")
                else:
                    db.update_application_status(job["url"], "failed", 
                                              error=result.error)
                    logger.error(f"❌ Failed to apply: {result.error}")
                    
            except Exception as e:
                logger.error(f"Failed to apply to job: {e}")
                db.update_application_status(job["url"], "failed", 
                                          error=str(e))
                
            # Sleep between applications
            await asyncio.sleep(2)
            
    finally:
        await manager.cleanup()

    # Show final summary
    summary = app_logger.get_summary()
    
    logger.info("\nApplication Summary")
    logger.info("=" * 50)
    logger.info(f"Total jobs processed: {summary['total']}")
    logger.info(f"Successfully applied: {summary['successful']}")
    logger.info(f"Failed applications: {summary['failed']}")
    logger.info(f"Skipped applications: {summary['skipped']}")
    logger.info(f"Success rate: {summary['success_rate']}%")
    
    # Save logs
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = Path("data/applications")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Save JSON log
    json_path = log_dir / f"applications_{timestamp}.json"
    with open(json_path, 'w') as f:
        json.dump(app_logger.get_logs(), f, indent=2)
    logger.info(f"\nDetailed logs saved to:")
    logger.info(f"- JSON: {json_path}")
    
    # Save report
    report_path = log_dir / f"applications_report_{timestamp}.txt"
    with open(report_path, 'w') as f:
        f.write(app_logger.get_report())
    logger.info(f"- Report: {report_path}")

async def run_script():
    """Run the job application script."""
    try:
        logger.info("\nStarting job application process")
        logger.info("=" * 50)
        
        # Load configuration
        config = load_config()
        if not config:
            raise ValueError("Failed to load configuration")
            
        # Load jobs data
        jobs = load_jobs()
        if not jobs:
            raise ValueError("No jobs found to process")
            
        logger.info(f"\nFound {len(jobs)} jobs to process")
        logger.info("=" * 50)
        
        # Initialize applicator manager
        manager = ApplicatorManager(config)
        
        # Process each job
        results = {
            'total': len(jobs),
            'success': 0,
            'failed': 0,
            'errors': {}
        }
        
        for i, job in enumerate(jobs, 1):
            try:
                logger.info(f"\nProcessing job {i}/{len(jobs)}")
                logger.info(f"Title: {job.get('title', 'Unknown Position')}")
                logger.info(f"Company: {job.get('company', 'Unknown Company')}")
                logger.info(f"URL: {job.get('url', 'No URL')}")
                logger.info("-" * 50)
                
                # Apply for job
                result = await manager.apply(job)
                
                # Update statistics
                if result.status == 'success':
                    results['success'] += 1
                    logger.success(f"✅ Successfully applied to {job.get('title')} at {job.get('company')}")
                else:
                    results['failed'] += 1
                    error_type = result.error.split(':')[0] if result.error else 'Unknown error'
                    results['errors'][error_type] = results['errors'].get(error_type, 0) + 1
                    logger.error(f"❌ Failed to apply: {result.error}")
                
                logger.info("=" * 50)
                
            except Exception as e:
                results['failed'] += 1
                error_type = str(e).split(':')[0]
                results['errors'][error_type] = results['errors'].get(error_type, 0) + 1
                logger.error(f"Error processing job: {str(e)}")
                continue
        
        # Print summary
        logger.info("\n📊 Application Process Summary")
        logger.info("=" * 50)
        logger.info(f"Total jobs processed: {results['total']}")
        logger.info(f"Successful applications: {results['success']} ({(results['success']/results['total'])*100:.1f}%)")
        logger.info(f"Failed applications: {results['failed']} ({(results['failed']/results['total'])*100:.1f}%)")
        
        if results['errors']:
            logger.info("\nCommon error types:")
            for error_type, count in sorted(results['errors'].items(), key=lambda x: x[1], reverse=True):
                logger.info(f"- {error_type}: {count} occurrences")
        
        logger.info("\n✨ Process completed!")
        
    except Exception as e:
        logger.error(f"Error running script: {str(e)}")
        raise
    finally:
        # Clean up resources
        if 'manager' in locals():
            await manager.cleanup()

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Apply to matched jobs')
    parser.add_argument('--config', default='config/config.yaml', help='Path to config file')
    parser.add_argument('--matches-dir', default='data/matches', help='Directory containing match files')
    parser.add_argument('--resume', required=True, help='Path to resume PDF')
    args = parser.parse_args()
    
    try:
        # Load config
        config = load_config()
        
        # Load most recent matches file
        matches_dir = Path(args.matches_dir)
        match_files = sorted(matches_dir.glob('matches_*.json'))
        if not match_files:
            logger.error("No match files found")
            return
            
        with open(match_files[-1], 'r') as f:
            matches = json.load(f)
            
        # Update resume path in config
        config['resume_path'] = args.resume
        
        # Run application process
        asyncio.run(apply_to_jobs(matches, config, args.resume))
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise

if __name__ == '__main__':
    asyncio.run(run_script()) 