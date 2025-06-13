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
    
    def __init__(self, config: Dict):
        """Initialize the Indeed applicator."""
        super().__init__(config)
        self.page = None  # Will be set when needed
        self.session_valid_until = None
        
    async def is_applicable(self, url: str) -> bool:
        """Check if this applicator can handle the given URL."""
        return 'indeed.com' in url.lower()
        
    async def login_if_needed(self) -> bool:
        """Perform Indeed login if required."""
        try:
            # Check if we're already logged in
            if self.session_valid_until and time.time() < self.session_valid_until:
                return True
                
            # Check if login is needed by looking for sign-in button
            sign_in_button = await self.page.query_selector("a[href*='login']")
            if not sign_in_button:
                # No sign-in button found, we might be logged in
                profile_button = await self.page.query_selector("button[aria-label*='profile']")
                if profile_button:
                    # Update session validity (24 hours from now)
                    self.session_valid_until = time.time() + 24 * 60 * 60
                    return True
                    
            # Navigate to login page if not already there
            if not await self.page.query_selector("input[id='ifl-InputFormField-3']"):
                await sign_in_button.click()
                await self.page.wait_for_load_state('networkidle')
                
            # Fill login form
            await self.safe_fill("input[id='ifl-InputFormField-3']", self.config['username'])
            await self.safe_fill("input[id='ifl-InputFormField-7']", self.config['password'])
            
            # Submit login form
            submit_button = await self.page.query_selector("button[type='submit']")
            if submit_button:
                await submit_button.click()
                await self.page.wait_for_load_state('networkidle')
                
                # Verify login success
                profile_button = await self.page.query_selector("button[aria-label*='profile']")
                if profile_button:
                    # Update session validity (24 hours from now)
                    self.session_valid_until = time.time() + 24 * 60 * 60
                    logger.info("Successfully logged in to Indeed")
                    return True
                    
            logger.error("Failed to login to Indeed")
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
            apply_button = await self.page.query_selector("button[id='indeedApplyButton']")
            if not apply_button:
                return self.create_result(job_data, 'skipped', 'No Apply button found')
                
            # Start application process
            await apply_button.click()
            await self.page.wait_for_timeout(self.automation_delay * 1000)
            
            # Process application steps
            while True:
                # Check for common form fields
                await self._fill_common_fields(resume_data)
                
                # Look for next or submit button
                next_button = await self.page.query_selector("button[id*='form-action-continue']")
                submit_button = await self.page.query_selector("button[id*='form-action-submit']")
                
                if submit_button:
                    # Final step - submit application
                    await submit_button.click()
                    await self.page.wait_for_timeout(self.automation_delay * 1000)
                    
                    # Check for success confirmation
                    success_element = await self.page.query_selector("div[class*='ia-success-message']")
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
            logger.error(f"Error applying to Indeed job: {str(e)}")
            return self.create_result(job_data, 'failed', str(e))
            
    async def _fill_common_fields(self, resume_data: Dict) -> None:
        """Fill common form fields found in Indeed applications."""
        try:
            # Personal Information
            await self.safe_fill("input[id*='input-firstName']", resume_data.get('first_name', ''))
            await self.safe_fill("input[id*='input-lastName']", resume_data.get('last_name', ''))
            await self.safe_fill("input[id*='input-email']", resume_data.get('email', ''))
            await self.safe_fill("input[id*='input-phoneNumber']", resume_data.get('phone', ''))
            
            # Resume Upload
            resume_selector = "input[type='file'][accept*='pdf']"
            if await self.page.query_selector(resume_selector):
                await self.upload_resume(resume_selector, str(self.config['resume_path']))
            
            # Cover Letter
            cover_letter = await self.page.query_selector("textarea[id*='input-coverLetter']")
            if cover_letter:
                await self.safe_fill("textarea[id*='input-coverLetter']", resume_data.get('cover_letter', ''))
            
            # Additional Questions
            await self._handle_additional_questions(resume_data)
            
        except Exception as e:
            logger.warning(f"Error filling common fields: {str(e)}")
            
    async def _handle_additional_questions(self, resume_data: Dict) -> None:
        """Handle Indeed-specific additional questions."""
        try:
            # Common Indeed questions
            questions = {
                "authorized": "Are you legally authorized to work in",
                "sponsorship": "Will you now or in the future require sponsorship",
                "start_date": "When can you start",
                "remote": "Are you comfortable working remotely",
                "onsite": "Are you willing to work onsite",
                "travel": "Are you willing to travel",
                "relocation": "Are you willing to relocate",
                "education": "What is your highest level of education",
                "experience": "How many years of relevant experience do you have",
                "certifications": "Do you have any relevant certifications",
                "languages": "What languages do you speak",
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
                        if key in ['authorized', 'remote', 'onsite']:
                            await self.safe_select(f"select#{input_id}", 'Yes')
                        elif key == 'sponsorship':
                            await self.safe_select(f"select#{input_id}", 'No')
                        elif key == 'start_date':
                            await self.safe_fill(f"input#{input_id}", resume_data.get('start_date', 'Immediately'))
                        elif key in ['travel', 'relocation']:
                            await self.safe_select(f"select#{input_id}", resume_data.get(key, 'Yes'))
                        elif key == 'education':
                            await self.safe_select(f"select#{input_id}", resume_data.get('highest_education', "Bachelor's Degree"))
                        elif key == 'experience':
                            await self.safe_select(f"select#{input_id}", str(len(resume_data.get('work_experience', []))))
                        elif key == 'certifications':
                            certs = ', '.join(resume_data.get('certifications', []))
                            await self.safe_fill(f"input#{input_id}", certs)
                        elif key == 'languages':
                            langs = ', '.join(resume_data.get('languages', ['English']))
                            await self.safe_fill(f"input#{input_id}", langs)
                        elif key == 'salary':
                            await self.safe_fill(f"input#{input_id}", resume_data.get('desired_salary', ''))
                            
            # Handle custom questions
            custom_questions = await self.page.query_selector_all("div[class*='ia-Questions-item']")
            for question in custom_questions:
                question_text = await question.text_content()
                if not question_text:
                    continue
                    
                # Try to intelligently answer based on question content
                question_text = question_text.lower()
                
                if any(word in question_text for word in ['why', 'interest', 'motivation']):
                    # Questions about motivation/interest
                    await self.safe_fill("textarea", resume_data.get('job_interest', ''), parent=question)
                elif any(word in question_text for word in ['project', 'achievement']):
                    # Questions about projects/achievements
                    await self.safe_fill("textarea", resume_data.get('key_achievements', ''), parent=question)
                elif any(word in question_text for word in ['challenge', 'difficult']):
                    # Questions about challenges
                    await self.safe_fill("textarea", resume_data.get('challenges_overcome', ''), parent=question)
                elif any(word in question_text for word in ['strength', 'skill']):
                    # Questions about strengths/skills
                    skills = ', '.join(resume_data.get('key_skills', []))
                    await self.safe_fill("textarea", skills, parent=question)
                    
        except Exception as e:
            logger.warning(f"Error handling additional questions: {str(e)}") 