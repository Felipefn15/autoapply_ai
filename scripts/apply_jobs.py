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

from app.automation import BaseApplicator, LinkedInApplicator, EmailApplicator
from app.automation.application_logger import ApplicationLogger

def load_config(config_path: str) -> Dict:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to config file
        
    Returns:
        Configuration dictionary
    """
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            logger.info("Loaded configuration")
            return config
    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
        raise

def load_matches(matches_dir: str) -> List[Dict]:
    """Load matched jobs from JSON files."""
    matches = []
    matches_dir = Path(matches_dir)
    
    try:
        # Get most recent matches file
        latest_matches = sorted(matches_dir.glob("matches_*.json"))[-1]
        with open(latest_matches, "r") as f:
            matches = json.load(f)
            
        logger.info(f"Loaded {len(matches)} matches from {latest_matches}")
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

async def apply_to_jobs(matches: List[Dict], config: Dict, resume_path: str) -> None:
    """Apply to matched jobs."""
    if not matches:
        logger.warning("No matches to apply to")
        return
        
    # Initialize applicators
    applicators = [
        LinkedInApplicator(config),
        EmailApplicator(config)
    ]
    
    # Initialize logger
    app_logger = ApplicationLogger()
    
    logger.info("\nStarting application process")
    logger.info("=" * 50)
    logger.info(f"Processing {len(matches)} matches...")
    
    for job in matches:
        logger.info(f"\nProcessing job: {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}")
        
        # Try each applicator
        applied = False
        for applicator in applicators:
            try:
                if await applicator.is_applicable(job.get('url', '')):
                    # Try to apply
                    result = await applicator.apply(job, {"resume_path": resume_path})
                    applied = result.status == "success"
                    if applied:
                        break
                        
            except Exception as e:
                logger.error(f"Error with {applicator.__class__.__name__}: {str(e)}")
                continue
                
        if not applied:
            logger.warning("No suitable applicator found or all attempts failed")
            app_logger.log_application(
                job=job,
                status="failed",
                method="unknown",
                error="No suitable applicator found or all attempts failed"
            )
    
    # Show final summary
    summary = app_logger.get_summary()
    
    logger.info("\nApplication Summary")
    logger.info("=" * 50)
    logger.info(f"Total jobs processed: {summary['total']}")
    logger.info(f"Successfully applied: {summary['successful']}")
    logger.info(f"Failed applications: {summary['failed']}")
    logger.info(f"Skipped applications: {summary['skipped']}")
    logger.info(f"Success rate: {summary['success_rate']:.1f}%")
    
    # Indicate where to find detailed logs
    logger.info("\nDetailed logs saved to:")
    logger.info(f"- JSON: data/applications/applications_{app_logger.current_session}.json")
    logger.info(f"- Report: data/applications/applications_report_{app_logger.current_session}.txt")

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

async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Apply to matched jobs")
    
    parser.add_argument(
        "--config",
        help="Configuration file",
        default="config/config.yaml"
    )
    
    parser.add_argument(
        "--resume",
        help="Resume file path",
        required=True
    )
    
    parser.add_argument(
        "--matches-dir",
        help="Directory containing job matches",
        default="data/matches"
    )
    
    args = parser.parse_args()
    
    try:
        # Load matches
        matches = load_matches(args.matches_dir)
        if not matches:
            return
            
        # Apply to jobs
        await apply_to_jobs(matches, {}, args.resume)
        
    except KeyboardInterrupt:
        logger.info("Application process stopped by user")
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 