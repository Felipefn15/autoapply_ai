"""
Email Sender Module - Handles sending emails for job applications
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger

class EmailSender:
    """Class to handle email sending."""
    
    def __init__(self, config: Dict):
        """Initialize the email sender."""
        self.config = config.get('email', {})
        self.smtp_server = self.config.get('smtp_server')
        self.smtp_port = self.config.get('smtp_port')
        self.username = self.config.get('username')
        self.password = self.config.get('password')
        
        if not all([self.smtp_server, self.smtp_port, self.username, self.password]):
            raise ValueError("Missing email configuration")
            
    def _create_message(
        self,
        to_email: str,
        subject: str,
        body: str,
        attachments: Optional[List[str]] = None
    ) -> MIMEMultipart:
        """Create email message with attachments."""
        msg = MIMEMultipart()
        msg['From'] = self.username
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add body
        msg.attach(MIMEText(body, 'plain'))
        
        # Add attachments
        if attachments:
            for file_path in attachments:
                try:
                    with open(file_path, 'rb') as f:
                        part = MIMEApplication(f.read(), Name=Path(file_path).name)
                        part['Content-Disposition'] = f'attachment; filename="{Path(file_path).name}"'
                        msg.attach(part)
                except Exception as e:
                    logger.error(f"Error attaching file {file_path}: {str(e)}")
                    
        return msg
        
    def send_application(self, job: Dict, cover_letter: str) -> bool:
        """Send job application email."""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = job.get('email', '')
            msg['Subject'] = f"Application for {job['title']} position"
            
            # Add cover letter
            msg.attach(MIMEText(cover_letter, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
                
            logger.info(f"Sent application email for {job['title']} at {job['company']}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending application email: {str(e)}")
            return False 