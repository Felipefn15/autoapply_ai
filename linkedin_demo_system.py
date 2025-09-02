#!/usr/bin/env python3
"""
LinkedIn Demo System - Sistema de demonstração sem login
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
import json
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

class LinkedInDemoSystem:
    """Sistema de demonstração do LinkedIn."""
    
    def __init__(self):
        self.applied_jobs = set()
        self.applied_posts = set()
        self.load_applied_data()
        
        # Simulated job database
        self.easy_apply_jobs = [
            {
                'title': 'Desenvolvedor Front-end Pleno',
                'company': 'Flexge - Global English',
                'location': 'Foz do Iguaçu, Paraná, Brazil',
                'url': 'https://www.linkedin.com/jobs/view/4294117359',
                'description': 'Desenvolvedor Front-end Pleno com experiência em React, React Native e TypeScript',
                'platform': 'linkedin',
                'job_id': '4294117359',
                'has_easy_apply': True,
                'keywords': ['react', 'frontend', 'typescript', 'javascript']
            },
            {
                'title': 'PP - Fullstack Web Engineer',
                'company': 'Thaloz',
                'location': 'Brazil',
                'url': 'https://www.linkedin.com/jobs/view/4283401866',
                'description': 'Senior Fullstack Web Developer para desenvolvimento de aplicações web',
                'platform': 'linkedin',
                'job_id': '4283401866',
                'has_easy_apply': True,
                'keywords': ['fullstack', 'web', 'engineer', 'python', 'javascript']
            },
            {
                'title': 'Senior React Developer',
                'company': 'TechCorp Brasil',
                'location': 'São Paulo, Brazil',
                'url': 'https://www.linkedin.com/jobs/view/4280000001',
                'description': 'Senior React Developer with 5+ years experience',
                'platform': 'linkedin',
                'job_id': '4280000001',
                'has_easy_apply': True,
                'keywords': ['react', 'senior', 'javascript', 'frontend']
            }
        ]
        
        # Simulated posts database
        self.hiring_posts = [
            {
                'post_id': 'post_001',
                'author': 'Tech Startup CEO',
                'content': 'Estamos contratando desenvolvedor React! Envie seu CV para rh@techstartup.com.br. Experiência em JavaScript, TypeScript e React Native.',
                'url': 'https://www.linkedin.com/posts/post_001',
                'timestamp': '2 hours ago',
                'keywords': ['react', 'javascript', 'typescript']
            },
            {
                'post_id': 'post_002',
                'author': 'Digital Agency',
                'content': 'Vaga de Python Developer! Aplicar em: https://digitalagency.com/vagas. Requisitos: Python, Django, APIs REST.',
                'url': 'https://www.linkedin.com/posts/post_002',
                'timestamp': '4 hours ago',
                'keywords': ['python', 'django', 'backend']
            },
            {
                'post_id': 'post_003',
                'author': 'FinTech Company',
                'content': 'Procuramos Full Stack Developer! Contato: contato@fintech.com.br ou WhatsApp: (11) 99999-9999. React + Node.js.',
                'url': 'https://www.linkedin.com/posts/post_003',
                'timestamp': '6 hours ago',
                'keywords': ['fullstack', 'react', 'nodejs']
            }
        ]
    
    def load_applied_data(self):
        """Load previously applied data."""
        try:
            # Load applied jobs
            jobs_file = Path("data/logs/demo_applied_jobs.json")
            if jobs_file.exists():
                with open(jobs_file, 'r', encoding='utf-8') as f:
                    self.applied_jobs = set(json.load(f))
            
            # Load applied posts
            posts_file = Path("data/logs/demo_applied_posts.json")
            if posts_file.exists():
                with open(posts_file, 'r', encoding='utf-8') as f:
                    self.applied_posts = set(json.load(f))
            
            logger.info(f"📚 Carregados {len(self.applied_jobs)} jobs e {len(self.applied_posts)} posts já aplicados")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar dados aplicados: {e}")
            self.applied_jobs = set()
            self.applied_posts = set()
    
    def save_applied_data(self):
        """Save applied data."""
        try:
            # Save applied jobs
            jobs_file = Path("data/logs/demo_applied_jobs.json")
            jobs_file.parent.mkdir(parents=True, exist_ok=True)
            with open(jobs_file, 'w', encoding='utf-8') as f:
                json.dump(list(self.applied_jobs), f, indent=2)
            
            # Save applied posts
            posts_file = Path("data/logs/demo_applied_posts.json")
            with open(posts_file, 'w', encoding='utf-8') as f:
                json.dump(list(self.applied_posts), f, indent=2)
                
        except Exception as e:
            logger.warning(f"⚠️ Erro ao salvar dados aplicados: {e}")
    
    async def run_cycle(self) -> dict:
        """Run a single cycle of LinkedIn applications."""
        cycle_start = datetime.now()
        logger.info(f"\n🔄 === CICLO DEMO LINKEDIN INICIADO ===")
        logger.info(f"⏰ Início: {cycle_start.strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # 1. Easy Apply Applications
            logger.info("🚀 1. Aplicando Easy Apply...")
            easy_apply_results = await self._run_easy_apply_cycle()
            
            # 2. Post Analysis and Applications
            logger.info("📝 2. Analisando posts e aplicando...")
            post_results = await self._run_post_analysis_cycle()
            
            # Calculate totals
            total_applications = easy_apply_results['applications'] + post_results['applications']
            total_successful = easy_apply_results['successful'] + post_results['successful']
            total_failed = easy_apply_results['failed'] + post_results['failed']
            
            # Calculate cycle duration
            cycle_duration = (datetime.now() - cycle_start).total_seconds()
            
            # Log cycle results
            logger.info(f"\n📊 === RESULTADOS DO CICLO ===")
            logger.info(f"🚀 Easy Apply: {easy_apply_results['applications']} aplicações ({easy_apply_results['successful']} sucessos)")
            logger.info(f"📝 Posts: {post_results['applications']} aplicações ({post_results['successful']} sucessos)")
            logger.info(f"📊 Total: {total_applications} aplicações ({total_successful} sucessos)")
            logger.info(f"⏱️ Duração do ciclo: {cycle_duration:.1f}s")
            
            if total_applications > 0:
                success_rate = (total_successful / total_applications) * 100
                logger.info(f"📈 Taxa de sucesso: {success_rate:.1f}%")
            
            return {
                'easy_apply': easy_apply_results,
                'post_applications': post_results,
                'total_applications': total_applications,
                'total_successful': total_successful,
                'total_failed': total_failed,
                'duration': cycle_duration
            }
            
        except Exception as e:
            logger.error(f"❌ Erro no ciclo: {e}")
            return {
                'easy_apply': {'applications': 0, 'successful': 0, 'failed': 0},
                'post_applications': {'applications': 0, 'successful': 0, 'failed': 0},
                'total_applications': 0,
                'total_successful': 0,
                'total_failed': 0,
                'duration': 0
            }
    
    async def _run_easy_apply_cycle(self) -> dict:
        """Run Easy Apply cycle."""
        try:
            # Get available jobs
            available_jobs = [job for job in self.easy_apply_jobs if job['url'] not in self.applied_jobs]
            
            if not available_jobs:
                logger.info("ℹ️ Nenhuma vaga Easy Apply disponível")
                return {'applications': 0, 'successful': 0, 'failed': 0}
            
            logger.info(f"📋 Encontradas {len(available_jobs)} vagas Easy Apply disponíveis")
            
            # Apply to jobs
            applications = 0
            successful = 0
            failed = 0
            
            for job in available_jobs[:3]:  # Limit to 3 applications per cycle
                try:
                    logger.info(f"🚀 Aplicando Easy Apply: {job['title']} - {job['company']}")
                    logger.info(f"🔗 URL: {job['url']}")
                    
                    # Simulate Easy Apply process
                    await asyncio.sleep(2)
                    
                    # Simulate success (90% success rate)
                    if random.random() < 0.9:
                        successful += 1
                        logger.info(f"✅ Easy Apply bem-sucedido: Application submitted for {job['title']}")
                        self.applied_jobs.add(job['url'])
                    else:
                        failed += 1
                        logger.error(f"❌ Easy Apply falhou: Form validation error")
                    
                    applications += 1
                    
                    # Delay between applications
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    failed += 1
                    logger.error(f"❌ Erro na aplicação Easy Apply: {e}")
                    applications += 1
            
            return {'applications': applications, 'successful': successful, 'failed': failed}
            
        except Exception as e:
            logger.error(f"❌ Erro no ciclo Easy Apply: {e}")
            return {'applications': 0, 'successful': 0, 'failed': 0}
    
    async def _run_post_analysis_cycle(self) -> dict:
        """Run post analysis and application cycle."""
        try:
            # Get available posts
            available_posts = [post for post in self.hiring_posts if post['post_id'] not in self.applied_posts]
            
            if not available_posts:
                logger.info("ℹ️ Nenhum post de contratação disponível")
                return {'applications': 0, 'successful': 0, 'failed': 0}
            
            logger.info(f"📋 Encontrados {len(available_posts)} posts de contratação disponíveis")
            
            # Analyze and apply to posts
            applications = 0
            successful = 0
            failed = 0
            
            for post in available_posts[:2]:  # Limit to 2 posts per cycle
                try:
                    logger.info(f"🔍 Analisando post: {post['author']}")
                    logger.info(f"📝 Conteúdo: {post['content'][:100]}...")
                    
                    # Analyze post
                    analysis = self._analyze_post(post)
                    logger.info(f"📊 Análise: {analysis['application_method']} (confiança: {analysis['confidence']})")
                    
                    # Apply based on analysis
                    if analysis['application_method'] == 'email':
                        result = await self._apply_via_email(analysis)
                    elif analysis['application_method'] == 'website':
                        result = await self._apply_via_website(analysis)
                    else:
                        result = {'success': False, 'error': 'Unknown application method'}
                    
                    if result.get('success', False):
                        successful += 1
                        logger.info(f"✅ Aplicação bem-sucedida: {result.get('message', 'Success')}")
                        self.applied_posts.add(post['post_id'])
                    else:
                        failed += 1
                        logger.error(f"❌ Aplicação falhou: {result.get('error', 'Unknown error')}")
                    
                    applications += 1
                    
                    # Delay between applications
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    failed += 1
                    logger.error(f"❌ Erro na aplicação via post: {e}")
                    applications += 1
            
            return {'applications': applications, 'successful': successful, 'failed': failed}
            
        except Exception as e:
            logger.error(f"❌ Erro no ciclo de análise de posts: {e}")
            return {'applications': 0, 'successful': 0, 'failed': 0}
    
    def _analyze_post(self, post: dict) -> dict:
        """Analyze post to determine application method."""
        content = post['content'].lower()
        
        # Extract emails
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, post['content'])
        
        # Extract URLs
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, post['content'])
        
        # Determine application method
        if emails:
            return {
                'post_id': post['post_id'],
                'application_method': 'email',
                'emails': emails,
                'confidence': 0.9
            }
        elif urls:
            return {
                'post_id': post['post_id'],
                'application_method': 'website',
                'urls': urls,
                'confidence': 0.8
            }
        else:
            return {
                'post_id': post['post_id'],
                'application_method': 'email',
                'emails': ['contato@empresa.com'],
                'confidence': 0.5
            }
    
    async def _apply_via_email(self, analysis: dict) -> dict:
        """Apply via email."""
        emails = analysis.get('emails', [])
        if not emails:
            return {'success': False, 'error': 'No email found'}
        
        target_email = emails[0]
        logger.info(f"📧 Enviando email para: {target_email}")
        
        # Simulate email sending
        await asyncio.sleep(1)
        
        # Simulate success (85% success rate)
        if random.random() < 0.85:
            return {
                'success': True,
                'message': f'Application email sent to {target_email}',
                'method': 'email',
                'email': target_email
            }
        else:
            return {'success': False, 'error': 'Email delivery failed'}
    
    async def _apply_via_website(self, analysis: dict) -> dict:
        """Apply via website."""
        urls = analysis.get('urls', [])
        if not urls:
            return {'success': False, 'error': 'No URL found'}
        
        target_url = urls[0]
        logger.info(f"🌐 Aplicando via website: {target_url}")
        
        # Simulate website application
        await asyncio.sleep(2)
        
        # Simulate success (75% success rate)
        if random.random() < 0.75:
            return {
                'success': True,
                'message': f'Application submitted via website: {target_url}',
                'method': 'website',
                'url': target_url
            }
        else:
            return {'success': False, 'error': 'Website application failed'}
    
    async def run_continuous(self, max_cycles: int = 3):
        """Run continuous LinkedIn application system."""
        logger.info("🚀 === SISTEMA DEMO LINKEDIN INICIADO ===")
        logger.info(f"⏰ Início: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"🔄 Máximo de ciclos: {max_cycles}")
        
        total_cycles = 0
        total_applications = 0
        total_successful = 0
        total_failed = 0
        
        try:
            while total_cycles < max_cycles:
                # Run single cycle
                cycle_result = await self.run_cycle()
                
                # Update totals
                total_cycles += 1
                total_applications += cycle_result['total_applications']
                total_successful += cycle_result['total_successful']
                total_failed += cycle_result['total_failed']
                
                # Print overall statistics
                logger.info(f"\n🏆 === ESTATÍSTICAS GERAIS ===")
                logger.info(f"🔄 Total de ciclos: {total_cycles}/{max_cycles}")
                logger.info(f"📊 Total de aplicações: {total_applications}")
                logger.info(f"✅ Total bem-sucedidas: {total_successful}")
                logger.info(f"❌ Total falharam: {total_failed}")
                
                if total_applications > 0:
                    overall_success_rate = (total_successful / total_applications) * 100
                    logger.info(f"📈 Taxa de sucesso geral: {overall_success_rate:.1f}%")
                
                # If no applications in this cycle, break
                if cycle_result['total_applications'] == 0:
                    logger.info("🎉 Nenhuma nova aplicação encontrada! Sistema finalizado.")
                    break
                
                # Wait before next cycle
                if total_cycles < max_cycles:
                    logger.info(f"⏳ Aguardando 10s antes do próximo ciclo...")
                    await asyncio.sleep(10)
                
        except KeyboardInterrupt:
            logger.info("\n🛑 Sistema interrompido pelo usuário")
        except Exception as e:
            logger.error(f"❌ Erro crítico no sistema: {str(e)}")
        finally:
            # Save applied data
            self.save_applied_data()
            
            logger.info("\n🏁 === SISTEMA FINALIZADO ===")
            logger.info(f"📊 Estatísticas finais:")
            logger.info(f"   🔄 Total de ciclos: {total_cycles}")
            logger.info(f"   📊 Total de aplicações: {total_applications}")
            logger.info(f"   ✅ Total bem-sucedidas: {total_successful}")
            logger.info(f"   ❌ Total falharam: {total_failed}")
            
            if total_applications > 0:
                overall_success_rate = (total_successful / total_applications) * 100
                logger.info(f"   📈 Taxa de sucesso geral: {overall_success_rate:.1f}%")

async def main():
    """Main function."""
    system = LinkedInDemoSystem()
    await system.run_continuous(max_cycles=3)

if __name__ == "__main__":
    asyncio.run(main())
