"""
Unit tests for the resume module
"""
import json
from pathlib import Path
import pytest
from unittest.mock import Mock, patch

from autoapply.core.resume import ResumeManager

@pytest.fixture
def resume_manager():
    """Create a ResumeManager instance for testing."""
    return ResumeManager()

@pytest.fixture
def example_resume_path():
    """Get path to example resume file."""
    return Path("data/resumes/examples/example_resume.txt")

@pytest.fixture
def example_resume_data():
    """Example parsed resume data."""
    return {
        "full_name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+55 11 99999-9999",
        "location": "São Paulo, Brazil",
        "current_role": "Senior Software Engineer",
        "experience_years": 8,
        "skills": [
            "Python",
            "JavaScript",
            "TypeScript",
            "SQL",
            "React",
            "Node.js",
            "Django",
            "FastAPI",
            "AWS",
            "Docker",
            "Kubernetes"
        ],
        "languages": ["English", "Portuguese"],
        "education": "Bachelor of Computer Science, University of São Paulo",
        "experience": [
            {
                "title": "Senior Software Engineer",
                "company": "TechCorp Inc.",
                "location": "Remote",
                "start_date": "2020-01",
                "end_date": "Present",
                "description": [
                    "Led development of microservices architecture using Python and FastAPI",
                    "Implemented CI/CD pipelines reducing deployment time by 60%",
                    "Mentored junior developers and conducted code reviews",
                    "Managed team of 5 developers across multiple time zones"
                ]
            },
            {
                "title": "Full Stack Developer",
                "company": "WebSolutions Ltd.",
                "location": "São Paulo, Brazil",
                "start_date": "2017-03",
                "end_date": "2019-12",
                "description": [
                    "Developed and maintained React-based front-end applications",
                    "Built RESTful APIs using Node.js and Express",
                    "Improved application performance by 40% through optimization",
                    "Collaborated with UX team to implement new features"
                ]
            }
        ],
        "certifications": [
            "AWS Certified Solutions Architect",
            "MongoDB Certified Developer",
            "Scrum Master Certified"
        ]
    }

def test_resume_manager_init(resume_manager):
    """Test ResumeManager initialization."""
    assert resume_manager.resumes_dir.exists()
    assert resume_manager.cache_dir.exists()
    assert resume_manager.output_dir.exists()

def test_generate_cache_key(resume_manager, example_resume_path):
    """Test cache key generation."""
    cache_key = resume_manager._generate_cache_key(example_resume_path)
    assert isinstance(cache_key, str)
    assert len(cache_key) == 32  # MD5 hash length

@patch("autoapply.core.resume.Path.read_bytes")
def test_generate_cache_key_error(mock_read_bytes, resume_manager, example_resume_path):
    """Test cache key generation with error."""
    mock_read_bytes.side_effect = Exception("File read error")
    cache_key = resume_manager._generate_cache_key(example_resume_path)
    assert cache_key == example_resume_path.stem

def test_parse_resume_from_cache(resume_manager, example_resume_path, example_resume_data):
    """Test parsing resume from cache."""
    # Setup mock cache
    cache_key = resume_manager._generate_cache_key(example_resume_path)
    cache_file = resume_manager.cache_dir / f"{cache_key}.json"
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    
    with cache_file.open('w') as f:
        json.dump(example_resume_data, f)
    
    # Test parsing
    result = resume_manager.parse(str(example_resume_path))
    assert result == example_resume_data

def test_parse_resume_no_cache(resume_manager, example_resume_path, example_resume_data):
    """Test parsing resume without cache."""
    # Ensure no cache exists
    cache_key = resume_manager._generate_cache_key(example_resume_path)
    cache_file = resume_manager.cache_dir / f"{cache_key}.json"
    if cache_file.exists():
        cache_file.unlink()
    
    # Mock the actual parsing
    with patch.object(resume_manager, '_parse_resume') as mock_parse:
        mock_parse.return_value = example_resume_data
        result = resume_manager.parse(str(example_resume_path))
        
        assert result == example_resume_data
        mock_parse.assert_called_once_with(example_resume_path)

def test_parse_resume_cache_error(resume_manager, example_resume_path, example_resume_data):
    """Test parsing resume with cache error."""
    # Setup corrupted cache
    cache_key = resume_manager._generate_cache_key(example_resume_path)
    cache_file = resume_manager.cache_dir / f"{cache_key}.json"
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    
    with cache_file.open('w') as f:
        f.write("invalid json")
    
    # Mock the actual parsing
    with patch.object(resume_manager, '_parse_resume') as mock_parse:
        mock_parse.return_value = example_resume_data
        result = resume_manager.parse(str(example_resume_path))
        
        assert result == example_resume_data
        mock_parse.assert_called_once_with(example_resume_path)

def test_parse_resume_error(resume_manager, example_resume_path):
    """Test parsing resume with error."""
    with patch.object(resume_manager, '_parse_resume') as mock_parse:
        mock_parse.side_effect = Exception("Parsing error")
        
        with pytest.raises(Exception) as exc_info:
            resume_manager.parse(str(example_resume_path))
        
        assert str(exc_info.value) == "Parsing error" 