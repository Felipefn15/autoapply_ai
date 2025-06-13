"""
Greenhouse Applicator Module - Handles job applications on Greenhouse
"""
from typing import Dict, Optional
import re
import time
from urllib.parse import urlparse

from playwright.sync_api import Page, expect
from loguru import logger

from .base_applicator import BaseApplicator, ApplicationResult

class GreenhouseApplicator(BaseApplicator):
    """Handles job applications on Greenhouse."""
    
    def __init__(self, config: Dict):
        """Initialize the Greenhouse applicator."""
        super().__init__(config)
        self.page = None  # Will be set when needed
        
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
            
            # Handle cookie popup if present
            await self.handle_cookies_popup()
            
            # Look for Apply button
            apply_button = await self.page.query_selector("a[href*='application']")
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
                next_button = await self.page.query_selector("button[type='submit']")
                
                if next_button:
                    # Get button text
                    button_text = await next_button.text_content()
                    
                    # Submit application
                    await next_button.click()
                    await self.page.wait_for_timeout(self.automation_delay * 1000)
                    
                    # Check if this was the final submit
                    if button_text and 'submit' in button_text.lower():
                        # Check for success confirmation
                        success_element = await self.page.query_selector("div[class*='thank']")
                        if success_element:
                            return self.create_result(job_data, 'success')
                        else:
                            return self.create_result(job_data, 'failed', 'Could not confirm submission')
                else:
                    # No more buttons found
                    return self.create_result(job_data, 'failed', 'Could not complete application flow')
                    
        except Exception as e:
            logger.error(f"Error applying to Greenhouse job: {str(e)}")
            return self.create_result(job_data, 'failed', str(e))
            
    async def _fill_common_fields(self, resume_data: Dict) -> None:
        """Fill common form fields found in Greenhouse applications."""
        try:
            # Personal Information
            await self.safe_fill("input[id*='first_name']", resume_data.get('first_name', ''))
            await self.safe_fill("input[id*='last_name']", resume_data.get('last_name', ''))
            await self.safe_fill("input[id*='email']", resume_data.get('email', ''))
            await self.safe_fill("input[id*='phone']", resume_data.get('phone', ''))
            
            # Location
            await self.safe_fill("input[id*='location']", resume_data.get('location', ''))
            
            # Resume Upload
            resume_selector = "input[type='file'][accept*='pdf']"
            if await self.page.query_selector(resume_selector):
                await self.upload_resume(resume_selector, str(self.config['resume_path']))
            
            # Cover Letter
            cover_letter = await self.page.query_selector("textarea[id*='cover_letter']")
            if cover_letter:
                await self.safe_fill("textarea[id*='cover_letter']", resume_data.get('cover_letter', ''))
            
            # LinkedIn Profile
            linkedin = await self.page.query_selector("input[id*='linkedin']")
            if linkedin:
                await self.safe_fill("input[id*='linkedin']", resume_data.get('linkedin_url', ''))
            
            # Portfolio/Website
            website = await self.page.query_selector("input[id*='website']")
            if website:
                await self.safe_fill("input[id*='website']", resume_data.get('portfolio_url', ''))
            
            # Additional Questions
            await self._handle_additional_questions(resume_data)
            
        except Exception as e:
            logger.warning(f"Error filling common fields: {str(e)}")
            
    async def _handle_additional_questions(self, resume_data: Dict) -> None:
        """Handle Greenhouse-specific additional questions."""
        try:
            # Common Greenhouse questions
            questions = {
                "authorized": "Are you authorized to work in",
                "sponsorship": "Do you require sponsorship",
                "start_date": "When can you start",
                "notice_period": "What is your notice period",
                "remote": "Are you willing to work remotely",
                "onsite": "Are you willing to work onsite",
                "travel": "Are you willing to travel",
                "relocation": "Are you willing to relocate",
                "education": "What is your highest level of education",
                "experience": "How many years of experience do you have",
                "salary": "What are your salary expectations"
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
                        elif key == 'notice_period':
                            await self.safe_fill(f"input#{input_id}", resume_data.get('notice_period', '2 weeks'))
                        elif key in ['travel', 'relocation']:
                            await self.safe_select(f"select#{input_id}", resume_data.get(key, 'Yes'))
                        elif key == 'education':
                            await self.safe_select(f"select#{input_id}", resume_data.get('highest_education', "Bachelor's Degree"))
                        elif key == 'experience':
                            await self.safe_select(f"select#{input_id}", str(len(resume_data.get('work_experience', []))))
                        elif key == 'salary':
                            await self.safe_fill(f"input#{input_id}", resume_data.get('desired_salary', ''))
                            
            # Handle custom questions
            custom_questions = await self.page.query_selector_all("div[class*='custom-question']")
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
                elif any(word in question_text for word in ['tool', 'technology', 'software']):
                    # Questions about tools/technologies
                    tools = ', '.join(resume_data.get('technical_skills', []))
                    await self.safe_fill("textarea", tools, parent=question)
                elif any(word in question_text for word in ['team', 'collaborate']):
                    # Questions about teamwork
                    await self.safe_fill("textarea", resume_data.get('teamwork_examples', ''), parent=question)
                elif any(word in question_text for word in ['leadership', 'manage']):
                    # Questions about leadership
                    await self.safe_fill("textarea", resume_data.get('leadership_examples', ''), parent=question)
                    
        except Exception as e:
            logger.warning(f"Error handling additional questions: {str(e)}") 