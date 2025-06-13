"""Automation package for job applications."""

from .base_applicator import BaseApplicator
from .linkedin_applicator import LinkedInApplicator
from .email_applicator import EmailApplicator
from .application_logger import ApplicationLogger

__all__ = [
    'BaseApplicator',
    'LinkedInApplicator',
    'EmailApplicator',
    'ApplicationLogger'
]
