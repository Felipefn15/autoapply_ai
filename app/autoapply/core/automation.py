"""
Automation Module - Handles automated job applications
"""
from typing import Dict, List
from pathlib import Path
import json
from datetime import datetime

from loguru import logger
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .jobs import JobPosting
from ..config.settings import config
from ..utils.logging import setup_logger

# Setup module logger
logger = setup_logger("automation")

class JobApplicator:
    """Handles automated job applications."""
    
    def __init__(self):
        """Initialize the job applicator."""
        # Setup directories
        self.data_dir = Path("data")
        self.applied_dir = self.data_dir / "matches/history"
        self.applied_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configuration
        self.config = config
        
        # Initialize webdriver
        self.driver = None
    
    def apply_batch(self, resume_data: Dict, jobs: List[JobPosting]) -> None:
        """
        Apply to a batch of jobs.
        
        Args:
            resume_data: Dictionary containing parsed resume information
            jobs: List of jobs to apply to
        """
        try:
            # Initialize webdriver
            self._setup_webdriver()
            
            # Apply to each job
            for job in jobs:
                try:
                    logger.info(f"Applying to {job.title} at {job.company}")
                    
                    # Check if already applied
                    if self._check_already_applied(job):
                        logger.info(f"Already applied to {job.title} at {job.company}")
                        continue
                    
                    # Apply to job
                    success = self._apply_to_job(resume_data, job)
                    
                    if success:
                        # Save application record
                        self._save_application_record(resume_data, job)
                        logger.info(f"Successfully applied to {job.title} at {job.company}")
                    else:
                        logger.warning(f"Failed to apply to {job.title} at {job.company}")
                    
                except Exception as e:
                    logger.error(f"Error applying to {job.title} at {job.company}: {str(e)}")
                    continue
                
        except Exception as e:
            logger.error(f"Error in batch application: {str(e)}")
        finally:
            self._cleanup_webdriver()
    
    def _setup_webdriver(self) -> None:
        """Setup Selenium webdriver."""
        try:
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')  # Run in headless mode
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            
            self.driver = webdriver.Chrome(options=options)
            self.driver.implicitly_wait(10)  # seconds
            
        except Exception as e:
            logger.error(f"Error setting up webdriver: {str(e)}")
            raise
    
    def _cleanup_webdriver(self) -> None:
        """Clean up webdriver."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.error(f"Error cleaning up webdriver: {str(e)}")
    
    def _check_already_applied(self, job: JobPosting) -> bool:
        """Check if already applied to a job."""
        try:
            # Generate filename for application record
            filename = f"{job.platform}_{job.company}_{job.title}".lower()
            filename = "".join(c if c.isalnum() else "_" for c in filename)
            record_file = self.applied_dir / f"{filename}.json"
            
            return record_file.exists()
            
        except Exception as e:
            logger.error(f"Error checking application record: {str(e)}")
            return False
    
    def _save_application_record(self, resume_data: Dict, job: JobPosting) -> None:
        """Save record of job application."""
        try:
            # Generate filename for application record
            filename = f"{job.platform}_{job.company}_{job.title}".lower()
            filename = "".join(c if c.isalnum() else "_" for c in filename)
            record_file = self.applied_dir / f"{filename}.json"
            
            # Create record
            record = {
                "job": job.dict(),
                "resume": resume_data,
                "applied_at": datetime.now().isoformat(),
                "platform": job.platform
            }
            
            # Save record
            with record_file.open('w') as f:
                json.dump(record, f, indent=2)
            
        except Exception as e:
            logger.error(f"Error saving application record: {str(e)}")
    
    def _apply_to_job(self, resume_data: Dict, job: JobPosting) -> bool:
        """
        Apply to a specific job.
        
        Args:
            resume_data: Dictionary containing parsed resume information
            job: Job to apply to
            
        Returns:
            True if application was successful, False otherwise
        """
        try:
            # Navigate to job URL
            self.driver.get(job.url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # TODO: Implement platform-specific application logic
            # This is a placeholder that always returns False
            logger.warning("Automatic job application not yet implemented")
            return False
            
        except Exception as e:
            logger.error(f"Error applying to job: {str(e)}")
            return False 