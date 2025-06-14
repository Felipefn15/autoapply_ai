"""
LinkedIn Applicator Module - Handles job applications on LinkedIn
"""
from typing import Dict, Optional
import asyncio
from pathlib import Path
import re
import time
from urllib.parse import urlparse

from playwright.async_api import Page, expect
from loguru import logger

from .base_applicator import BaseApplicator, ApplicationResult

class LinkedInApplicator(BaseApplicator):
    """Handles job applications on LinkedIn."""
    
    def __init__(self, config: Dict):
        """Initialize the LinkedIn applicator."""
        super().__init__(config)
        self.page = None  # Will be set when needed
        self.session_valid_until = None
        self.linkedin_email = config.get('oauth', {}).get('linkedin', {}).get('email', '')
        self.linkedin_password = config.get('oauth', {}).get('linkedin', {}).get('password', '')
        
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
            await self.page.goto('https://www.linkedin.com/login', wait_until='networkidle')
            
            # Wait for login form to be visible
            await self.page.wait_for_selector('#username', state='visible', timeout=10000)
            await self.page.wait_for_selector('#password', state='visible', timeout=10000)
            
            # Fill login form
            await self.page.fill('#username', self.linkedin_email)
            await self.page.fill('#password', self.linkedin_password)
            
            # Click login button and wait for navigation
            async with self.page.expect_navigation(wait_until='networkidle'):
                await self.page.click('button[type="submit"]')
            
            # Additional wait to ensure page loads
            await self.page.wait_for_load_state('domcontentloaded')
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
            logger.info(f"Starting LinkedIn application process for: {job_data.get('title')}")
            
            # Navigate to job page
            url = job_data.get('url')
            if not url:
                raise ValueError("No URL provided for LinkedIn job")
                
            logger.info(f"Navigating to job page: {url}")
            await self.page.goto(url)
            await self.page.wait_for_load_state('networkidle')
            
            # Wait for job details to load
            logger.info("Waiting for job details to load...")
            await self.page.wait_for_selector('.jobs-unified-top-card', timeout=10000)
            
            # Check if already applied
            if await self._check_if_already_applied():
                logger.warning("Already applied to this job")
                return ApplicationResult(
                    company=job_data.get('company', 'Unknown'),
                    position=job_data.get('title', 'Unknown'),
                    url=job_data.get('url', ''),
                    platform='linkedin',
                    status='skipped',
                    application_method='direct',
                    direct_apply_status=False,
                    email_sent_status=False,
                    error='Already applied to this job'
                )
            
            # Find apply button
            logger.info("Looking for apply button...")
            apply_button = await self.page.query_selector('button[aria-label*="Apply"]')
            if not apply_button:
                logger.warning("Apply button not found - job might require external application")
                return ApplicationResult(
                    company=job_data.get('company', 'Unknown'),
                    position=job_data.get('title', 'Unknown'),
                    url=job_data.get('url', ''),
                    platform='linkedin',
                    status='failed',
                    application_method='direct',
                    direct_apply_status=False,
                    email_sent_status=False,
                    error='No apply button found - might require external application'
                )
            
            # Click apply button
            logger.info("Clicking apply button...")
            await apply_button.click()
            await asyncio.sleep(2)  # Wait for modal to open
            
            # Handle application form
            logger.info("Handling application form...")
            success = await self._fill_application_form(resume_data)
            
            if success:
                logger.success("Successfully submitted LinkedIn application!")
                return ApplicationResult(
                    company=job_data.get('company', 'Unknown'),
                    position=job_data.get('title', 'Unknown'),
                    url=job_data.get('url', ''),
                    platform='linkedin',
                    status='success',
                    application_method='direct',
                    direct_apply_status=True,
                    email_sent_status=False,
                    notes='Application submitted successfully'
                )
            else:
                logger.error("Failed to complete LinkedIn application form")
                return ApplicationResult(
                    company=job_data.get('company', 'Unknown'),
                    position=job_data.get('title', 'Unknown'),
                    url=job_data.get('url', ''),
                    platform='linkedin',
                    status='failed',
                    application_method='direct',
                    direct_apply_status=False,
                    email_sent_status=False,
                    error='Failed to complete application form'
                )
            
        except Exception as e:
            logger.error(f"Error in LinkedIn application process: {str(e)}")
            return ApplicationResult(
                company=job_data.get('company', 'Unknown'),
                position=job_data.get('title', 'Unknown'),
                url=job_data.get('url', ''),
                platform='linkedin',
                status='failed',
                application_method='direct',
                direct_apply_status=False,
                email_sent_status=False,
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
            
    async def _check_if_already_applied(self) -> bool:
        """Check if already applied to this job."""
        try:
            # Look for "Applied" indicator
            applied_text = await self.page.query_selector('text="Applied"')
            if applied_text:
                return True
                
            # Look for disabled apply button
            disabled_button = await self.page.query_selector('button[aria-label*="Apply"][disabled]')
            if disabled_button:
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error checking if already applied: {str(e)}")
            return False
            
    async def _fill_application_form(self, resume_data: Dict) -> bool:
        """Fill out the LinkedIn application form."""
        try:
            # Wait for form to load
            logger.info("Waiting for application form...")
            await self.page.wait_for_selector('.jobs-easy-apply-modal', timeout=5000)
            
            # Check for resume upload
            resume_upload = await self.page.query_selector('input[type="file"]')
            if resume_upload:
                logger.info("Uploading resume...")
                await self.upload_resume(
                    selector='input[type="file"]',
                    resume_path=resume_data.get('resume_path', '')
                )
                await asyncio.sleep(2)
            
            # Look for next/submit button
            while True:
                # Check for error messages
                error_messages = await self.page.query_selector_all('.artdeco-inline-feedback--error')
                if error_messages:
                    error_texts = [await msg.text_content() for msg in error_messages]
                    logger.error(f"Form validation errors: {error_texts}")
                    return False
                
                # Look for next/submit button
                next_button = await self.page.query_selector('button[aria-label*="Submit"] >> visible=true')
                if not next_button:
                    next_button = await self.page.query_selector('button[aria-label*="Next"] >> visible=true')
                
                if not next_button:
                    logger.warning("No next/submit button found")
                    return False
                
                # Click the button
                button_text = await next_button.text_content()
                logger.info(f"Clicking button: {button_text}")
                await next_button.click()
                await asyncio.sleep(2)
                
                # Check if we're done
                success_message = await self.page.query_selector('text="Application submitted"')
                if success_message:
                    return True
                
                # Check for additional questions
                questions = await self.page.query_selector_all('input:not([type="hidden"]), textarea')
                if questions:
                    logger.info(f"Found {len(questions)} form fields to fill")
                    for question in questions:
                        await self._fill_form_field(question, resume_data)
                
            return True
            
        except Exception as e:
            logger.error(f"Error filling application form: {str(e)}")
            return False
            
    async def _fill_form_field(self, field, resume_data: Dict) -> None:
        """Fill a single form field."""
        try:
            # Get field type and label
            field_type = await field.get_attribute('type') or 'text'
            field_id = await field.get_attribute('id')
            label = await self.page.query_selector(f'label[for="{field_id}"]')
            label_text = await label.text_content() if label else 'Unknown field'
            
            logger.info(f"Filling field: {label_text} (type: {field_type})")
            
            # Handle different field types
            if field_type == 'text':
                if 'name' in label_text.lower():
                    if 'first' in label_text.lower():
                        await field.fill(resume_data.get('first_name', ''))
                    elif 'last' in label_text.lower():
                        await field.fill(resume_data.get('last_name', ''))
                elif 'email' in label_text.lower():
                    await field.fill(resume_data.get('email', ''))
                elif 'phone' in label_text.lower():
                    await field.fill(resume_data.get('phone', ''))
                else:
                    await field.fill('Yes')  # Default text response
            elif field_type == 'number':
                if 'experience' in label_text.lower():
                    await field.fill(str(resume_data.get('experience_years', 5)))
                else:
                    await field.fill('5')  # Default years
            elif field_type == 'radio':
                await field.check()
            elif field_type == 'checkbox':
                if any(word in label_text.lower() for word in ['agree', 'accept', 'confirm']):
                    await field.check()
                
        except Exception as e:
            logger.error(f"Error filling form field: {str(e)}")
            
    async def upload_resume(self, selector: str, resume_path: str) -> bool:
        """Upload resume file."""
        try:
            # Check if resume exists
            if not Path(resume_path).exists():
                logger.error(f"Resume not found at: {resume_path}")
                return False
                
            # Upload file
            file_chooser = await self.page.query_selector(selector)
            if file_chooser:
                await file_chooser.set_input_files(resume_path)
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error uploading resume: {str(e)}")
            return False 