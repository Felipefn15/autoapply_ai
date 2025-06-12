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
    
    async def is_applicable(self, url: str) -> bool:
        """Check if this applicator can handle the given URL."""
        return 'linkedin.com' in url.lower()
        
    async def login_if_needed(self) -> bool:
        """Perform LinkedIn login if required."""
        try:
            # Check if already logged in
            profile_button = await self.page.query_selector("button[aria-label*='profile']")
            if profile_button:
                return True
                
            # Get credentials from config
            email = self.config.get('linkedin_email')
            password = self.config.get('linkedin_password')
            
            if not email or not password:
                logger.error("LinkedIn credentials not found in config")
                return False
                
            # Find and fill login form
            await self.safe_fill("#username", email)
            await self.safe_fill("#password", password)
            
            # Click sign in button
            if not await self.safe_click("button[type='submit']"):
                logger.error("Could not find login button")
                return False
                
            # Wait for navigation and check if login was successful
            try:
                await self.page.wait_for_selector("button[aria-label*='profile']", timeout=10000)
                logger.info("Successfully logged in to LinkedIn")
                return True
            except:
                logger.error("Login to LinkedIn failed")
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
                    success_element = await self.page.query_selector("h2[class*='success']")
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
            await self.safe_fill("input[id*='first-name']", resume_data.get('first_name', ''))
            await self.safe_fill("input[id*='last-name']", resume_data.get('last_name', ''))
            await self.safe_fill("input[id*='email']", resume_data.get('email', ''))
            await self.safe_fill("input[id*='phone']", resume_data.get('phone', ''))
            
            # Location
            await self.safe_fill("input[id*='city']", resume_data.get('city', ''))
            await self.safe_fill("input[id*='state']", resume_data.get('state', ''))
            await self.safe_fill("input[id*='zip']", resume_data.get('zip_code', ''))
            
            # Work Authorization
            auth_selector = "select[id*='work-authorization']"
            if await self.page.query_selector(auth_selector):
                auth_status = 'Yes' if resume_data.get('work_authorization') else 'No'
                await self.safe_select(auth_selector, auth_status)
            
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
            questions = await self.page.query_selector_all("div[class*='question']")
            
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
                
                # Salary expectations
                elif any(word in question_text for word in ['salary', 'compensation']):
                    salary = str(resume_data.get('salary_expectation', ''))
                    await self.safe_fill("input[type='text']", salary, parent=question)
                
                # Yes/No questions
                elif any(word in question_text for word in ['willing to', 'able to', 'can you']):
                    # Default to Yes for most questions
                    await self.safe_select("select", "Yes", parent=question)
                
                # Notice period
                elif 'notice period' in question_text:
                    notice = str(resume_data.get('notice_period', '2 weeks'))
                    await self.safe_fill("input[type='text']", notice, parent=question)
                
        except Exception as e:
            logger.warning(f"Error handling additional questions: {str(e)}") 