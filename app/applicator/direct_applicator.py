"""Direct applicator module for handling direct job applications."""
from typing import Dict
import webbrowser
from loguru import logger

class DirectApplicator:
    """Class for handling direct job applications."""
    
    def apply(self, job: Dict) -> bool:
        """Apply to a job via direct application URL.
        
        Args:
            job: Dictionary containing job information
            
        Returns:
            bool: True if application URL was opened successfully, False otherwise
        """
        try:
            # Get application URL
            url = job.get('apply_url') or job.get('url')
            if not url:
                logger.error("No application URL found")
                return False
                
            # Open URL in browser
            webbrowser.open(url)
            logger.info(f"Opened application URL for {job['company']}")
            return True
            
        except Exception as e:
            logger.error(f"Error opening application URL: {str(e)}")
            return False 