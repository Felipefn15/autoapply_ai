"""
Email Sender Module - Handles sending job application emails
"""
import os
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Dict, List, Optional
import smtplib
import re
import aiosmtplib

from loguru import logger

class EmailSender:
    """Handles sending job application emails."""
    
    def __init__(self, config: Dict):
        """Initialize the email sender with configuration."""
        email_config = config.get('email', {})
        self.host = email_config.get('smtp_host', 'smtp.gmail.com')
        self.port = email_config.get('smtp_port', 587)
        self.username = email_config.get('smtp_username', '')
        self.password = email_config.get('smtp_password', '')
        self.from_name = email_config.get('from_name', '')
        self.from_email = email_config.get('from_email', '')
        
        # Load signature
        signature_path = email_config.get('signature_path', '')
        self.signature = self._load_signature(signature_path)
        
    async def send_email(self, to_email: str, subject: str, body: str,
                        attachments: Optional[List[str]] = None) -> bool:
        """
        Send an email.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body text
            attachments: List of file paths to attach
            
        Returns:
            bool: Whether the email was sent successfully
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add body
            msg.attach(MIMEText(self._create_email_body(body), 'html'))
            
            # Add attachments
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        self._attach_file(msg, file_path)
                    else:
                        logger.warning(f"Attachment not found: {file_path}")
            
            # Send email
            await aiosmtplib.send(
                message=msg.as_string(),
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                use_tls=True
            )
            
            logger.info(f"Email sent to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False
            
    def _load_signature(self, signature_path: str) -> str:
        """Load email signature from file."""
        try:
            if signature_path and os.path.exists(signature_path):
                with open(signature_path, 'r') as f:
                    return f.read().strip()
        except Exception as e:
            logger.warning(f"Error loading signature: {str(e)}")
            
        return f"\n\nBest regards,\n{self.from_name}"
            
    def _create_email_body(self, body_text: str) -> str:
        """Create HTML email body with signature."""
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            {body_text}
            
            <div style="margin-top: 20px; border-top: 1px solid #ccc; padding-top: 20px;">
                {self.signature}
            </div>
        </body>
        </html>
        """
            
    def _attach_file(self, msg: MIMEMultipart, file_path: str):
        """Attach a file to the email."""
        try:
            filename = os.path.basename(file_path)
            with open(file_path, 'rb') as f:
                part = MIMEApplication(f.read())
                part.add_header(
                    'Content-Disposition',
                    'attachment',
                    filename=filename
                )
                msg.attach(part)
        except Exception as e:
            logger.error(f"Error attaching file {file_path}: {str(e)}")
            
    def extract_email_from_text(self, text: str) -> Optional[str]:
        """Extract email address from text."""
        if not text:
            return None
            
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        match = re.search(email_pattern, text)
        return match.group(0) if match else None 