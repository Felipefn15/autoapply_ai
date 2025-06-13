"""
Unit tests for applicator manager
"""
import pytest
from unittest.mock import Mock, patch
from typing import Dict

from app.automation.applicator_manager import ApplicatorManager
from app.automation.base_applicator import ApplicationResult

@pytest.fixture
def mock_config() -> Dict:
    """Create a mock configuration."""
    return {
        'oauth': {
            'linkedin': {
                'email': 'test@example.com',
                'password': 'password123'
            },
            'indeed': {
                'email': 'test@example.com',
                'password': 'password123'
            },
            'remotive': {
                'email': 'test@example.com',
                'password': 'password123'
            },
            'weworkremotely': {
                'email': 'test@example.com',
                'password': 'password123'
            },
            'greenhouse': {}
        },
        'job_search': {
            'platforms': {
                'linkedin': {
                    'enabled': True,
                    'search_interval': 3600,
                    'keywords': ['software engineer', 'python'],
                    'locations': ['San Francisco', 'Remote'],
                    'remote_only': True
                },
                'indeed': {
                    'enabled': True,
                    'search_interval': 3600,
                    'keywords': ['software engineer', 'python'],
                    'locations': ['San Francisco', 'Remote'],
                    'remote_only': True
                },
                'remotive': {
                    'enabled': True,
                    'search_interval': 3600,
                    'keywords': ['software engineer', 'python']
                },
                'weworkremotely': {
                    'enabled': True,
                    'search_interval': 3600,
                    'keywords': ['software engineer', 'python']
                },
                'greenhouse': {
                    'enabled': True,
                    'search_interval': 3600,
                    'keywords': ['software engineer', 'python']
                }
            },
            'matching': {
                'min_score': 0.7,
                'required_skills': ['python', 'javascript'],
                'preferred_skills': ['react', 'node.js'],
                'excluded_keywords': ['senior', 'lead'],
                'max_applications_per_day': 10
            }
        },
        'application': {
            'email': {
                'smtp_host': 'smtp.gmail.com',
                'smtp_port': 587,
                'smtp_username': 'test@example.com',
                'smtp_password': 'password123',
                'from_name': 'John Doe',
                'from_email': 'test@example.com',
                'signature': 'templates/email_signature.txt'
            },
            'cover_letter': {
                'enabled': True,
                'template': 'templates/cover_letter.txt'
            }
        },
        'api': {
            'groq': {
                'api_key': 'test_api_key',
                'model': 'mixtral-8x7b-32768'
            }
        }
    }

@pytest.fixture
def mock_job() -> Dict:
    """Create mock job data."""
    return {
        'platform': 'linkedin',
        'id': '12345',
        'title': 'Software Engineer',
        'company': 'Test Company',
        'location': 'Remote',
        'url': 'https://linkedin.com/jobs/12345',
        'description': 'Test job description'
    }

class TestApplicatorManager:
    """Tests for ApplicatorManager."""
    
    def test_init(self, mock_config):
        """Test initialization."""
        manager = ApplicatorManager(mock_config)
        assert manager.config == mock_config
        assert len(manager.applicators) == 5
        
    def test_init_components(self, mock_config):
        """Test component initialization."""
        manager = ApplicatorManager(mock_config)
        manager._init_components()
        
        assert manager.resume_parser is not None
        assert manager.job_searcher is not None
        assert manager.job_matcher is not None
        assert manager.cover_letter_generator is not None
        assert manager.email_sender is not None
        
    def test_init_database(self, mock_config):
        """Test database initialization."""
        manager = ApplicatorManager(mock_config)
        manager._init_database()
        
        assert manager.db_session is not None
        
    @pytest.mark.asyncio
    async def test_process_job(self, mock_config, mock_job):
        """Test job processing."""
        manager = ApplicatorManager(mock_config)
        
        # Mock successful application
        with patch('app.automation.linkedin_applicator.LinkedInApplicator.apply') as mock_apply:
            mock_apply.return_value = ApplicationResult(
                company='Test Company',
                position='Software Engineer',
                url='https://linkedin.com/jobs/12345',
                status='success'
            )
            
            result = await manager.process_job(mock_job)
            assert result.status == 'success'
            
        # Mock failed application
        with patch('app.automation.linkedin_applicator.LinkedInApplicator.apply') as mock_apply:
            mock_apply.return_value = ApplicationResult(
                company='Test Company',
                position='Software Engineer',
                url='https://linkedin.com/jobs/12345',
                status='failed',
                error_message='Test error'
            )
            
            result = await manager.process_job(mock_job)
            assert result.status == 'failed'
            assert result.error_message == 'Test error'
            
        # Mock skipped application
        with patch('app.automation.linkedin_applicator.LinkedInApplicator.apply') as mock_apply:
            mock_apply.return_value = ApplicationResult(
                company='Test Company',
                position='Software Engineer',
                url='https://linkedin.com/jobs/12345',
                status='skipped',
                error_message='No apply button found'
            )
            
            result = await manager.process_job(mock_job)
            assert result.status == 'skipped'
            assert result.error_message == 'No apply button found'
            
    def test_is_job_processed(self, mock_config, mock_job):
        """Test job processing check."""
        manager = ApplicatorManager(mock_config)
        manager._init_database()
        
        # Test unprocessed job
        assert not manager._is_job_processed(mock_job)
        
        # Test processed job
        from app.db.models import Job
        job_record = Job(
            platform='linkedin',
            platform_id='12345',
            title='Software Engineer',
            company='Test Company',
            location='Remote',
            url='https://linkedin.com/jobs/12345'
        )
        manager.db_session.add(job_record)
        manager.db_session.commit()
        
        assert manager._is_job_processed(mock_job)
        
    def test_record_application(self, mock_config, mock_job):
        """Test application recording."""
        manager = ApplicatorManager(mock_config)
        manager._init_database()
        
        # Record application
        manager._record_application(
            mock_job,
            match_score=0.8,
            cover_letter='Test cover letter'
        )
        
        # Verify record
        from app.db.models import Job, Application
        job = manager.db_session.query(Job).filter_by(
            platform='linkedin',
            platform_id='12345'
        ).first()
        
        assert job is not None
        assert job.title == 'Software Engineer'
        assert job.company == 'Test Company'
        assert job.match_score == 0.8
        
        application = manager.db_session.query(Application).filter_by(
            job_id=job.id
        ).first()
        
        assert application is not None
        assert application.cover_letter == 'Test cover letter'
        assert application.status == 'applied'
        
    def test_reset_daily_count_if_needed(self, mock_config):
        """Test daily count reset."""
        manager = ApplicatorManager(mock_config)
        
        # Test initial state
        assert manager.applications_today == 0
        
        # Test after applications
        manager.applications_today = 5
        manager._reset_daily_count_if_needed()
        assert manager.applications_today == 5
        
        # Test after day change
        from datetime import datetime, timedelta
        manager.last_reset_date = datetime.now().date() - timedelta(days=1)
        manager._reset_daily_count_if_needed()
        assert manager.applications_today == 0
        
    def test_update_resume_if_needed(self, mock_config):
        """Test resume update."""
        manager = ApplicatorManager(mock_config)
        manager._init_components()
        
        # Test initial update
        manager._update_resume_if_needed()
        assert manager.last_resume_update > 0
        
        # Test no update needed
        last_update = manager.last_resume_update
        manager._update_resume_if_needed()
        assert manager.last_resume_update == last_update
        
        # Test update after interval
        manager.last_resume_update = 0
        manager._update_resume_if_needed()
        assert manager.last_resume_update > last_update 