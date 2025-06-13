"""
Setup configuration for AutoApply.AI
"""
from setuptools import setup, find_packages

setup(
    name="autoapply_ai",
    version="0.1.0",
    description="AutoApply.AI - Automated job search and application system",
    author="Felipe",
    author_email="felipe@example.com",
    packages=find_packages(),
    install_requires=[
        "aiohttp",
        "beautifulsoup4",
        "groq==0.27.0",
        "loguru",
        "PyPDF2==3.0.1",
        "pyyaml",
        "nltk==3.8.1",
        "SQLAlchemy==2.0.28",
        "scikit-learn==1.7.0",
        "numpy==1.26.4",
        "lxml==5.1.0",
        "html5lib==1.1",
        "PyMuPDF==1.23.26",
        "playwright==1.42.0",
        "pandas==2.2.1",
        "python-multipart==0.0.6",
        "fastapi==0.104.1",
        "uvicorn==0.24.0",
        "python-docx==1.0.1",
        "pydantic==2.5.2",
        "seaborn",
    ],
    entry_points={
        "console_scripts": [
            "autoapply=autoapply.cli.main:run"
        ]
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Office/Business"
    ],
    url="https://github.com/felipe/autoapply_ai",
) 