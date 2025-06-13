"""Job posting model."""
from dataclasses import dataclass, asdict
from typing import List, Optional
import re

@dataclass
class JobPosting:
    """Job posting model."""
    
    title: str
    company: str
    location: str
    description: str
    requirements: List[str]
    url: str
    source: str
    remote: bool
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None

    def __post_init__(self):
        """Post initialization processing."""
        # Clean requirements
        self.requirements = [r.strip() for r in self.requirements if r.strip()]
        
        # Ensure remote is boolean
        self.remote = bool(self.remote)
        
        # Normalize fields
        self.title = self.title.strip()
        self.company = self.company.strip()
        self.location = self.location.strip()
        self.description = self.description.strip()
        
        # Check for remote in title/location
        self.remote = self.remote or 'remote' in self.title.lower() or 'remote' in self.location.lower()

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'JobPosting':
        """Create from dictionary."""
        return cls(**data) 