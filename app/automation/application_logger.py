"""
Application Logger Module
Comprehensive logging system for job searches and applications
"""
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
from enum import Enum
from dataclasses import dataclass
import hashlib

from loguru import logger

class ApplicationStatus(Enum):
    """Application status enum."""
    PENDING = "pending"
    APPLIED = "applied"
    FAILED = "failed"
    SKIPPED = "skipped"
    DUPLICATE = "duplicate"  # New status for duplicate jobs
    ALREADY_APPLIED = "already_applied"  # New status for previously applied jobs

@dataclass
class JobSearchLog:
    """Log entry for job search operations."""
    timestamp: str
    platform: str
    keywords: List[str]
    jobs_found: int
    search_duration: float
    errors: List[str]
    success: bool

@dataclass
class JobApplicationLog:
    """Log entry for job application operations."""
    timestamp: str
    job_title: str
    company: str
    platform: str
    job_url: str
    application_method: str
    status: ApplicationStatus
    match_score: float
    cover_letter_length: int
    error_message: Optional[str]
    application_duration: float
    success: bool

@dataclass
class SessionLog:
    """Complete session log with all operations."""
    session_id: str
    start_time: str
    end_time: str
    total_jobs_found: int
    total_applications: int
    successful_applications: int
    failed_applications: int
    skipped_applications: int
    success_rate: float
    platforms_searched: List[str]
    search_logs: List[JobSearchLog]
    application_logs: List[JobApplicationLog]
    errors: List[str]
    warnings: List[str]

class ApplicationLogger:
    """Application logger for tracking job applications."""
    
    def __init__(self):
        """Initialize the application logger."""
        self.session_id = None
        self.session_start_time = None
        self.search_logs: List[JobSearchLog] = []
        self.application_logs: List[JobApplicationLog] = []
        self.session_log = None
        
        # Anti-duplication system
        self.applied_jobs: Set[str] = set()  # Set of job hashes already applied to
        self.job_history: Dict[str, Dict] = {}  # Job history with details
        self.duplicate_count = 0
        self.already_applied_count = 0
        
        # Load existing application history
        self._load_application_history()
    
    def start_session(self) -> str:
        """Start a new application session."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.session_id = f"session_{timestamp}"
            self.session_start_time = datetime.now()
            
            # Reset session-specific counters
            self.duplicate_count = 0
            self.already_applied_count = 0
            
            logger.info(f"🚀 Started new application session: {self.session_id}")
            return self.session_id
            
        except Exception as e:
            logger.error(f"❌ Error starting session: {str(e)}")
            return "error_session"
    
    def log_job_search(self, platform: str, keywords: List[str], jobs_found: int, 
                       search_duration: float, errors: List[str] = None, success: bool = True) -> str:
        """
        Log a job search operation.
        
        Args:
            platform: Job platform/source
            keywords: List of keywords used for the search
            jobs_found: Number of jobs found
            search_duration: Duration of the search in seconds
            errors: List of errors encountered during search
            success: Boolean indicating if the search was successful
            
        Returns:
            str: Search ID
        """
        try:
            search_id = f"search_{int(time.time())}_{len(self.search_logs)}"
            search_log = JobSearchLog(
                timestamp=datetime.now().isoformat(),
                platform=platform,
                keywords=keywords,
                jobs_found=jobs_found,
                search_duration=search_duration,
                errors=errors if errors else [],
                success=success
            )
            self.search_logs.append(search_log)
            logger.info(f"📊 Logged search: {platform} - {len(keywords)} keywords")
            return search_id
        except Exception as e:
            logger.error(f"❌ Error logging job search: {str(e)}")
            return f"error_search_{int(time.time())}"
    
    def _load_application_history(self):
        """Load existing application history to avoid duplicates."""
        try:
            history_file = Path("data/logs/application_history.json")
            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                    self.applied_jobs = set(history.get('applied_jobs', []))
                    self.job_history = history.get('job_history', {})
                    logger.info(f"📚 Loaded {len(self.applied_jobs)} previous applications from history")
        except Exception as e:
            logger.warning(f"⚠️ Could not load application history: {str(e)}")
    
    def _save_application_history(self):
        """Save current application history to avoid future duplicates."""
        try:
            history_file = Path("data/logs/application_history.json")
            history_file.parent.mkdir(parents=True, exist_ok=True)
            
            history = {
                'applied_jobs': list(self.applied_jobs),
                'job_history': self.job_history,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
                
            logger.info(f"💾 Application history saved with {len(self.applied_jobs)} jobs")
        except Exception as e:
            logger.error(f"❌ Error saving application history: {str(e)}")
    
    def _generate_job_hash(self, job_data: Dict) -> str:
        """Generate a unique hash for a job to identify duplicates."""
        try:
            # Create a unique identifier based on key job attributes
            key_fields = [
                job_data.get('title', '').lower().strip(),
                job_data.get('company', '').lower().strip(),
                job_data.get('url', '').strip()
            ]
            
            # Clean and normalize fields
            cleaned_fields = [field.replace(' ', '').replace('-', '').replace('_', '') for field in key_fields if field]
            
            # Generate hash
            job_string = '|'.join(cleaned_fields)
            return hashlib.md5(job_string.encode('utf-8')).hexdigest()
        except Exception as e:
            logger.error(f"❌ Error generating job hash: {str(e)}")
            # Fallback to URL hash
            return hashlib.md5(job_data.get('url', '').encode('utf-8')).hexdigest()
    
    def _is_duplicate_job(self, job_data: Dict) -> tuple[bool, Optional[str], Optional[str]]:
        """
        Check if a job is a duplicate or already applied to.
        
        Returns:
            tuple: (is_duplicate, duplicate_type, existing_job_hash)
        """
        job_hash = self._generate_job_hash(job_data)
        
        # Check if already applied to this exact job
        if job_hash in self.applied_jobs:
            return True, "already_applied", job_hash
        
        # Check for similar jobs (same company + similar title)
        company = job_data.get('company', 'Unknown').lower().strip()
        title = job_data.get('title', '').lower().strip()
        
        for existing_hash, existing_job in self.job_history.items():
            existing_company = existing_job.get('company', 'Unknown').lower().strip()
            existing_title = existing_job.get('title', '').lower().strip()
            
            # Check if same company and similar title
            if (company and existing_company and company == existing_company and
                title and existing_title and self._similar_titles(title, existing_title)):
                return True, "duplicate", existing_hash
        
        return False, None, None
    
    def _similar_titles(self, title1: str, title2: str) -> bool:
        """Check if two job titles are similar (potential duplicates)."""
        try:
            # Normalize titles
            t1 = title1.lower().replace('-', ' ').replace('_', ' ').strip()
            t2 = title2.lower().replace('-', ' ').replace('_', ' ').strip()
            
            # Split into words
            words1 = set(t1.split())
            words2 = set(t2.split())
            
            # Calculate similarity
            if not words1 or not words2:
                return False
            
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            
            similarity = len(intersection) / len(union)
            
            # Consider similar if >70% similarity
            return similarity > 0.7
        except Exception:
            return False
    
    def log_job_application(self, job_data: Dict, status: ApplicationStatus, 
                           match_score: float = 0.0, error: str = None, 
                           platform: str = "Unknown") -> str:
        """
        Log a job application with anti-duplication check.
        
        Args:
            job_data: Job information dictionary
            status: Application status
            match_score: Job match score
            error: Error message if any
            platform: Job platform/source
            
        Returns:
            str: Application ID
        """
        try:
            # Check for duplicates before logging
            is_duplicate, duplicate_type, existing_hash = self._is_duplicate_job(job_data)
            
            if is_duplicate:
                if duplicate_type == "already_applied":
                    status = ApplicationStatus.ALREADY_APPLIED
                    self.already_applied_count += 1
                    logger.warning(f"⚠️ Already applied to: {job_data.get('title', 'Unknown')} at {job_data.get('company', 'Unknown')}")
                else:
                    status = ApplicationStatus.DUPLICATE
                    self.duplicate_count += 1
                    logger.warning(f"⚠️ Duplicate job detected: {job_data.get('title', 'Unknown')} at {job_data.get('company', 'Unknown')}")
            
            # Generate application ID
            application_id = f"app_{int(time.time())}_{len(self.application_logs)}"
            
            # Create application log with correct structure
            application_log = JobApplicationLog(
                timestamp=datetime.now().isoformat(),
                job_title=job_data.get('title', 'Unknown'),
                company=job_data.get('company', 'Unknown'),
                platform=platform,
                job_url=job_data.get('url', ''),
                application_method="AutoApply.AI",
                status=status,
                match_score=match_score,
                cover_letter_length=0,
                error_message=error,
                application_duration=0.0,
                success=(status == ApplicationStatus.APPLIED)
            )
            
            self.application_logs.append(application_log)
            
            # If this is a new successful application, add to history
            if status == ApplicationStatus.APPLIED and not is_duplicate:
                job_hash = self._generate_job_hash(job_data)
                self.applied_jobs.add(job_hash)
                self.job_history[job_hash] = {
                    'title': job_data.get('title', ''),
                    'company': job_data.get('company', ''),
                    'url': job_data.get('url', ''),
                    'platform': platform,
                    'applied_at': datetime.now().isoformat(),
                    'match_score': match_score
                }
                
                # Save history after each new application
                self._save_application_history()
            
            logger.info(f"📝 Logged application: {job_data.get('title', 'Unknown')} - {status.value}")
            return application_id
            
        except Exception as e:
            logger.error(f"❌ Error logging job application: {str(e)}")
            return f"error_{int(time.time())}" 

    def end_session(self) -> Dict:
        """End the current session and generate final report."""
        if not self.session_id:
            logger.warning("⚠️ No active session to end")
            return {}
        
        try:
            end_time = datetime.now()
            session_duration = (end_time - self.session_start_time).total_seconds()
            
            # Calculate statistics including duplicates
            total_applications = len(self.application_logs)
            successful_applications = len([app for app in self.application_logs if app.status == ApplicationStatus.APPLIED])
            failed_applications = len([app for app in self.application_logs if app.status == ApplicationStatus.FAILED])
            skipped_applications = len([app for app in self.application_logs if app.status == ApplicationStatus.SKIPPED])
            duplicate_applications = len([app for app in self.application_logs if app.status == ApplicationStatus.DUPLICATE])
            already_applied = len([app for app in self.application_logs if app.status == ApplicationStatus.ALREADY_APPLIED])
            
            # Calculate success rate excluding duplicates and already applied
            effective_applications = total_applications - duplicate_applications - already_applied
            success_rate = (successful_applications / effective_applications * 100) if effective_applications > 0 else 0
            
            # Get unique platforms
            platforms = list(set([log.platform for log in self.search_logs]))
            
            # Create session log
            self.session_log = SessionLog(
                session_id=self.session_id,
                start_time=self.session_start_time.isoformat(),
                end_time=end_time.isoformat(),
                total_jobs_found=sum(log.jobs_found for log in self.search_logs),
                total_applications=total_applications,
                successful_applications=successful_applications,
                failed_applications=failed_applications,
                skipped_applications=skipped_applications,
                success_rate=success_rate,
                platforms_searched=platforms,
                search_logs=self.search_logs,
                application_logs=self.application_logs,
                errors=[],
                warnings=[]
            )
            
            # Save session log
            self._save_session_log()
            
            # Generate reports
            self._generate_session_report()
            
            # Generate CSV reports
            csv_report_path = self.generate_csv_report()
            summary_csv_path = self.generate_summary_csv()
            
            # Log final summary with anti-duplication stats
            logger.info("")
            logger.info("📊 SESSION SUMMARY: " + self.session_id)
            logger.info("=" * 60)
            logger.info(f"Total jobs found: {self.session_log.total_jobs_found}")
            logger.info(f"Total applications: {total_applications}")
            logger.info(f"✅ Successful applications: {successful_applications}")
            logger.info(f"❌ Failed applications: {failed_applications}")
            logger.info(f"⏭️ Skipped applications: {skipped_applications}")
            logger.info(f"🔄 Duplicate jobs detected: {duplicate_applications}")
            logger.info(f"📚 Already applied jobs: {already_applied}")
            logger.info(f"📈 Effective success rate: {success_rate:.1f}%")
            logger.info(f"🌐 Platforms searched: {', '.join(platforms)}")
            logger.info("📊 CSV Reports:")
            logger.info(f"   📄 Detailed report: {csv_report_path}")
            logger.info(f"   📈 Summary report: {summary_csv_path}")
            
            # Save final application history
            self._save_application_history()
            
            return self.session_log.__dict__
            
        except Exception as e:
            logger.error(f"❌ Error ending session: {str(e)}")
            return {}
    
    def _save_session_log(self):
        """Save the current session log to file."""
        try:
            if not self.session_log:
                return
            
            # Create logs directory if it doesn't exist
            logs_dir = Path("data/logs")
            logs_dir.mkdir(parents=True, exist_ok=True)
            
            # Save session log as JSON
            session_file = logs_dir / f"session_{self.session_id}_log.json"
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(self.session_log.__dict__, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"💾 Session log saved: {session_file}")
            
        except Exception as e:
            logger.error(f"❌ Error saving session log: {str(e)}")
    
    def _generate_session_report(self):
        """Generate a text report for the current session."""
        try:
            if not self.session_log:
                return
            
            # Create reports directory
            reports_dir = Path("data/logs/reports")
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate report content
            report_content = f"""
📊 SESSION REPORT: {self.session_log.session_id}
{'=' * 60}

📅 Session Details:
   Start Time: {self.session_log.start_time}
   End Time: {self.session_log.end_time}
   Duration: {self.session_log.end_time} - {self.session_log.start_time}

🔍 Search Summary:
   Total Jobs Found: {self.session_log.total_jobs_found}
   Platforms Searched: {', '.join(self.session_log.platforms_searched)}

📝 Application Summary:
   Total Applications: {self.session_log.total_applications}
   Successful: {self.session_log.successful_applications}
   Failed: {self.session_log.failed_applications}
   Skipped: {self.session_log.skipped_applications}
   Success Rate: {self.session_log.success_rate:.1f}%

🔄 Anti-Duplication Stats:
   Duplicate Jobs Detected: {len([app for app in self.application_logs if app.status == ApplicationStatus.DUPLICATE])}
   Already Applied Jobs: {len([app for app in self.application_logs if app.status == ApplicationStatus.ALREADY_APPLIED])}

📋 Application Details:
"""
            
            # Add application details
            for i, app in enumerate(self.application_logs, 1):
                report_content += f"""
{i}. {app.job_title} - {app.company}
   Platform: {app.platform}
   Status: {app.status.value}
   Match Score: {app.match_score:.1f}%
   URL: {app.job_url}
"""
            
            # Save report
            report_file = reports_dir / f"session_{self.session_id}_report.txt"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            logger.info(f"📄 Session report generated: {report_file}")
            
        except Exception as e:
            logger.error(f"❌ Error generating session report: {str(e)}")
    
    def generate_csv_report(self) -> str:
        """Generate a detailed CSV report for the current session."""
        try:
            import csv
            
            # Create logs directory
            logs_dir = Path("data/logs")
            logs_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_file = logs_dir / f"autoapply_report_{timestamp}.csv"
            
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow([
                    'Timestamp', 'Job Title', 'Company', 'Platform', 'URL',
                    'Status', 'Match Score', 'Application Method', 'Error Message'
                ])
                
                # Write data
                for app in self.application_logs:
                    writer.writerow([
                        app.timestamp,
                        app.job_title,
                        app.company,
                        app.platform,
                        app.job_url,
                        app.status.value,
                        f"{app.match_score:.1f}%",
                        app.application_method,
                        app.error_message or ''
                    ])
            
            logger.info(f"📊 CSV report generated: {csv_file}")
            return str(csv_file)
            
        except Exception as e:
            logger.error(f"❌ Error generating CSV report: {str(e)}")
            return ""
    
    def generate_summary_csv(self) -> str:
        """Generate a summary CSV report for the current session."""
        try:
            import csv
            
            # Create logs directory
            logs_dir = Path("data/logs")
            logs_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_file = logs_dir / f"autoapply_summary_{timestamp}.csv"
            
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow([
                    'Metric', 'Value'
                ])
                
                # Write summary data
                summary_data = [
                    ['Session ID', self.session_id],
                    ['Start Time', self.session_start_time.isoformat() if self.session_start_time else ''],
                    ['End Time', datetime.now().isoformat()],
                    ['Total Jobs Found', sum(log.jobs_found for log in self.search_logs)],
                    ['Total Applications', len(self.application_logs)],
                    ['Successful Applications', len([app for app in self.application_logs if app.status == ApplicationStatus.APPLIED])],
                    ['Failed Applications', len([app for app in self.application_logs if app.status == ApplicationStatus.FAILED])],
                    ['Skipped Applications', len([app for app in self.application_logs if app.status == ApplicationStatus.SKIPPED])],
                    ['Duplicate Jobs Detected', len([app for app in self.application_logs if app.status == ApplicationStatus.DUPLICATE])],
                    ['Already Applied Jobs', len([app for app in self.application_logs if app.status == ApplicationStatus.ALREADY_APPLIED])],
                    ['Platforms Searched', ', '.join(set(log.platform for log in self.search_logs))]
                ]
                
                for row in summary_data:
                    writer.writerow(row)
            
            logger.info(f"📈 Summary CSV generated: {csv_file}")
            return str(csv_file)
            
        except Exception as e:
            logger.error(f"❌ Error generating summary CSV: {str(e)}")
            return ""