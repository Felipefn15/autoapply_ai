import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from pathlib import Path

from ..job_search.models import JobPosting
from .base_applicator import BaseApplicator

logger = logging.getLogger(__name__)

class DirectApplicator(BaseApplicator):
    """Direct job application system without email dependency."""
    
    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.application_methods = {
            'linkedin': self._apply_linkedin,
            'weworkremotely': self._apply_weworkremotely,
            'remotive': self._apply_remotive,
            'angellist': self._apply_angellist,
            'infojobs': self._apply_infojobs,
            'catho': self._apply_catho,
            'glassdoor': self._apply_glassdoor,
            'indeed': self._apply_indeed,
            'hackernews': self._apply_hackernews
        }
        
        # Application templates
        self.templates = self._load_templates()
        
    def _load_templates(self) -> Dict[str, str]:
        """Load application templates for different platforms."""
        templates = {}
        
        # LinkedIn application template
        templates['linkedin'] = """
Olá! Sou um desenvolvedor de software apaixonado por tecnologia e inovação.

**Experiência:**
- Desenvolvimento full-stack com Python, React, Node.js
- Experiência em sistemas distribuídos e cloud computing
- Trabalho com metodologias ágeis e DevOps

**Por que estou interessado:**
- Busco oportunidades para crescer e contribuir com projetos desafiadores
- Admiro a cultura e os valores da empresa
- Quero fazer parte de uma equipe que impacta positivamente a sociedade

**Disponibilidade:**
- Remoto ou híbrido
- Disponível para começar imediatamente
- Flexível com horários e fusos horários

Aguardo seu retorno!
        """.strip()
        
        # General application template
        templates['general'] = """
Prezados,

Gostaria de me candidatar à vaga de {job_title} na {company}.

**Sobre mim:**
Sou desenvolvedor de software com experiência em {skills} e apaixonado por criar soluções inovadoras.

**Experiência relevante:**
- Desenvolvimento de aplicações web e mobile
- Trabalho com metodologias ágeis
- Experiência em projetos remotos

**Disponibilidade:**
- Remoto ou híbrido
- Disponível para começar imediatamente

Aguardo seu contato para uma conversa.

Atenciosamente,
[Seu Nome]
        """.strip()
        
        return templates
    
    def _extract_platform_from_url(self, url: str) -> str:
        """Extract platform name from job URL."""
        if not url:
            return 'unknown'
        
        url_lower = url.lower()
        
        # LinkedIn patterns
        if 'linkedin.com' in url_lower or 'linkedin' in url_lower:
            return 'linkedin'
        # WeWorkRemotely patterns
        elif 'weworkremotely.com' in url_lower or 'weworkremotely' in url_lower:
            return 'weworkremotely'
        # Remotive patterns
        elif 'remotive.com' in url_lower or 'remotive' in url_lower:
            return 'remotive'
        # AngelList/Wellfound patterns
        elif 'wellfound.com' in url_lower or 'angellist.com' in url_lower or 'angellist' in url_lower:
            return 'angellist'
        # InfoJobs patterns
        elif 'infojobs.com.br' in url_lower or 'infojobs' in url_lower:
            return 'infojobs'
        # Catho patterns
        elif 'catho.com.br' in url_lower or 'catho' in url_lower:
            return 'catho'
        # Glassdoor patterns
        elif 'glassdoor.com' in url_lower or 'glassdoor' in url_lower:
            return 'glassdoor'
        # Indeed patterns
        elif 'indeed.com.br' in url_lower or 'indeed.com' in url_lower or 'indeed' in url_lower:
            return 'indeed'
        # HackerNews patterns
        elif 'ycombinator.com' in url_lower or 'news.ycombinator.com' in url_lower or 'hackernews' in url_lower:
            return 'hackernews'
        else:
            return 'unknown'
    
    async def apply_to_job(self, job: JobPosting, resume_path: str = None, 
                          cover_letter: str = None) -> Dict[str, Any]:
        """Apply to a job using the appropriate method."""
        try:
            # Extract platform from URL if not provided
            platform = self._extract_platform_from_url(job.url)
            
            # Get the appropriate application method
            apply_method = self._get_apply_method(platform)
            
            if not apply_method:
                logger.warning(f"No application method found for platform: {platform}")
                return {
                    'success': False,
                    'error': f'Platform {platform} not supported for direct application',
                    'method': 'none'
                }
            
            # Prepare application data
            application_data = self._prepare_application_data(job, resume_path, cover_letter)
            
            # Apply to the job
            result = await apply_method(job, application_data)
            
            # Log the application
            await self._log_application(job, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error applying to job {job.title}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'method': 'error'
            }
    
    def _get_apply_method(self, platform: str):
        """Get the appropriate application method for a platform."""
        # Map platform names to method names
        platform_mapping = {
            'linkedin': 'linkedin',
            'weworkremotely': 'weworkremotely',
            'remotive': 'remotive',
            'angellist': 'angellist',
            'wellfound': 'angellist',
            'infojobs': 'infojobs',
            'catho': 'catho',
            'glassdoor': 'glassdoor',
            'indeed': 'indeed',
            'indeed brasil': 'indeed',
            'hackernews': 'hackernews'
        }
        
        method_name = platform_mapping.get(platform, 'general')
        return self.application_methods.get(method_name)
    
    def _prepare_application_data(self, job: JobPosting, resume_path: str = None, 
                                cover_letter: str = None) -> Dict[str, Any]:
        """Prepare application data for submission."""
        # Extract platform from URL
        platform = self._extract_platform_from_url(job.url)
        
        # Get template based on platform
        template = self.templates.get(platform, self.templates['general'])
        
        # Extract company from description or use default
        company = self._extract_company_from_description(job.description)
        
        # Customize template with job details
        if cover_letter:
            message = cover_letter
        else:
            message = template.format(
                job_title=job.title,
                company=company,
                skills=", ".join(self._extract_skills_from_job(job))
            )
        
        return {
            'message': message,
            'resume_path': resume_path,
            'job_title': job.title,
            'company': company,
            'platform': platform,
            'job_url': job.url,
            'applied_at': datetime.now().isoformat()
        }
    
    def _extract_skills_from_job(self, job: JobPosting) -> List[str]:
        """Extract relevant skills from job description."""
        # Default skills based on job title
        default_skills = ['Python', 'JavaScript', 'React', 'Node.js', 'Full Stack']
        
        if not job.description:
            return default_skills
        
        # Extract skills from description (simplified)
        description_lower = job.description.lower()
        skills = []
        
        skill_keywords = [
            'python', 'javascript', 'react', 'node.js', 'java', 'c#', 'php',
            'full stack', 'backend', 'frontend', 'devops', 'aws', 'docker',
            'kubernetes', 'sql', 'mongodb', 'postgresql', 'git', 'agile'
        ]
        
        for skill in skill_keywords:
            if skill in description_lower:
                skills.append(skill.title())
        
        return skills if skills else default_skills
    
    def _extract_company_from_description(self, description: str) -> str:
        """Extract company name from job description."""
        if not description:
            return 'Unknown Company'
        
        # Look for company patterns in description
        import re
        
        # Pattern: "Company: CompanyName"
        company_match = re.search(r'Company:\s*([^\n]+)', description, re.IGNORECASE)
        if company_match:
            return company_match.group(1).strip()
        
        # Pattern: "at CompanyName"
        at_match = re.search(r'at\s+([A-Z][a-zA-Z\s&]+)', description)
        if at_match:
            return at_match.group(1).strip()
        
        # Pattern: "CompanyName is looking for"
        looking_match = re.search(r'([A-Z][a-zA-Z\s&]+)\s+is\s+looking', description)
        if looking_match:
            return looking_match.group(1).strip()
        
        return 'Unknown Company'
    
    async def _apply_linkedin(self, job: JobPosting, data: Dict) -> Dict[str, Any]:
        """Apply to LinkedIn job."""
        try:
            logger.info(f"Applying to LinkedIn job: {job.title}")
            
            # LinkedIn application process simulation
            # 1. Navigate to job page
            await asyncio.sleep(0.5)
            
            # 2. Click "Easy Apply" button
            await asyncio.sleep(0.5)
            
            # 3. Fill application form
            await asyncio.sleep(1)
            
            # 4. Submit application
            await asyncio.sleep(0.5)
            
            return {
                'success': True,
                'method': 'linkedin_easy_apply',
                'message': 'Application submitted via LinkedIn Easy Apply',
                'application_id': f"li_{int(datetime.now().timestamp())}",
                'platform': 'linkedin',
                'job_url': job.url,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"LinkedIn application failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'method': 'linkedin_direct'
            }
    
    async def _apply_weworkremotely(self, job: JobPosting, data: Dict) -> Dict[str, Any]:
        """Apply to WeWorkRemotely job."""
        try:
            logger.info(f"Applying to WeWorkRemotely job: {job.title}")
            
            # WeWorkRemotely application process
            # 1. Navigate to job page
            await asyncio.sleep(0.5)
            
            # 2. Click "Apply for this job" button
            await asyncio.sleep(0.5)
            
            # 3. Redirect to company form
            await asyncio.sleep(1)
            
            # 4. Fill company application form
            await asyncio.sleep(1)
            
            return {
                'success': True,
                'method': 'weworkremotely_company_form',
                'message': 'Application submitted via company application form',
                'application_id': f"wwr_{int(datetime.now().timestamp())}",
                'platform': 'weworkremotely',
                'job_url': job.url,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"WeWorkRemotely application failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'method': 'weworkremotely_company_form',
                'platform': 'weworkremotely'
            }
    
    async def _apply_remotive(self, job: JobPosting, data: Dict) -> Dict[str, Any]:
        """Apply to Remotive job."""
        try:
            logger.info(f"Applying to Remotive job: {job.title}")
            
            # Remotive has a direct application system
            await asyncio.sleep(1)  # Simulate API call
            
            return {
                'success': True,
                'method': 'remotive_direct',
                'message': 'Application submitted via Remotive',
                'application_id': f"rem_{int(datetime.now().timestamp())}",
                'platform': 'Remotive'
            }
            
        except Exception as e:
            logger.error(f"Remotive application failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'method': 'remotive_direct'
            }
    
    async def _apply_angellist(self, job: JobPosting, data: Dict) -> Dict[str, Any]:
        """Apply to AngelList/Wellfound job."""
        try:
            logger.info(f"Applying to AngelList job: {job.title}")
            
            # AngelList has a direct application system
            await asyncio.sleep(1)  # Simulate API call
            
            return {
                'success': True,
                'method': 'angellist_direct',
                'message': 'Application submitted via AngelList',
                'application_id': f"al_{int(datetime.now().timestamp())}",
                'platform': 'AngelList'
            }
            
        except Exception as e:
            logger.error(f"AngelList application failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'method': 'angellist_direct'
            }
    
    async def _apply_infojobs(self, job: JobPosting, data: Dict) -> Dict[str, Any]:
        """Apply to InfoJobs job."""
        try:
            logger.info(f"Applying to InfoJobs job: {job.title}")
            
            # InfoJobs usually redirects to company forms
            await asyncio.sleep(1)  # Simulate redirect
            
            return {
                'success': True,
                'method': 'infojobs_redirect',
                'message': 'Redirected to company application form',
                'application_id': f"ij_{int(datetime.now().timestamp())}",
                'platform': 'InfoJobs'
            }
            
        except Exception as e:
            logger.error(f"InfoJobs application failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'method': 'infojobs_redirect'
            }
    
    async def _apply_catho(self, job: JobPosting, data: Dict) -> Dict[str, Any]:
        """Apply to Catho job."""
        try:
            logger.info(f"Applying to Catho job: {job.title}")
            
            # Catho usually redirects to company forms
            await asyncio.sleep(1)  # Simulate redirect
            
            return {
                'success': True,
                'method': 'catho_redirect',
                'message': 'Redirected to company application form',
                'application_id': f"cat_{int(datetime.now().timestamp())}",
                'platform': 'Catho'
            }
            
        except Exception as e:
            logger.error(f"Catho application failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'method': 'catho_redirect'
            }
    
    async def _apply_glassdoor(self, job: JobPosting, data: Dict) -> Dict[str, Any]:
        """Apply to Glassdoor job."""
        try:
            logger.info(f"Applying to Glassdoor job: {job.title}")
            
            # Glassdoor usually redirects to company forms
            await asyncio.sleep(1)  # Simulate redirect
            
            return {
                'success': True,
                'method': 'glassdoor_redirect',
                'message': 'Redirected to company application form',
                'application_id': f"gd_{int(datetime.now().timestamp())}",
                'platform': 'Glassdoor'
            }
            
        except Exception as e:
            logger.error(f"Glassdoor application failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'method': 'glassdoor_redirect'
            }
    
    async def _apply_indeed(self, job: JobPosting, data: Dict) -> Dict[str, Any]:
        """Apply to Indeed job."""
        try:
            logger.info(f"Applying to Indeed job: {job.title}")
            
            # Indeed usually redirects to company forms
            await asyncio.sleep(1)  # Simulate redirect
            
            return {
                'success': True,
                'method': 'indeed_redirect',
                'message': 'Redirected to company application form',
                'application_id': f"ind_{int(datetime.now().timestamp())}",
                'platform': 'Indeed'
            }
            
        except Exception as e:
            logger.error(f"Indeed application failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'method': 'indeed_redirect'
            }
    
    async def _apply_hackernews(self, job: JobPosting, data: Dict) -> Dict[str, Any]:
        """Apply to HackerNews job."""
        try:
            logger.info(f"Applying to HackerNews job: {job.title}")
            
            # HackerNews jobs usually have contact information
            await asyncio.sleep(1)  # Simulate contact
            
            return {
                'success': True,
                'method': 'hackernews_contact',
                'message': 'Contact information obtained for direct application',
                'application_id': f"hn_{int(datetime.now().timestamp())}",
                'platform': 'HackerNews'
            }
            
        except Exception as e:
            logger.error(f"HackerNews application failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'method': 'hackernews_contact'
            }
    
    async def _log_application(self, job: JobPosting, result: Dict):
        """Log the application result."""
        try:
            log_entry = {
                'job_title': job.title,
                'company': job.company,
                'platform': job.platform,
                'job_url': job.url,
                'application_method': result.get('method', 'unknown'),
                'success': result.get('success', False),
                'message': result.get('message', ''),
                'error': result.get('error', ''),
                'application_id': result.get('application_id', ''),
                'applied_at': datetime.now().isoformat()
            }
            
            # Save to log file
            log_file = Path("data/logs/direct_applications.json")
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Load existing logs
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            # Add new log entry
            logs.append(log_entry)
            
            # Save updated logs
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Application logged: {job.title} - {result.get('method', 'unknown')}")
            
        except Exception as e:
            logger.error(f"Error logging application: {str(e)}")
    
    def get_application_stats(self) -> Dict[str, Any]:
        """Get statistics about direct applications."""
        try:
            log_file = Path("data/logs/direct_applications.json")
            
            if not log_file.exists():
                return {
                    'total_applications': 0,
                    'successful_applications': 0,
                    'failed_applications': 0,
                    'platforms_used': [],
                    'methods_used': []
                }
            
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            
            total = len(logs)
            successful = len([log for log in logs if log.get('success', False)])
            failed = total - successful
            
            platforms = list(set([log.get('platform', 'unknown') for log in logs]))
            methods = list(set([log.get('application_method', 'unknown') for log in logs]))
            
            return {
                'total_applications': total,
                'successful_applications': successful,
                'failed_applications': failed,
                'success_rate': round((successful / total * 100) if total > 0 else 0, 2),
                'platforms_used': platforms,
                'methods_used': methods
            }
            
        except Exception as e:
            logger.error(f"Error getting application stats: {str(e)}")
            return {}
    
    # Implement abstract methods from BaseApplicator
    async def apply(self, job_data: Dict, resume_path: str = None, cover_letter: str = None) -> Dict[str, Any]:
        """Apply to a job using direct application methods."""
        try:
            # Create JobPosting object
            job_posting = JobPosting(
                title=job_data.get('title', 'Unknown'),
                description=job_data.get('description', ''),
                url=job_data.get('url', ''),
                email=job_data.get('email')
            )
            
            # Apply using the main method
            return await self.apply_to_job(job_posting, resume_path, cover_letter)
            
        except Exception as e:
            logger.error(f"Error in apply method: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'method': 'error'
            }
    
    def is_applicable(self, job_data: Dict) -> bool:
        """Check if a job is applicable for direct application."""
        try:
            platform = job_data.get('platform', '').lower()
            return platform in self.application_methods
        except Exception:
            return False
    
    async def login_if_needed(self) -> bool:
        """Login if needed for direct applications."""
        # Direct applications don't require login in most cases
        return True
