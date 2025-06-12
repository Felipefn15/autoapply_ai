"""
Email Sender Module - Handles sending application emails
"""
from typing import Dict, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from pathlib import Path
import os

from loguru import logger

class EmailSender:
    """Handles sending application emails."""
    
    def __init__(self, config: Dict):
        """Initialize email sender with configuration."""
        self.config = config
        self.smtp_server = config.get('smtp_server', 'smtp.gmail.com')
        self.smtp_port = int(config.get('smtp_port', 587))
        self.smtp_username = config.get('smtp_username')
        self.smtp_password = config.get('smtp_password')
        self.sender_email = config.get('sender_email')
        
    def send_application_email(self, 
                             to_email: str,
                             subject: str,
                             body: str,
                             resume_path: str,
                             job_data: Dict) -> bool:
        """
        Send application email with resume attachment.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body text
            resume_path: Path to resume PDF
            job_data: Job posting data
            
        Returns:
            bool: True if email was sent successfully
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add body
            msg.attach(MIMEText(body, 'plain'))
            
            # Add resume attachment
            with open(resume_path, 'rb') as f:
                resume = MIMEApplication(f.read(), _subtype='pdf')
                resume.add_header('Content-Disposition', 'attachment', 
                                filename=os.path.basename(resume_path))
                msg.attach(resume)
            
            # Connect to SMTP server
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
                
            logger.info(f"Successfully sent application email to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending application email: {str(e)}")
            return False
            
    def extract_email_from_text(self, text: str) -> Optional[str]:
        """
        Extract email address from text.
        
        Args:
            text: Text to search for email
            
        Returns:
            Optional[str]: Found email address or None
        """
        import re
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        match = re.search(email_pattern, text)
        return match.group(0) if match else None 