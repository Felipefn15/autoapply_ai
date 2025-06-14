"""Cover letter generator module for creating personalized cover letters."""
import os
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import json

from loguru import logger
from jinja2 import Environment, FileSystemLoader
import pdfkit

from ..job_search.post_analyzer import JobPostInfo
from ..job_search.resume_analyzer import ResumeInfo

@dataclass
class CoverLetterTemplate:
    """Template configuration for cover letter generation."""
    name: str
    description: str
    style: Dict[str, str]
    sections: List[str]
    html_template: str
    css_template: str

class CoverLetterGenerator:
    """Generates personalized cover letters for job applications."""
    
    def __init__(self, templates_dir: str = "templates/cover_letter"):
        """Initialize the cover letter generator."""
        self.templates_dir = templates_dir
        self.env = Environment(loader=FileSystemLoader(templates_dir))
        
        # Load available templates
        self.templates = self._load_templates()
        
        # PDF generation options
        self.pdf_options = {
            'page-size': 'Letter',
            'margin-top': '1in',
            'margin-right': '1in',
            'margin-bottom': '1in',
            'margin-left': '1in',
            'encoding': "UTF-8",
            'no-outline': None,
            'enable-local-file-access': None
        }
        
    def _load_templates(self) -> Dict[str, CoverLetterTemplate]:
        """Load available cover letter templates from the templates directory."""
        templates = {}
        
        # Scan templates directory
        for template_dir in os.listdir(self.templates_dir):
            config_path = os.path.join(self.templates_dir, template_dir, 'config.json')
            if os.path.isfile(config_path):
                try:
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                        
                    template = CoverLetterTemplate(
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
        
    def generate_cover_letter(
        self,
        candidate: ResumeInfo,
        job: JobPostInfo,
        template_name: str = "professional",
        output_path: str = "cover_letter.pdf",
        custom_content: Optional[Dict] = None
    ) -> str:
        """Generate a personalized cover letter for a job application."""
        # Get template
        template = self.templates.get(template_name)
        if not template:
            raise ValueError(f"Template {template_name} not found")
            
        # Generate content
        content = self._generate_content(candidate, job, custom_content)
        
        # Load templates
        html_template = self.env.get_template(template.html_template)
        css_template = self.env.get_template(template.css_template)
        
        # Generate HTML and CSS
        html_content = html_template.render(**content)
        css_content = css_template.render(**template.style)
        
        # Create temporary files
        temp_html = 'temp_cover_letter.html'
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
                
    def _generate_content(
        self,
        candidate: ResumeInfo,
        job: JobPostInfo,
        custom_content: Optional[Dict] = None
    ) -> Dict:
        """Generate personalized content for the cover letter."""
        today = datetime.now().strftime("%B %d, %Y")
        
        # Start with basic content
        content = {
            'date': today,
            'candidate': {
                'name': candidate.name,
                'email': candidate.email,
                'phone': candidate.phone,
                'location': candidate.location
            },
            'company': {
                'name': job.company,
                'location': job.location
            },
            'job': {
                'title': job.title,
                'type': job.employment_type,
                'remote': job.remote_type
            }
        }
        
        # Generate opening paragraph
        content['opening'] = self._generate_opening(candidate, job)
        
        # Generate body paragraphs
        content['body'] = self._generate_body(candidate, job)
        
        # Generate closing paragraph
        content['closing'] = self._generate_closing(candidate, job)
        
        # Add any custom content
        if custom_content:
            content.update(custom_content)
            
        return content
        
    def _generate_opening(self, candidate: ResumeInfo, job: JobPostInfo) -> str:
        """Generate the opening paragraph."""
        # Start with a standard greeting
        opening = f"Dear Hiring Manager,\n\n"
        
        # Add personalized introduction
        opening += f"I am writing to express my strong interest in the {job.title} position "
        if job.remote_type == 'remote':
            opening += f"at {job.company}. "
        else:
            opening += f"at {job.company} in {job.location}. "
            
        # Add enthusiasm and connection
        opening += "With my background in "
        
        # Mention relevant experience
        relevant_experience = []
        for exp in candidate.experience[:2]:  # Use top 2 most recent experiences
            if exp.get('title'):
                relevant_experience.append(exp['title'])
                
        if relevant_experience:
            opening += f"{' and '.join(relevant_experience)}, "
        else:
            opening += "software development, "
            
        opening += "I am confident in my ability to contribute effectively to your team."
        
        return opening
        
    def _generate_body(self, candidate: ResumeInfo, job: JobPostInfo) -> List[str]:
        """Generate the body paragraphs."""
        paragraphs = []
        
        # Skills and qualifications paragraph
        skills_para = "My technical expertise aligns well with your requirements, including "
        
        # Highlight matching required skills
        matching_skills = []
        if job.skills_required:
            matching_required = job.skills_required & candidate.skills
            if matching_required:
                matching_skills.extend(matching_required)
                
        # Add some preferred skills if available
        if job.skills_preferred:
            matching_preferred = job.skills_preferred & candidate.skills
            if matching_preferred:
                matching_skills.extend(list(matching_preferred)[:2])  # Add up to 2 preferred skills
                
        if matching_skills:
            skills_para += f"{', '.join(matching_skills[:-1])} and {matching_skills[-1]}. "
        else:
            skills_para += "a strong foundation in software development and problem-solving. "
            
        paragraphs.append(skills_para)
        
        # Experience and achievements paragraph
        if candidate.experience:
            exp_para = ""
            latest_exp = candidate.experience[0]  # Most recent experience
            
            if latest_exp.get('responsibilities'):
                # Pick most relevant achievements
                achievements = self._select_relevant_achievements(
                    latest_exp['responsibilities'],
                    job
                )
                
                if achievements:
                    exp_para = f"In my current role as {latest_exp['title']} at {latest_exp['company']}, "
                    exp_para += f"I have {achievements[0].lower()} "
                    if len(achievements) > 1:
                        exp_para += f"and {achievements[1].lower()} "
                    exp_para += "These experiences have prepared me well for the challenges and opportunities at your company."
                    
                    paragraphs.append(exp_para)
                    
        # Cultural fit and motivation paragraph
        culture_para = f"I am particularly drawn to {job.company} because of "
        
        if job.remote_type == 'remote':
            culture_para += "the opportunity to work with a distributed team and contribute to "
        else:
            culture_para += "the chance to join your team in person and contribute to "
            
        culture_para += "innovative solutions that make a real impact. "
        culture_para += "I am confident that my collaborative nature, problem-solving skills, "
        culture_para += "and dedication to continuous learning would make me a valuable addition to your team."
        
        paragraphs.append(culture_para)
        
        return paragraphs
        
    def _generate_closing(self, candidate: ResumeInfo, job: JobPostInfo) -> str:
        """Generate the closing paragraph."""
        closing = "Thank you for considering my application. "
        closing += "I am excited about the possibility of joining "
        closing += f"{job.company} and would welcome the opportunity to discuss how "
        closing += "I can contribute to your team's success. "
        closing += "I look forward to speaking with you soon.\n\n"
        closing += f"Best regards,\n{candidate.name}"
        
        return closing
        
    def _select_relevant_achievements(self, responsibilities: List[str], job: JobPostInfo) -> List[str]:
        """Select achievements most relevant to the job posting."""
        scored_achievements = []
        
        for resp in responsibilities:
            score = 0
            resp_lower = resp.lower()
            
            # Check for skill mentions
            for skill in job.skills_required | job.skills_preferred:
                if skill.lower() in resp_lower:
                    score += 2
                    
            # Check for impact words
            impact_words = [
                'developed', 'implemented', 'improved', 'increased',
                'reduced', 'managed', 'led', 'created', 'designed',
                'achieved', 'delivered', 'launched', 'optimized'
            ]
            
            for word in impact_words:
                if word in resp_lower:
                    score += 1
                    
            # Check for metrics
            if any(char.isdigit() for char in resp):
                score += 1
                
            scored_achievements.append((score, resp))
            
        # Sort by relevance and take top achievements
        scored_achievements.sort(reverse=True)
        return [ach for _, ach in scored_achievements[:2]]  # Return top 2 achievements 