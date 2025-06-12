"""
Indeed Applicator Module - Handles job applications on Indeed
"""
from typing import Dict, Optional
import re
import time
from urllib.parse import urlparse

from playwright.sync_api import Page, expect
from loguru import logger

from .base_applicator import BaseApplicator, ApplicationResult

class IndeedApplicator(BaseApplicator):
    """Handles job applications on Indeed."""
    
    async def is_applicable(self, url: str) -> bool:
        """Check if this applicator can handle the given URL."""
        return 'indeed.com' in url.lower()
        
    async def login_if_needed(self) -> bool:
        """Perform Indeed login if required."""
        try:
            # Check if already logged in
            profile_button = await self.page.query_selector("[data-gnav-element-name='ProfileMenu']")
            if profile_button:
                return True
                
            # Get credentials from config
            email = self.config.get('indeed_email')
            password = self.config.get('indeed_password')
            
            if not email or not password:
                logger.error("Indeed credentials not found in config")
                return False
                
            # Click sign in button
            sign_in = await self.page.query_selector("a[href*='login']")
            if sign_in:
                await sign_in.click()
                await self.page.wait_for_timeout(self.automation_delay * 1000)
            
            # Find and fill login form
            await self.safe_fill("#ifl-InputFormField-3", email)
            await self.safe_click("button[type='submit']")
            await self.page.wait_for_timeout(self.automation_delay * 1000)
            
            await self.safe_fill("#ifl-InputFormField-7", password)
            if not await self.safe_click("button[type='submit']"):
                logger.error("Could not find password submit button")
                return False
                
            # Wait for navigation and check if login was successful
            try:
                await self.page.wait_for_selector("[data-gnav-element-name='ProfileMenu']", timeout=10000)
                logger.info("Successfully logged in to Indeed")
                return True
            except:
                logger.error("Login to Indeed failed")
                return False
                
        except Exception as e:
            logger.error(f"Error during Indeed login: {str(e)}")
            return False
            
    async def apply(self, job_data: Dict, resume_data: Dict) -> ApplicationResult:
        """Apply to a job on Indeed."""
        try:
            # Navigate to job page
            await self.page.goto(job_data['url'])
            await self.page.wait_for_load_state('networkidle')
            
            # Handle cookie popup if present
            await self.handle_cookies_popup()
            
            # Check if we need to login
            if not await self.login_if_needed():
                return self.create_result(job_data, 'failed', 'Login required but failed')
                
            # Look for Apply button
            apply_button = await self.page.query_selector("button[id*='indeed-apply-button']")
            if not apply_button:
                return self.create_result(job_data, 'skipped', 'No Apply button found')
                
            # Start application process
            await apply_button.click()
            await self.page.wait_for_timeout(self.automation_delay * 1000)
            
            # Switch to application modal if needed
            modal = await self.page.query_selector("iframe[id*='modal-iframe']")
            if modal:
                await self.page.frame_locator("iframe[id*='modal-iframe']").first.wait_for_load_state()
            
            # Process application steps
            while True:
                # Check for common form fields
                await self._fill_common_fields(resume_data)
                
                # Look for continue or submit button
                continue_button = await self.page.query_selector("button[id*='form-action-continue']")
                submit_button = await self.page.query_selector("button[id*='form-action-submit']")
                
                if submit_button:
                    # Final step - submit application
                    await submit_button.click()
                    await self.page.wait_for_timeout(self.automation_delay * 1000)
                    
                    # Check for success confirmation
                    success_element = await self.page.query_selector("[data-testid='applied-success']")
                    if success_element:
                        return self.create_result(job_data, 'success')
                    else:
                        return self.create_result(job_data, 'failed', 'Could not confirm submission')
                        
                elif continue_button:
                    # Move to next step
                    await continue_button.click()
                    await self.page.wait_for_timeout(self.automation_delay * 1000)
                else:
                    # No more buttons found
                    return self.create_result(job_data, 'failed', 'Could not complete application flow')
                    
        except Exception as e:
            logger.error(f"Error applying to Indeed job: {str(e)}")
            return self.create_result(job_data, 'failed', str(e))
            
    async def _fill_common_fields(self, resume_data: Dict) -> None:
        """Fill common form fields found in Indeed applications."""
        try:
            # Personal Information
            await self.safe_fill("[id*='input-firstName']", resume_data.get('first_name', ''))
            await self.safe_fill("[id*='input-lastName']", resume_data.get('last_name', ''))
            await self.safe_fill("[id*='input-email']", resume_data.get('email', ''))
            await self.safe_fill("[id*='input-phoneNumber']", resume_data.get('phone', ''))
            
            # Location
            await self.safe_fill("[id*='input-location']", f"{resume_data.get('city', '')}, {resume_data.get('state', '')}")
            
            # Resume Upload
            resume_selector = "input[type='file'][accept*='pdf']"
            if await self.page.query_selector(resume_selector):
                await self.upload_resume(resume_selector, str(self.config['resume_path']))
            
            # Additional Questions
            await self._handle_additional_questions(resume_data)
            
        except Exception as e:
            logger.warning(f"Error filling common fields: {str(e)}")
            
    async def _handle_additional_questions(self, resume_data: Dict) -> None:
        """Handle additional application questions."""
        try:
            # Look for common question patterns
            questions = await self.page.query_selector_all("[class*='question-container']")
            
            for question in questions:
                # Get question text
                question_text = await question.text_content()
                if not question_text:
                    continue
                    
                question_text = question_text.lower()
                
                # Experience questions
                if any(word in question_text for word in ['years', 'experience']):
                    experience = str(resume_data.get('experience_years', ''))
                    await self.safe_fill("input[type='text']", experience, parent=question)
                
                # Education questions
                elif any(word in question_text for word in ['degree', 'education']):
                    education = resume_data.get('education', '')
                    await self.safe_fill("input[type='text']", education, parent=question)
                
                # Salary expectations
                elif any(word in question_text for word in ['salary', 'compensation']):
                    salary = str(resume_data.get('salary_expectation', ''))
                    await self.safe_fill("input[type='text']", salary, parent=question)
                
                # Yes/No questions
                elif any(word in question_text for word in ['willing to', 'able to', 'can you']):
                    # Default to Yes for most questions
                    await self.safe_select("select", "Yes", parent=question)
                
                # Start date
                elif 'start date' in question_text:
                    start_date = resume_data.get('available_start_date', 'Immediately')
                    await self.safe_fill("input[type='text']", start_date, parent=question)
                
                # Work authorization
                elif 'authorized' in question_text:
                    auth_status = 'Yes' if resume_data.get('work_authorization') else 'No'
                    await self.safe_select("select", auth_status, parent=question)
                
        except Exception as e:
            logger.warning(f"Error handling additional questions: {str(e)}") 