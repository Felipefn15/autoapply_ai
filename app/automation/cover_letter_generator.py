"""
Cover Letter Generator Module

Uses Groq API to generate personalized cover letters based on:
- Job details
- Resume information
- Required skills
- Achievements
"""
from typing import Dict, Optional
import json
from pathlib import Path
import groq
from loguru import logger

class CoverLetterGenerator:
    """Generates personalized cover letters using Groq API."""
    
    def __init__(self, api_key: str, model: str = "mixtral-8x7b-32768"):
        """Initialize the cover letter generator."""
        self.client = groq.Client(api_key=api_key)
        self.model = model
        
        # Load templates
        self.templates = self._load_templates()
        
    def generate(self, job: Dict) -> Optional[str]:
        """Generate a personalized cover letter for a job."""
        try:
            # Create prompt
            prompt = self._create_prompt(job)
            
            # Generate cover letter
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.templates['system_prompt']},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000,
                top_p=1,
                stream=False
            )
            
            # Extract and clean generated text
            cover_letter = response.choices[0].message.content.strip()
            
            # Post-process
            cover_letter = self._post_process(cover_letter)
            
            return cover_letter
            
        except Exception as e:
            logger.error(f"Error generating cover letter: {str(e)}")
            return None
            
    def _load_templates(self) -> Dict[str, str]:
        """Load cover letter templates and prompts."""
        templates = {
            'system_prompt': """You are an expert cover letter writer. Your task is to create a compelling, 
            personalized cover letter that highlights the candidate's relevant experience and skills for the 
            specific job. The cover letter should be professional, engaging, and demonstrate genuine interest 
            in the role and company. Focus on matching the candidate's qualifications with the job requirements.
            
            Guidelines:
            - Keep the tone professional but conversational
            - Highlight specific achievements and experiences
            - Show enthusiasm for the role and company
            - Keep paragraphs concise and focused
            - Avoid generic statements and clichés
            - Include specific details about the company and role
            - Match keywords from the job description
            - End with a clear call to action
            
            Format:
            [Today's Date]
            
            [Hiring Manager's Name/Title (if available)]
            [Company Name]
            
            Dear [Appropriate Greeting],
            
            [Opening Paragraph: Introduction and why you're excited about the role]
            
            [Body Paragraph 1: Your relevant experience and key achievements]
            
            [Body Paragraph 2: Specific skills and how they match the role]
            
            [Closing Paragraph: Enthusiasm, call to action, and thank you]
            
            Sincerely,
            [Candidate's Name]
            [Contact Information]""",
            
            'job_prompt': """Please write a cover letter for the following job:
            
            Job Title: {title}
            Company: {company}
            Location: {location}
            
            Job Description:
            {description}
            
            Candidate Information:
            Current Role: {current_role}
            Years of Experience: {years_experience}
            Key Skills: {skills}
            Recent Achievements: {achievements}
            
            Please create a personalized cover letter that:
            1. Shows enthusiasm for this specific role at {company}
            2. Highlights the most relevant experience and skills
            3. Demonstrates understanding of the company's needs
            4. Includes specific achievements that relate to the role
            5. Maintains a professional but engaging tone"""
        }
        return templates
        
    def _create_prompt(self, job: Dict) -> str:
        """Create prompt for cover letter generation."""
        # Format skills list
        skills = []
        for category, skill_list in job.get('skills', {}).items():
            skills.extend(skill_list)
        skills_str = ', '.join(skills)
        
        # Format achievements
        achievements = job.get('achievements', [])
        achievements_str = '\n- ' + '\n- '.join(achievements) if achievements else 'Not provided'
        
        # Create prompt using template
        prompt = self.templates['job_prompt'].format(
            title=job['title'],
            company=job['company'],
            location=job.get('location', 'Not specified'),
            description=job['description'],
            current_role=job.get('current_role', 'Not provided'),
            years_experience=job.get('years_of_experience', 'Not provided'),
            skills=skills_str,
            achievements=achievements_str
        )
        
        return prompt
        
    def _post_process(self, text: str) -> str:
        """Clean and format the generated cover letter."""
        # Remove any markdown formatting
        text = text.replace('```', '').strip()
        
        # Ensure proper spacing
        text = text.replace('\n\n\n', '\n\n')
        
        # Remove any system message artifacts
        text = text.replace('Here\'s a personalized cover letter:', '')
        text = text.replace('Here is your cover letter:', '')
        
        return text.strip() 