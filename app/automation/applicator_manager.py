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
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import yaml

from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.automation.cover_letter_generator import CoverLetterGenerator
from app.automation.email_sender import EmailSender
from app.automation.job_matcher import JobMatcher
from app.automation.job_searcher import JobSearcher
from app.automation.platform_applicator import PlatformApplicator
from app.db.models import Application, Base, Job
from app.resume.parser import ResumeParser

class ApplicatorManager:
    """Manages the entire job application process."""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize the application manager."""
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize components
        self._init_database()
        self._init_components()
        
        # Track application counts
        self.applications_today = 0
        self.last_resume_update = 0
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info("Configuration loaded successfully")
            return config
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
            
    def _init_components(self):
        """Initialize all system components."""
        try:
            # Initialize resume parser
            self.resume_parser = ResumeParser()
            
            # Initialize job searcher for each platform
            self.job_searcher = JobSearcher(self.config['job_search']['platforms'])
            
            # Initialize job matcher
            self.job_matcher = JobMatcher(
                min_score=self.config['job_search']['matching']['min_score'],
                required_skills=self.config['job_search']['matching']['required_skills'],
                preferred_skills=self.config['job_search']['matching']['preferred_skills'],
                excluded_keywords=self.config['job_search']['matching']['excluded_keywords']
            )
            
            # Initialize cover letter generator
            self.cover_letter_generator = CoverLetterGenerator(
                api_key=self.config['api']['groq']['api_key'],
                model=self.config['api']['groq']['model']
            )
            
            # Initialize email sender
            self.email_sender = EmailSender(
                host=self.config['application']['email']['smtp_host'],
                port=self.config['application']['email']['smtp_port'],
                username=self.config['application']['email']['smtp_username'],
                password=self.config['application']['email']['smtp_password'],
                from_name=self.config['application']['email']['from_name'],
                from_email=self.config['application']['email']['from_email'],
                signature_path=self.config['application']['email']['signature']
            )
            
            # Initialize platform applicators
            self.platform_applicator = PlatformApplicator(
                linkedin_config=self.config['oauth']['linkedin'],
                indeed_config=self.config['oauth']['indeed']
            )
            
            logger.info("All components initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing components: {str(e)}")
            raise
            
    def run(self):
        """Run the main application loop."""
        try:
            while True:
                # Check if we need to update resume data
                self._update_resume_if_needed()
                
                # Reset daily application count if needed
                self._reset_daily_count_if_needed()
                
                # Search for new jobs
                new_jobs = self.job_searcher.search()
                
                # Process each new job
                for job in new_jobs:
                    self._process_job(job)
                    
                # Sleep before next iteration
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logger.info("Application manager stopped by user")
        except Exception as e:
            logger.error(f"Error in main loop: {str(e)}")
            raise
            
    def _update_resume_if_needed(self):
        """Update resume data if update interval has passed."""
        current_time = time.time()
        if current_time - self.last_resume_update > self.config['resume']['update_interval']:
            try:
                # Parse resume
                resume_data = self.resume_parser.parse(self.config['resume']['path'])
                
                # Update job matcher with new resume data
                self.job_matcher.update_resume_data(resume_data)
                
                self.last_resume_update = current_time
                logger.info("Resume data updated successfully")
            except Exception as e:
                logger.error(f"Error updating resume data: {str(e)}")
                
    def _reset_daily_count_if_needed(self):
        """Reset daily application count at midnight."""
        current_date = datetime.now().date()
        if not hasattr(self, 'last_reset_date') or self.last_reset_date < current_date:
            self.applications_today = 0
            self.last_reset_date = current_date
            logger.info("Daily application count reset")
            
    def _process_job(self, job: Dict):
        """Process a single job posting."""
        try:
            # Check if we've already processed this job
            if self._is_job_processed(job):
                return
                
            # Check if we've hit daily limit
            if self.applications_today >= self.config['job_search']['matching']['max_applications_per_day']:
                logger.info("Daily application limit reached")
                return
                
            # Calculate match score
            match_score = self.job_matcher.calculate_match(job)
            
            # Skip if below minimum score
            if match_score < self.config['job_search']['matching']['min_score']:
                logger.debug(f"Job {job['id']} skipped - low match score: {match_score}")
                return
                
            # Generate cover letter if enabled
            cover_letter = None
            if self.config['application']['cover_letter']['enabled']:
                cover_letter = self.cover_letter_generator.generate(job)
                
            # Try platform-specific application first
            application_successful = False
            if job['platform'] in ['linkedin', 'indeed']:
                try:
                    application_successful = self.platform_applicator.apply(
                        platform=job['platform'],
                        job_id=job['id'],
                        cover_letter=cover_letter
                    )
                except Exception as e:
                    logger.error(f"Error applying through platform: {str(e)}")
                    
            # Fall back to email if platform application failed
            if not application_successful and job.get('contact_email'):
                try:
                    self.email_sender.send_application(
                        to_email=job['contact_email'],
                        job_title=job['title'],
                        company_name=job['company'],
                        cover_letter=cover_letter,
                        resume_path=self.config['resume']['path']
                    )
                    application_successful = True
                except Exception as e:
                    logger.error(f"Error sending application email: {str(e)}")
                    
            # Record application in database
            if application_successful:
                self._record_application(job, match_score, cover_letter)
                self.applications_today += 1
                logger.info(f"Successfully applied to job {job['id']}")
                
        except Exception as e:
            logger.error(f"Error processing job {job['id']}: {str(e)}")
            
    def _is_job_processed(self, job: Dict) -> bool:
        """Check if we've already processed this job."""
        existing = self.db_session.query(Job).filter_by(
            platform=job['platform'],
            platform_id=job['id']
        ).first()
        return existing is not None
        
    def _record_application(self, job: Dict, match_score: float, cover_letter: Optional[str]):
        """Record application in database."""
        try:
            # Create job record
            job_record = Job(
                platform=job['platform'],
                platform_id=job['id'],
                title=job['title'],
                company=job['company'],
                location=job.get('location', ''),
                description=job['description'],
                url=job['url'],
                contact_email=job.get('contact_email'),
                match_score=match_score
            )
            self.db_session.add(job_record)
            
            # Create application record
            application = Application(
                job=job_record,
                applied_at=datetime.now(),
                cover_letter=cover_letter
            )
            self.db_session.add(application)
            
            # Save cover letter to file if present
            if cover_letter:
                cover_letter_dir = Path(self.config['storage']['cover_letters_dir'])
                cover_letter_dir.mkdir(parents=True, exist_ok=True)
                
                filename = f"{job['company']}_{job['id']}.txt"
                with open(cover_letter_dir / filename, 'w') as f:
                    f.write(cover_letter)
            
            self.db_session.commit()
            logger.info(f"Application recorded for job {job['id']}")
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error recording application: {str(e)}")
            raise 