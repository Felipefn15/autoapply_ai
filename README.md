# AutoApply.AI

AutoApply.AI is an automated job search and application system that helps you find and apply to relevant job opportunities across multiple platforms.

## Features

- **Multi-platform Job Search**: Search for jobs across LinkedIn, Indeed, Remotive, WeWorkRemotely, Stack Overflow, GitHub Jobs, AngelList, and Hacker News
- **Smart Job Matching**: Match jobs with your profile based on skills, experience, and preferences
- **Automated Applications**: Apply to jobs automatically or send customized emails
- **Detailed Analytics**: Analyze job market trends, salary ranges, and application success rates
- **Configurable**: Customize search criteria, application preferences, and automation settings

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/autoapply_ai.git
cd autoapply_ai
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up your configuration:
- Copy `config/profile.yaml.example` to `config/profile.yaml` and update with your information
- Copy `config/config.yaml.example` to `config/config.yaml` and update settings
- Copy `config/job_search.yaml.example` to `config/job_search.yaml` and customize search parameters

## Usage

The system can be used in two ways:

### 1. Interactive Menu

Run the main application with:
```bash
python app/main.py
```

This will show a menu with options to:
1. Search for Jobs
2. Match Jobs with Profile
3. Apply to Matched Jobs
4. View Job Analysis
5. Run Complete Workflow

### 2. Individual Scripts

You can also run each component separately:

1. Search for jobs:
```bash
python scripts/search_jobs.py --config-dir config
```

2. Match jobs with your profile:
```bash
python scripts/match_jobs.py --profile config/profile.yaml
```

3. Apply to matched jobs:
```bash
python scripts/apply_jobs.py --config config/config.yaml --resume data/resume/resume.pdf
```

4. Analyze results:
```bash
python scripts/analyze_jobs.py --data-dir data
```

## Configuration

### Profile Configuration (profile.yaml)

Contains your personal information, experience, skills, and preferences:
- Personal details and contact information
- Work experience and education
- Required and preferred skills
- Job preferences (location, salary, industry, etc.)
- Application preferences

### Job Search Configuration (job_search.yaml)

Customize job search parameters:
- Keywords and locations
- Platform-specific settings
- Search intervals
- Filters and requirements

### Main Configuration (config.yaml)

System-wide settings:
- Application automation settings
- Email configuration
- Rate limiting and delays
- Output directories

## Directory Structure

```
autoapply_ai/
├── app/
│   ├── automation/
│   ├── email/
│   ├── job_search/
│   └── main.py
├── config/
│   ├── config.yaml
│   ├── job_search.yaml
│   └── profile.yaml
├── data/
│   ├── jobs/
│   ├── matches/
│   ├── applications/
│   └── analysis/
├── scripts/
│   ├── search_jobs.py
│   ├── match_jobs.py
│   ├── apply_jobs.py
│   └── analyze_jobs.py
└── requirements.txt
```

## Output

The system generates various outputs in the `data` directory:

- `data/jobs/`: Raw job postings and search results
- `data/matches/`: Jobs matched with your profile
- `data/applications/`: Application results and status
- `data/analysis/`: Analytics reports and visualizations

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 