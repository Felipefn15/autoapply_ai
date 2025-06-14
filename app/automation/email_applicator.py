"""Email-based job applicator."""
from typing import Dict
import asyncio
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

from loguru import logger

from .base_applicator import BaseApplicator, ApplicationResult

class EmailApplicator(BaseApplicator):
    """Handles job applications via email."""
    
    def __init__(self, config: Dict):
        """Initialize the applicator."""
        self.config = config
        
    async def is_applicable(self, url: str) -> bool:
        """Check if this applicator can handle the given URL."""
        # Email applicator is used when job has an email address
        return True
        
    async def login_if_needed(self) -> bool:
        """No login needed for email applications."""
        return True
        
    async def apply(self, job: Dict, resume_data: Dict) -> ApplicationResult:
        """Apply to job by sending an email."""
        try:
            # Get email configuration
            email_config = self.config.get('email', {})
            smtp_server = email_config.get('smtp_server')
            smtp_port = email_config.get('smtp_port')
            username = email_config.get('username')
            password = email_config.get('password')
            
            if not all([smtp_server, smtp_port, username, password]):
                raise ValueError("Missing email configuration")
            
            # Get recipient email
            to_email = job.get('email')
            if not to_email:
                raise ValueError("No recipient email found")
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = username
            msg['To'] = to_email
            msg['Subject'] = f"Application for {job['title']} position"
            
            # Generate email body
            body = self._generate_email_body(job, resume_data)
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach resume
            resume_path = self.config.get('resume_path')
            if resume_path and Path(resume_path).exists():
                with open(resume_path, 'rb') as f:
                    resume = MIMEApplication(f.read(), _subtype='pdf')
                    resume.add_header('Content-Disposition', 'attachment', filename='resume.pdf')
                    msg.attach(resume)
            else:
                logger.warning(f"Resume not found: {resume_path}")
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(username, password)
                server.send_message(msg)
            
            logger.success(f"Email sent successfully to {to_email}")
            return ApplicationResult(status='success')
            
        except Exception as e:
            logger.error(f"Error in email application: {str(e)}")
            return ApplicationResult(
                status='failed',
                error=str(e)
            )
            
    def _generate_email_body(self, job: Dict, resume_data: Dict) -> str:
        """Generate email body."""
        body = f"""Dear Hiring Manager,

I am writing to express my interest in the {job.get('title')} position at {job.get('company')}.

With {resume_data.get('experience_years', 'several')} years of experience in software development, I believe I would be a great fit for this role. My skills include {', '.join(resume_data.get('skills', [])[:3])}.

I would welcome the opportunity to discuss how my background aligns with your needs.

Best regards,
{resume_data.get('first_name', '')} {resume_data.get('last_name', '')}"""
        return body 