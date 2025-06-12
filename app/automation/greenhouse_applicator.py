"""
Greenhouse Applicator Module
"""
from typing import Dict, Optional
import re
from datetime import datetime
import time

from playwright.sync_api import Page
from loguru import logger

from .base_applicator import BaseApplicator, ApplicationResult

class GreenhouseApplicator(BaseApplicator):
    """Handles job applications on Greenhouse."""
    
    async def is_applicable(self, url: str) -> bool:
        """Check if this applicator can handle the given URL."""
        return 'greenhouse.io' in url.lower()
        
    async def login_if_needed(self) -> bool:
        """No login needed for Greenhouse."""
        return True
        
    async def apply(self, job_data: Dict, resume_data: Dict) -> ApplicationResult:
        """Apply to a job on Greenhouse."""
        try:
            # Navigate to job page
            await self.page.goto(job_data['url'])
            await self.page.wait_for_load_state('networkidle')
            
            # Check for application form
            apply_button = await self.page.query_selector('#apply_button')
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
            submit_button = await self.page.query_selector('#submit_app')
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
            logger.error(f"Error applying on Greenhouse: {str(e)}")
            return self.create_result(
                job_data,
                'failed',
                str(e)
            )
    
    async def _extract_email_from_description(self) -> Optional[str]:
        """Extract email from job description."""
        try:
            description = await self.page.text_content('#content')
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
            # Fill basic information
            await self._fill_basic_info(resume_data)
            
            # Upload resume
            await self._upload_resume(resume_data)
            
            # Fill additional questions
            await self._fill_additional_questions(resume_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Error filling application form: {str(e)}")
            return False
    
    async def _fill_basic_info(self, resume_data: Dict) -> None:
        """Fill basic information fields."""
        try:
            # Fill first name
            first_name = await self.page.query_selector('#first_name')
            if first_name:
                await first_name.fill(resume_data.get('first_name', ''))
            
            # Fill last name
            last_name = await self.page.query_selector('#last_name')
            if last_name:
                await last_name.fill(resume_data.get('last_name', ''))
            
            # Fill email
            email = await self.page.query_selector('#email')
            if email:
                await email.fill(resume_data.get('email', ''))
            
            # Fill phone
            phone = await self.page.query_selector('#phone')
            if phone:
                await phone.fill(resume_data.get('phone', ''))
            
        except Exception as e:
            logger.error(f"Error filling basic info: {str(e)}")
            raise
    
    async def _upload_resume(self, resume_data: Dict) -> None:
        """Upload resume file."""
        try:
            resume_input = await self.page.query_selector('input[type="file"]')
            if resume_input:
                await resume_input.set_input_files(resume_data.get('resume_path', ''))
                await self.page.wait_for_timeout(self.automation_delay * 1000)
        except Exception as e:
            logger.error(f"Error uploading resume: {str(e)}")
            raise
    
    async def _fill_additional_questions(self, resume_data: Dict) -> None:
        """Fill additional application questions."""
        try:
            # Handle text questions
            text_inputs = await self.page.query_selector_all('input[type="text"]')
            for input in text_inputs:
                label = await input.evaluate('el => el.labels[0]?.textContent')
                if label:
                    label = label.lower()
                    if 'linkedin' in label:
                        await input.fill(resume_data.get('linkedin_url', ''))
                    elif 'github' in label:
                        await input.fill(resume_data.get('github_url', ''))
                    elif 'portfolio' in label:
                        await input.fill(resume_data.get('portfolio_url', ''))
            
            # Handle radio buttons for yes/no questions
            radios = await self.page.query_selector_all('input[type="radio"]')
            for radio in radios:
                label = await radio.evaluate('el => el.labels[0]?.textContent')
                if label:
                    label = label.lower()
                    if 'authorized' in label and 'yes' in label:
                        await radio.click()
                    elif 'require visa' in label and 'no' in label:
                        await radio.click()
                    elif 'remote' in label and 'yes' in label:
                        await radio.click()
            
            # Handle textareas (usually for cover letter or additional info)
            textareas = await self.page.query_selector_all('textarea')
            for textarea in textareas:
                label = await textarea.evaluate('el => el.labels[0]?.textContent')
                if label:
                    label = label.lower()
                    if 'cover letter' in label:
                        await textarea.fill(resume_data.get('cover_letter', ''))
                    elif 'additional information' in label:
                        await textarea.fill(resume_data.get('additional_info', ''))
            
        except Exception as e:
            logger.error(f"Error filling additional questions: {str(e)}")
            raise 