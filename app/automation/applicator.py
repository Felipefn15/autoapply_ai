"""
Job Applicator Module - Handles automated job applications using Playwright
"""
import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Optional

import groq
from playwright.sync_api import Page, Playwright, sync_playwright
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class ApplicationResult(BaseModel):
    """Data model for application results."""
    company: str
    position: str
    url: str
    status: str  # 'success', 'failed', 'skipped'
    error_message: Optional[str]
    application_id: Optional[str]
    cover_letter: Optional[str]

class JobApplicator:
    """Handles automated job applications using Playwright."""
    
    def __init__(self):
        """Initialize the job applicator."""
        self.client = groq.Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.automation_delay = float(os.getenv("AUTOMATION_DELAY", "2"))
        self.resume_path = Path(os.getenv("RESUME_PATH", "data/resumes/resume.pdf"))
    
    def apply_batch(self, resume_data: Dict, jobs: List[Dict]) -> List[ApplicationResult]:
        """
        Apply to multiple jobs in sequence.
        
        Args:
            resume_data: Dictionary containing parsed resume information
            jobs: List of job postings to apply to
            
        Returns:
            List of ApplicationResult objects
        """
        results = []
        
        with sync_playwright() as playwright:
            # Launch browser
            browser = playwright.chromium.launch(headless=False)  # Set to True in production
            context = browser.new_context()
            page = context.new_page()
            
            for job in jobs:
                try:
                    result = self._apply_to_job(page, resume_data, job)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error applying to {job.get('company')} - {job.get('title')}: {str(e)}")
                    results.append(
                        ApplicationResult(
                            company=job.get('company', 'Unknown'),
                            position=job.get('title', 'Unknown'),
                            url=job.get('url', ''),
                            status='failed',
                            error_message=str(e)
                        )
                    )
            
            # Close browser
            context.close()
            browser.close()
        
        return results
    
    def _apply_to_job(self, page: Page, resume_data: Dict, job: Dict) -> ApplicationResult:
        """Apply to a single job posting."""
        logger.info(f"Applying to {job.get('company')} - {job.get('title')}")
        
        try:
            # Navigate to job posting
            page.goto(job['url'])
            time.sleep(self.automation_delay)  # Basic rate limiting
            
            # Detect application form type
            form_type = self._detect_form_type(page)
            
            if form_type == 'linkedin':
                return self._apply_linkedin(page, resume_data, job)
            elif form_type == 'indeed':
                return self._apply_indeed(page, resume_data, job)
            elif form_type == 'greenhouse':
                return self._apply_greenhouse(page, resume_data, job)
            elif form_type == 'lever':
                return self._apply_lever(page, resume_data, job)
            else:
                return ApplicationResult(
                    company=job['company'],
                    position=job['title'],
                    url=job['url'],
                    status='skipped',
                    error_message='Unsupported application form type'
                )
                
        except Exception as e:
            return ApplicationResult(
                company=job['company'],
                position=job['title'],
                url=job['url'],
                status='failed',
                error_message=str(e)
            )
    
    def _detect_form_type(self, page: Page) -> str:
        """Detect the type of application form on the page."""
        url = page.url.lower()
        
        if 'linkedin.com' in url:
            return 'linkedin'
        elif 'indeed.com' in url:
            return 'indeed'
        elif 'greenhouse.io' in url:
            return 'greenhouse'
        elif 'lever.co' in url:
            return 'lever'
        else:
            return 'unknown'
    
    def _generate_cover_letter(self, resume_data: Dict, job: Dict) -> str:
        """Generate a customized cover letter using GROQ."""
        try:
            prompt = f"""
            Please write a professional cover letter for the following job:
            
            Company: {job['company']}
            Position: {job['title']}
            Job Description: {job['description']}
            
            Candidate Information:
            Name: {resume_data['full_name']}
            Skills: {', '.join(resume_data['skills'])}
            Experience: {resume_data['experience']}
            
            The cover letter should:
            1. Be personalized for the company and role
            2. Highlight relevant skills and experience
            3. Show enthusiasm and cultural fit
            4. Be concise (max 300 words)
            """
            
            response = self.client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[
                    {"role": "system", "content": "You are an expert cover letter writer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating cover letter: {str(e)}")
            return ""
    
    # Platform-specific application methods
    
    def _apply_linkedin(self, page: Page, resume_data: Dict, job: Dict) -> ApplicationResult:
        """Apply to a job on LinkedIn."""
        try:
            # Check if "Easy Apply" is available
            easy_apply_button = page.get_by_role("button", name="Easy Apply")
            if not easy_apply_button.is_visible():
                return ApplicationResult(
                    company=job['company'],
                    position=job['title'],
                    url=job['url'],
                    status='skipped',
                    error_message='No Easy Apply button found'
                )
            
            # Click Easy Apply
            easy_apply_button.click()
            time.sleep(self.automation_delay)
            
            # Fill out basic information if needed
            # This is a simplified version - would need more robust handling
            self._fill_linkedin_form(page, resume_data)
            
            # Submit application
            submit_button = page.get_by_role("button", name="Submit application")
            if submit_button.is_visible():
                submit_button.click()
                time.sleep(self.automation_delay)
                
                return ApplicationResult(
                    company=job['company'],
                    position=job['title'],
                    url=job['url'],
                    status='success',
                    application_id=None  # LinkedIn doesn't provide an ID
                )
            
            return ApplicationResult(
                company=job['company'],
                position=job['title'],
                url=job['url'],
                status='failed',
                error_message='Could not find submit button'
            )
            
        except Exception as e:
            return ApplicationResult(
                company=job['company'],
                position=job['title'],
                url=job['url'],
                status='failed',
                error_message=str(e)
            )
    
    def _apply_indeed(self, page: Page, resume_data: Dict, job: Dict) -> ApplicationResult:
        """Apply to a job on Indeed."""
        # Similar implementation to LinkedIn
        # Would need Indeed-specific form handling
        return ApplicationResult(
            company=job['company'],
            position=job['title'],
            url=job['url'],
            status='skipped',
            error_message='Indeed application not implemented in MVP'
        )
    
    def _apply_greenhouse(self, page: Page, resume_data: Dict, job: Dict) -> ApplicationResult:
        """Apply to a job through Greenhouse."""
        # Similar implementation
        return ApplicationResult(
            company=job['company'],
            position=job['title'],
            url=job['url'],
            status='skipped',
            error_message='Greenhouse application not implemented in MVP'
        )
    
    def _apply_lever(self, page: Page, resume_data: Dict, job: Dict) -> ApplicationResult:
        """Apply to a job through Lever."""
        # Similar implementation
        return ApplicationResult(
            company=job['company'],
            position=job['title'],
            url=job['url'],
            status='skipped',
            error_message='Lever application not implemented in MVP'
        )
    
    def _fill_linkedin_form(self, page: Page, resume_data: Dict) -> None:
        """Fill out a LinkedIn Easy Apply form."""
        # This would need to be much more robust in production
        # Handle different form types, required fields, etc.
        try:
            # Example field handling
            name_input = page.get_by_label("Full name")
            if name_input.is_visible():
                name_input.fill(resume_data['full_name'])
            
            email_input = page.get_by_label("Email")
            if email_input.is_visible() and resume_data.get('email'):
                email_input.fill(resume_data['email'])
            
            phone_input = page.get_by_label("Phone")
            if phone_input.is_visible() and resume_data.get('phone'):
                phone_input.fill(resume_data['phone'])
            
            # Handle resume upload if needed
            resume_upload = page.get_by_label("Resume")
            if resume_upload.is_visible():
                resume_upload.set_input_files(str(self.resume_path))
            
            # Click through any "Next" buttons
            while True:
                next_button = page.get_by_role("button", name="Next")
                if next_button.is_visible():
                    next_button.click()
                    time.sleep(self.automation_delay)
                else:
                    break
                    
        except Exception as e:
            logger.error(f"Error filling LinkedIn form: {str(e)}")
            raise 