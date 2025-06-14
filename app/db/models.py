"""Database models for job applications."""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Job(Base):
    """Job posting model."""
    __tablename__ = 'jobs'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    location = Column(String(255))
    description = Column(Text)
    url = Column(String(1024), unique=True)
    platform = Column(String(50))  # linkedin, indeed, etc.
    salary_min = Column(Float)
    salary_max = Column(Float)
    salary_currency = Column(String(10))
    remote = Column(Boolean)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    applications = relationship("Application", back_populates="job")
    
    def __repr__(self):
        return f"<Job(title='{self.title}', company='{self.company}')>"

class Application(Base):
    """Job application model."""
    __tablename__ = 'applications'
    
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey('jobs.id'))
    status = Column(String(50))  # success, failed, skipped
    application_method = Column(String(50))  # direct, email, form
    direct_apply_status = Column(Boolean)
    email_sent_status = Column(Boolean)
    error_message = Column(Text)
    notes = Column(Text)
    applied_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    job = relationship("Job", back_populates="applications")
    
    def __repr__(self):
        return f"<Application(job='{self.job.title}', status='{self.status}')>" 