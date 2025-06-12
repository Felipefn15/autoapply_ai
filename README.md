# AutoApply.AI

An automated job application system that helps you find and apply to relevant jobs across multiple platforms.

## Features

- **Multi-Platform Job Search**
  - LinkedIn
  - Indeed
  - Remotive
  - WeWorkRemotely
  - Greenhouse

- **Smart Job Matching**
  - Resume parsing and analysis
  - Skill matching
  - Experience level matching
  - Semantic similarity scoring
  - Customizable matching thresholds
  - Compatibility score calculation
  - Intelligent filtering based on requirements

- **Automated Applications**
  - Platform-specific application automation
  - Email application fallback
  - Resume attachment
  - Dynamic cover letter generation
  - Application history tracking
  - SQLite database for job and application storage
  - Comprehensive logging system

- **AI-Powered Cover Letters**
  - Personalized for each job using Groq API
  - Highlights relevant experience
  - Matches job requirements
  - Professional formatting
  - Company-specific customization
  - Customizable templates

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/autoapply_ai.git
cd autoapply_ai
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install spaCy language model:
```bash
python -m spacy download en_core_web_sm
```

5. Configure the application:
   - Copy `config/config.yaml.example` to `config/config.yaml`
   - Update the configuration with your settings:
     - Resume path
     - Email credentials
     - API keys
     - Job search preferences

## Configuration

The system is configured through `config/config.yaml`. Key settings include:

- **Resume Configuration**
  - Path to your resume PDF
  - Update interval
  - Cache settings
  - Parser configurations

- **Job Search Settings**
  - Enabled platforms
  - Search intervals
  - Keywords and locations
  - Remote work preferences
  - Platform-specific search criteria

- **Application Settings**
  - Cover letter customization
  - Email configuration
  - SMTP settings
  - Application limits
  - Template configurations
    - Cover letter template (templates/cover_letter.txt)
    - Email signature template (templates/email_signature.txt)

- **API Configuration**
  - Groq API key for cover letter generation
  - OAuth credentials for job platforms
  - Platform-specific API settings

- **System Components**
  - Resume parser settings
  - Job matcher thresholds
  - Cover letter generator preferences
  - Email sender configurations
  - Application manager settings
  - Database configurations

## Usage

1. Start the application:
```bash
python -m app.main
```

2. The system will:
   - Parse your resume
   - Search for jobs across platforms
   - Match jobs against your profile
   - Apply automatically when matches are found
   - Track all applications

3. Monitor the application:
   - Check logs in `logs/autoapply.log`
   - Review applications in `data/applications.db`
   - View generated cover letters in `data/cover_letters/`

## Directory Structure

```
autoapply_ai/
├── app/
│   ├── automation/
│   │   ├── applicator_manager.py
│   │   ├── cover_letter_generator.py
│   │   ├── email_sender.py
│   │   ├── job_matcher.py
│   │   └── job_searcher.py
│   ├── db/
│   │   └── models.py
│   └── resume/
│       └── parser.py
├── config/
│   └── config.yaml
├── data/
│   ├── applications.db
│   ├── cache/           # Cache for parsed resumes and job searches
│   ├── resumes/         # Store user resumes
│   │   └── examples/    # Example resume templates
│   ├── cover_letters/   # Generated cover letters
│   ├── attachments/     # Resume attachments and other files
│   └── jobs/           # Job search results and matches
│       ├── raw/        # Raw job listings from platforms
│       └── processed/  # Processed and matched job listings
├── logs/
│   └── autoapply.log
├── templates/
│   ├── cover_letter.txt
│   └── email_signature.txt
├── tests/
├── README.md
└── requirements.txt
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Groq](https://groq.com/) for their powerful language models
- Job platform providers for their services
- Open source community for various tools and libraries 