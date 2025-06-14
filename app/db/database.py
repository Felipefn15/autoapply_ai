"""Database module for managing job applications."""
import sqlite3
from typing import List, Dict
from pathlib import Path

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
            # Create data directory if it doesn't exist
            Path('data').mkdir(exist_ok=True)
            
            # Connect and create tables
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create applications table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS applications (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT,
                        company TEXT,
                        url TEXT,
                        email TEXT,
                        description TEXT,
                        application_method TEXT,
                        status TEXT DEFAULT 'pending',
                        error TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            raise
            
    def get_pending_applications(self) -> List[Dict]:
        """Get all pending applications."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM applications 
                    WHERE status = 'pending'
                    ORDER BY created_at ASC
                ''')
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error getting pending applications: {str(e)}")
            return []
            
    def mark_as_applied(self, application_id: int):
        """Mark application as successfully applied."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE applications 
                    SET status = 'applied',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (application_id,))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error marking application as applied: {str(e)}")
            
    def mark_as_failed(self, application_id: int, error: str):
        """Mark application as failed with error message."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE applications 
                    SET status = 'failed',
                        error = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (error, application_id))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error marking application as failed: {str(e)}")
            
    def add_application(self, job_data: Dict) -> int:
        """Add a new job application to the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO applications (
                        title, company, url, email, description, application_method, status
                    ) VALUES (?, ?, ?, ?, ?, ?, 'pending')
                ''', (
                    job_data.get('title'),
                    job_data.get('company'),
                    job_data.get('url'),
                    job_data.get('email'),
                    job_data.get('description'),
                    job_data.get('application_method')
                ))
                
                conn.commit()
                return cursor.lastrowid
                
        except Exception as e:
            logger.error(f"Error adding application: {str(e)}")
            return None 