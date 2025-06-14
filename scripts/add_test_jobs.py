"""Script to add test jobs to the database."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.db.database import Database

def add_test_jobs():
    """Add test jobs to the database."""
    # Test jobs data
    jobs = [
        {
            'title': 'Senior Software Engineer',
            'company': 'TechCorp',
            'url': 'https://www.linkedin.com/jobs/view/123456',
            'email': 'careers@techcorp.com',
            'application_method': 'email',
            'description': '''
            We're looking for a Senior Software Engineer to join our team.
            
            Required Skills:
            - Python
            - JavaScript
            - React
            - AWS
            
            Contact us at careers@techcorp.com or jobs [at] techcorp [dot] com
            '''
        },
        {
            'title': 'Full Stack Developer',
            'company': 'StartupX',
            'url': 'https://www.linkedin.com/jobs/view/789012',
            'email': None,
            'application_method': 'linkedin',
            'description': '''
            Join our fast-growing startup!
            
            Tech Stack:
            - Node.js
            - React
            - MongoDB
            
            Send your application to: developer (at) startupx.com
            '''
        },
        {
            'title': 'Backend Engineer',
            'company': 'DataCo',
            'url': 'https://www.linkedin.com/jobs/view/345678',
            'email': 'hiring@dataco.com',
            'application_method': 'email',
            'description': '''
            Backend Engineer position available.
            
            Requirements:
            - Python
            - Django
            - PostgreSQL
            
            Questions? Email us at hiring [at] dataco [dot] com
            '''
        }
    ]
    
    # Initialize database
    db = Database()
    
    # Add jobs
    for job in jobs:
        job_id = db.add_application(job)
        print(f"Added job: {job['title']} (ID: {job_id})")

if __name__ == '__main__':
    add_test_jobs() 