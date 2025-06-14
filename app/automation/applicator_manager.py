"""
Application Manager Module

Coordinates the entire job application process:
1. Resume parsing
2. Job search and matching
3. Application submission
4. Email fallback
5. History tracking
"""
import os
import time
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import yaml

from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from playwright.async_api import async_playwright

from app.automation.linkedin_applicator import LinkedInApplicator
from app.automation.email_applicator import EmailApplicator
from app.db.models import Application, Base, Job
from app.utils.text_extractor import extract_emails_from_text
from .base_applicator import BaseApplicator, ApplicationResult

class ApplicatorManager:
    """Manages different job application methods."""
    
    def __init__(self, config: Dict = None):
        """Initialize the manager."""
        self.config = config or {}
        self.browser = None
        self.context = None
        self.page = None
        
    async def setup(self):
        """Set up the manager."""
        await self._initialize_browser()
        
    async def apply_to_job(self, job: Dict) -> ApplicationResult:
        """Apply to a job using the appropriate method."""
        try:
            # First, try to find email in the job data
            email = job.get('email')
            
            # If no email found, try to extract from description
            if not email:
                logger.info("No email found in job data, trying to extract from description...")
                description = job.get('description', '')
                title = job.get('title', '')
                company = job.get('company', '')
                
                # Try to extract email from all available text
                all_text = f"{title}\n{company}\n{description}"
                emails = extract_emails_from_text(all_text)
                
                if emails:
                    email = emails[0]  # Use the first found email
                    logger.info(f"Found email address: {email}")
                    job['email'] = email
                else:
                    logger.warning("No email address found in job description")
                    
                    # Try to find company domain from URL
                    url = job.get('url', '')
                    if url:
                        import re
                        domain_match = re.search(r'https?://(?:www\.)?([^/]+)', url)
                        if domain_match:
                            domain = domain_match.group(1)
                            # Try common email formats
                            potential_emails = [
                                f"jobs@{domain}",
                                f"careers@{domain}",
                                f"recruiting@{domain}",
                                f"hr@{domain}",
                                f"hiring@{domain}"
                            ]
                            logger.info(f"Trying common email formats with domain {domain}")
                            for potential_email in potential_emails:
                                # Here you might want to validate if the email exists
                                # For now, we'll use the first format as a fallback
                                email = potential_emails[0]
                                job['email'] = email
                                logger.info(f"Using fallback email address: {email}")
                                break
            
            if email:
                # Try email application
                email_applicator = EmailApplicator(self.config)
                result = await email_applicator.apply(job)
                
                if result.status == 'success':
                    return result
                    
                logger.warning(f"Email application failed: {result.error_message}")
            
            # If email application failed or no email found, try direct application
            if job.get('url', '').startswith('https://www.linkedin.com/'):
                logger.info("Trying LinkedIn direct application...")
                linkedin_applicator = LinkedInApplicator(self.config)
                return await linkedin_applicator.apply(job)
            
            # If we get here, no application method worked
            error_msg = "No valid application method found"
            if result and result.error_message:
                error_msg = result.error_message
                
            return ApplicationResult(
                status='failed',
                error=error_msg,
                application_method='unknown'
            )
            
        except Exception as e:
            logger.error(f"Error in application process: {str(e)}")
            return ApplicationResult(
                status='failed',
                error=str(e),
                application_method='unknown'
            )
            
    async def cleanup(self):
        """Clean up resources."""
        if self.browser:
            logger.info("Cleaning up browser resources...")
            await self.browser.close()
            self.browser = None
            self.context = None
            self.page = None
            
    async def _initialize_browser(self):
        """Initialize browser if not already initialized."""
        if not self.browser:
            logger.info("Initializing browser...")
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                headless=False,  # Make browser visible
                args=['--start-maximized'],  # Start maximized
                slow_mo=1000  # Add delay between actions for visibility
            )
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},  # Set viewport size
                record_video_dir=str(Path("./logs/videos"))  # Record videos
            )
            self.page = await self.context.new_page()
            logger.info("Browser initialized successfully")
            
    def _get_resume_data(self) -> Dict:
        """Get resume data from config."""
        resume_config = self.config.get('resume', {})
        return {
            'resume_path': self.config.get('resume_path', 'resume.pdf'),
            'first_name': resume_config.get('first_name', ''),
            'last_name': resume_config.get('last_name', ''),
            'email': resume_config.get('email', ''),
            'phone': resume_config.get('phone', ''),
            'experience_years': resume_config.get('experience_years', 5),
            'skills': resume_config.get('skills', []),
            'desired_salary': resume_config.get('desired_salary', ''),
            'willing_to_relocate': resume_config.get('willing_to_relocate', True),
            'willing_to_travel': resume_config.get('willing_to_travel', True)
        }
            
    def _init_database(self):
        """Initialize the SQLite database."""
        try:
            # Create database directory if needed
            db_path = self.config.get('storage', {}).get('applications_db', 'data/applications.db')
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            # Initialize database
            engine = create_engine(f"sqlite:///{db_path}")
            Base.metadata.create_all(engine)
            
            # Create session factory
            Session = sessionmaker(bind=engine)
            self.db_session = Session()
            
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            raise
            
    def _is_job_processed(self, job: Dict) -> bool:
        """Check if we've already processed this job."""
        try:
            # Get platform-specific ID
            platform_id = str(job.get('id', ''))  # Convert to string for consistency
            if not platform_id:
                # Try alternative ID fields
                platform_id = str(job.get('job_id', '')) or str(job.get('posting_id', ''))
                
            if not platform_id:
                logger.warning(f"[CHECK] No ID found for job: {job.get('title', 'Unknown')} ({job.get('platform', 'Unknown')})")
                return False
                
            # Check database
            existing = self.db_session.query(Job).filter_by(
                platform=job.get('platform', 'unknown'),
                url=job.get('url', '')
            ).first()
            
            return existing is not None
            
        except Exception as e:
            logger.error(f"Error checking job status: {str(e)}")
            return False
            
    def _record_application(self, job: Dict, application_status: Dict):
        """Record application in database."""
        try:
            # Create job record if it doesn't exist
            job_record = self.db_session.query(Job).filter_by(
                url=job.get('url', '')
            ).first()
            
            if not job_record:
                job_record = Job(
                    platform=job.get('platform', 'unknown'),
                    title=job.get('title', 'Unknown'),
                    company=job.get('company', 'Unknown'),
                    location=job.get('location', 'Unknown'),
                    url=job.get('url', ''),
                    description=job.get('description', ''),
                    remote=job.get('remote', False)
                )
                self.db_session.add(job_record)
            
            # Create application record
            application_record = Application(
                job=job_record,
                status=application_status.get('status', 'unknown'),
                error_message=application_status.get('error'),
                direct_apply_status=application_status.get('direct_apply', False),
                email_sent_status=application_status.get('email_sent', False)
            )
            self.db_session.add(application_record)
            self.db_session.commit()
            
        except Exception as e:
            logger.error(f"Error recording application: {str(e)}")
            self.db_session.rollback() 