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
from playwright.sync_api import sync_playwright

from app.automation.linkedin_applicator import LinkedInApplicator
from app.automation.indeed_applicator import IndeedApplicator
from app.automation.remotive_applicator import RemotiveApplicator
from app.automation.weworkremotely_applicator import WeWorkRemotelyApplicator
from app.automation.greenhouse_applicator import GreenhouseApplicator
from app.automation.cover_letter_generator import CoverLetterGenerator
from app.automation.email_generator import EmailGenerator
from app.automation.email_sender import EmailSender
from app.automation.job_matcher import JobMatcher
from app.automation.job_searcher import JobSearcher
from app.db.models import Application, Base, Job
from app.resume.parser import ResumeParser
from .base_applicator import BaseApplicator, ApplicationResult
from .email_applicator import EmailApplicator

class ApplicatorManager:
    """Manages job application automation across different platforms."""
    
    def __init__(self, config: Dict):
        """Initialize the manager."""
        self.config = config
        self.applicators: List[BaseApplicator] = []
        self.browser = None
        self.context = None
        
    async def setup(self):
        """Set up the browser and applicators."""
        try:
            # Start browser
            playwright = sync_playwright().start()
            self.browser = playwright.chromium.launch(headless=False)
            self.context = self.browser.new_context()
            
            # Initialize applicators
            self.applicators = [
                LinkedInApplicator(self.config),
                EmailApplicator(self.config)
            ]
            
            # Set browser context for each applicator
            for applicator in self.applicators:
                applicator.page = self.context.new_page()
                
            return True
            
        except Exception as e:
            logger.error(f"Error setting up applicator manager: {str(e)}")
            return False
            
    async def cleanup(self):
        """Clean up resources."""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
        except Exception as e:
            logger.error(f"Error cleaning up: {str(e)}")
            
    async def apply_to_job(self, job_data: Dict) -> ApplicationResult:
        """
        Apply to a job using the appropriate applicator.
        
        Args:
            job_data: Job data dictionary
            
        Returns:
            ApplicationResult object
        """
        try:
            # Ensure we're set up
            if not self.applicators:
                if not await self.setup():
                    raise Exception("Failed to set up applicator manager")
                    
            # Find suitable applicator
            applicator = await self._get_applicator(job_data.get('url', ''))
            if not applicator:
                return ApplicationResult(
                    company=job_data.get('company', 'Unknown'),
                    position=job_data.get('title', 'Unknown'),
                    url=job_data.get('url', ''),
                    platform=job_data.get('platform', 'Unknown'),
                    status='failed',
                    application_method='unknown',
                    direct_apply_status=False,
                    email_sent_status=False,
                    error_message='No suitable applicator found'
                )
                
            # Get resume path
            resume_path = self.config.get('resume_path', '')
            if not resume_path:
                raise Exception("Resume path not configured")
                
            # Apply to job
            result = await applicator.apply(
                job_data=job_data,
                resume_data={'resume_path': resume_path}
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error applying to job: {str(e)}")
            return ApplicationResult(
                company=job_data.get('company', 'Unknown'),
                position=job_data.get('title', 'Unknown'),
                url=job_data.get('url', ''),
                platform=job_data.get('platform', 'Unknown'),
                status='failed',
                application_method='unknown',
                direct_apply_status=False,
                email_sent_status=False,
                error_message=str(e)
            )
            
    async def _get_applicator(self, url: str) -> BaseApplicator:
        """Get the appropriate applicator for a job URL."""
        for applicator in self.applicators:
            try:
                if await applicator.is_applicable(url):
                    return applicator
            except Exception:
                continue
                
        return None

    def _load_config(self, config: Dict) -> Dict:
        """
        Load configuration.
        
        Args:
            config: Configuration dictionary or path to config file
            
        Returns:
            Configuration dictionary
        """
        try:
            # If config is already a dict, use it directly
            if isinstance(config, dict):
                return config
                
            # Otherwise treat it as a path
            config_path = Path(config)
            if not config_path.exists():
                raise FileNotFoundError(f"Config file not found: {config_path}")
                
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
                
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            raise
            
    def _init_database(self):
        """Initialize the SQLite database."""
        try:
            # Create database directory if needed
            db_path = self.config['storage']['applications_db']
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
                platform=job['platform'],
                platform_id=platform_id
            ).first()
            
            return existing is not None
            
        except Exception as e:
            logger.error(f"Error checking job status: {str(e)}")
            return False
            
    def _record_application(self, job: Dict, application_status: Dict):
        """Record application in database."""
        try:
            # Create job record
            job_record = Job(
                platform=job['platform'],
                platform_id=str(job.get('id', '')),
                title=job['title'],
                company=job['company'],
                location=job.get('location', 'Unknown'),
                url=job['url'],
                description=job.get('description', ''),
                requirements=', '.join(job.get('requirements', [])),
                salary_min=job.get('salary_min'),
                salary_max=job.get('salary_max'),
                remote=job.get('remote', False)
            )
            
            # Create application record
            application_record = Application(
                job=job_record,
                applied_at=datetime.now(),
                status=application_status.get('status', 'unknown'),
                error=application_status.get('error'),
                direct_apply=application_status.get('direct_apply', False),
                email_sent=application_status.get('email_sent', False)
            )
            
            # Save to database
            self.db_session.add(job_record)
            self.db_session.add(application_record)
            self.db_session.commit()
            
            logger.info(f"[RECORD] Application recorded for job: {job['title']}")
            
        except Exception as e:
            logger.error(f"Error recording application: {str(e)}")
            self.db_session.rollback() 