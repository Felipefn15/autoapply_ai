"""
Applicator Manager Module - Manages all job application automations
"""
from typing import Dict, List, Optional
import asyncio
from datetime import datetime
import json
from pathlib import Path

from playwright.sync_api import sync_playwright
from loguru import logger

from .base_applicator import ApplicationResult
# from .linkedin_applicator import LinkedInApplicator
# from .indeed_applicator import IndeedApplicator
from .email_sender import EmailSender
from .email_generator import EmailGenerator
from ..config import config

class ApplicatorManager:
    """Manages job applications across multiple platforms."""
    
    def __init__(self):
        """Initialize the applicator manager."""
        self.config = config
        self.applicators = []
        self.history_dir = Path("data/applications/history")
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self.email_sender = EmailSender(config)
        self.email_generator = EmailGenerator(config)
        
    def apply_to_jobs(self, resume_data: Dict, jobs: List[Dict]) -> List[ApplicationResult]:
        """
        Apply to multiple jobs across different platforms.
        
        Args:
            resume_data: Dictionary containing parsed resume information
            jobs: List of jobs to apply to
            
        Returns:
            List of ApplicationResult objects
        """
        results = []
        
        with sync_playwright() as playwright:
            # Launch browser
            browser = playwright.chromium.launch(
                headless=False if self.config.get('debug_mode') else True
            )
            
            # Create context with custom viewport
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )
            
            # Create page
            page = context.new_page()
            
            # Initialize applicators
            self.applicators = [
                # LinkedInApplicator(page, self.config),
                # IndeedApplicator(page, self.config)
                # Outras plataformas podem ser adicionadas aqui futuramente
            ]
            
            # Process each job
            for job in jobs:
                try:
                    # Skip if already applied
                    if self._check_already_applied(job):
                        logger.info(f"Already applied to {job['title']} at {job['company']}")
                        continue
                    
                    # Find appropriate applicator
                    applicator = self._get_applicator(job['url'])
                    if not applicator:
                        logger.warning(f"No applicator found for {job['url']}")
                        continue
                    
                    # Try automated application first
                    logger.info(f"Attempting automated application to {job['title']} at {job['company']}")
                    result = asyncio.run(applicator.apply(job, resume_data))
                    
                    # If automated application failed, try email fallback
                    if result.status != 'success':
                        logger.info(f"Automated application failed, trying email fallback for {job['title']}")
                        email_result = self._try_email_fallback(job, resume_data)
                        if email_result:
                            result = email_result
                    
                    # Save result
                    self._save_application_result(job, result)
                    results.append(result)
                    
                    if result.status == 'success':
                        logger.info(f"Successfully applied to {job['title']} at {job['company']}")
                    else:
                        logger.warning(f"Failed to apply to {job['title']} at {job['company']}: {result.error_message}")
                    
                    # Add delay between applications
                    if self.config.get('application_delay'):
                        time.sleep(float(self.config['application_delay']))
                    
                except Exception as e:
                    logger.error(f"Error applying to {job['title']} at {job['company']}: {str(e)}")
                    continue
            
            # Cleanup
            context.close()
            browser.close()
        
        return results
    
    def _try_email_fallback(self, job: Dict, resume_data: Dict) -> Optional[ApplicationResult]:
        """
        Try to apply via email if automated application failed.
        
        Args:
            job: Job posting data
            resume_data: Resume data
            
        Returns:
            Optional[ApplicationResult]: Result of email application attempt
        """
        try:
            # Extract email from job data
            email = None
            
            # Try to find email in job description
            if 'description' in job:
                email = self.email_sender.extract_email_from_text(job['description'])
            
            # Try to find email in company website
            if not email and 'company_website' in job:
                # TODO: Implement web scraping to find contact email
                pass
            
            if not email:
                logger.warning(f"No contact email found for {job['company']}")
                return None
            
            # Generate email content
            email_content = self.email_generator.generate_application_email(job, resume_data)
            
            # Send email
            success = self.email_sender.send_application_email(
                to_email=email,
                subject=email_content['subject'],
                body=email_content['body'],
                resume_path=self.config['automation']['resume_path'],
                job_data=job
            )
            
            if success:
                return ApplicationResult(
                    company=job['company'],
                    position=job['title'],
                    url=job['url'],
                    status='success',
                    application_id=f"email_{datetime.now().isoformat()}",
                    applied_at=datetime.now()
                )
            else:
                return ApplicationResult(
                    company=job['company'],
                    position=job['title'],
                    url=job['url'],
                    status='failed',
                    error_message='Failed to send application email',
                    applied_at=datetime.now()
                )
                
        except Exception as e:
            logger.error(f"Error in email fallback: {str(e)}")
            return None
    
    def _get_applicator(self, url: str) -> Optional[BaseApplicator]:
        """Get appropriate applicator for the given URL."""
        for applicator in self.applicators:
            if asyncio.run(applicator.is_applicable(url)):
                return applicator
        return None
    
    def _check_already_applied(self, job: Dict) -> bool:
        """Check if already applied to a job."""
        try:
            # Generate filename for application record
            filename = f"{job['platform']}_{job['company']}_{job['title']}".lower()
            filename = "".join(c if c.isalnum() else "_" for c in filename)
            record_file = self.history_dir / f"{filename}.json"
            
            return record_file.exists()
            
        except Exception as e:
            logger.error(f"Error checking application record: {str(e)}")
            return False
    
    def _save_application_result(self, job: Dict, result: ApplicationResult) -> None:
        """Save application result to history."""
        try:
            # Generate filename
            filename = f"{job['platform']}_{job['company']}_{job['title']}".lower()
            filename = "".join(c if c.isalnum() else "_" for c in filename)
            record_file = self.history_dir / f"{filename}.json"
            
            # Create record
            record = {
                "job": job,
                "result": {
                    "status": result.status,
                    "error_message": result.error_message,
                    "application_id": result.application_id,
                    "applied_at": datetime.now().isoformat()
                }
            }
            
            # Save record
            with record_file.open('w') as f:
                json.dump(record, f, indent=2)
            
        except Exception as e:
            logger.error(f"Error saving application result: {str(e)}")
            
    def get_application_stats(self) -> Dict:
        """Get statistics about applications."""
        try:
            stats = {
                "total": 0,
                "success": 0,
                "failed": 0,
                "skipped": 0,
                "by_platform": {},
                "by_company": {},
                "by_method": {
                    "automated": 0,
                    "email": 0
                }
            }
            
            # Process all history files
            for file in self.history_dir.glob("*.json"):
                try:
                    with file.open('r') as f:
                        record = json.load(f)
                    
                    # Update counts
                    stats["total"] += 1
                    status = record["result"]["status"]
                    stats[status] += 1
                    
                    # Update platform stats
                    platform = record["job"]["platform"]
                    if platform not in stats["by_platform"]:
                        stats["by_platform"][platform] = {"total": 0, "success": 0}
                    stats["by_platform"][platform]["total"] += 1
                    if status == "success":
                        stats["by_platform"][platform]["success"] += 1
                    
                    # Update company stats
                    company = record["job"]["company"]
                    if company not in stats["by_company"]:
                        stats["by_company"][company] = {"total": 0, "success": 0}
                    stats["by_company"][company]["total"] += 1
                    if status == "success":
                        stats["by_company"][company]["success"] += 1
                    
                    # Update method stats
                    if record["result"]["application_id"] and record["result"]["application_id"].startswith("email"):
                        stats["by_method"]["email"] += 1
                    else:
                        stats["by_method"]["automated"] += 1
                    
                except Exception as e:
                    logger.error(f"Error processing history file {file}: {str(e)}")
                    continue
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting application stats: {str(e)}")
            return {} 