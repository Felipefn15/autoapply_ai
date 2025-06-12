"""
Setup configuration for AutoApply.AI
"""
from setuptools import setup, find_packages

setup(
    name="autoapply",
    version="0.1.0",
    description="Automated job search and application tool",
    author="Felipe",
    author_email="felipe@example.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "typer>=0.9.0",
        "rich>=13.0.0",
        "loguru>=0.7.0",
        "pydantic>=2.0.0",
        "requests>=2.31.0",
        "selenium>=4.0.0",
        "groq>=0.3.0",
        "python-dotenv>=1.0.0"
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
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Office/Business"
    ]
) 