"""
Job Search Platforms
"""
from .linkedin import LinkedInScraper
from .hackernews import HackerNewsScraper
from .weworkremotely import WeWorkRemotelyScraper
from .remotive import RemotiveScraper
from .angellist import AngelListScraper
from .infojobs import InfoJobsScraper
from .catho import CathoScraper

__all__ = [
    'LinkedInScraper',
    'HackerNewsScraper',
    'WeWorkRemotelyScraper',
    'RemotiveScraper',
    'AngelListScraper',
    'InfoJobsScraper',
    'CathoScraper'
] 