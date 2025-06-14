"""
Email sender implementation using SendGrid.
"""
import os
from typing import List, Optional
from pathlib import Path

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, 
    Email, 
    To, 
    Content, 
    Attachment, 
    FileContent, 
    FileName,
    FileType,
    Disposition
)
import base64
from loguru import logger

class EmailSender:
    """Handles email sending via SendGrid."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the email sender with SendGrid API key."""
        self.api_key = api_key or os.getenv('SENDGRID_API_KEY')
        if not self.api_key:
            raise ValueError("SendGrid API key not provided and SENDGRID_API_KEY env var not set")
        self.client = SendGridAPIClient(self.api_key)

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        attachments: Optional[List[Path]] = None,
        is_html: bool = True
    ) -> bool:
        """
        Send an email using SendGrid.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body content
            from_email: Sender email (optional, uses config default if not provided)
            from_name: Sender name (optional, uses config default if not provided)
            attachments: List of file paths to attach (optional)
            is_html: Whether the body content is HTML (default True)
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            # Set up the from email
            from_email = from_email or os.getenv('SENDGRID_FROM_EMAIL')
            if not from_email:
                raise ValueError("Sender email not provided and SENDGRID_FROM_EMAIL env var not set")
            
            from_name = from_name or os.getenv('SENDGRID_FROM_NAME', '')
            sender = Email(from_email, from_name) if from_name else Email(from_email)
            
            # Create the email
            content_type = 'text/html' if is_html else 'text/plain'
            message = Mail(
                from_email=sender,
                to_emails=To(to_email),
                subject=subject,
                html_content=body if is_html else None,
                plain_text_content=body if not is_html else None
            )

            # Add attachments if any
            if attachments:
                for attachment_path in attachments:
                    with open(attachment_path, 'rb') as f:
                        file_content = base64.b64encode(f.read()).decode()
                        
                    attachment = Attachment()
                    attachment.file_content = FileContent(file_content)
                    attachment.file_name = FileName(attachment_path.name)
                    attachment.file_type = FileType('application/octet-stream')
                    attachment.disposition = Disposition('attachment')
                    message.add_attachment(attachment)

            # Send the email
            response = self.client.send(message)
            
            # Log success
            logger.info(f"Email sent successfully to {to_email}. Status code: {response.status_code}")
            return True

        except Exception as e:
            # Log error
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    def send_bulk_emails(
        self,
        to_emails: List[str],
        subject: str,
        body: str,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        attachments: Optional[List[Path]] = None,
        is_html: bool = True
    ) -> dict:
        """
        Send emails to multiple recipients.
        
        Args:
            to_emails: List of recipient email addresses
            subject: Email subject
            body: Email body content
            from_email: Sender email (optional)
            from_name: Sender name (optional)
            attachments: List of file paths to attach (optional)
            is_html: Whether the body content is HTML
            
        Returns:
            dict: Results for each recipient {'email': bool_success}
        """
        results = {}
        for email in to_emails:
            success = self.send_email(
                to_email=email,
                subject=subject,
                body=body,
                from_email=from_email,
                from_name=from_name,
                attachments=attachments,
                is_html=is_html
            )
            results[email] = success
        return results 