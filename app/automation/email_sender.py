"""
Email Sender Module

Handles sending job application emails with:
- Professional formatting
- Resume attachments
- Cover letter attachments
- HTML email templates
- Email signature
"""
import os
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional
import smtplib
from loguru import logger

class EmailSender:
    """Handles sending job application emails."""
    
    def __init__(self, host: str, port: int, username: str, password: str,
                 from_name: str, from_email: str, signature_path: str):
        """Initialize the email sender."""
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_name = from_name
        self.from_email = from_email
        
        # Load email signature
        self.signature = self._load_signature(signature_path)
        
        # Load email templates
        self.templates = self._load_templates()
        
    def send_application(self, to_email: str, job_title: str, company_name: str,
                        cover_letter: Optional[str] = None, resume_path: Optional[str] = None) -> bool:
        """Send a job application email."""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = f"Application for {job_title} position at {company_name}"
            
            # Create email body
            body = self._create_email_body(job_title, company_name, cover_letter)
            msg.attach(MIMEText(body, 'html'))
            
            # Attach resume if provided
            if resume_path:
                self._attach_file(msg, resume_path, 'resume.pdf')
            
            # Attach cover letter as separate file if provided
            if cover_letter:
                cover_letter_attachment = MIMEText(cover_letter)
                cover_letter_attachment.add_header(
                    'Content-Disposition',
                    'attachment',
                    filename='cover_letter.txt'
                )
                msg.attach(cover_letter_attachment)
            
            # Send email
            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            logger.info(f"Application email sent to {to_email} for {job_title} at {company_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending application email: {str(e)}")
            return False
            
    def _load_signature(self, signature_path: str) -> str:
        """Load email signature from file."""
        try:
            with open(signature_path, 'r') as f:
                return f.read().strip()
        except Exception as e:
            logger.warning(f"Error loading signature: {str(e)}")
            return f"\n\nBest regards,\n{self.from_name}"
            
    def _load_templates(self) -> dict:
        """Load email templates."""
        return {
            'application': """
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <p>Dear Hiring Manager,</p>
                
                <p>I am writing to express my strong interest in the {job_title} position at {company_name}. 
                Please find attached my resume and cover letter for your consideration.</p>
                
                {cover_letter_html}
                
                <p>I look forward to discussing how I can contribute to your team.</p>
                
                <div style="margin-top: 20px; border-top: 1px solid #ccc; padding-top: 20px;">
                    {signature}
                </div>
            </body>
            </html>
            """
        }
        
    def _create_email_body(self, job_title: str, company_name: str, cover_letter: Optional[str] = None) -> str:
        """Create HTML email body."""
        # Format cover letter for HTML if provided
        cover_letter_html = ""
        if cover_letter:
            paragraphs = cover_letter.split('\n\n')
            cover_letter_html = "\n".join(f"<p>{p}</p>" for p in paragraphs)
        
        # Create email body from template
        body = self.templates['application'].format(
            job_title=job_title,
            company_name=company_name,
            cover_letter_html=cover_letter_html,
            signature=self.signature
        )
        
        return body
        
    def _attach_file(self, msg: MIMEMultipart, file_path: str, filename: str):
        """Attach a file to the email."""
        try:
            with open(file_path, 'rb') as f:
                part = MIMEApplication(f.read(), _subtype="pdf")
                part.add_header(
                    'Content-Disposition',
                    'attachment',
                    filename=filename
                )
                msg.attach(part)
        except Exception as e:
            logger.error(f"Error attaching file {file_path}: {str(e)}")
            raise
            
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