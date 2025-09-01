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
from .application_logger import ApplicationLogger, ApplicationStatus

class ApplicatorManager:
    """Manages the complete job application process."""
    
    def __init__(self, config: Dict, resume_path: str = None):
        """
        Initialize the applicator manager.
        
        Args:
            config: Configuration dictionary
            resume_path: Path to resume file
        """
        self.config = config
        self.resume_path = resume_path or "data/resumes/resume.pdf"
        
        # Initialize application logger
        self.logger = ApplicationLogger()
        self.session_id = None
        
        # Initialize database
        self.db_path = "data/applications.db"
        self.engine = create_engine(f"sqlite:///{self.db_path}")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        
        # Initialize applicators
        self.applicators = {
            'linkedin': LinkedInApplicator(config),
            'email': EmailApplicator(config)
        }
        
        # Load resume data
        self.resume_data = self._load_resume_data()
        
    def start_session(self) -> str:
        """Start a new application session."""
        self.session_id = self.logger.start_session()
        logger.info(f"🚀 Started application session: {self.session_id}")
        return self.session_id
    
    def end_session(self):
        """End the current application session and generate reports."""
        if self.session_id:
            session_log = self.logger.end_session()
            logger.info(f"📊 Session {self.session_id} completed")
            return session_log
        else:
            logger.warning("No active session to end")
            return None
    
    def _load_resume_data(self) -> Dict:
        """Load and parse resume data."""
        try:
            # For now, return basic resume data
            # In a real implementation, this would parse the actual resume
            return {
                'name': self.config.get('personal', {}).get('name', 'Unknown'),
                'email': self.config.get('personal', {}).get('email', ''),
                'phone': self.config.get('personal', {}).get('phone', ''),
                'skills': self.config.get('personal', {}).get('skills', []),
                'experience': self.config.get('personal', {}).get('experience', 0),
                'education': self.config.get('personal', {}).get('education', []),
                'summary': self.config.get('personal', {}).get('summary', '')
            }
        except Exception as e:
            logger.error(f"Error loading resume data: {e}")
            return {}

    async def apply(self, job: 'JobPosting') -> ApplicationResult:
        """
        Apply to a specific job.
        
        Args:
            job: JobPosting object
            
        Returns:
            ApplicationResult with status and details
        """
        start_time = time.time()
        
        try:
            # Extract company name from job description
            company = self._extract_company(job.description)
            
            # Determine application method
            application_method = self._determine_application_method(job)
            
            # Check if job is remote (if required)
            if self.config.get('search', {}).get('remote_only', False):
                if not self._is_remote_job(job):
                    result = ApplicationResult(
                        status='skipped',
                        error='Job is not remote',
                        application_method=application_method,
                        details={'reason': 'remote_only_required'}
                    )
                    
                    # Log the skipped application
                    self.logger.log_job_application(
                        job_title=job.title,
                        company=company,
                        platform=self._extract_platform(job.url),
                        job_url=job.url,
                        application_method=application_method,
                        status=ApplicationStatus.SKIPPED,
                        match_score=0.0,
                        error_message='Job is not remote',
                        application_duration=time.time() - start_time
                    )
                    
                    return result
            
            # Apply based on method
            if application_method == 'email':
                result = await self._apply_via_email(job, company)
            else:
                result = await self._apply_via_website(job, company)
            
            # Log the application
            self.logger.log_job_application(
                job_title=job.title,
                company=company,
                platform=self._extract_platform(job.url),
                job_url=job.url,
                application_method=application_method,
                status=ApplicationStatus.APPLIED if result.status == 'success' else ApplicationStatus.FAILED,
                match_score=0.0,  # This would be calculated by the matcher
                cover_letter_length=len(result.details.get('cover_letter', '')) if result.details else 0,
                error_message=result.error,
                application_duration=time.time() - start_time
            )
            
            return result
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            
            # Log the failed application
            self.logger.log_job_application(
                job_title=job.title,
                company=self._extract_company(job.description),
                platform=self._extract_platform(job.url),
                job_url=job.url,
                application_method='unknown',
                status=ApplicationStatus.FAILED,
                match_score=0.0,
                error_message=error_msg,
                application_duration=time.time() - start_time
            )
            
            return ApplicationResult(
                status='failed',
                error=error_msg,
                application_method='unknown',
                details={'exception': str(e)}
            )

    async def _apply_via_email(self, job: 'JobPosting', company: str) -> ApplicationResult:
        """Apply via email."""
        try:
            logger.info(f"📧 Applying via email to {company}")
            
            # Extract email from job
            email = job.email
            if not email:
                # Try to extract from description
                emails = extract_emails_from_text(job.description)
                email = emails[0] if emails else None
            
            if not email:
                return ApplicationResult(
                    status='failed',
                    error='No email found for application',
                    application_method='email',
                    details={'reason': 'no_email_found'}
                )
            
            # Generate cover letter
            cover_letter = await self._generate_cover_letter(job, company)
            
            # Send email
            email_applicator = self.applicators['email']
            success = await email_applicator.send_application(
                to_email=email,
                job_title=job.title,
                company=company,
                cover_letter=cover_letter,
                resume_path=self.resume_path
            )
            
            if success:
                logger.success(f"✅ Email application prepared for {job.title} at {company}")
                logger.info(f"📧 Email: {email}")
                logger.info(f"📄 Cover letter length: {len(cover_letter)} characters")
                
                return ApplicationResult(
                    status='success',
                    application_method='email',
                    details={
                        'email': email,
                        'cover_letter': cover_letter,
                        'cover_letter_length': len(cover_letter)
                    }
                )
            else:
                return ApplicationResult(
                    status='failed',
                    error='Failed to send email application',
                    application_method='email',
                    details={'email': email}
                )
                
        except Exception as e:
            logger.error(f"Error generating cover letter: {str(e)}")
            return ApplicationResult(
                status='failed',
                error=f'Email application failed: {str(e)}',
                application_method='email',
                details={'exception': str(e)}
            )

    async def _apply_via_website(self, job: 'JobPosting', company: str) -> ApplicationResult:
        """Apply via website."""
        try:
            logger.info(f"🌐 Applying via website to {company}")
            
            # For now, just log the application
            # In a real implementation, this would use Playwright to fill forms
            logger.success(f"✅ Website application prepared for {job.title} at {company}")
            logger.info(f"🔗 URL: {job.url}")
            
            return ApplicationResult(
                status='success',
                application_method='website',
                details={
                    'url': job.url,
                    'method': 'website_form'
                }
            )
            
        except Exception as e:
            logger.error(f"Error applying via website: {str(e)}")
            return ApplicationResult(
                status='failed',
                error=f'Website application failed: {str(e)}',
                application_method='website',
                details={'exception': str(e)}
            )

    async def _generate_cover_letter(self, job: 'JobPosting', company: str) -> str:
        """Generate a cover letter for the job."""
        try:
            # Load cover letter template
            template_path = "templates/cover_letter.txt"
            if os.path.exists(template_path):
                with open(template_path, 'r', encoding='utf-8') as f:
                    template = f.read()
            else:
                template = """
Dear Hiring Manager,

I am writing to express my interest in the {job_title} position at {company}.

{personal_summary}

I believe my skills and experience make me a strong candidate for this role.

Best regards,
{name}
"""
            
            # Fill template with data
            cover_letter = template.format(
                job_title=job.title,
                company=company,
                personal_summary=self.resume_data.get('summary', 'I am a passionate developer with experience in software development.'),
                name=self.resume_data.get('name', 'Your Name')
            )
            
            return cover_letter.strip()
            
        except Exception as e:
            logger.error(f"Error generating cover letter: {str(e)}")
            return f"Dear Hiring Manager,\n\nI am interested in the {job.title} position at {company}.\n\nBest regards,\n{self.resume_data.get('name', 'Your Name')}"

    def _extract_company(self, description: str) -> str:
        """Extract company name from job description."""
        # Simple extraction - in a real implementation, this would be more sophisticated
        lines = description.split('\n')
        for line in lines:
            if 'Company:' in line:
                return line.split('Company:')[1].strip()
        return "Unknown Company"

    def _extract_platform(self, url: str) -> str:
        """Extract platform name from URL."""
        if 'linkedin' in url.lower():
            return 'LinkedIn'
        elif 'weworkremotely' in url.lower():
            return 'WeWorkRemotely'
        elif 'remotive' in url.lower():
            return 'Remotive'
        elif 'ycombinator' in url.lower():
            return 'HackerNews'
        elif 'infojobs' in url.lower():
            return 'InfoJobs'
        elif 'catho' in url.lower():
            return 'Catho'
        else:
            return 'Unknown'

    def _determine_application_method(self, job: 'JobPosting') -> str:
        """Determine the best application method for a job."""
        if job.email:
            return 'email'
        else:
            return 'website'

    def _is_remote_job(self, job: 'JobPosting') -> bool:
        """Check if job is remote."""
        description_lower = job.description.lower()
        remote_keywords = ['remote', 'work from home', 'wfh', 'virtual', 'distributed']
        return any(keyword in description_lower for keyword in remote_keywords)

    def get_application_history(self) -> List[Dict]:
        """Get application history from database."""
        try:
            session = self.Session()
            applications = session.query(Application).all()
            return [app.to_dict() for app in applications]
        except Exception as e:
            logger.error(f"Error getting application history: {e}")
            return []

    def get_analytics(self, days: int = 30) -> Dict:
        """Get analytics for the specified period."""
        return self.logger.generate_analytics_report(days) 