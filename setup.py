from setuptools import setup, find_packages

setup(
    name="autoapply-ai",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "PyMuPDF==1.23.26",
        "requests==2.31.0",
        "beautifulsoup4==4.12.3",
        "playwright==1.42.0",
        "groq==0.27.0",
        "pandas==2.2.1",
        "pydantic==2.5.2",
        "python-dotenv==1.0.0",
        "pytest==8.0.2",
        "black==24.2.0",
        "isort==5.13.2",
        "loguru==0.7.2"
    ],
    python_requires=">=3.8",
) 