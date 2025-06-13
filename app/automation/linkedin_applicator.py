"""
LinkedIn Applicator Module - Handles job applications on LinkedIn
"""
from typing import Dict, Optional
import asyncio
from pathlib import Path
import re
import time
from urllib.parse import urlparse

from playwright.sync_api import Page, expect
from loguru import logger

from .base_applicator import BaseApplicator, ApplicationResult

class LinkedInApplicator(BaseApplicator):
    """Handles job applications on LinkedIn."""
    
    def __init__(self, config: Dict):
        """Initialize the LinkedIn applicator."""
        super().__init__(config)
        self.page = None  # Will be set when needed
        self.session_valid_until = None
        self.linkedin_email = config.get('linkedin_email', '')
        self.linkedin_password = config.get('linkedin_password', '')
        
    async def is_applicable(self, url: str) -> bool:
        """Check if this applicator can handle the given URL."""
        return bool(url and 'linkedin.com' in url.lower())
        
    async def login_if_needed(self) -> bool:
        """Login to LinkedIn if not already logged in."""
        try:
            # Check if already logged in
            if await self._is_logged_in():
                logger.debug("Already logged in to LinkedIn")
                return True
                
            logger.info("Logging in to LinkedIn...")
            
            # Go to login page
            await self.page.goto('https://www.linkedin.com/login')
            await self.page.wait_for_load_state('networkidle')
            
            # Fill login form
            await self.safe_fill('#username', self.linkedin_email)
            await self.safe_fill('#password', self.linkedin_password)
            
            # Click login button
            await self.safe_click('button[type="submit"]')
            
            # Wait for login to complete
            await self.page.wait_for_load_state('networkidle')
            
            # Verify login success
            if await self._is_logged_in():
                logger.info("Successfully logged in to LinkedIn")
                return True
                
            logger.error("Failed to log in to LinkedIn")
            return False
            
        except Exception as e:
            logger.error(f"Error logging in to LinkedIn: {str(e)}")
            return False
            
    async def apply(self, job_data: Dict, resume_data: Dict) -> ApplicationResult:
        """Apply to the job on LinkedIn."""
        try:
            # Go to job page
            await self.page.goto(job_data['url'])
            await self.page.wait_for_load_state('networkidle')
            
            # Check if already applied
            if await self._is_already_applied():
                return self.create_result(
                    job_data=job_data,
                    status='skipped',
                    notes='Already applied to this job'
                )
                
            # Find and click apply button
            apply_button = await self._find_apply_button()
            if not apply_button:
                return self.create_result(
                    job_data=job_data,
                    status='failed',
                    error='Apply button not found'
                )
                
            await apply_button.click()
            await self.page.wait_for_load_state('networkidle')
            
            # Handle application form
            success = await self._fill_application_form(resume_data)
            if not success:
                return self.create_result(
                    job_data=job_data,
                    status='failed',
                    error='Failed to fill application form'
                )
                
            # Submit application
            submit_button = await self._find_submit_button()
            if not submit_button:
                return self.create_result(
                    job_data=job_data,
                    status='failed',
                    error='Submit button not found'
                )
                
            await submit_button.click()
            await self.page.wait_for_load_state('networkidle')
            
            # Verify submission
            if await self._verify_submission():
                return self.create_result(
                    job_data=job_data,
                    status='success',
                    notes='Application submitted successfully'
                )
                
            return self.create_result(
                job_data=job_data,
                status='failed',
                error='Failed to verify submission'
            )
            
        except Exception as e:
            logger.error(f"Error applying on LinkedIn: {str(e)}")
            return self.create_result(
                job_data=job_data,
                status='failed',
                error=str(e)
            )
            
    async def _is_logged_in(self) -> bool:
        """Check if logged in to LinkedIn."""
        try:
            # Look for elements that indicate logged-in state
            profile_nav = await self.page.query_selector('nav[aria-label="Primary"]')
            return bool(profile_nav)
        except Exception:
            return False
            
    async def _is_already_applied(self) -> bool:
        """Check if already applied to the job."""
        try:
            applied_text = await self.page.query_selector_all('text="You applied to this job"')
            return bool(applied_text)
        except Exception:
            return False
            
    async def _find_apply_button(self) -> Optional[Page]:
        """Find the apply button on the job page."""
        try:
            # Try different button selectors
            selectors = [
                'button:has-text("Apply")',
                'button:has-text("Easy Apply")',
                'a:has-text("Apply")',
                'a:has-text("Easy Apply")'
            ]
            
            for selector in selectors:
                button = await self.page.query_selector(selector)
                if button:
                    return button
                    
            return None
            
        except Exception:
            return None
            
    async def _find_submit_button(self) -> Optional[Page]:
        """Find the submit button on the application form."""
        try:
            # Try different button selectors
            selectors = [
                'button:has-text("Submit")',
                'button:has-text("Submit application")',
                'button[type="submit"]'
            ]
            
            for selector in selectors:
                button = await self.page.query_selector(selector)
                if button:
                    return button
                    
            return None
            
        except Exception:
            return None
            
    async def _fill_application_form(self, resume_data: Dict) -> bool:
        """Fill out the application form."""
        try:
            # Upload resume if needed
            resume_upload = await self.page.query_selector('input[type="file"]')
            if resume_upload:
                await self.upload_resume(
                    selector='input[type="file"]',
                    resume_path=resume_data.get('resume_path', '')
                )
                
            # Fill any additional fields
            # TODO: Handle other common form fields
            
            return True
            
        except Exception as e:
            logger.error(f"Error filling form: {str(e)}")
            return False
            
    async def _verify_submission(self) -> bool:
        """Verify that the application was submitted successfully."""
        try:
            # Look for success indicators
            success_texts = [
                'Application submitted',
                'Successfully submitted',
                'Thank you for applying'
            ]
            
            for text in success_texts:
                element = await self.page.query_selector(f'text="{text}"')
                if element:
                    return True
                    
            return False
            
        except Exception:
            return False
            
    async def _fill_common_fields(self, resume_data: Dict) -> None:
        """Fill common form fields found in LinkedIn applications."""
        try:
            # Personal Information
            await self.safe_fill("input[id*='firstName']", resume_data.get('first_name', ''))
            await self.safe_fill("input[id*='lastName']", resume_data.get('last_name', ''))
            await self.safe_fill("input[id*='email']", resume_data.get('email', ''))
            await self.safe_fill("input[id*='phone']", resume_data.get('phone', ''))
            
            # Work Experience
            work_exp_selector = "select[id*='years-of-experience']"
            if await self.page.query_selector(work_exp_selector):
                await self.safe_select(work_exp_selector, str(len(resume_data.get('work_experience', []))))
            
            # Resume Upload
            resume_selector = "input[type='file'][accept*='pdf']"
            if await self.page.query_selector(resume_selector):
                await self.upload_resume(resume_selector, str(self.config['resume_path']))
            
            # Cover Letter
            cover_letter = await self.page.query_selector("textarea[id*='cover-letter']")
            if cover_letter:
                await self.safe_fill("textarea[id*='cover-letter']", resume_data.get('cover_letter', ''))
            
            # Additional Questions
            await self._handle_additional_questions(resume_data)
            
        except Exception as e:
            logger.warning(f"Error filling common fields: {str(e)}")
            
    async def _handle_additional_questions(self, resume_data: Dict) -> None:
        """Handle LinkedIn-specific additional questions."""
        try:
            # Common LinkedIn questions
            questions = {
                "authorized": "Are you legally authorized to work in",
                "sponsorship": "Will you now or in the future require sponsorship",
                "remote": "Are you comfortable working remotely",
                "onsite": "Are you comfortable working onsite",
                "travel": "Are you willing to travel",
                "relocation": "Are you willing to relocate",
                "background": "Are you willing to undergo a background check",
                "salary": "What is your desired salary"
            }
            
            for key, text in questions.items():
                # Look for questions by text content
                question = await self.page.query_selector(f"label:has-text('{text}')")
                if question:
                    # Get associated input field
                    input_id = await question.get_attribute('for')
                    if input_id:
                        # Handle different question types
                        if key in ['authorized', 'remote', 'onsite', 'background']:
                            await self.safe_select(f"select#{input_id}", 'Yes')
                        elif key == 'sponsorship':
                            await self.safe_select(f"select#{input_id}", 'No')
                        elif key in ['travel', 'relocation']:
                            await self.safe_select(f"select#{input_id}", resume_data.get(key, 'Yes'))
                        elif key == 'salary':
                            await self.safe_fill(f"input#{input_id}", resume_data.get('desired_salary', ''))
                            
        except Exception as e:
            logger.warning(f"Error handling additional questions: {str(e)}") 