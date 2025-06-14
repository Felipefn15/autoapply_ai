"""Text extraction utilities."""
import re
from typing import List, Optional
from bs4 import BeautifulSoup
from loguru import logger

def clean_text(text: str) -> str:
    """Clean text by removing HTML and normalizing whitespace."""
    try:
        # Parse HTML
        soup = BeautifulSoup(text, 'html.parser')
        # Get text content
        text = soup.get_text()
        # Normalize whitespace
        text = ' '.join(text.split())
        return text
    except:
        return text

def extract_emails_from_text(text: str) -> List[str]:
    """
    Extract email addresses from text.
    Handles various email formats including obfuscated ones.
    """
    if not text:
        return []
        
    # Clean text
    text = clean_text(text)
    
    # Pre-process text to handle common obfuscation patterns
    text = text.replace(' [at] ', '@')
    text = text.replace(' (at) ', '@')
    text = text.replace('[at]', '@')
    text = text.replace('(at)', '@')
    text = text.replace(' [dot] ', '.')
    text = text.replace(' (dot) ', '.')
    text = text.replace('[dot]', '.')
    text = text.replace('(dot)', '.')
    text = text.replace(' AT ', '@')
    text = text.replace(' DOT ', '.')
    
    # Common email patterns
    patterns = [
        # Standard email
        r'[\w\.-]+@[\w\.-]+\.\w+',
        # With spaces around @
        r'[\w\.-]+\s*@\s*[\w\.-]+\.\w+',
        # With [at] or (at)
        r'[\w\.-]+\s*[\[\(]at[\]\)]\s*[\w\.-]+\.\w+',
        # With [dot] or (dot)
        r'[\w\.-]+@[\w\.-]+\s*[\[\(]dot[\]\)]\s*\w+',
        # With spaces and "at"/"dot" words
        r'[\w\.-]+\s+at\s+[\w\.-]+\s+dot\s+\w+',
    ]
    
    emails = set()
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            email = match.group(0)
            # Clean up the email
            email = email.strip().lower()
            email = re.sub(r'\s+', '', email)
            if is_valid_email(email):
                emails.add(email)
                
    # Look for emails in context
    context_patterns = [
        r'(?:email|e-mail|contact|apply|send|resume to|cv to)[^@]*?([\w\.-]+@[\w\.-]+\.\w+)',
        r'(?:email|e-mail|contact|apply|send|resume to|cv to)[^@]*?([\w\.-]+\s*@\s*[\w\.-]+\.\w+)',
    ]
    
    for pattern in context_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            email = match.group(1)
            # Clean up the email
            email = email.strip().lower()
            email = re.sub(r'\s+', '', email)
            if is_valid_email(email):
                emails.add(email)
                
    return list(emails)

def is_valid_email(email: str) -> bool:
    """Validate email address format."""
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, email)) 