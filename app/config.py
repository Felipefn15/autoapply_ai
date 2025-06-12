"""
Configuration module for AutoApply.AI
"""
import os
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LocationConfig(BaseModel):
    """Location settings configuration."""
    country: str = Field(default="Brazil")
    city: str = Field(default="São Paulo")
    timezone: str = Field(default="America/Sao_Paulo")

class SalaryConfig(BaseModel):
    """Salary preferences configuration."""
    min_salary_usd: int = Field(default=80000)
    max_salary_usd: int = Field(default=200000)
    preferred_currency: str = Field(default="USD")
    
class WorkPreferences(BaseModel):
    """Work preferences configuration."""
    remote_only: bool = Field(default=True)
    accept_hybrid: bool = Field(default=False)
    work_timezone_range: tuple[int, int] = Field(default=(-3, 3))
    preferred_languages: List[str] = Field(default=["Portuguese", "English"])
    accept_contract: bool = Field(default=True)
    accept_fulltime: bool = Field(default=True)
    accept_parttime: bool = Field(default=False)

class TechnicalPreferences(BaseModel):
    """Technical preferences configuration."""
    experience_years: int = Field(default=5)
    seniority_level: str = Field(default="Senior")
    primary_skills: List[str] = Field(default=[
        "Python", "JavaScript", "React", "Node.js"
    ])
    secondary_skills: List[str] = Field(default=[
        "AWS", "Docker", "Kubernetes"
    ])

class ApplicationConfig(BaseModel):
    """Application settings configuration."""
    auto_apply: bool = Field(default=False)
    max_applications_per_day: int = Field(default=10)
    blacklisted_companies: List[str] = Field(default=[])
    preferred_companies: List[str] = Field(default=[])

class Config(BaseModel):
    """Main configuration class."""
    location: LocationConfig = Field(default_factory=LocationConfig)
    salary: SalaryConfig = Field(default_factory=SalaryConfig)
    work_preferences: WorkPreferences = Field(default_factory=WorkPreferences)
    technical: TechnicalPreferences = Field(default_factory=TechnicalPreferences)
    application: ApplicationConfig = Field(default_factory=ApplicationConfig)
    
    # Paths
    cache_dir: Path = Field(default=Path("data/cache"))
    resume_dir: Path = Field(default=Path("data/resumes"))
    output_dir: Path = Field(default=Path("data/output"))
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Create configuration from environment variables."""
        return cls(
            location=LocationConfig(
                country=os.getenv("COUNTRY", "Brazil"),
                city=os.getenv("CITY", "São Paulo"),
                timezone=os.getenv("TIMEZONE", "America/Sao_Paulo")
            ),
            salary=SalaryConfig(
                min_salary_usd=int(os.getenv("MIN_SALARY_USD", "80000")),
                max_salary_usd=int(os.getenv("MAX_SALARY_USD", "200000")),
                preferred_currency=os.getenv("PREFERRED_CURRENCY", "USD")
            ),
            work_preferences=WorkPreferences(
                remote_only=os.getenv("REMOTE_ONLY", "true").lower() == "true",
                accept_hybrid=os.getenv("ACCEPT_HYBRID", "false").lower() == "true",
                work_timezone_range=tuple(map(int, os.getenv("WORK_TIMEZONE_RANGE", "-3,3").split(","))),
                preferred_languages=os.getenv("PREFERRED_LANGUAGES", "Portuguese,English").split(","),
                accept_contract=os.getenv("ACCEPT_CONTRACT", "true").lower() == "true",
                accept_fulltime=os.getenv("ACCEPT_FULLTIME", "true").lower() == "true",
                accept_parttime=os.getenv("ACCEPT_PARTTIME", "false").lower() == "true"
            ),
            technical=TechnicalPreferences(
                experience_years=int(os.getenv("EXPERIENCE_YEARS", "5")),
                seniority_level=os.getenv("SENIORITY_LEVEL", "Senior"),
                primary_skills=os.getenv("PRIMARY_SKILLS", "Python,JavaScript,React,Node.js").split(","),
                secondary_skills=os.getenv("SECONDARY_SKILLS", "AWS,Docker,Kubernetes").split(",")
            ),
            application=ApplicationConfig(
                auto_apply=os.getenv("AUTO_APPLY", "false").lower() == "true",
                max_applications_per_day=int(os.getenv("MAX_APPLICATIONS_PER_DAY", "10")),
                blacklisted_companies=os.getenv("BLACKLISTED_COMPANIES", "").split(",") if os.getenv("BLACKLISTED_COMPANIES") else [],
                preferred_companies=os.getenv("PREFERRED_COMPANIES", "").split(",") if os.getenv("PREFERRED_COMPANIES") else []
            ),
            cache_dir=Path(os.getenv("CACHE_DIR", "data/cache")),
            resume_dir=Path(os.getenv("RESUME_PATH", "data/resumes")),
            output_dir=Path(os.getenv("OUTPUT_PATH", "data/output"))
        )

# Global configuration instance
config = Config.from_env() 