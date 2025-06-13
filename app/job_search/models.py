"""Job posting model."""
from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class JobPosting:
    """Job posting model."""
    
    title: str
    description: str
    email: Optional[str] = None
    url: Optional[str] = None  # mantido para referência

    def __post_init__(self):
        """Post initialization processing."""
        # Normalize fields
        self.title = self.title.strip()
        self.description = self.description.strip()
        if self.email:
            self.email = self.email.strip()

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'JobPosting':
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in ['title', 'description', 'email', 'url']}) 