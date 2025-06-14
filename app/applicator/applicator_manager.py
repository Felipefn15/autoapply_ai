"""Applicator manager module for handling different types of job applications."""
from typing import Dict, Optional
from loguru import logger

from app.applicator.email_applicator import EmailApplicator
from app.applicator.direct_applicator import DirectApplicator

class ApplicatorManager:
    """Manager class for handling different types of job applications."""
    
    def __init__(self):
        """Initialize applicator manager."""
        self.applicators = {
            'email': EmailApplicator(),
            'direct': DirectApplicator()
        }
    
    def apply(self, job: Dict) -> bool:
        """Apply to a job using the appropriate applicator.
        
        Args:
            job: Dictionary containing job information
            
        Returns:
            bool: True if application was successful, False otherwise
        """
        try:
            # Get application method
            method = job.get('application_method', 'unknown')
            
            # Get appropriate applicator
            applicator = self.applicators.get(method)
            if not applicator:
                logger.error(f"No applicator found for method: {method}")
                return False
                
            # Apply to job
            return applicator.apply(job)
            
        except Exception as e:
            logger.error(f"Error applying to job: {str(e)}")
            return False 