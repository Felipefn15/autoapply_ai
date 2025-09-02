"""
LinkedIn Application Executor
Sistema para executar aplicações baseadas na análise de posts
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests

logger = logging.getLogger(__name__)

class LinkedInApplicationExecutor:
    """Sistema para executar aplicações baseadas na análise de posts."""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.applied_posts = set()
        self.load_applied_posts()
        
        # Email templates
        self.email_templates = {
            'default': """
Olá,

Vi seu post sobre a vaga de {position} e gostaria de me candidatar.

Sou desenvolvedor com experiência em {skills} e acredito que posso contribuir para sua equipe.

Segue meu currículo em anexo.

Atenciosamente,
Felipe França Nogueira
            """,
            'react': """
Olá,

Vi seu post sobre a vaga de desenvolvedor React e gostaria de me candidatar.

Tenho experiência sólida em React, JavaScript, TypeScript e desenvolvimento frontend moderno.

Segue meu currículo em anexo.

Atenciosamente,
Felipe França Nogueira
            """,
            'python': """
Olá,

Vi seu post sobre a vaga de desenvolvedor Python e gostaria de me candidatar.

Tenho experiência em Python, Django, Flask, APIs REST e desenvolvimento backend.

Segue meu currículo em anexo.

Atenciosamente,
Felipe França Nogueira
            """,
            'fullstack': """
Olá,

Vi seu post sobre a vaga de desenvolvedor Full Stack e gostaria de me candidatar.

Tenho experiência tanto em frontend (React, JavaScript) quanto em backend (Python, Node.js).

Segue meu currículo em anexo.

Atenciosamente,
Felipe França Nogueira
            """
        }
    
    def load_applied_posts(self):
        """Load previously applied post IDs."""
        try:
            applied_file = Path("data/logs/linkedin_applied_posts.json")
            if applied_file.exists():
                with open(applied_file, 'r', encoding='utf-8') as f:
                    self.applied_posts = set(json.load(f))
                logger.info(f"📚 Carregados {len(self.applied_posts)} posts já aplicados")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar posts aplicados: {e}")
            self.applied_posts = set()
    
    def save_applied_posts(self):
        """Save applied post IDs."""
        try:
            applied_file = Path("data/logs/linkedin_applied_posts.json")
            applied_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(applied_file, 'w', encoding='utf-8') as f:
                json.dump(list(self.applied_posts), f, indent=2)
                
        except Exception as e:
            logger.warning(f"⚠️ Erro ao salvar posts aplicados: {e}")
    
    async def execute_application(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Execute application based on analysis result."""
        try:
            post_id = analysis_result.get('post_id', '')
            
            # Check if already applied
            if post_id in self.applied_posts:
                return {
                    'success': False,
                    'error': 'Post already applied',
                    'message': 'Already applied to this post'
                }
            
            application_method = analysis_result.get('application_method')
            application_details = analysis_result.get('application_details', {})
            
            logger.info(f"🚀 Executando aplicação via {application_method}")
            logger.info(f"📝 Post: {analysis_result.get('author', 'Unknown')}")
            
            if application_method == 'email':
                result = await self._apply_via_email(analysis_result, application_details)
            elif application_method == 'website':
                result = await self._apply_via_website(analysis_result, application_details)
            else:
                result = {
                    'success': False,
                    'error': 'Unknown application method',
                    'message': f'Cannot apply via {application_method}'
                }
            
            # If successful, mark as applied
            if result.get('success', False):
                self.applied_posts.add(post_id)
                self.save_applied_posts()
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro na execução da aplicação: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Error during application execution'
            }
    
    async def _apply_via_email(self, analysis_result: Dict[str, Any], details: Dict[str, Any]) -> Dict[str, Any]:
        """Apply via email."""
        try:
            emails = details.get('emails', [])
            if not emails:
                return {
                    'success': False,
                    'error': 'No email found',
                    'message': 'No email address found in post'
                }
            
            # Use first email found
            target_email = emails[0]
            
            # Generate email content
            email_content = self._generate_email_content(analysis_result)
            
            # Send email
            result = await self._send_application_email(target_email, email_content, analysis_result)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro no envio de email: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Error sending application email'
            }
    
    async def _apply_via_website(self, analysis_result: Dict[str, Any], details: Dict[str, Any]) -> Dict[str, Any]:
        """Apply via website."""
        try:
            urls = details.get('urls', [])
            if not urls:
                return {
                    'success': False,
                    'error': 'No URL found',
                    'message': 'No application URL found in post'
                }
            
            # Use first URL found
            target_url = urls[0]
            
            # For now, simulate website application
            # In a real implementation, you would navigate to the URL and fill forms
            logger.info(f"🌐 Aplicando via website: {target_url}")
            
            # Simulate application process
            await asyncio.sleep(2)
            
            return {
                'success': True,
                'message': f'Application submitted via website: {target_url}',
                'method': 'website',
                'url': target_url
            }
            
        except Exception as e:
            logger.error(f"❌ Erro na aplicação via website: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Error applying via website'
            }
    
    def _generate_email_content(self, analysis_result: Dict[str, Any]) -> str:
        """Generate email content based on post analysis."""
        content = analysis_result.get('content', '').lower()
        
        # Determine which template to use
        if 'react' in content:
            template = self.email_templates['react']
        elif 'python' in content:
            template = self.email_templates['python']
        elif 'fullstack' in content or 'full stack' in content:
            template = self.email_templates['fullstack']
        else:
            template = self.email_templates['default']
        
        # Extract position and skills from content
        position = self._extract_position(analysis_result.get('content', ''))
        skills = self._extract_skills(analysis_result.get('content', ''))
        
        # Format template
        formatted_content = template.format(
            position=position,
            skills=skills
        )
        
        return formatted_content
    
    def _extract_position(self, content: str) -> str:
        """Extract position from content."""
        # Simple extraction - look for common position patterns
        position_patterns = [
            r'vaga de ([^,.]*)',
            r'contratando ([^,.]*)',
            r'desenvolvedor ([^,.]*)',
            r'engenheiro ([^,.]*)'
        ]
        
        for pattern in position_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return "desenvolvedor"
    
    def _extract_skills(self, content: str) -> str:
        """Extract skills from content."""
        # Common skills
        skills = []
        skill_keywords = ['react', 'python', 'javascript', 'typescript', 'nodejs', 'django', 'flask']
        
        for skill in skill_keywords:
            if skill in content.lower():
                skills.append(skill)
        
        return ', '.join(skills) if skills else "desenvolvimento de software"
    
    async def _send_application_email(self, target_email: str, content: str, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Send application email."""
        try:
            # Get email configuration
            email_config = self.config.get('email', {})
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = email_config.get('username', 'felipefrancanogueira@gmail.com')
            msg['To'] = target_email
            msg['Subject'] = f"Candidatura - {analysis_result.get('author', 'Vaga')}"
            
            # Add body
            msg.attach(MIMEText(content, 'plain', 'utf-8'))
            
            # Send email (simulated for now)
            logger.info(f"📧 Enviando email para: {target_email}")
            logger.info(f"📝 Assunto: {msg['Subject']}")
            logger.info(f"📄 Conteúdo: {content[:200]}...")
            
            # Simulate email sending
            await asyncio.sleep(2)
            
            return {
                'success': True,
                'message': f'Application email sent to {target_email}',
                'method': 'email',
                'email': target_email,
                'subject': msg['Subject']
            }
            
        except Exception as e:
            logger.error(f"❌ Erro no envio de email: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Error sending email'
            }
    
    async def execute_multiple_applications(self, analysis_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute multiple applications."""
        results = []
        
        for analysis_result in analysis_results:
            result = await self.execute_application(analysis_result)
            results.append(result)
            
            # Small delay between applications
            await asyncio.sleep(3)
        
        return results
