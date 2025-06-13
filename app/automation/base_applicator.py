"""
Base Applicator Module - Defines base class for job application automation
"""
from typing import Dict, Optional, Protocol
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
import time
import json
from pathlib import Path

from playwright.sync_api import Page, expect
from loguru import logger

from .application_logger import ApplicationLogger

@dataclass
class ApplicationResult:
    """Result of a job application attempt."""
    company: str
    position: str
    url: str
    platform: str
    status: str  # 'success', 'failed', 'skipped'
    application_method: str  # 'direct', 'email', 'form'
    direct_apply_status: bool  # Whether direct application was successful
    email_sent_status: bool  # Whether email was sent successfully
    application_id: Optional[str] = None
    error_message: Optional[str] = None
    applied_at: Optional[datetime] = None
    notes: Optional[str] = None

    def to_log_string(self) -> str:
        """Convert result to a log-friendly string."""
        status_parts = []
        
        # Add main status with color
        status_color = {
            'success': '🟢',
            'failed': '🔴',
            'skipped': '🟡'
        }.get(self.status.lower(), '⚪')
        
        status_parts.append(f"{status_color} [{self.status.upper()}]")
        
        # Add application methods with icons
        methods = []
        if self.direct_apply_status:
            methods.append("direct=✅")
        elif self.application_method == 'direct':
            methods.append("direct=❌")
            
        if self.email_sent_status:
            methods.append("email=✅")
        elif self.application_method == 'email':
            methods.append("email=❌")
            
        if methods:
            status_parts.append(" | ".join(methods))
            
        # Add error if present
        if self.error_message:
            status_parts.append(f"❗error={self.error_message[:50]}...")
            
        # Add timestamp
        if self.applied_at:
            status_parts.append(f"📅 {self.applied_at.strftime('%Y-%m-%d %H:%M:%S')}")
            
        # Add notes if present
        if self.notes:
            status_parts.append(f"📝 {self.notes[:50]}...")
            
        return f"{' '.join(status_parts)}\n🎯 {self.position}\n🏢 {self.company}\n🔗 {self.url}\n"

class BaseApplicator(ABC):
    """Base class for platform-specific applicators."""
    
    def __init__(self, config: Dict):
        """Initialize the applicator."""
        self.config = config
        self.automation_delay = float(config.get('automation_delay', 2))
        self.page = None  # Will be set by platform-specific applicators
        self.logger = ApplicationLogger()
        
    @abstractmethod
    async def is_applicable(self, url: str) -> bool:
        """Check if this applicator can handle the given URL."""
        pass
        
    @abstractmethod
    async def login_if_needed(self) -> bool:
        """Perform login if required. Return True if successful."""
        pass
        
    @abstractmethod
    async def apply(self, job_data: Dict, resume_data: Dict) -> ApplicationResult:
        """Apply to the job."""
        pass
        
    async def safe_click(self, selector: str, delay: float = None) -> bool:
        """Safely click an element with retry."""
        try:
            delay = delay or self.automation_delay
            logger.debug(f"Attempting to click: {selector}")
            await self.page.wait_for_selector(selector, state="visible", timeout=10000)
            element = await self.page.query_selector(selector)
            if element:
                await element.click()
                await self.page.wait_for_timeout(delay * 1000)
                logger.debug(f"Successfully clicked: {selector}")
                return True
            logger.warning(f"Element not found: {selector}")
            return False
        except Exception as e:
            logger.warning(f"Error clicking {selector}: {str(e)}")
            return False
            
    async def safe_fill(self, selector: str, value: str, delay: float = None) -> bool:
        """Safely fill a form field with retry."""
        try:
            delay = delay or self.automation_delay
            logger.debug(f"Attempting to fill {selector} with value: {value[:20]}...")
            await self.page.wait_for_selector(selector, state="visible", timeout=10000)
            element = await self.page.query_selector(selector)
            if element:
                await element.fill(value)
                await self.page.wait_for_timeout(delay * 1000)
                logger.debug(f"Successfully filled: {selector}")
                return True
            logger.warning(f"Element not found: {selector}")
            return False
        except Exception as e:
            logger.warning(f"Error filling {selector}: {str(e)}")
            return False
            
    async def safe_select(self, selector: str, value: str, delay: float = None) -> bool:
        """Safely select an option from a dropdown."""
        try:
            delay = delay or self.automation_delay
            logger.debug(f"Attempting to select {value} from {selector}")
            await self.page.wait_for_selector(selector, state="visible", timeout=10000)
            await self.page.select_option(selector, value)
            await self.page.wait_for_timeout(delay * 1000)
            logger.debug(f"Successfully selected {value} from {selector}")
            return True
        except Exception as e:
            logger.warning(f"Error selecting {selector}: {str(e)}")
            return False
            
    async def upload_resume(self, selector: str, resume_path: str, delay: float = None) -> bool:
        """Safely upload a resume file."""
        try:
            delay = delay or self.automation_delay
            logger.debug(f"Attempting to upload resume to {selector}")
            await self.page.wait_for_selector(selector, state="visible", timeout=10000)
            input_element = await self.page.query_selector(selector)
            if input_element:
                await input_element.set_input_files(resume_path)
                await self.page.wait_for_timeout(delay * 1000)
                logger.debug(f"Successfully uploaded resume to {selector}")
                return True
            logger.warning(f"Upload element not found: {selector}")
            return False
        except Exception as e:
            logger.warning(f"Error uploading resume to {selector}: {str(e)}")
            return False
            
    def create_result(self, job_data: Dict, status: str, error: Optional[str] = None) -> ApplicationResult:
        """Create an application result object."""
        result = ApplicationResult(
            company=job_data.get('company', 'Unknown'),
            position=job_data.get('title', 'Unknown'),
            url=job_data.get('url', ''),
            platform=job_data.get('platform', 'Unknown'),
            status=status,
            application_method=job_data.get('application_method', 'direct'),
            direct_apply_status=status == 'success' and job_data.get('application_method') == 'direct',
            email_sent_status=status == 'success' and job_data.get('application_method') == 'email',
            application_id=job_data.get('id'),
            error_message=error,
            applied_at=datetime.now(),
            notes=job_data.get('notes')
        )
        
        # Log the application attempt
        self.logger.log_application(
            job=job_data,
            status=status,
            method=result.application_method,
            error=error,
            notes=job_data.get('notes')
        )
        
        return result
        
    async def check_captcha(self) -> bool:
        """Check for and handle common captcha patterns."""
        # Implementation will depend on the specific captcha service used
        # This is a placeholder for future implementation
        return False
        
    async def handle_cookies_popup(self) -> bool:
        """Handle common cookie consent popups."""
        try:
            # Common cookie popup button selectors
            selectors = [
                "button[id*='cookie-accept']",
                "button[id*='cookie-consent']",
                "button[id*='accept-cookies']",
                "button[class*='cookie-accept']",
                "button[class*='accept-cookies']",
                "[aria-label*='Accept cookies']",
                "[data-testid*='cookie-accept']"
            ]
            
            for selector in selectors:
                button = await self.page.query_selector(selector)
                if button:
                    await button.click()
                    await self.page.wait_for_timeout(1000)  # Wait for popup to close
                    break
                    
        except Exception as e:
            logger.warning(f"Error handling cookie popup: {str(e)}")
            
    async def scroll_to_bottom(self, scroll_delay: float = 1.0) -> None:
        """Scroll to the bottom of the page gradually."""
        prev_height = 0
        while True:
            curr_height = await self.page.evaluate("document.body.scrollHeight")
            if curr_height == prev_height:
                break
            await self.page.evaluate(f"window.scrollTo(0, {curr_height})")
            await self.page.wait_for_timeout(scroll_delay * 1000)
            prev_height = curr_height 