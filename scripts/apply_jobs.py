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
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from app.automation.applicator_manager import ApplicatorManager
from app.automation.application_logger import ApplicationLogger
from app.db.database import Database
from app.utils.text_extractor import extract_emails_from_text

import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

def load_config() -> Dict:
    """Load configuration from config file."""
    try:
        config_path = Path("config/config.yaml")
        if not config_path.exists():
            logger.error("Configuration file not found")
            return {}
            
        with open(config_path) as f:
            return yaml.safe_load(f)
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
        
        # Save updated config
        with open("config/config.yaml", 'w') as f:
            yaml.dump(config, f)
            
        return matches
        
    except Exception as e:
        logger.error(f"Error loading matches: {str(e)}")
        return []

def load_resume(resume_path: str) -> str:
    """Load resume content."""
    try:
        with open(resume_path, 'r') as f:
            resume = f.read()
        logger.info("Loaded resume")
        return resume
    except Exception as e:
        logger.error(f"Error loading resume: {str(e)}")
        raise

def save_results(results: List[Dict], output_dir: str):
    """
    Save application results.
    
    Args:
        results: List of application results
        output_dir: Directory to save results in
    """
    try:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = output_dir / f"applications_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
            
        logger.info(f"Saved results to {results_file}")
        
        # Generate report
        report = []
        report.append("Job Application Results")
        report.append("=" * 30)
        
        # Count statistics
        total = len(results)
        successful = sum(1 for r in results if r.get('success', False))
        failed = sum(1 for r in results if not r.get('success', False))
        
        report.append(f"\nTotal Applications: {total}")
        report.append(f"Successful: {successful}")
        report.append(f"Failed: {failed}")
        
        report.append("\nDetailed Results:")
        for result in results:
            job_id = result.get('job_id', 'unknown')
            success = result.get('success', False)
            error = result.get('error', '')
            
            report.append(f"\nJob ID: {job_id}")
            report.append(f"Status: {'Success' if success else 'Failed'}")
            if error:
                report.append(f"Error: {error}")
            
        report_file = output_dir / f"applications_report_{timestamp}.txt"
        with open(report_file, 'w') as f:
            f.write('\n'.join(report))
            
        logger.info(f"Saved application report to {report_file}")
        
    except Exception as e:
        logger.error(f"Error saving results: {str(e)}")
        raise

def extract_application_info(job: Dict) -> Dict:
    """Extract application method and contact information from job data."""
    info = {
        "platform": job.get("platform", "unknown"),
        "method": "unknown",
        "emails": []
    }
    
    # Check for direct application URL
    if job.get("apply_url") or (job.get("url", "").startswith("https://www.linkedin.com/") or 
                               job.get("url", "").startswith("https://weworkremotely.com/")):
        info["method"] = "direct"
        
    # Check for email addresses
    description = job.get("description", "")
    title = job.get("title", "")
    company = job.get("company", "")
    
    # Try to extract email from all available text
    all_text = f"{title}\n{company}\n{description}"
    emails = extract_emails_from_text(all_text)
    
    if emails:
        info["method"] = "email"
        info["emails"] = emails
        
    # If no application method found, try to infer from URL
    if info["method"] == "unknown" and job.get("url"):
        url = job.get("url", "").lower()
        if "linkedin.com" in url:
            info["method"] = "direct"
            info["platform"] = "linkedin"
        elif "weworkremotely.com" in url:
            info["method"] = "direct"
            info["platform"] = "weworkremotely"
        elif "github.com" in url:
            info["method"] = "direct"
            info["platform"] = "github"
        
    return info

async def apply_to_jobs(matches: List[Dict], config: Dict, resume_path: str) -> None:
    """Apply to matched jobs."""
    if not matches:
        logger.warning("No matches to apply to")
        return
        
    # Initialize database
    db = Database()
    
    # Initialize applicator manager
    manager = ApplicatorManager(config)
    await manager.setup()
    
    # Initialize logger
    app_logger = ApplicationLogger()
    
    logger.info("\nStarting application process")
    logger.info("=" * 50)
    logger.info(f"Processing {len(matches)} matches...")
    
    try:
        # First, add all matches to the database as pending applications
        for job in matches:
            # Skip if already in database
            if db.get_application_by_url(job["url"]):
                continue
                
            # Extract application info
            app_info = extract_application_info(job)
            
            # Add job to database
            db.add_application({
                "title": job["title"],
                "company": job["company"],
                "location": job["location"],
                "description": job["description"],
                "url": job["url"],
                "platform": app_info["platform"],
                "application_method": app_info["method"],
                "emails": app_info["emails"],
                "status": "pending",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            })
            
        # Now process pending applications
        pending = db.get_pending_applications()
        logger.info(f"Found {len(pending)} pending applications")
        
        for job in pending:
            logger.info(f"\nProcessing job: {job['title']}")
            logger.info("=" * 50)
            
            try:
                # Apply to job
                result = await manager.apply_to_job(job, resume_path)
                
                # Log result
                app_logger.log_application_attempt(job, result)
                
                # Update database
                if result["success"]:
                    db.update_application_status(job["url"], "applied")
                else:
                    db.update_application_status(job["url"], "failed", 
                                              error=result.get("error"))
                    
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

def generate_cover_letter(job: Dict, profile: Dict) -> str:
    """Generate a cover letter for the job."""
    try:
        company = job['company']
        title = job['title']
        matched_skills = job.get('matched_skills', [])
        
        # Get achievements that match the job
        achievements = []
        if 'application_preferences' in profile:
            all_achievements = profile['application_preferences'].get('highlight_achievements', [])
            for achievement in all_achievements:
                if any(skill.lower() in achievement.lower() for skill in matched_skills):
                    achievements.append(achievement)
        
        # Build cover letter
        paragraphs = []
        
        # Introduction
        paragraphs.append(f"Dear Hiring Manager at {company},")
        paragraphs.append(f"\nI am writing to express my strong interest in the {title} position at {company}. With over {profile.get('experience', {}).get('years', 7)} years of experience in software development and a proven track record in {', '.join(matched_skills[:3])}, I am confident in my ability to contribute significantly to your team.")
        
        # Experience and achievements
        if achievements:
            paragraphs.append("\nSome relevant achievements from my career include:")
            for achievement in achievements[:3]:
                paragraphs.append(f"- {achievement}")
        
        # Why this company
        paragraphs.append(f"\nI am particularly drawn to {company} because of its innovative approach to technology and commitment to excellence. My experience with {', '.join(matched_skills)} aligns perfectly with your requirements, and I am excited about the opportunity to contribute to your team's success.")
        
        # Closing
        paragraphs.append("\nThank you for considering my application. I look forward to discussing how my skills and experience can benefit your team.")
        
        paragraphs.append("\nBest regards,")
        paragraphs.append(profile.get('personal', {}).get('name', ''))
        
        return '\n'.join(paragraphs)
        
    except Exception as e:
        logger.error(f"Error generating cover letter: {str(e)}")
        raise

def send_application_email(job: Dict, profile: Dict, config: Dict):
    """Send application email."""
    try:
        # Get email configuration
        email_config = config.get('email', {})
        smtp_server = email_config.get('smtp_server')
        smtp_port = email_config.get('smtp_port')
        username = email_config.get('username')
        password = email_config.get('password')
        
        if not all([smtp_server, smtp_port, username, password]):
            raise ValueError("Missing email configuration")
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = username
        msg['To'] = job.get('email', '')
        msg['Subject'] = f"Application for {job['title']} position"
        
        # Add cover letter
        cover_letter = generate_cover_letter(job, profile)
        msg.attach(MIMEText(cover_letter, 'plain'))
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(username, password)
            server.send_message(msg)
            
        logger.info(f"Sent application email for {job['title']} at {job['company']}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending application email: {str(e)}")
        return False

def apply_via_website(job: Dict, profile: Dict, config: Dict):
    """Apply for job via website."""
    try:
        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        if config.get('browser', {}).get('user_agent'):
            chrome_options.add_argument(f"user-agent={config['browser']['user_agent']}")
            
        # Create driver
        driver = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(driver, config.get('browser', {}).get('timeout', 30))
        
        try:
            # Navigate to application page
            driver.get(job['apply_url'])
            
            # Wait for form to load
            form = wait.until(EC.presence_of_element_located((By.TAG_NAME, 'form')))
            
            # Fill common fields
            common_fields = {
                'name': profile.get('personal', {}).get('name', ''),
                'email': profile.get('personal', {}).get('email', ''),
                'phone': profile.get('personal', {}).get('phone', ''),
                'linkedin': profile.get('personal', {}).get('linkedin', ''),
                'github': profile.get('personal', {}).get('github', ''),
                'cover_letter': generate_cover_letter(job, profile)
            }
            
            # Try to fill fields
            for field_name, value in common_fields.items():
                try:
                    field = form.find_element(By.NAME, field_name)
                    field.send_keys(value)
                except:
                    continue
            
            # Submit form
            form.submit()
            
            # Wait for confirmation
            time.sleep(5)
            
            logger.info(f"Submitted application for {job['title']} at {job['company']}")
            return True
            
        finally:
            driver.quit()
            
    except Exception as e:
        logger.error(f"Error applying via website: {str(e)}")
        return False

def apply_for_jobs(jobs: List[Dict], profile: Dict, config: Dict) -> List[Dict]:
    """Apply for jobs."""
    try:
        for job in jobs:
            try:
                if job.get('application_status') != 'pending':
                    continue
                    
                success = False
                if job.get('application_method') == 'direct' and job.get('apply_url'):
                    success = apply_via_website(job, profile, config)
                elif job.get('application_method') == 'email' and job.get('email'):
                    success = send_application_email(job, profile, config)
                
                job['application_status'] = 'applied' if success else 'failed'
                if not success:
                    job['application_error'] = "Failed to submit application"
                    
                # Add delay between applications
                delay = config.get('application', {}).get('delay_between_apps', 30)
                time.sleep(delay)
                
            except Exception as e:
                job['application_status'] = 'failed'
                job['application_error'] = str(e)
                logger.error(f"Error applying for job: {str(e)}")
                continue
                
        return jobs
        
    except Exception as e:
        logger.error(f"Error in apply_for_jobs: {str(e)}")
        raise

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