"""
Configuration settings for the application
"""
from typing import Dict, List, Optional
from pathlib import Path
import json
import os

from pydantic import BaseModel, EmailStr

class TechnicalPreferences(BaseModel):
    """Technical preferences for job matching."""
    role_type: str
    seniority_level: str
    primary_skills: List[str]
    secondary_skills: List[str]
    min_experience_years: int
    max_experience_years: int
    preferred_stack: List[str]

class WorkPreferences(BaseModel):
    """Work preferences for job matching."""
    remote_only: bool
    accept_hybrid: bool
    accept_contract: bool
    accept_fulltime: bool
    accept_parttime: bool
    preferred_languages: List[str]
    preferred_timezones: List[str]

class LocationPreferences(BaseModel):
    """Location preferences for job matching."""
    country: str
    city: str
    state: str
    timezone: str
    willing_to_relocate: bool
    preferred_countries: List[str]

class SalaryPreferences(BaseModel):
    """Salary preferences for job matching."""
    min_salary_usd: int
    preferred_currency: str
    require_salary_range: bool
    accept_equity: bool
    min_equity_percent: float

class ApplicationPreferences(BaseModel):
    """Application preferences."""
    max_applications_per_day: int
    blacklisted_companies: List[str]
    preferred_companies: List[str]
    cover_letter_required: bool
    follow_up_days: int

class EmailConfig(BaseModel):
    """Email configuration."""
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    sender_email: Optional[EmailStr] = None
    sender_name: Optional[str] = None
    use_app_password: bool = True
    email_signature: Optional[str] = None

    @classmethod
    def from_env(cls) -> 'EmailConfig':
        """Create EmailConfig from environment variables."""
        return cls(
            smtp_server=os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            smtp_port=int(os.getenv('SMTP_PORT', '587')),
            smtp_username=os.getenv('SMTP_USERNAME'),
            smtp_password=os.getenv('SMTP_PASSWORD'),
            sender_email=os.getenv('SENDER_EMAIL'),
            sender_name=os.getenv('SENDER_NAME'),
            use_app_password=os.getenv('USE_APP_PASSWORD', 'true').lower() == 'true',
            email_signature=os.getenv('EMAIL_SIGNATURE')
        )

class AutomationConfig(BaseModel):
    """Configuration for automation."""
    debug_mode: bool = False
    automation_delay: float = 2.0
    application_delay: float = 5.0
    resume_path: str = "data/resumes/resume.pdf"
    linkedin_email: Optional[str] = None
    linkedin_password: Optional[str] = None
    indeed_email: Optional[str] = None
    indeed_password: Optional[str] = None
    max_retries: int = 3
    retry_delay: float = 5.0
    screenshot_on_error: bool = True
    screenshot_dir: str = "data/screenshots"
    enable_email_fallback: bool = True
    email_fallback_delay: float = 10.0

class APIConfig(BaseModel):
    """API configuration."""
    groq_api_key: str
    groq_model: str = "llama3-70b-8192"
    groq_temperature: float = 0.3
    groq_max_tokens: int = 1000
    groq_rate_limit: int = 10

class Config(BaseModel):
    """Main configuration class."""
    technical: TechnicalPreferences
    work_preferences: WorkPreferences
    location: LocationPreferences
    salary: SalaryPreferences
    application: ApplicationPreferences
    automation: AutomationConfig
    api: APIConfig
    email: EmailConfig

def load_config() -> Config:
    """Load configuration from file and environment variables."""
    try:
        # Load from config file
        config_file = Path("config/config.json")
        if config_file.exists():
            with config_file.open() as f:
                config_data = json.load(f)
        else:
            config_data = {}
        
        # Override with environment variables
        if os.getenv("GROQ_API_KEY"):
            config_data.setdefault("api", {})["groq_api_key"] = os.getenv("GROQ_API_KEY")
            
        if os.getenv("LINKEDIN_EMAIL"):
            config_data.setdefault("automation", {})["linkedin_email"] = os.getenv("LINKEDIN_EMAIL")
            
        if os.getenv("LINKEDIN_PASSWORD"):
            config_data.setdefault("automation", {})["linkedin_password"] = os.getenv("LINKEDIN_PASSWORD")
            
        if os.getenv("INDEED_EMAIL"):
            config_data.setdefault("automation", {})["indeed_email"] = os.getenv("INDEED_EMAIL")
            
        if os.getenv("INDEED_PASSWORD"):
            config_data.setdefault("automation", {})["indeed_password"] = os.getenv("INDEED_PASSWORD")
            
        if os.getenv("RESUME_PATH"):
            config_data.setdefault("automation", {})["resume_path"] = os.getenv("RESUME_PATH")
            
        if os.getenv("DEBUG_MODE"):
            config_data.setdefault("automation", {})["debug_mode"] = os.getenv("DEBUG_MODE").lower() == "true"
        
        # Load email config from environment
        config_data["email"] = EmailConfig.from_env().dict()
        
        return Config(**config_data)
        
    except Exception as e:
        raise Exception(f"Error loading configuration: {str(e)}")

# Global config instance
config = load_config() 