"""
Application Logger - Manages detailed logs for job applications
"""
from datetime import datetime
import json
from pathlib import Path
from typing import Dict, Optional
from loguru import logger

class ApplicationLogger:
    """Manages detailed logs for job applications."""
    
    def __init__(self, log_dir: str = "data/applications"):
        """Initialize the logger."""
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.current_session = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.applications_log = []
        
    def log_application(self, 
                       job: Dict,
                       status: str,
                       method: str,
                       error: Optional[str] = None,
                       notes: Optional[str] = None) -> None:
        """
        Log an application attempt.
        
        Args:
            job: Job data dictionary
            status: Application status (success, failed, skipped)
            method: Application method (direct, email)
            error: Optional error message
            notes: Optional additional notes
        """
        # Create log entry
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "job_title": job.get("title", "Unknown"),
            "company": job.get("company", "Unknown"),
            "location": job.get("location", "Unknown"),
            "url": job.get("url", ""),
            "platform": job.get("platform", "Unknown"),
            "status": status,
            "method": method,
            "error": error,
            "notes": notes
        }
        
        # Add to memory
        self.applications_log.append(log_entry)
        
        # Log to console with formatting
        self._print_log_entry(log_entry)
        
        # Save to file
        self._save_logs()
        
    def _print_log_entry(self, entry: Dict) -> None:
        """Print a formatted log entry to console."""
        status_colors = {
            "success": "🟢",
            "failed": "🔴",
            "skipped": "🟡"
        }
        
        method_icons = {
            "direct": "🌐",
            "email": "📧",
            "form": "📝"
        }
        
        logger.info("\nApplication Attempt:")
        logger.info("=" * 50)
        logger.info(f"{status_colors.get(entry['status'].lower(), '⚪')} Status: {entry['status'].upper()}")
        logger.info(f"🕒 Time: {datetime.fromisoformat(entry['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"🎯 Position: {entry['job_title']}")
        logger.info(f"🏢 Company: {entry['company']}")
        logger.info(f"📍 Location: {entry['location']}")
        logger.info(f"🔗 URL: {entry['url']}")
        logger.info(f"⚡ Platform: {entry['platform']}")
        logger.info(f"{method_icons.get(entry['method'], '❓')} Method: {entry['method']}")
        
        if entry['error']:
            logger.info(f"❌ Error: {entry['error']}")
        
        if entry['notes']:
            logger.info(f"📝 Notes: {entry['notes']}")
            
        logger.info("-" * 50)
        
    def _save_logs(self) -> None:
        """Save logs to JSON file."""
        # Save detailed JSON
        json_file = self.log_dir / f"applications_{self.current_session}.json"
        with open(json_file, "w") as f:
            json.dump(self.applications_log, f, indent=2)
            
        # Save human-readable report
        report_file = self.log_dir / f"applications_report_{self.current_session}.txt"
        with open(report_file, "w") as f:
            f.write("AutoApply.AI - Application Report\n")
            f.write("=" * 50 + "\n\n")
            
            # Summary
            total = len(self.applications_log)
            successful = sum(1 for log in self.applications_log if log["status"].lower() == "success")
            failed = sum(1 for log in self.applications_log if log["status"].lower() == "failed")
            skipped = sum(1 for log in self.applications_log if log["status"].lower() == "skipped")
            
            f.write(f"Total Applications: {total}\n")
            f.write(f"Successful: {successful}\n")
            f.write(f"Failed: {failed}\n")
            f.write(f"Skipped: {skipped}\n\n")
            
            # Detailed logs
            f.write("Detailed Application Log\n")
            f.write("=" * 50 + "\n\n")
            
            for entry in self.applications_log:
                f.write(f"Position: {entry['job_title']}\n")
                f.write(f"Company: {entry['company']}\n")
                f.write(f"Status: {entry['status'].upper()}\n")
                f.write(f"Method: {entry['method']}\n")
                f.write(f"Time: {datetime.fromisoformat(entry['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"URL: {entry['url']}\n")
                
                if entry['error']:
                    f.write(f"Error: {entry['error']}\n")
                
                if entry['notes']:
                    f.write(f"Notes: {entry['notes']}\n")
                    
                f.write("-" * 50 + "\n\n")
                
    def get_summary(self) -> Dict:
        """Get application summary statistics."""
        total = len(self.applications_log)
        successful = sum(1 for log in self.applications_log if log["status"].lower() == "success")
        failed = sum(1 for log in self.applications_log if log["status"].lower() == "failed")
        skipped = sum(1 for log in self.applications_log if log["status"].lower() == "skipped")
        
        return {
            "total": total,
            "successful": successful,
            "failed": failed,
            "skipped": skipped,
            "success_rate": (successful / total * 100) if total > 0 else 0
        } 