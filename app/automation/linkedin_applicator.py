"""
LinkedIn Applicator Module - Handles job applications on LinkedIn
"""
from typing import Dict, Optional
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
        
    async def is_applicable(self, url: str) -> bool:
        """Check if this applicator can handle the given URL."""
        return 'linkedin.com' in url.lower()
        
    async def login_if_needed(self) -> bool:
        """Perform LinkedIn login if required."""
        try:
            # Check if we're already logged in
            if self.session_valid_until and time.time() < self.session_valid_until:
                return True
                
            # Check if login is needed by looking for sign-in button
            sign_in_button = await self.page.query_selector("a[href*='signin']")
            if not sign_in_button:
                # No sign-in button found, we might be logged in
                profile_button = await self.page.query_selector("button[aria-label*='Me']")
                if profile_button:
                    # Update session validity (24 hours from now)
                    self.session_valid_until = time.time() + 24 * 60 * 60
                    return True
                    
            # Navigate to login page if not already there
            if not await self.page.query_selector("input[id='username']"):
                await sign_in_button.click()
                await self.page.wait_for_load_state('networkidle')
                
            # Fill login form
            await self.safe_fill("input[id='username']", self.config['username'])
            await self.safe_fill("input[id='password']", self.config['password'])
            
            # Submit login form
            submit_button = await self.page.query_selector("button[type='submit']")
            if submit_button:
                await submit_button.click()
                await self.page.wait_for_load_state('networkidle')
                
                # Verify login success
                profile_button = await self.page.query_selector("button[aria-label*='Me']")
                if profile_button:
                    # Update session validity (24 hours from now)
                    self.session_valid_until = time.time() + 24 * 60 * 60
                    logger.info("Successfully logged in to LinkedIn")
                    return True
                    
            logger.error("Failed to login to LinkedIn")
            return False
            
        except Exception as e:
            logger.error(f"Error during LinkedIn login: {str(e)}")
            return False
            
    async def apply(self, job_data: Dict, resume_data: Dict) -> ApplicationResult:
        """Apply to a job on LinkedIn."""
        try:
            # Navigate to job page
            await self.page.goto(job_data['url'])
            await self.page.wait_for_load_state('networkidle')
            
            # Handle cookie popup if present
            await self.handle_cookies_popup()
            
            # Check if we need to login
            if not await self.login_if_needed():
                return self.create_result(job_data, 'failed', 'Login required but failed')
                
            # Look for Easy Apply button
            easy_apply_button = await self.page.query_selector("button[aria-label*='Easy Apply']")
            if not easy_apply_button:
                return self.create_result(job_data, 'skipped', 'No Easy Apply button found')
                
            # Start application process
            await easy_apply_button.click()
            await self.page.wait_for_timeout(self.automation_delay * 1000)
            
            # Process application steps
            while True:
                # Check for common form fields
                await self._fill_common_fields(resume_data)
                
                # Look for next or submit button
                next_button = await self.page.query_selector("button[aria-label*='Continue']")
                submit_button = await self.page.query_selector("button[aria-label*='Submit']")
                
                if submit_button:
                    # Final step - submit application
                    await submit_button.click()
                    await self.page.wait_for_timeout(self.automation_delay * 1000)
                    
                    # Check for success confirmation
                    success_element = await self.page.query_selector("div[aria-label*='application submitted']")
                    if success_element:
                        return self.create_result(job_data, 'success')
                    else:
                        return self.create_result(job_data, 'failed', 'Could not confirm submission')
                elif next_button:
                    # Move to next step
                    await next_button.click()
                    await self.page.wait_for_timeout(self.automation_delay * 1000)
                else:
                    # No more buttons found
                    return self.create_result(job_data, 'failed', 'Could not complete application flow')
                    
        except Exception as e:
            logger.error(f"Error applying to LinkedIn job: {str(e)}")
            return self.create_result(job_data, 'failed', str(e))
            
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