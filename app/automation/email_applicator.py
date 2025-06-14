"""Email-based job applicator."""
from typing import Dict, List
import asyncio
from pathlib import Path
import yagmail
from loguru import logger

from .base_applicator import BaseApplicator, ApplicationResult

class EmailApplicator(BaseApplicator):
    """Handles job applications via email."""
    
    def __init__(self, config: Dict):
        """Initialize the applicator."""
        super().__init__(config)  # Call parent class init
        self.yag = None
        
    async def is_applicable(self, url: str) -> bool:
        """Check if this applicator can handle the given URL.
        Email applicator is always applicable as it's our fallback method.
        """
        return True
        
    async def login_if_needed(self) -> bool:
        """Set up email client if not already done."""
        if self.yag is None:
            return self._setup_yagmail()
        return True
        
    def _setup_yagmail(self) -> bool:
        """Set up yagmail client."""
        try:
            email_config = self.config.get('application', {}).get('email', {})
            username = email_config.get('username')
            password = email_config.get('password')
            
            if not username or not password:
                logger.error("Missing email credentials")
                return False
                
            self.yag = yagmail.SMTP(username, password)
            return True
            
        except Exception as e:
            logger.error(f"Error setting up yagmail: {str(e)}")
            return False
            
    def _get_skills_text(self, resume_data: Dict) -> str:
        """Extract and format skills from resume data."""
        # Get skills as a list
        skills = resume_data.get('skills', [])
        
        # Handle different skill formats
        if isinstance(skills, str):
            skills = [s.strip() for s in skills.split(',')]
        elif isinstance(skills, dict):
            # If skills is a dict (from ResumeParser), flatten all categories
            all_skills = []
            for category_skills in skills.values():
                if isinstance(category_skills, list):
                    all_skills.extend(category_skills)
            skills = all_skills
        elif not isinstance(skills, list):
            skills = []
            
        # Get the first 3 skills or use defaults
        if not skills:
            skills = ['software development', 'problem solving', 'team collaboration']
        
        top_skills = skills[:3]
        return ', '.join(top_skills)
            
    def _generate_email_body(self, job: Dict, resume_data: Dict) -> str:
        """Generate email body."""
        logger.info("Generating email content...")
        
        # Get skills text
        skills_text = self._get_skills_text(resume_data)
        
        # Get name components safely
        first_name = resume_data.get('first_name', '')
        last_name = resume_data.get('last_name', '')
        
        # Try alternate name fields if first/last not found
        if not first_name and not last_name:
            full_name = resume_data.get('name', '').strip()
            if full_name:
                name_parts = full_name.split()
                if len(name_parts) >= 2:
                    first_name = name_parts[0]
                    last_name = ' '.join(name_parts[1:])
                else:
                    first_name = full_name
        
        full_name = f"{first_name} {last_name}".strip()
        if not full_name:
            full_name = "Job Applicant"  # Fallback
        
        # Get job details safely
        job_title = job.get('title', 'the open position')
        company_name = job.get('company', 'your company')
        
        # Get experience years safely
        experience_years = resume_data.get('experience_years') or resume_data.get('years_of_experience', 'several')
        
        body = f"""Dear Hiring Manager,

I am writing to express my interest in the {job_title} position at {company_name}.

With {experience_years} years of experience in software development, I believe I would be a great fit for this role. My key skills include {skills_text}.

I would welcome the opportunity to discuss how my background aligns with your needs.

Best regards,
{full_name}"""

        return body
            
    async def apply(self, job: Dict, resume_data: Dict) -> ApplicationResult:
        """Apply to job by sending an email."""
        try:
            # Log job details
            logger.info(f"\nPreparing email application for:")
            logger.info(f"Company: {job.get('company', 'Unknown')}")
            logger.info(f"Position: {job.get('title', 'Unknown')}")
            logger.info(f"Job URL: {job.get('url', 'No URL')}")
            
            # Get recipient email
            to_email = job.get('email')
            if not to_email:
                error_msg = "No recipient email found in job data"
                logger.error(error_msg)
                return ApplicationResult(
                    status='failed',
                    error=error_msg,
                    application_method='email'
                )
            
            logger.info(f"Sending application to: {to_email}")
            
            # Set up yagmail
            if not await self.login_if_needed():
                return ApplicationResult(
                    status='failed',
                    error='Failed to set up email client',
                    application_method='email'
                )
            
            # Generate email body
            body = self._generate_email_body(job, resume_data)
            
            # Prepare attachments
            attachments = []
            resume_path = self.config.get('application', {}).get('email', {}).get('resume_path')
            if resume_path and Path(resume_path).exists():
                logger.info(f"Attaching resume from: {resume_path}")
                attachments.append(resume_path)
            else:
                logger.warning(f"Resume not found at path: {resume_path}")
            
            # Send email
            subject = f"Application for {job.get('title')} position"
            try:
                self.yag.send(
                    to=to_email,
                    subject=subject,
                    contents=body,
                    attachments=attachments
                )
                logger.success(f"✅ Email sent successfully to {to_email}")
                return ApplicationResult(
                    status='success',
                    application_method='email'
                )
            except Exception as e:
                error_msg = f"Failed to send email: {str(e)}"
                logger.error(error_msg)
                return ApplicationResult(
                    status='failed',
                    error=error_msg,
                    application_method='email'
                )
            
        except Exception as e:
            error_msg = f"Unexpected error in email application: {str(e)}"
            logger.error(error_msg)
            return ApplicationResult(
                status='failed',
                error=error_msg,
                application_method='email'
            ) 