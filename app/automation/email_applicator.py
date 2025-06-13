"""Email-based job applicator."""
from typing import Dict
import asyncio
from pathlib import Path

from loguru import logger

from .base_applicator import BaseApplicator, ApplicationResult
from .email_generator import generate_email
from .email_sender import EmailSender

class EmailApplicator(BaseApplicator):
    """Handles job applications via email."""
    
    def __init__(self, config: Dict):
        """Initialize the applicator."""
        super().__init__(config)
        self.email_sender = EmailSender(config)
        
    async def is_applicable(self, url: str) -> bool:
        """Check if this applicator can handle the given URL."""
        # Email applicator is used as fallback when job has an email
        return bool(url and '@' in url)
        
    async def login_if_needed(self) -> bool:
        """No login needed for email applications."""
        return True
        
    async def apply(self, job_data: Dict, resume_data: Dict) -> ApplicationResult:
        """Apply to the job by sending an email."""
        try:
            # Generate email content
            email_content = generate_email(
                job_data=job_data,
                resume_data=resume_data
            )
            
            # Send email
            success = await self.email_sender.send_email(
                to_email=job_data.get('email', ''),
                subject=f"Application for {job_data.get('title', 'Position')}",
                body=email_content,
                attachments=[resume_data.get('resume_path', '')]
            )
            
            if success:
                return self.create_result(
                    job_data=job_data,
                    status='success',
                    notes='Email sent successfully'
                )
            else:
                return self.create_result(
                    job_data=job_data,
                    status='failed',
                    error='Failed to send email'
                )
                
        except Exception as e:
            logger.error(f"Error in email application: {str(e)}")
            return self.create_result(
                job_data=job_data,
                status='failed',
                error=str(e)
            ) 