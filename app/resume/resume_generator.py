"""Resume generator module for creating tailored resumes."""
import os
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime
import json

from loguru import logger
from jinja2 import Environment, FileSystemLoader
import pdfkit

from ..job_search.post_analyzer import JobPostInfo
from ..job_search.resume_analyzer import ResumeInfo

@dataclass
class ResumeTemplate:
    """Template configuration for resume generation."""
    name: str
    description: str
    style: Dict[str, str]
    sections: List[str]
    html_template: str
    css_template: str

class ResumeGenerator:
    """Generates tailored resumes for specific job applications."""
    
    def __init__(self, templates_dir: str = "templates/resume"):
        """Initialize the resume generator."""
        self.templates_dir = templates_dir
        self.env = Environment(loader=FileSystemLoader(templates_dir))
        
        # Load available templates
        self.templates = self._load_templates()
        
        # PDF generation options
        self.pdf_options = {
            'page-size': 'Letter',
            'margin-top': '0.5in',
            'margin-right': '0.5in',
            'margin-bottom': '0.5in',
            'margin-left': '0.5in',
            'encoding': "UTF-8",
            'no-outline': None,
            'enable-local-file-access': None
        }
        
    def _load_templates(self) -> Dict[str, ResumeTemplate]:
        """Load available resume templates from the templates directory."""
        templates = {}
        
        # Scan templates directory
        for template_dir in os.listdir(self.templates_dir):
            config_path = os.path.join(self.templates_dir, template_dir, 'config.json')
            if os.path.isfile(config_path):
                try:
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                        
                    template = ResumeTemplate(
                        name=config['name'],
                        description=config['description'],
                        style=config['style'],
                        sections=config['sections'],
                        html_template=os.path.join(template_dir, 'template.html'),
                        css_template=os.path.join(template_dir, 'style.css')
                    )
                    
                    templates[template.name] = template
                except Exception as e:
                    logger.error(f"Error loading template {template_dir}: {e}")
                    
        return templates
        
    def generate_resume(
        self,
        base_resume: ResumeInfo,
        job: JobPostInfo,
        template_name: str = "modern",
        output_path: str = "resume.pdf"
    ) -> str:
        """Generate a tailored resume for a specific job application."""
        # Get template
        template = self.templates.get(template_name)
        if not template:
            raise ValueError(f"Template {template_name} not found")
            
        # Tailor resume content
        tailored_content = self._tailor_resume(base_resume, job)
        
        # Load templates
        html_template = self.env.get_template(template.html_template)
        css_template = self.env.get_template(template.css_template)
        
        # Generate HTML and CSS
        html_content = html_template.render(**tailored_content)
        css_content = css_template.render(**template.style)
        
        # Create temporary files
        temp_html = 'temp_resume.html'
        temp_css = 'temp_style.css'
        
        try:
            # Write temporary files
            with open(temp_html, 'w') as f:
                f.write(f'<style>{css_content}</style>\n{html_content}')
                
            # Generate PDF
            pdfkit.from_file(temp_html, output_path, options=self.pdf_options)
            
            return output_path
            
        finally:
            # Cleanup temporary files
            if os.path.exists(temp_html):
                os.remove(temp_html)
            if os.path.exists(temp_css):
                os.remove(temp_css)
                
    def _tailor_resume(self, base_resume: ResumeInfo, job: JobPostInfo) -> Dict:
        """Tailor resume content for the specific job."""
        # Start with base resume content
        content = {
            'contact': {
                'name': base_resume.name,
                'email': base_resume.email,
                'phone': base_resume.phone,
                'location': base_resume.location,
                'linkedin': base_resume.linkedin_url,
                'github': base_resume.github_url,
                'portfolio': base_resume.portfolio_url
            },
            'summary': self._tailor_summary(base_resume.summary, job),
            'skills': self._tailor_skills(base_resume.skills, job),
            'experience': self._tailor_experience(base_resume.experience, job),
            'education': base_resume.education,
            'projects': self._tailor_projects(base_resume.projects, job),
            'certifications': base_resume.certifications,
            'languages': base_resume.languages
        }
        
        return content
        
    def _tailor_summary(self, summary: Optional[str], job: JobPostInfo) -> str:
        """Tailor the professional summary for the job."""
        if not summary:
            # Generate a basic summary if none exists
            summary = f"Experienced professional seeking a position as {job.title}"
            
        # Add job-specific keywords
        keywords = []
        if job.skills_required:
            keywords.extend(job.skills_required)
        if job.skills_preferred:
            keywords.extend(job.skills_preferred)
            
        # Enhance summary with relevant keywords
        enhanced_summary = summary
        for keyword in keywords[:3]:  # Use top 3 keywords
            if keyword.lower() not in enhanced_summary.lower():
                enhanced_summary += f" with expertise in {keyword}"
                
        return enhanced_summary
        
    def _tailor_skills(self, skills: Set[str], job: JobPostInfo) -> Dict[str, List[str]]:
        """Organize and prioritize skills based on job requirements."""
        # Categorize skills
        categorized_skills = {
            'top': [],  # Required by job
            'relevant': [],  # Preferred by job
            'other': []  # Other skills
        }
        
        # Prioritize required skills
        for skill in skills:
            if skill in job.skills_required:
                categorized_skills['top'].append(skill)
            elif skill in job.skills_preferred:
                categorized_skills['relevant'].append(skill)
            else:
                categorized_skills['other'].append(skill)
                
        return categorized_skills
        
    def _tailor_experience(self, experience: List[Dict], job: JobPostInfo) -> List[Dict]:
        """Tailor work experience entries for the job."""
        # Sort experience by relevance
        scored_experience = []
        
        for exp in experience:
            score = self._calculate_experience_relevance(exp, job)
            scored_experience.append((score, exp))
            
        # Sort by score and take top entries
        scored_experience.sort(reverse=True)
        tailored_experience = []
        
        for score, exp in scored_experience[:5]:  # Keep top 5 most relevant experiences
            # Highlight relevant responsibilities
            exp = exp.copy()  # Create a copy to modify
            exp['responsibilities'] = self._highlight_relevant_responsibilities(
                exp['responsibilities'],
                job
            )
            tailored_experience.append(exp)
            
        return tailored_experience
        
    def _calculate_experience_relevance(self, experience: Dict, job: JobPostInfo) -> float:
        """Calculate relevance score for an experience entry."""
        score = 0.0
        
        # Check title relevance
        if experience.get('title'):
            title = experience['title'].lower()
            job_title = job.title.lower()
            
            if title == job_title:
                score += 1.0
            elif any(word in title for word in job_title.split()):
                score += 0.5
                
        # Check skills mentioned in responsibilities
        if experience.get('responsibilities'):
            mentioned_skills = set()
            for resp in experience['responsibilities']:
                resp_lower = resp.lower()
                for skill in job.skills_required | job.skills_preferred:
                    if skill.lower() in resp_lower:
                        mentioned_skills.add(skill)
                        
            skill_score = len(mentioned_skills) / len(job.skills_required | job.skills_preferred)
            score += skill_score
            
        return score
        
    def _highlight_relevant_responsibilities(
        self,
        responsibilities: List[str],
        job: JobPostInfo
    ) -> List[str]:
        """Prioritize and enhance relevant responsibilities."""
        scored_responsibilities = []
        
        for resp in responsibilities:
            score = 0
            resp_lower = resp.lower()
            
            # Check for skill mentions
            for skill in job.skills_required | job.skills_preferred:
                if skill.lower() in resp_lower:
                    score += 1
                    
            # Check for relevant keywords
            keywords = [job.title.lower()] + [
                'developed', 'implemented', 'managed', 'led', 'created',
                'designed', 'improved', 'reduced', 'increased', 'achieved'
            ]
            
            for keyword in keywords:
                if keyword in resp_lower:
                    score += 0.5
                    
            scored_responsibilities.append((score, resp))
            
        # Sort by relevance and take top entries
        scored_responsibilities.sort(reverse=True)
        return [resp for _, resp in scored_responsibilities[:5]]  # Keep top 5 responsibilities
        
    def _tailor_projects(self, projects: List[Dict], job: JobPostInfo) -> List[Dict]:
        """Select and prioritize relevant projects."""
        # Score projects by relevance
        scored_projects = []
        
        for project in projects:
            score = 0.0
            
            # Check technologies used
            if project.get('technologies'):
                relevant_techs = project['technologies'] & (job.skills_required | job.skills_preferred)
                score += len(relevant_techs) / len(job.skills_required | job.skills_preferred)
                
            # Check description for relevant keywords
            if project.get('description'):
                desc_lower = project['description'].lower()
                for skill in job.skills_required | job.skills_preferred:
                    if skill.lower() in desc_lower:
                        score += 0.5
                        
            scored_projects.append((score, project))
            
        # Sort by relevance and take top projects
        scored_projects.sort(reverse=True)
        return [project for _, project in scored_projects[:3]]  # Keep top 3 projects 