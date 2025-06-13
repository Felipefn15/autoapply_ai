"""
Unit tests for job applicators
"""
import pytest
from unittest.mock import Mock, patch
from typing import Dict

from app.automation.base_applicator import BaseApplicator, ApplicationResult
from app.automation.linkedin_applicator import LinkedInApplicator
from app.automation.indeed_applicator import IndeedApplicator
from app.automation.remotive_applicator import RemotiveApplicator
from app.automation.weworkremotely_applicator import WeWorkRemotelyApplicator
from app.automation.greenhouse_applicator import GreenhouseApplicator

@pytest.fixture
def mock_config() -> Dict:
    """Create a mock configuration."""
    return {
        'automation_delay': 1,
        'resume_path': 'data/resumes/resume.pdf',
        'linkedin_email': 'test@example.com',
        'linkedin_password': 'password123',
        'indeed_email': 'test@example.com',
        'indeed_password': 'password123',
        'remotive_email': 'test@example.com',
        'remotive_password': 'password123',
        'weworkremotely_email': 'test@example.com',
        'weworkremotely_password': 'password123'
    }

@pytest.fixture
def mock_job_data() -> Dict:
    """Create mock job data."""
    return {
        'id': '12345',
        'title': 'Software Engineer',
        'company': 'Test Company',
        'location': 'Remote',
        'url': 'https://example.com/job/12345',
        'description': 'Test job description'
    }

@pytest.fixture
def mock_resume_data() -> Dict:
    """Create mock resume data."""
    return {
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'john.doe@example.com',
        'phone': '+1 (555) 123-4567',
        'location': 'San Francisco, CA',
        'experience_years': '5',
        'salary_expectation': '120000',
        'work_authorization': True,
        'linkedin_url': 'https://linkedin.com/in/johndoe',
        'github_url': 'https://github.com/johndoe',
        'portfolio_url': 'https://johndoe.dev'
    }

class TestLinkedInApplicator:
    """Tests for LinkedIn applicator."""
    
    @pytest.mark.asyncio
    async def test_is_applicable(self, mock_config):
        """Test URL matching."""
        applicator = LinkedInApplicator(mock_config)
        
        assert await applicator.is_applicable('https://linkedin.com/jobs/123')
        assert await applicator.is_applicable('https://www.linkedin.com/jobs/123')
        assert not await applicator.is_applicable('https://indeed.com/jobs/123')
    
    @pytest.mark.asyncio
    async def test_login_if_needed(self, mock_config):
        """Test login process."""
        applicator = LinkedInApplicator(mock_config)
        applicator.page = Mock()
        
        # Mock already logged in
        applicator.page.query_selector.return_value = Mock()
        assert await applicator.login_if_needed()
        
        # Mock not logged in but successful login
        applicator.page.query_selector.side_effect = [None, Mock()]
        assert await applicator.login_if_needed()
        
        # Mock login failure
        applicator.page.query_selector.side_effect = [None, None]
        assert not await applicator.login_if_needed()
    
    @pytest.mark.asyncio
    async def test_apply(self, mock_config, mock_job_data, mock_resume_data):
        """Test job application process."""
        applicator = LinkedInApplicator(mock_config)
        applicator.page = Mock()
        
        # Mock successful application
        applicator.page.query_selector.return_value = Mock()
        result = await applicator.apply(mock_job_data, mock_resume_data)
        assert isinstance(result, ApplicationResult)
        assert result.status == 'success'
        
        # Mock no apply button
        applicator.page.query_selector.return_value = None
        result = await applicator.apply(mock_job_data, mock_resume_data)
        assert result.status == 'skipped'
        
        # Mock application error
        applicator.page.query_selector.side_effect = Exception('Test error')
        result = await applicator.apply(mock_job_data, mock_resume_data)
        assert result.status == 'failed'

class TestIndeedApplicator:
    """Tests for Indeed applicator."""
    
    @pytest.mark.asyncio
    async def test_is_applicable(self, mock_config):
        """Test URL matching."""
        applicator = IndeedApplicator(mock_config)
        
        assert await applicator.is_applicable('https://indeed.com/jobs/123')
        assert await applicator.is_applicable('https://www.indeed.com/jobs/123')
        assert not await applicator.is_applicable('https://linkedin.com/jobs/123')
    
    @pytest.mark.asyncio
    async def test_login_if_needed(self, mock_config):
        """Test login process."""
        applicator = IndeedApplicator(mock_config)
        applicator.page = Mock()
        
        # Mock already logged in
        applicator.page.query_selector.return_value = Mock()
        assert await applicator.login_if_needed()
        
        # Mock not logged in but successful login
        applicator.page.query_selector.side_effect = [None, Mock()]
        assert await applicator.login_if_needed()
        
        # Mock login failure
        applicator.page.query_selector.side_effect = [None, None]
        assert not await applicator.login_if_needed()
    
    @pytest.mark.asyncio
    async def test_apply(self, mock_config, mock_job_data, mock_resume_data):
        """Test job application process."""
        applicator = IndeedApplicator(mock_config)
        applicator.page = Mock()
        
        # Mock successful application
        applicator.page.query_selector.return_value = Mock()
        result = await applicator.apply(mock_job_data, mock_resume_data)
        assert isinstance(result, ApplicationResult)
        assert result.status == 'success'
        
        # Mock no apply button
        applicator.page.query_selector.return_value = None
        result = await applicator.apply(mock_job_data, mock_resume_data)
        assert result.status == 'skipped'
        
        # Mock application error
        applicator.page.query_selector.side_effect = Exception('Test error')
        result = await applicator.apply(mock_job_data, mock_resume_data)
        assert result.status == 'failed'

class TestRemotiveApplicator:
    """Tests for Remotive applicator."""
    
    @pytest.mark.asyncio
    async def test_is_applicable(self, mock_config):
        """Test URL matching."""
        applicator = RemotiveApplicator(mock_config)
        
        assert await applicator.is_applicable('https://remotive.com/jobs/123')
        assert await applicator.is_applicable('https://www.remotive.com/jobs/123')
        assert not await applicator.is_applicable('https://linkedin.com/jobs/123')
    
    @pytest.mark.asyncio
    async def test_login_if_needed(self, mock_config):
        """Test login process."""
        applicator = RemotiveApplicator(mock_config)
        applicator.page = Mock()
        
        # Mock already logged in
        applicator.page.query_selector.return_value = Mock()
        assert await applicator.login_if_needed()
        
        # Mock not logged in but successful login
        applicator.page.query_selector.side_effect = [None, Mock()]
        assert await applicator.login_if_needed()
        
        # Mock login failure
        applicator.page.query_selector.side_effect = [None, None]
        assert not await applicator.login_if_needed()
    
    @pytest.mark.asyncio
    async def test_apply(self, mock_config, mock_job_data, mock_resume_data):
        """Test job application process."""
        applicator = RemotiveApplicator(mock_config)
        applicator.page = Mock()
        
        # Mock successful application
        applicator.page.query_selector.return_value = Mock()
        result = await applicator.apply(mock_job_data, mock_resume_data)
        assert isinstance(result, ApplicationResult)
        assert result.status == 'success'
        
        # Mock no apply button
        applicator.page.query_selector.return_value = None
        result = await applicator.apply(mock_job_data, mock_resume_data)
        assert result.status == 'skipped'
        
        # Mock application error
        applicator.page.query_selector.side_effect = Exception('Test error')
        result = await applicator.apply(mock_job_data, mock_resume_data)
        assert result.status == 'failed'

class TestWeWorkRemotelyApplicator:
    """Tests for WeWorkRemotely applicator."""
    
    @pytest.mark.asyncio
    async def test_is_applicable(self, mock_config):
        """Test URL matching."""
        applicator = WeWorkRemotelyApplicator(mock_config)
        
        assert await applicator.is_applicable('https://weworkremotely.com/jobs/123')
        assert await applicator.is_applicable('https://www.weworkremotely.com/jobs/123')
        assert not await applicator.is_applicable('https://linkedin.com/jobs/123')
    
    @pytest.mark.asyncio
    async def test_login_if_needed(self, mock_config):
        """Test login process."""
        applicator = WeWorkRemotelyApplicator(mock_config)
        applicator.page = Mock()
        
        # Mock already logged in
        applicator.page.query_selector.return_value = Mock()
        assert await applicator.login_if_needed()
        
        # Mock not logged in but successful login
        applicator.page.query_selector.side_effect = [None, Mock()]
        assert await applicator.login_if_needed()
        
        # Mock login failure
        applicator.page.query_selector.side_effect = [None, None]
        assert not await applicator.login_if_needed()
    
    @pytest.mark.asyncio
    async def test_apply(self, mock_config, mock_job_data, mock_resume_data):
        """Test job application process."""
        applicator = WeWorkRemotelyApplicator(mock_config)
        applicator.page = Mock()
        
        # Mock successful application
        applicator.page.query_selector.return_value = Mock()
        result = await applicator.apply(mock_job_data, mock_resume_data)
        assert isinstance(result, ApplicationResult)
        assert result.status == 'success'
        
        # Mock no apply button
        applicator.page.query_selector.return_value = None
        result = await applicator.apply(mock_job_data, mock_resume_data)
        assert result.status == 'skipped'
        
        # Mock application error
        applicator.page.query_selector.side_effect = Exception('Test error')
        result = await applicator.apply(mock_job_data, mock_resume_data)
        assert result.status == 'failed'

class TestGreenhouseApplicator:
    """Tests for Greenhouse applicator."""
    
    @pytest.mark.asyncio
    async def test_is_applicable(self, mock_config):
        """Test URL matching."""
        applicator = GreenhouseApplicator(mock_config)
        
        assert await applicator.is_applicable('https://boards.greenhouse.io/company/jobs/123')
        assert await applicator.is_applicable('https://company.greenhouse.io/jobs/123')
        assert not await applicator.is_applicable('https://linkedin.com/jobs/123')
    
    @pytest.mark.asyncio
    async def test_login_if_needed(self, mock_config):
        """Test login process."""
        applicator = GreenhouseApplicator(mock_config)
        # Greenhouse doesn't require login
        assert await applicator.login_if_needed()
    
    @pytest.mark.asyncio
    async def test_apply(self, mock_config, mock_job_data, mock_resume_data):
        """Test job application process."""
        applicator = GreenhouseApplicator(mock_config)
        applicator.page = Mock()
        
        # Mock successful application
        applicator.page.query_selector.return_value = Mock()
        result = await applicator.apply(mock_job_data, mock_resume_data)
        assert isinstance(result, ApplicationResult)
        assert result.status == 'success'
        
        # Mock no apply button
        applicator.page.query_selector.return_value = None
        result = await applicator.apply(mock_job_data, mock_resume_data)
        assert result.status == 'skipped'
        
        # Mock application error
        applicator.page.query_selector.side_effect = Exception('Test error')
        result = await applicator.apply(mock_job_data, mock_resume_data)
        assert result.status == 'failed' 