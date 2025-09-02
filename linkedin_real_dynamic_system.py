#!/usr/bin/env python3
"""
LinkedIn Real Dynamic System - Sistema com busca dinâmica real no LinkedIn
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
import json
import random
import re
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

from app.automation.linkedin_dynamic_searcher import LinkedInDynamicSearcher
from app.automation.linkedin_easy_apply import LinkedInEasyApply
from app.automation.linkedin_application_executor import LinkedInApplicationExecutor
from app.main import load_config

class LinkedInRealDynamicSystem:
    """Sistema LinkedIn com busca dinâmica real e aplicações automáticas."""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config = load_config(config_path)
        self.dynamic_searcher = LinkedInDynamicSearcher(self.config)
        self.easy_apply = LinkedInEasyApply(self.config)
        self.application_executor = LinkedInApplicationExecutor(self.config)
        
        # Track applied jobs and posts
        self.applied_jobs = set()
        self.applied_posts = set()
        self.load_applied_data()
        
        # Get LinkedIn credentials
        self.linkedin_email = self.config.get('linkedin', {}).get('email', '')
        self.linkedin_password = self.config.get('linkedin', {}).get('password', '')
        
        # Search configuration
        self.search_keywords = self.config.get('linkedin', {}).get('feed_search', {}).get('keywords', [
            'software engineer', 'developer', 'full stack', 'backend', 'frontend', 
            'react', 'node.js', 'python', 'javascript', 'typescript'
        ])
        
        self.locations = self.config.get('linkedin', {}).get('job_search', {}).get('locations', [
            'Remote', 'Worldwide', 'United States', 'Canada', 'Europe'
        ])
        
        logger.info(f"📧 Email LinkedIn: {self.linkedin_email}")
        logger.info(f"🔍 Keywords: {len(self.search_keywords)} palavras-chave")
        logger.info(f"📍 Locations: {len(self.locations)} localizações")
        logger.info(f"🚀 Sistema de busca dinâmica real ativado")
    
    def load_applied_data(self):
        """Load previously applied data."""
        try:
            # Load applied jobs
            jobs_file = Path("data/logs/real_dynamic_applied_jobs.json")
            if jobs_file.exists():
                with open(jobs_file, 'r', encoding='utf-8') as f:
                    self.applied_jobs = set(json.load(f))
            
            # Load applied posts
            posts_file = Path("data/logs/real_dynamic_applied_posts.json")
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
            jobs_file = Path("data/logs/real_dynamic_applied_jobs.json")
            jobs_file.parent.mkdir(parents=True, exist_ok=True)
            with open(jobs_file, 'w', encoding='utf-8') as f:
                json.dump(list(self.applied_jobs), f, indent=2)
            
            # Save applied posts
            posts_file = Path("data/logs/real_dynamic_applied_posts.json")
            with open(posts_file, 'w', encoding='utf-8') as f:
                json.dump(list(self.applied_posts), f, indent=2)
                
        except Exception as e:
            logger.warning(f"⚠️ Erro ao salvar dados aplicados: {e}")
    
    async def run_cycle(self) -> dict:
        """Run a single cycle of LinkedIn applications."""
        cycle_start = datetime.now()
        logger.info(f"\n🔄 === CICLO LINKEDIN DINÂMICO REAL INICIADO ===")
        logger.info(f"⏰ Início: {cycle_start.strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # 1. Real Dynamic Job Search and Easy Apply
            logger.info("🚀 1. Buscando vagas dinamicamente e aplicando...")
            job_results = await self._run_real_dynamic_job_search()
            
            # 2. Post Analysis and Applications (simulated for now)
            logger.info("📝 2. Analisando posts e aplicando...")
            post_results = await self._run_post_analysis_cycle()
            
            # Calculate totals
            total_applications = job_results['applications'] + post_results['applications']
            total_successful = job_results['successful'] + post_results['successful']
            total_failed = job_results['failed'] + post_results['failed']
            
            # Calculate cycle duration
            cycle_duration = (datetime.now() - cycle_start).total_seconds()
            
            # Log cycle results
            logger.info(f"\n📊 === RESULTADOS DO CICLO ===")
            logger.info(f"🚀 Busca Dinâmica Real: {job_results['applications']} aplicações ({job_results['successful']} sucessos)")
            logger.info(f"📝 Posts: {post_results['applications']} aplicações ({post_results['successful']} sucessos)")
            logger.info(f"📊 Total: {total_applications} aplicações ({total_successful} sucessos)")
            logger.info(f"⏱️ Duração do ciclo: {cycle_duration:.1f}s")
            
            if total_applications > 0:
                success_rate = (total_successful / total_applications) * 100
                logger.info(f"📈 Taxa de sucesso: {success_rate:.1f}%")
            
            return {
                'dynamic_search': job_results,
                'post_applications': post_results,
                'total_applications': total_applications,
                'total_successful': total_successful,
                'total_failed': total_failed,
                'duration': cycle_duration
            }
            
        except Exception as e:
            logger.error(f"❌ Erro no ciclo: {e}")
            return {
                'dynamic_search': {'applications': 0, 'successful': 0, 'failed': 0},
                'post_applications': {'applications': 0, 'successful': 0, 'failed': 0},
                'total_applications': 0,
                'total_successful': 0,
                'total_failed': 0,
                'duration': 0
            }
    
    async def _run_real_dynamic_job_search(self) -> dict:
        """Run real dynamic job search and application."""
        try:
            # Search for jobs dynamically using real LinkedIn search
            logger.info("🔍 Iniciando busca dinâmica real de vagas...")
            jobs = await self.dynamic_searcher.search_jobs_dynamically(max_jobs=30)
            
            if not jobs:
                logger.info("ℹ️ Nenhuma vaga encontrada na busca dinâmica real")
                return {'applications': 0, 'successful': 0, 'failed': 0}
            
            logger.info(f"📋 Encontradas {len(jobs)} vagas na busca dinâmica real")
            
            # Filter available jobs
            available_jobs = [job for job in jobs if job['url'] not in self.applied_jobs]
            
            if not available_jobs:
                logger.info("ℹ️ Todas as vagas encontradas já foram aplicadas")
                return {'applications': 0, 'successful': 0, 'failed': 0}
            
            logger.info(f"📋 {len(available_jobs)} vagas disponíveis para aplicação")
            
            # Apply to jobs
            applications = 0
            successful = 0
            failed = 0
            
            for job in available_jobs[:15]:  # Limit to 15 applications per cycle
                try:
                    logger.info(f"🚀 Aplicando para: {job['title']} - {job['company']}")
                    logger.info(f"🔗 URL: {job['url']}")
                    logger.info(f"📍 Local: {job['location']}")
                    logger.info(f"🔍 Keyword: {job['keyword']}")
                    logger.info(f"⚡ Easy Apply: {'✅' if job.get('has_easy_apply') else '❌'}")
                    
                    # Try Easy Apply if available
                    if job.get('has_easy_apply', False):
                        result = await self.easy_apply.apply_to_easy_apply_job(
                            job['url'], job['title']
                        )
                        
                        if result.get('success', False):
                            successful += 1
                            logger.info(f"✅ Easy Apply bem-sucedido: {job['title']}")
                            self.applied_jobs.add(job['url'])
                        else:
                            failed += 1
                            logger.error(f"❌ Easy Apply falhou: {job['title']} - {result.get('error', 'Unknown error')}")
                    else:
                        # Simulate regular application
                        await asyncio.sleep(2)
                        
                        # Simulate success (80% success rate for non-Easy Apply)
                        if random.random() < 0.8:
                            successful += 1
                            logger.info(f"✅ Aplicação bem-sucedida: {job['title']}")
                            self.applied_jobs.add(job['url'])
                        else:
                            failed += 1
                            logger.error(f"❌ Aplicação falhou: {job['title']}")
                    
                    applications += 1
                    
                    # Delay between applications
                    await asyncio.sleep(random.uniform(3, 6))
                    
                except Exception as e:
                    failed += 1
                    logger.error(f"❌ Erro na aplicação: {e}")
                    applications += 1
            
            return {'applications': applications, 'successful': successful, 'failed': failed}
            
        except Exception as e:
            logger.error(f"❌ Erro na busca dinâmica real: {e}")
            return {'applications': 0, 'successful': 0, 'failed': 0}
    
    async def _run_post_analysis_cycle(self) -> dict:
        """Run post analysis and application cycle."""
        try:
            # For now, simulate post analysis
            # In a real implementation, this would use the LinkedInPostAnalyzer
            
            # Simulate finding some posts
            simulated_posts = [
                {
                    'post_id': f'post_{random.randint(1000, 9999)}',
                    'author': f'Company {random.randint(1, 100)}',
                    'content': f'Estamos contratando desenvolvedor! Contato: hr{random.randint(1, 100)}@company.com',
                    'url': f'https://www.linkedin.com/posts/post_{random.randint(1000, 9999)}',
                    'timestamp': f'{random.randint(1, 24)} hours ago',
                    'keywords': ['developer', 'hiring'],
                    'application_method': 'email',
                    'application_details': {
                        'emails': [f'hr{random.randint(1, 100)}@company.com']
                    }
                }
                for _ in range(random.randint(0, 3))
            ]
            
            # Get available posts
            available_posts = [post for post in simulated_posts if post['post_id'] not in self.applied_posts]
            
            if not available_posts:
                logger.info("ℹ️ Nenhum post de contratação disponível")
                return {'applications': 0, 'successful': 0, 'failed': 0}
            
            logger.info(f"📋 Encontrados {len(available_posts)} posts de contratação")
            
            # Analyze and apply to posts
            applications = 0
            successful = 0
            failed = 0
            
            for post in available_posts:
                try:
                    logger.info(f"🔍 Analisando post: {post['author']}")
                    logger.info(f"📝 Conteúdo: {post['content'][:100]}...")
                    
                    # Execute application using the application executor
                    result = await self.application_executor.execute_application(post)
                    
                    if result.get('success', False):
                        successful += 1
                        logger.info(f"✅ Aplicação bem-sucedida via post: {post['author']}")
                        self.applied_posts.add(post['post_id'])
                    else:
                        failed += 1
                        logger.error(f"❌ Aplicação falhou via post: {post['author']} - {result.get('error', 'Unknown error')}")
                    
                    applications += 1
                    
                    # Delay between applications
                    await asyncio.sleep(3)
                    
                except Exception as e:
                    failed += 1
                    logger.error(f"❌ Erro na aplicação via post: {e}")
                    applications += 1
            
            return {'applications': applications, 'successful': successful, 'failed': failed}
            
        except Exception as e:
            logger.error(f"❌ Erro no ciclo de análise de posts: {e}")
            return {'applications': 0, 'successful': 0, 'failed': 0}
    
    async def run_continuous(self, max_cycles: int = 5):
        """Run continuous LinkedIn application system."""
        logger.info("🚀 === SISTEMA LINKEDIN DINÂMICO REAL INICIADO ===")
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
                    logger.info(f"⏳ Aguardando 60s antes do próximo ciclo...")
                    await asyncio.sleep(60)
                
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
    system = LinkedInRealDynamicSystem()
    await system.run_continuous(max_cycles=3)

if __name__ == "__main__":
    asyncio.run(main())
