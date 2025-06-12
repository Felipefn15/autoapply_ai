"""
Settings Module - Configuration for AutoApply.AI
"""
from typing import List, Optional
from pathlib import Path
import json

from pydantic import BaseModel, Field

class TechnicalPreferences(BaseModel):
    """Technical preferences for job search."""
    role_type: str = Field(default="Software Engineer", description="Type of role (e.g. Software Engineer, Data Scientist)")
    seniority_level: str = Field(default="Senior", description="Seniority level (e.g. Junior, Mid, Senior)")
    primary_skills: List[str] = Field(default=["Python", "JavaScript", "React"], description="Primary technical skills")
    secondary_skills: List[str] = Field(default=["Node.js", "TypeScript"], description="Secondary technical skills")
    min_experience_years: int = Field(default=5, description="Minimum years of experience")
    max_experience_years: int = Field(default=15, description="Maximum years of experience")
    preferred_stack: List[str] = Field(default=["Python", "React", "Node.js"], description="Preferred tech stack")

class WorkPreferences(BaseModel):
    """Work preferences for job search."""
    remote_only: bool = Field(default=True, description="Only consider remote positions")
    accept_hybrid: bool = Field(default=False, description="Accept hybrid positions")
    accept_contract: bool = Field(default=True, description="Accept contract positions")
    accept_fulltime: bool = Field(default=True, description="Accept full-time positions")
    accept_parttime: bool = Field(default=False, description="Accept part-time positions")
    preferred_languages: List[str] = Field(default=["English", "Portuguese"], description="Preferred working languages")
    preferred_timezones: List[str] = Field(default=["UTC-3", "UTC-4", "UTC-5"], description="Preferred working timezones")

class LocationPreferences(BaseModel):
    """Location preferences for job search."""
    country: str = Field(default="Brazil", description="Country of residence")
    city: str = Field(default="São Paulo", description="City of residence")
    state: str = Field(default="SP", description="State of residence")
    timezone: str = Field(default="UTC-3", description="Local timezone")
    willing_to_relocate: bool = Field(default=False, description="Willing to relocate")
    preferred_countries: List[str] = Field(default=["USA", "Canada"], description="Preferred countries if willing to relocate")

class SalaryPreferences(BaseModel):
    """Salary preferences for job search."""
    min_salary_usd: int = Field(default=120000, description="Minimum salary in USD")
    preferred_currency: str = Field(default="USD", description="Preferred salary currency")
    require_salary_range: bool = Field(default=True, description="Only consider positions with salary range")
    accept_equity: bool = Field(default=True, description="Accept equity compensation")
    min_equity_percent: float = Field(default=0.1, description="Minimum equity percentage")

class ApplicationPreferences(BaseModel):
    """Application preferences."""
    max_applications_per_day: int = Field(default=10, description="Maximum applications per day")
    blacklisted_companies: List[str] = Field(default=[], description="Companies to exclude")
    preferred_companies: List[str] = Field(default=[], description="Preferred companies")
    cover_letter_required: bool = Field(default=True, description="Generate cover letter for applications")
    follow_up_days: int = Field(default=7, description="Days to wait before follow-up")
    auto_apply: bool = Field(default=False, description="Enable automatic job applications")

class APIConfig(BaseModel):
    """API configuration."""
    groq_api_key: Optional[str] = Field(default=None, description="GROQ API key")
    groq_model: str = Field(default="llama3-70b-8192", description="GROQ model to use")
    groq_temperature: float = Field(default=0.3, description="GROQ temperature parameter")
    groq_max_tokens: int = Field(default=1000, description="GROQ max tokens parameter")
    groq_rate_limit: int = Field(default=10, description="GROQ API calls per minute")

class Config(BaseModel):
    """Main configuration class."""
    technical: TechnicalPreferences = Field(default_factory=TechnicalPreferences)
    work_preferences: WorkPreferences = Field(default_factory=WorkPreferences)
    location: LocationPreferences = Field(default_factory=LocationPreferences)
    salary: SalaryPreferences = Field(default_factory=SalaryPreferences)
    application: ApplicationPreferences = Field(default_factory=ApplicationPreferences)
    api: APIConfig = Field(default_factory=APIConfig)

    @classmethod
    def load(cls, config_file: Path = None) -> 'Config':
        """Load configuration from file."""
        if config_file is None:
            config_file = Path("config.json")
        
        if config_file.exists():
            try:
                with config_file.open('r') as f:
                    data = json.load(f)
                return cls(**data)
            except Exception as e:
                print(f"Error loading config: {str(e)}")
                return cls()
        return cls()
    
    def save(self, config_file: Path = None) -> None:
        """Save configuration to file."""
        if config_file is None:
            config_file = Path("config.json")
        
        try:
            with config_file.open('w') as f:
                json.dump(self.dict(), f, indent=2)
        except Exception as e:
            print(f"Error saving config: {str(e)}")

# Load configuration
config = Config.load() 