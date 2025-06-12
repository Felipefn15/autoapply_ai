"""Database models for the application."""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Job(Base):
    """Model for storing job postings."""
    __tablename__ = 'jobs'
    
    id = Column(Integer, primary_key=True)
    platform = Column(String(50), nullable=False)  # linkedin, indeed, etc.
    platform_id = Column(String(100), nullable=False)
    title = Column(String(200), nullable=False)
    company = Column(String(200), nullable=False)
    location = Column(String(200))
    description = Column(Text)
    url = Column(String(500), nullable=False)
    contact_email = Column(String(200))
    match_score = Column(Float)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationship with applications
    applications = relationship("Application", back_populates="job")
    
    def __repr__(self):
        return f"<Job(id={self.id}, platform={self.platform}, company={self.company}, title={self.title})>"

class Application(Base):
    """Model for storing job applications."""
    __tablename__ = 'applications'
    
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey('jobs.id'), nullable=False)
    applied_at = Column(DateTime, nullable=False)
    cover_letter = Column(Text)
    status = Column(String(50), default='applied')  # applied, rejected, interview, offer
    status_updated_at = Column(DateTime, default=datetime.now)
    notes = Column(Text)
    
    # Relationship with job
    job = relationship("Job", back_populates="applications")
    
    def __repr__(self):
        return f"<Application(id={self.id}, job_id={self.job_id}, status={self.status})>"
    
    def update_status(self, new_status: str, notes: Optional[str] = None):
        """Update application status with timestamp."""
        self.status = new_status
        self.status_updated_at = datetime.now()
        if notes:
            self.notes = notes 