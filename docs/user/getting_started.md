# Getting Started with AutoApply.AI

This guide will help you get started with AutoApply.AI, an automated job search and application tool.

## Prerequisites

Before you begin, make sure you have:

1. Python 3.8 or higher installed
2. A GROQ API key (get one at [groq.com](https://groq.com))
3. Your resume in PDF or TXT format
4. Chrome browser installed (for automated applications)

## Installation

1. Install AutoApply.AI:
```bash
pip install autoapply
```

2. Create a configuration file:
```bash
autoapply configure --config config.json
```

3. Edit the configuration file with your preferences and API keys.

## Basic Usage

### 1. Search for Jobs

To search for matching jobs without applying:

```bash
autoapply search path/to/your/resume.pdf --platform remotive --limit 10
```

This will:
- Parse your resume
- Search for jobs on the specified platform
- Match jobs against your resume
- Display the best matches

### 2. Apply to Jobs

To automatically apply to matching jobs:

```bash
autoapply apply path/to/your/resume.pdf --platform remotive --limit 5 --min-score 0.8
```

This will:
- Perform the same steps as search
- Filter jobs by minimum match score
- Attempt to apply to the top matching jobs

## Configuration

The configuration file (`config.json`) contains several sections:

### Technical Preferences

```json
{
  "technical": {
    "role_type": "Software Engineer",
    "seniority_level": "Senior",
    "primary_skills": ["Python", "JavaScript", "React"],
    "secondary_skills": ["Node.js", "TypeScript"],
    "min_experience_years": 5,
    "max_experience_years": 15,
    "preferred_stack": ["Python", "React", "Node.js"]
  }
}
```

### Work Preferences

```json
{
  "work_preferences": {
    "remote_only": true,
    "accept_hybrid": false,
    "accept_contract": true,
    "accept_fulltime": true,
    "accept_parttime": false,
    "preferred_languages": ["English", "Portuguese"],
    "preferred_timezones": ["UTC-3", "UTC-4", "UTC-5"]
  }
}
```

### Location Preferences

```json
{
  "location": {
    "country": "Brazil",
    "city": "São Paulo",
    "state": "SP",
    "timezone": "UTC-3",
    "willing_to_relocate": false,
    "preferred_countries": ["USA", "Canada"]
  }
}
```

### Salary Preferences

```json
{
  "salary": {
    "min_salary_usd": 120000,
    "preferred_currency": "USD",
    "require_salary_range": true,
    "accept_equity": true,
    "min_equity_percent": 0.1
  }
}
```

### Application Preferences

```json
{
  "application": {
    "max_applications_per_day": 10,
    "blacklisted_companies": [],
    "preferred_companies": ["Google", "Microsoft", "Amazon"],
    "cover_letter_required": true,
    "follow_up_days": 7
  }
}
```

### API Configuration

```json
{
  "api": {
    "groq_api_key": "your-api-key-here",
    "groq_model": "llama3-70b-8192",
    "groq_temperature": 0.3,
    "groq_max_tokens": 1000,
    "groq_rate_limit": 10
  }
}
```

## Resume Format

For best results, your resume should:

1. Be in PDF or TXT format
2. Include clear section headers (e.g., "Experience", "Skills", "Education")
3. List skills explicitly
4. Include dates for experience in a consistent format
5. Specify current location and willingness to relocate
6. List language proficiencies

Example resume sections:

```
SKILLS
Programming Languages: Python, JavaScript, TypeScript
Frameworks: React, Node.js, Django
Tools: Git, Docker, AWS
Languages: English (Fluent), Portuguese (Native)

EXPERIENCE
Senior Software Engineer | Company Name | Remote
January 2020 - Present
- Led development of microservices using Python
- Implemented CI/CD pipelines
- Managed team of 5 developers
```

## Job Platforms

Currently supported job platforms:

1. **Remotive**
   - Remote-only jobs
   - Global opportunities
   - Tech-focused positions

2. **WeWorkRemotely**
   - Remote-only jobs
   - Various categories
   - Detailed job descriptions

## Troubleshooting

Common issues and solutions:

1. **API Rate Limits**
   - Reduce `groq_rate_limit` in config
   - Wait a few minutes between searches
   - Check your API usage

2. **No Matches Found**
   - Check your minimum match score
   - Review your technical preferences
   - Ensure resume is properly formatted

3. **Application Failures**
   - Check browser installation
   - Verify internet connection
   - Review application logs

## Next Steps

1. Review the [API Documentation](../api/README.md)
2. Check out [Advanced Features](advanced_features.md)
3. Join our [Community](https://github.com/yourusername/autoapply_ai/discussions)

For more detailed information, visit our [Documentation](https://autoapply.ai/docs). 