"""Test module for resume parser functionality."""
import os
from pathlib import Path
import pytest
from app.resume.parser import ResumeParser

# Test data directory setup
TEST_DATA_DIR = Path("tests/test_data")
TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)

def create_sample_txt_resume():
    """Create a sample text resume for testing."""
    content = """John Doe
john.doe@email.com
(123) 456-7890
San Francisco, CA

SUMMARY
Experienced software engineer with a passion for building scalable applications.

EXPERIENCE
Senior Software Engineer at Tech Corp
• Led development of cloud-native applications
• Managed team of 5 engineers
• Implemented CI/CD pipelines

Software Engineer at StartUp Inc
• Developed RESTful APIs
• Improved system performance by 40%

EDUCATION
Master of Science in Computer Science from Stanford University
• GPA: 3.8
• Research focus: Machine Learning

SKILLS
Python, Java, Docker, Kubernetes, AWS, Machine Learning, CI/CD"""
    
    resume_path = TEST_DATA_DIR / "sample_resume.txt"
    resume_path.write_text(content)
    return resume_path

def test_resume_parser_txt():
    """Test resume parsing with a text file."""
    # Create test resume
    resume_path = create_sample_txt_resume()
    
    # Initialize parser
    parser = ResumeParser()
    
    # Parse resume
    result = parser.parse(resume_path)
    
    # Verify basic information
    assert result["full_name"] == "John Doe"
    assert result["email"] == "john.doe@email.com"
    assert result["phone"] == "(123) 456-7890"
    assert "San Francisco, CA" in result["location"]
    
    # Verify skills
    assert len(result["skills"]) >= 5
    assert "Python" in result["skills"]
    assert "Java" in result["skills"]
    
    # Verify experience
    assert len(result["experience"]) >= 2
    tech_corp = next(exp for exp in result["experience"] if "Tech Corp" in exp["company"])
    assert "Senior Software Engineer" in tech_corp["position"]
    
    # Verify education
    assert len(result["education"]) >= 1
    stanford = next(edu for edu in result["education"] if "Stanford" in edu["institution"])
    assert "Master of Science" in stanford["degree"]
    
    # Verify format information
    assert result["original_format"] == "txt"
    assert len(result["text_content"]) > 0

def test_resume_parser_pdf():
    """Test resume parsing with a PDF file."""
    # Skip if no PDF resume available
    pdf_path = TEST_DATA_DIR / "sample_resume.pdf"
    if not pdf_path.exists():
        pytest.skip("PDF resume not available for testing")
    
    # Initialize parser
    parser = ResumeParser()
    
    # Parse resume
    result = parser.parse(pdf_path)
    
    # Basic verification that PDF parsing works
    assert result["full_name"]
    assert len(result["text_content"]) > 0
    assert result["original_format"] == "pdf"

if __name__ == "__main__":
    # Create test directory if it doesn't exist
    TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Run tests
    pytest.main([__file__, "-v"]) 