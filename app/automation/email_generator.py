"""
Email Generator Module - Generates application emails using LLM
"""
from typing import Dict, Optional
import json

from loguru import logger
from groq import Groq

def generate_email(job_data: Dict, resume_data: Dict) -> str:
    """
    Generate an application email for a job.
    
    Args:
        job_data: Job posting data
        resume_data: Resume data
        
    Returns:
        Generated email body text
    """
    try:
        # Create default email content
        default_email = f"""Dear Hiring Manager,

I am writing to express my interest in the {job_data.get('title', 'open')} position at {job_data.get('company', 'your company')}.

With {resume_data.get('experience_years', 'several')} years of experience in the field, I believe I would be a great fit for this role. My skills include {', '.join(resume_data.get('skills', [])[:3])}.

I would welcome the opportunity to discuss how my experience aligns with your needs.

Best regards,
{resume_data.get('first_name', '')} {resume_data.get('last_name', '')}"""

        # Try to use EmailGenerator if config is available
        if 'api' in job_data.get('config', {}):
            try:
                generator = EmailGenerator(job_data['config'])
                email_content = generator.generate_application_email(job_data, resume_data)
                return email_content['body']
            except Exception as e:
                logger.warning(f"Failed to use EmailGenerator, falling back to default: {str(e)}")
                return default_email
        else:
            return default_email
            
    except Exception as e:
        logger.error(f"Error generating email: {str(e)}")
        return default_email

class EmailGenerator:
    """Generates application emails using LLM."""
    
    def __init__(self, config: Dict):
        """Initialize email generator with configuration."""
        self.config = config
        self.client = Groq(api_key=config['api']['groq_api_key'])
        self.model = config['api']['groq_model']
        self.temperature = config['api']['groq_temperature']
        self.max_tokens = config['api']['groq_max_tokens']
        
    def generate_application_email(self, job_data: Dict, resume_data: Dict) -> Dict:
        """
        Generate application email content using LLM.
        
        Args:
            job_data: Job posting data
            resume_data: Resume data
            
        Returns:
            Dict containing subject and body of the email
        """
        try:
            # Prepare prompt
            prompt = f"""Generate a professional application email for the following job posting.
            The email should be concise, highlight relevant experience, and express genuine interest.
            
            Job Details:
            - Title: {job_data.get('title', 'Not specified')}
            - Company: {job_data.get('company', 'Not specified')}
            - Description: {job_data.get('description', 'Not specified')}
            - Requirements: {job_data.get('requirements', 'Not specified')}
            
            Candidate Details:
            - Experience: {resume_data.get('experience_years', 'Not specified')} years
            - Skills: {', '.join(resume_data.get('skills', []))}
            - Current Role: {resume_data.get('current_role', 'Not specified')}
            - Education: {resume_data.get('education', 'Not specified')}
            
            Return a JSON object with two keys:
            1. 'subject': A compelling email subject line
            2. 'body': The email body text
            
            The email should:
            - Be professional but conversational
            - Highlight relevant experience and skills
            - Show enthusiasm for the role
            - Be concise (max 3 paragraphs)
            - Include a clear call to action
            """
            
            # Generate content
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at writing professional application emails."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            # Parse response
            response_text = completion.choices[0].message.content
            email_content = json.loads(response_text)
            
            return {
                'subject': email_content['subject'],
                'body': email_content['body']
            }
            
        except Exception as e:
            logger.error(f"Error generating application email: {str(e)}")
            return {
                'subject': f"Application for {job_data.get('title', '')} position",
                'body': f"""Dear Hiring Manager,

I am writing to express my interest in the {job_data.get('title', '')} position at {job_data.get('company', '')}.

With {resume_data.get('experience_years', 'several')} years of experience in the field, I believe I would be a great fit for this role. My skills include {', '.join(resume_data.get('skills', [])[:3])}.

I would welcome the opportunity to discuss how my experience aligns with your needs.

Best regards,
{resume_data.get('first_name', '')} {resume_data.get('last_name', '')}"""
            }

__all__ = ['generate_email', 'EmailGenerator'] 