"""Email applicator module for handling email-based job applications."""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Optional
from pathlib import Path

from loguru import logger

class EmailApplicator:
    """Class for handling email-based job applications."""
    
    def __init__(self):
        """Initialize email applicator."""
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = None
        self.sender_password = None
        
    def _load_credentials(self) -> bool:
        """Load email credentials from environment variables."""
        import os
        
        self.sender_email = os.getenv("APPLICATOR_EMAIL")
        self.sender_password = os.getenv("APPLICATOR_EMAIL_PASSWORD")
        
        if not self.sender_email or not self.sender_password:
            logger.error("Email credentials not found in environment variables")
            return False
            
        return True
        
    def _prepare_email(self, job: Dict) -> Optional[MIMEMultipart]:
        """Prepare email message for job application.
        
        Args:
            job: Dictionary containing job information
            
        Returns:
            MIMEMultipart: Prepared email message or None if preparation fails
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = job['contact_email']
            msg['Subject'] = f"Application for {job['title']} position at {job['company']}"
            
            # Load email template
            template_path = Path("templates/email/professional.html")
            if not template_path.exists():
                logger.error("Email template not found")
                return None
                
            with open(template_path, 'r') as f:
                template = f.read()
                
            # Replace placeholders
            body = template.format(
                company=job['company'],
                position=job['title'],
                # Add more placeholders as needed
            )
            
            msg.attach(MIMEText(body, 'html'))
            return msg
            
        except Exception as e:
            logger.error(f"Error preparing email: {str(e)}")
            return None
            
    def apply(self, job: Dict) -> bool:
        """Apply to a job via email.
        
        Args:
            job: Dictionary containing job information
            
        Returns:
            bool: True if application was successful, False otherwise
        """
        try:
            # Load credentials
            if not self._load_credentials():
                return False
                
            # Prepare email
            msg = self._prepare_email(job)
            if not msg:
                return False
                
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
                
            logger.info(f"Successfully sent application email to {job['company']}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending application email: {str(e)}")
            return False 