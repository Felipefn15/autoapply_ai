"""
Application Logger Module
Comprehensive logging system for job searches and applications
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

from loguru import logger

class ApplicationStatus(Enum):
    """Application status enumeration."""
    PENDING = "pending"
    APPLIED = "applied"
    FAILED = "failed"
    SKIPPED = "skipped"
    INTERVIEW = "interview"
    REJECTED = "rejected"
    ACCEPTED = "accepted"

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
    """Comprehensive application logger."""
    
    def __init__(self, log_dir: str = "data/logs"):
        """Initialize the application logger."""
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.log_dir / "sessions").mkdir(exist_ok=True)
        (self.log_dir / "searches").mkdir(exist_ok=True)
        (self.log_dir / "applications").mkdir(exist_ok=True)
        (self.log_dir / "reports").mkdir(exist_ok=True)
        
        self.current_session = None
        self.session_logs = []
        self.search_logs = []
        self.application_logs = []
        
    def start_session(self, session_id: Optional[str] = None) -> str:
        """Start a new logging session."""
        if not session_id:
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.current_session = session_id
        self.session_logs = []
        self.search_logs = []
        self.application_logs = []
        
        logger.info(f"🚀 Started new application session: {session_id}")
        return session_id
    
    def log_job_search(self, platform: str, keywords: List[str], jobs_found: int, 
                      search_duration: float, errors: List[str] = None) -> None:
        """Log a job search operation."""
        search_log = JobSearchLog(
            timestamp=datetime.now().isoformat(),
            platform=platform,
            keywords=keywords,
            jobs_found=jobs_found,
            search_duration=search_duration,
            errors=errors or [],
            success=len(errors or []) == 0
        )
        
        self.search_logs.append(search_log)
        
        # Log to console
        if search_log.success:
            logger.success(f"✅ {platform}: Found {jobs_found} jobs in {search_duration:.2f}s")
        else:
            logger.warning(f"⚠️ {platform}: Found {jobs_found} jobs with {len(errors)} errors")
            for error in errors:
                logger.error(f"   Error: {error}")
    
    def log_job_application(self, job_title: str, company: str, platform: str, 
                          job_url: str, application_method: str, status: ApplicationStatus,
                          match_score: float, cover_letter_length: int = 0,
                          error_message: Optional[str] = None, 
                          application_duration: float = 0.0) -> None:
        """Log a job application operation."""
        application_log = JobApplicationLog(
            timestamp=datetime.now().isoformat(),
            job_title=job_title,
            company=company,
            platform=platform,
            job_url=job_url,
            application_method=application_method,
            status=status,
            match_score=match_score,
            cover_letter_length=cover_letter_length,
            error_message=error_message,
            application_duration=application_duration,
            success=status in [ApplicationStatus.APPLIED, ApplicationStatus.INTERVIEW, ApplicationStatus.ACCEPTED]
        )
        
        self.application_logs.append(application_log)
        
        # Log to console
        status_emoji = {
            ApplicationStatus.APPLIED: "✅",
            ApplicationStatus.FAILED: "❌",
            ApplicationStatus.SKIPPED: "⏭️",
            ApplicationStatus.INTERVIEW: "🎯",
            ApplicationStatus.REJECTED: "❌",
            ApplicationStatus.ACCEPTED: "🎉"
        }
        
        emoji = status_emoji.get(status, "❓")
        logger.info(f"{emoji} {job_title} at {company} - {status.value} (Score: {match_score:.1%})")
        
        if error_message:
            logger.error(f"   Error: {error_message}")
    
    def end_session(self) -> SessionLog:
        """End the current session and generate summary."""
        if not self.current_session:
            raise ValueError("No active session to end")
        
        end_time = datetime.now().isoformat()
        
        # Calculate session statistics
        total_jobs_found = sum(log.jobs_found for log in self.search_logs)
        total_applications = len(self.application_logs)
        successful_applications = len([log for log in self.application_logs if log.success])
        failed_applications = len([log for log in self.application_logs if log.status == ApplicationStatus.FAILED])
        skipped_applications = len([log for log in self.application_logs if log.status == ApplicationStatus.SKIPPED])
        
        success_rate = (successful_applications / total_applications * 100) if total_applications > 0 else 0
        
        platforms_searched = list(set(log.platform for log in self.search_logs))
        
        # Collect errors and warnings
        errors = []
        warnings = []
        
        for search_log in self.search_logs:
            errors.extend(search_log.errors)
        
        for app_log in self.application_logs:
            if app_log.error_message:
                errors.append(app_log.error_message)
        
        session_log = SessionLog(
            session_id=self.current_session,
            start_time=self.search_logs[0].timestamp if self.search_logs else end_time,
            end_time=end_time,
            total_jobs_found=total_jobs_found,
            total_applications=total_applications,
            successful_applications=successful_applications,
            failed_applications=failed_applications,
            skipped_applications=skipped_applications,
            success_rate=success_rate,
            platforms_searched=platforms_searched,
            search_logs=self.search_logs,
            application_logs=self.application_logs,
            errors=errors,
            warnings=warnings
        )
        
        # Save session log
        self._save_session_log(session_log)
        
        # Generate and save reports
        self._generate_session_report(session_log)
        
        # Generate CSV reports
        csv_report_path = self.generate_csv_report()
        summary_csv_path = self.generate_summary_csv()
        
        # Log summary to console
        logger.info(f"\n📊 SESSION SUMMARY: {self.current_session}")
        logger.info("=" * 60)
        logger.info(f"Total jobs found: {total_jobs_found}")
        logger.info(f"Total applications: {total_applications}")
        logger.info(f"Successful applications: {successful_applications}")
        logger.info(f"Failed applications: {failed_applications}")
        logger.info(f"Skipped applications: {skipped_applications}")
        logger.info(f"Success rate: {success_rate:.1f}%")
        logger.info(f"Platforms searched: {', '.join(platforms_searched)}")
        logger.info(f"📊 CSV Reports:")
        logger.info(f"   📄 Detailed report: {csv_report_path}")
        logger.info(f"   📈 Summary report: {summary_csv_path}")
        
        return session_log
    
    def _save_session_log(self, session_log: SessionLog) -> None:
        """Save session log to file."""
        session_file = self.log_dir / "sessions" / f"{session_log.session_id}.json"
        
        # Convert to dict for JSON serialization
        session_dict = asdict(session_log)
        
        # Convert enums to strings
        for app_log in session_dict['application_logs']:
            app_log['status'] = app_log['status'].value
        
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_dict, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Session log saved: {session_file}")
    
    def _generate_session_report(self, session_log: SessionLog) -> None:
        """Generate a human-readable session report."""
        report_file = self.log_dir / "reports" / f"{session_log.session_id}_report.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("AUTOAPPLY.AI - SESSION REPORT\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Session ID: {session_log.session_id}\n")
            f.write(f"Start Time: {session_log.start_time}\n")
            f.write(f"End Time: {session_log.end_time}\n\n")
            
            f.write("SUMMARY\n")
            f.write("-" * 20 + "\n")
            f.write(f"Total jobs found: {session_log.total_jobs_found}\n")
            f.write(f"Total applications: {session_log.total_applications}\n")
            f.write(f"Successful applications: {session_log.successful_applications}\n")
            f.write(f"Failed applications: {session_log.failed_applications}\n")
            f.write(f"Skipped applications: {session_log.skipped_applications}\n")
            f.write(f"Success rate: {session_log.success_rate:.1f}%\n")
            f.write(f"Platforms searched: {', '.join(session_log.platforms_searched)}\n\n")
            
            f.write("JOB SEARCHES\n")
            f.write("-" * 20 + "\n")
            for search_log in session_log.search_logs:
                f.write(f"Platform: {search_log.platform}\n")
                f.write(f"  Keywords: {', '.join(search_log.keywords)}\n")
                f.write(f"  Jobs found: {search_log.jobs_found}\n")
                f.write(f"  Duration: {search_log.search_duration:.2f}s\n")
                f.write(f"  Success: {search_log.success}\n")
                if search_log.errors:
                    f.write(f"  Errors: {len(search_log.errors)}\n")
                    for error in search_log.errors:
                        f.write(f"    - {error}\n")
                f.write("\n")
            
            f.write("JOB APPLICATIONS\n")
            f.write("-" * 20 + "\n")
            for app_log in session_log.application_logs:
                f.write(f"Job: {app_log.job_title}\n")
                f.write(f"  Company: {app_log.company}\n")
                f.write(f"  Platform: {app_log.platform}\n")
                f.write(f"  Method: {app_log.application_method}\n")
                f.write(f"  Status: {app_log.status.value}\n")
                f.write(f"  Match Score: {app_log.match_score:.1%}\n")
                f.write(f"  Duration: {app_log.application_duration:.2f}s\n")
                if app_log.error_message:
                    f.write(f"  Error: {app_log.error_message}\n")
                f.write("\n")
            
            if session_log.errors:
                f.write("ERRORS\n")
                f.write("-" * 20 + "\n")
                for error in session_log.errors:
                    f.write(f"- {error}\n")
                f.write("\n")
        
        logger.info(f"📄 Session report generated: {report_file}")
    
    def get_recent_sessions(self, limit: int = 10) -> List[SessionLog]:
        """Get recent session logs."""
        session_files = sorted(
            (self.log_dir / "sessions").glob("*.json"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )[:limit]
        
        sessions = []
        for session_file in session_files:
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_dict = json.load(f)
                
                # Convert status strings back to enums
                for app_log in session_dict['application_logs']:
                    app_log['status'] = ApplicationStatus(app_log['status'])
                
                # Reconstruct SessionLog object
                session_log = SessionLog(**session_dict)
                sessions.append(session_log)
                
            except Exception as e:
                logger.error(f"Error loading session {session_file}: {e}")
        
        return sessions
    
    def generate_analytics_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate analytics report for the last N days."""
        sessions = self.get_recent_sessions(limit=100)  # Get more sessions for analysis
        
        # Filter sessions by date
        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
        recent_sessions = [
            s for s in sessions 
            if datetime.fromisoformat(s.start_time).timestamp() > cutoff_date
        ]
        
        if not recent_sessions:
            return {"error": "No sessions found in the specified period"}
        
        # Calculate analytics
        total_sessions = len(recent_sessions)
        total_jobs_found = sum(s.total_jobs_found for s in recent_sessions)
        total_applications = sum(s.total_applications for s in recent_sessions)
        total_successful = sum(s.successful_applications for s in recent_sessions)
        
        avg_success_rate = sum(s.success_rate for s in recent_sessions) / total_sessions
        
        # Platform statistics
        platform_stats = {}
        for session in recent_sessions:
            for search_log in session.search_logs:
                platform = search_log.platform
                if platform not in platform_stats:
                    platform_stats[platform] = {
                        'searches': 0,
                        'jobs_found': 0,
                        'success_rate': 0
                    }
                platform_stats[platform]['searches'] += 1
                platform_stats[platform]['jobs_found'] += search_log.jobs_found
        
        # Calculate platform success rates
        for platform in platform_stats:
            platform_apps = [
                app for session in recent_sessions
                for app in session.application_logs
                if app.platform == platform
            ]
            if platform_apps:
                success_rate = len([app for app in platform_apps if app.success]) / len(platform_apps) * 100
                platform_stats[platform]['success_rate'] = success_rate
        
        analytics = {
            'period_days': days,
            'total_sessions': total_sessions,
            'total_jobs_found': total_jobs_found,
            'total_applications': total_applications,
            'total_successful_applications': total_successful,
            'average_success_rate': avg_success_rate,
            'platform_statistics': platform_stats,
            'recent_sessions': [
                {
                    'session_id': s.session_id,
                    'date': s.start_time[:10],
                    'jobs_found': s.total_jobs_found,
                    'applications': s.total_applications,
                    'success_rate': s.success_rate
                }
                for s in recent_sessions[:10]  # Last 10 sessions
            ]
        }
        
        # Save analytics report
        analytics_file = self.log_dir / "reports" / f"analytics_{days}days.json"
        with open(analytics_file, 'w', encoding='utf-8') as f:
            json.dump(analytics, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📊 Analytics report generated: {analytics_file}")
        return analytics 

    def generate_csv_report(self, output_path: str = None) -> str:
        """Generate a comprehensive CSV report with all job searches and applications."""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"data/logs/autoapply_report_{timestamp}.csv"
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        import csv
        
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Header
            writer.writerow([
                'Data/Hora',
                'Tipo',
                'Plataforma',
                'Título da Vaga',
                'Empresa',
                'URL da Vaga',
                'Método de Aplicação',
                'Status',
                'Score de Match',
                'Duração (s)',
                'Erro',
                'Detalhes'
            ])
            
            # Write search logs
            for search_log in self.search_logs:
                writer.writerow([
                    search_log.timestamp,
                    'BUSCA',
                    search_log.platform,
                    f"Busca por: {', '.join(search_log.keywords)}",
                    'N/A',
                    'N/A',
                    'N/A',
                    'SUCESSO' if not search_log.errors else 'ERRO',
                    'N/A',
                    f"{search_log.search_duration:.2f}",
                    '; '.join(search_log.errors) if search_log.errors else '',
                    f"Encontradas: {search_log.jobs_found} vagas"
                ])
            
            # Write application logs
            for app_log in self.application_logs:
                writer.writerow([
                    app_log.timestamp,
                    'CANDIDATURA',
                    app_log.platform,
                    app_log.job_title,
                    app_log.company,
                    app_log.job_url,
                    app_log.application_method,
                    app_log.status.value.upper(),
                    f"{app_log.match_score:.1%}",
                    f"{app_log.application_duration:.2f}",
                    app_log.error_message if app_log.error_message else '',
                    f"Cover letter: {app_log.cover_letter_length} chars" if app_log.cover_letter_length > 0 else 'N/A'
                ])
        
        logger.info(f"📊 Relatório CSV gerado: {output_path}")
        return str(output_path)
    
    def generate_summary_csv(self, output_path: str = None) -> str:
        """Generate a summary CSV with key metrics."""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"data/logs/autoapply_summary_{timestamp}.csv"
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        import csv
        
        # Calculate metrics
        total_jobs_found = sum(log.jobs_found for log in self.search_logs)
        total_applications = len(self.application_logs)
        successful_applications = len([log for log in self.application_logs if log.success])
        failed_applications = len([log for log in self.application_logs if log.status == ApplicationStatus.FAILED])
        skipped_applications = len([log for log in self.application_logs if log.status == ApplicationStatus.SKIPPED])
        
        platforms_searched = list(set(log.platform for log in self.search_logs))
        platforms_applied = list(set(log.platform for log in self.application_logs))
        
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Summary metrics
            writer.writerow(['Métrica', 'Valor'])
            writer.writerow(['Data/Hora Execução', datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
            writer.writerow(['Sessão ID', self.current_session])
            writer.writerow(['Total Vagas Encontradas', total_jobs_found])
            writer.writerow(['Total Candidaturas', total_applications])
            writer.writerow(['Candidaturas Bem-sucedidas', successful_applications])
            writer.writerow(['Candidaturas Falharam', failed_applications])
            writer.writerow(['Candidaturas Puladas', skipped_applications])
            writer.writerow(['Taxa de Sucesso', f"{(successful_applications/total_applications*100):.1f}%" if total_applications > 0 else "0%"])
            writer.writerow(['Plataformas Buscadas', ', '.join(platforms_searched)])
            writer.writerow(['Plataformas com Candidaturas', ', '.join(platforms_applied)])
            
            # Platform breakdown
            writer.writerow([])
            writer.writerow(['Plataforma', 'Vagas Encontradas', 'Candidaturas', 'Sucessos', 'Falhas'])
            
            platform_stats = {}
            for search_log in self.search_logs:
                platform = search_log.platform
                if platform not in platform_stats:
                    platform_stats[platform] = {'jobs': 0, 'applications': 0, 'successes': 0, 'failures': 0}
                platform_stats[platform]['jobs'] += search_log.jobs_found
            
            for app_log in self.application_logs:
                platform = app_log.platform
                if platform not in platform_stats:
                    platform_stats[platform] = {'jobs': 0, 'applications': 0, 'successes': 0, 'failures': 0}
                platform_stats[platform]['applications'] += 1
                if app_log.success:
                    platform_stats[platform]['successes'] += 1
                elif app_log.status == ApplicationStatus.FAILED:
                    platform_stats[platform]['failures'] += 1
            
            for platform, stats in platform_stats.items():
                writer.writerow([
                    platform,
                    stats['jobs'],
                    stats['applications'],
                    stats['successes'],
                    stats['failures']
                ])
        
        logger.info(f"📈 Resumo CSV gerado: {output_path}")
        return str(output_path) 