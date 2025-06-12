"""
Remotive Applicator Module
"""
from typing import Dict, Optional
import re
from datetime import datetime
import time

from playwright.sync_api import Page
from loguru import logger

from .base_applicator import BaseApplicator, ApplicationResult

class RemotiveApplicator(BaseApplicator):
    """Handles job applications on Remotive."""
    
    async def is_applicable(self, url: str) -> bool:
        """Check if this applicator can handle the given URL."""
        return 'remotive.com' in url.lower()
        
    async def login_if_needed(self) -> bool:
        """No login needed for Remotive."""
        return True
        
    async def apply(self, job_data: Dict, resume_data: Dict) -> ApplicationResult:
        """Apply to a job on Remotive."""
        try:
            # Navigate to job page
            await self.page.goto(job_data['url'])
            await self.page.wait_for_load_state('networkidle')
            
            # Check if there's an external application link
            external_link = await self._get_external_link()
            if external_link:
                # Save the external link for manual application
                return self.create_result(
                    job_data,
                    'external',
                    f'External application required: {external_link}'
                )
            
            # Check for application form
            apply_button = await self.page.query_selector('button:has-text("Apply for this position")')
            if not apply_button:
                # Try to find email in job description
                email = await self._extract_email_from_description()
                if email:
                    return self.create_result(
                        job_data,
                        'email_required',
                        f'Application via email: {email}'
                    )
                return self.create_result(
                    job_data,
                    'skipped',
                    'No application method found'
                )
            
            # Click apply button
            await apply_button.click()
            await self.page.wait_for_timeout(self.automation_delay * 1000)
            
            # Fill out application form
            success = await self._fill_application_form(resume_data)
            if not success:
                return self.create_result(
                    job_data,
                    'failed',
                    'Failed to fill application form'
                )
            
            # Submit application
            submit_button = await self.page.query_selector('button[type="submit"]')
            if submit_button:
                await submit_button.click()
                await self.page.wait_for_timeout(self.automation_delay * 1000)
                
                return self.create_result(
                    job_data,
                    'success',
                    None
                )
            
            return self.create_result(
                job_data,
                'failed',
                'Could not find submit button'
            )
            
        except Exception as e:
            logger.error(f"Error applying on Remotive: {str(e)}")
            return self.create_result(
                job_data,
                'failed',
                str(e)
            )
    
    async def _get_external_link(self) -> Optional[str]:
        """Get external application link if present."""
        try:
            link = await self.page.query_selector('a[href*="apply"]')
            if link:
                return await link.get_attribute('href')
            return None
        except:
            return None
    
    async def _extract_email_from_description(self) -> Optional[str]:
        """Extract email from job description."""
        try:
            description = await self.page.text_content('.job-description')
            if description:
                email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', description)
                if email_match:
                    return email_match.group(0)
            return None
        except:
            return None
    
    async def _fill_application_form(self, resume_data: Dict) -> bool:
        """Fill out the application form."""
        try:
            # Fill name
            name_input = await self.page.query_selector('input[name="name"]')
            if name_input:
                await name_input.fill(resume_data.get('name', ''))
            
            # Fill email
            email_input = await self.page.query_selector('input[name="email"]')
            if email_input:
                await email_input.fill(resume_data.get('email', ''))
            
            # Upload resume
            resume_input = await self.page.query_selector('input[type="file"]')
            if resume_input:
                await resume_input.set_input_files(resume_data.get('resume_path', ''))
            
            # Fill cover letter if required
            cover_letter_input = await self.page.query_selector('textarea[name="cover_letter"]')
            if cover_letter_input:
                await cover_letter_input.fill(resume_data.get('cover_letter', ''))
            
            return True
            
        except Exception as e:
            logger.error(f"Error filling application form: {str(e)}")
            return False 