"""Database module for managing job applications."""
import sqlite3
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime

from loguru import logger

class Database:
    """Database manager for job applications."""
    
    def __init__(self, db_path: str = 'data/applications.db'):
        """Initialize database connection."""
        self.db_path = db_path
        self._ensure_db_exists()
        
    def _ensure_db_exists(self):
        """Ensure database and tables exist."""
        try:
            Path('data').mkdir(exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create jobs table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS jobs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        company TEXT NOT NULL,
                        location TEXT,
                        description TEXT,
                        url TEXT,
                        apply_url TEXT,
                        salary_min REAL,
                        salary_max REAL,
                        remote BOOLEAN,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(title, company)
                    )
                """)
                
                # Create applications table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS applications (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        job_id INTEGER NOT NULL,
                        match_score REAL NOT NULL,
                        method TEXT NOT NULL,
                        status TEXT NOT NULL,
                        error TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (job_id) REFERENCES jobs (id),
                        UNIQUE(job_id)
                    )
                """)
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error ensuring database exists: {str(e)}")
            raise
            
    def add_job(self, job: Dict) -> Optional[int]:
        """Add a job to the database.
        
        Args:
            job: Dictionary containing job information
            
        Returns:
            int: ID of the added job, or None if failed
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insert job
                cursor.execute("""
                    INSERT OR IGNORE INTO jobs (
                        title, company, location, description,
                        url, apply_url, salary_min, salary_max, remote
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    job.get('title'),
                    job.get('company', 'Unknown'),
                    job.get('location'),
                    job.get('description'),
                    job.get('url'),
                    job.get('apply_url'),
                    job.get('salary_min'),
                    job.get('salary_max'),
                    job.get('remote', False)
                ))
                
                # Get job ID (either newly inserted or existing)
                if cursor.rowcount > 0:
                    return cursor.lastrowid
                else:
                    cursor.execute("""
                        SELECT id FROM jobs
                        WHERE title = ? AND company = ?
                    """, (job.get('title'), job.get('company', 'Unknown')))
                    result = cursor.fetchone()
                    return result[0] if result else None
                    
        except Exception as e:
            logger.error(f"Error adding job: {str(e)}")
            return None
            
    def add_application(self, job_id: int, match_score: float, method: str, status: str) -> bool:
        """Add an application to the database.
        
        Args:
            job_id: ID of the job being applied to
            match_score: Match score for the job (0-100)
            method: Application method (email, direct, etc.)
            status: Application status (pending, applied, failed)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO applications (
                        job_id, match_score, method, status
                    ) VALUES (?, ?, ?, ?)
                """, (job_id, match_score, method, status))
                
                return True
                
        except Exception as e:
            logger.error(f"Error adding application: {str(e)}")
            return False
            
    def mark_as_failed(self, job_id: int, error: str) -> bool:
        """Mark an application as failed.
        
        Args:
            job_id: ID of the job
            error: Error message
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE applications
                    SET status = 'failed', error = ?
                    WHERE job_id = ?
                """, (error, job_id))
                
                return True
                
        except Exception as e:
            logger.error(f"Error marking application as failed: {str(e)}")
            return False
            
    def mark_as_applied(self, job_id: int) -> bool:
        """Mark an application as applied.
        
        Args:
            job_id: ID of the job
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE applications
                    SET status = 'applied'
                    WHERE job_id = ?
                """, (job_id,))
                
                return True
                
        except Exception as e:
            logger.error(f"Error marking application as applied: {str(e)}")
            return False
            
    def get_pending_applications(self) -> List[Dict]:
        """Get all pending applications.
        
        Returns:
            List[Dict]: List of pending applications
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        a.id as application_id,
                        a.match_score,
                        a.method,
                        j.*
                    FROM applications a
                    JOIN jobs j ON a.job_id = j.id
                    WHERE a.status = 'pending'
                    ORDER BY a.match_score DESC
                """)
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error getting pending applications: {str(e)}")
            return []
            
    def get_application_by_title_company(self, title: str, company: str) -> Dict:
        """Get application by title and company."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute(
                    'SELECT * FROM applications WHERE title = ? AND company = ?',
                    (title, company)
                )
                row = cursor.fetchone()
                
                return dict(row) if row else None
                
        except Exception as e:
            logger.error(f"Error getting application by title and company: {str(e)}")
            return None 