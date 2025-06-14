"""Email generator module for creating personalized application emails."""
from typing import Dict, List, Optional
from dataclasses import dataclass
import re

from loguru import logger

from ..job_search.post_analyzer import JobPostInfo
from ..job_search.resume_analyzer import ResumeInfo

@dataclass
class EmailTemplate:
    """Template for application emails."""
    subject: str
    body: str
    signature: str

class EmailGenerator:
    """Generates personalized application emails."""
    
    def __init__(self):
        """Initialize the email generator."""
        # Common email templates
        self.templates = {
            'direct_application': EmailTemplate(
                subject="Application for {job_title} position at {company}",
                body="""Dear {recipient},

I am writing to express my interest in the {job_title} position at {company}. With my background in {experience}, I believe I would be a strong addition to your team.

{skills_paragraph}

{experience_paragraph}

{closing_paragraph}

I have attached my resume for your review. I look forward to discussing how I can contribute to {company}'s success.

{signature}""",
                signature="""Best regards,
{name}
{email}
{phone}"""
            ),
            
            'referral': EmailTemplate(
                subject="Referred by {referrer} - {job_title} position",
                body="""Dear {recipient},

I was referred by {referrer} for the {job_title} position at {company}. Having discussed the role with them, I am very excited about the opportunity to join your team.

{skills_paragraph}

{experience_paragraph}

{closing_paragraph}

I have attached my resume for your consideration. I look forward to the opportunity to discuss how I can contribute to your team.

{signature}""",
                signature="""Best regards,
{name}
{email}
{phone}"""
            ),
            
            'follow_up': EmailTemplate(
                subject="Following up on {job_title} application",
                body="""Dear {recipient},

I hope this email finds you well. I am writing to follow up on my application for the {job_title} position at {company}, which I submitted on {application_date}.

I remain very interested in this opportunity and would welcome the chance to discuss how my background in {experience} aligns with your needs.

{closing_paragraph}

Thank you for your time and consideration.

{signature}""",
                signature="""Best regards,
{name}
{email}
{phone}"""
            )
        }
        
    def generate_email(
        self,
        candidate: ResumeInfo,
        job: JobPostInfo,
        template_type: str = 'direct_application',
        custom_content: Optional[Dict] = None
    ) -> Dict[str, str]:
        """Generate a personalized application email."""
        # Get template
        template = self.templates.get(template_type)
        if not template:
            raise ValueError(f"Template type {template_type} not found")
            
        # Generate content
        content = self._generate_content(candidate, job, custom_content)
        
        # Format template
        email = {
            'subject': template.subject.format(**content),
            'body': template.body.format(**content),
            'signature': template.signature.format(**content)
        }
        
        return email
        
    def _generate_content(
        self,
        candidate: ResumeInfo,
        job: JobPostInfo,
        custom_content: Optional[Dict] = None
    ) -> Dict[str, str]:
        """Generate content for email template placeholders."""
        # Basic content
        content = {
            'recipient': custom_content.get('recipient', 'Hiring Manager') if custom_content else 'Hiring Manager',
            'job_title': job.title,
            'company': job.company,
            'name': candidate.name,
            'email': candidate.email,
            'phone': candidate.phone or '',
            'referrer': custom_content.get('referrer', '') if custom_content else '',
            'application_date': custom_content.get('application_date', '') if custom_content else ''
        }
        
        # Generate experience summary
        experience_summary = self._generate_experience_summary(candidate)
        content['experience'] = experience_summary
        
        # Generate skills paragraph
        content['skills_paragraph'] = self._generate_skills_paragraph(candidate, job)
        
        # Generate experience paragraph
        content['experience_paragraph'] = self._generate_experience_paragraph(candidate, job)
        
        # Generate closing paragraph
        content['closing_paragraph'] = self._generate_closing_paragraph(job)
        
        # Add any additional custom content
        if custom_content:
            content.update(custom_content)
            
        return content
        
    def _generate_experience_summary(self, candidate: ResumeInfo) -> str:
        """Generate a brief summary of relevant experience."""
        if not candidate.experience:
            return "software development"
            
        # Get the most recent experience
        latest_exp = candidate.experience[0]
        if latest_exp.get('title'):
            return latest_exp['title'].lower()
            
        return "software development"
        
    def _generate_skills_paragraph(self, candidate: ResumeInfo, job: JobPostInfo) -> str:
        """Generate a paragraph highlighting relevant skills."""
        # Find matching skills
        matching_skills = []
        if job.skills_required:
            matching_required = job.skills_required & candidate.skills
            if matching_required:
                matching_skills.extend(matching_required)
                
        if job.skills_preferred:
            matching_preferred = job.skills_preferred & candidate.skills
            if matching_preferred:
                matching_skills.extend(list(matching_preferred)[:2])
                
        if not matching_skills:
            return "My technical background includes strong problem-solving abilities and a solid foundation in software development principles."
            
        # Format skills paragraph
        skills_text = "My technical expertise aligns well with your requirements, particularly in "
        if len(matching_skills) == 1:
            skills_text += f"{matching_skills[0]}."
        else:
            skills_text += f"{', '.join(matching_skills[:-1])} and {matching_skills[-1]}."
            
        return skills_text
        
    def _generate_experience_paragraph(self, candidate: ResumeInfo, job: JobPostInfo) -> str:
        """Generate a paragraph highlighting relevant experience."""
        if not candidate.experience:
            return ""
            
        # Get the most recent experience
        latest_exp = candidate.experience[0]
        if not latest_exp.get('responsibilities'):
            return ""
            
        # Select relevant achievements
        achievements = self._select_relevant_achievements(latest_exp['responsibilities'], job)
        if not achievements:
            return ""
            
        # Format experience paragraph
        exp_text = f"In my current role as {latest_exp['title']} at {latest_exp['company']}, "
        exp_text += f"I have {achievements[0].lower()}"
        
        if len(achievements) > 1:
            exp_text += f" and {achievements[1].lower()}"
            
        exp_text += ". This experience has prepared me well for the challenges at your company."
        
        return exp_text
        
    def _generate_closing_paragraph(self, job: JobPostInfo) -> str:
        """Generate a closing paragraph."""
        closing = f"I am particularly excited about the opportunity to join {job.company} "
        
        if job.remote_type == 'remote':
            closing += "and contribute to your distributed team. "
        else:
            closing += "and work alongside your talented team. "
            
        closing += "I am confident that my skills and enthusiasm would make me a valuable addition to your organization."
        
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