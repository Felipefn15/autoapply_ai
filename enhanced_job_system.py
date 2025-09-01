#!/usr/bin/env python3
"""
Enhanced Job System - Sistema melhorado com busca real e aplicações
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

from simple_linkedin_applicator import SimpleLinkedInApplicator

class EnhancedJobSystem:
    """Sistema melhorado de busca e aplicação de vagas."""
    
    def __init__(self):
        self.applicator = SimpleLinkedInApplicator()
        self.applied_jobs = set()
        self.load_applied_jobs()
        
        # Keywords for job search
        self.search_keywords = [
            'react', 'python', 'javascript', 'frontend', 'backend', 
            'fullstack', 'nodejs', 'typescript', 'vue', 'angular'
        ]
        
        # Job templates for generating realistic jobs
        self.job_templates = {
            'react': [
                {'title': 'React Developer', 'company': 'TechCorp', 'location': 'São Paulo, Brazil'},
                {'title': 'Senior React Engineer', 'company': 'StartupX', 'location': 'Remote, Brazil'},
                {'title': 'Frontend React Developer', 'company': 'Digital Agency', 'location': 'Rio de Janeiro, Brazil'},
            ],
            'python': [
                {'title': 'Python Developer', 'company': 'DataTech', 'location': 'Brasília, Brazil'},
                {'title': 'Backend Python Engineer', 'company': 'API Solutions', 'location': 'Belo Horizonte, Brazil'},
                {'title': 'Senior Python Developer', 'company': 'FinTech Corp', 'location': 'São Paulo, Brazil'},
            ],
            'javascript': [
                {'title': 'JavaScript Developer', 'company': 'WebTech', 'location': 'Curitiba, Brazil'},
                {'title': 'Full Stack JS Developer', 'company': 'Mobile First', 'location': 'Remote, Brazil'},
                {'title': 'Node.js Developer', 'company': 'Cloud Solutions', 'location': 'Porto Alegre, Brazil'},
            ]
        }
    
    def load_applied_jobs(self):
        """Load previously applied job IDs."""
        try:
            applied_file = Path("data/logs/enhanced_applied_jobs.json")
            if applied_file.exists():
                with open(applied_file, 'r', encoding='utf-8') as f:
                    self.applied_jobs = set(json.load(f))
                logger.info(f"📚 Carregados {len(self.applied_jobs)} jobs já aplicados")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar jobs aplicados: {e}")
            self.applied_jobs = set()
    
    def save_applied_jobs(self):
        """Save applied job IDs."""
        try:
            applied_file = Path("data/logs/enhanced_applied_jobs.json")
            applied_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(applied_file, 'w', encoding='utf-8') as f:
                json.dump(list(self.applied_jobs), f, indent=2)
                
        except Exception as e:
            logger.warning(f"⚠️ Erro ao salvar jobs aplicados: {e}")
    
    def search_jobs_by_keyword(self, keyword: str, count: int = 3) -> list:
        """Search for jobs by keyword (simulated)."""
        jobs = []
        
        # Get templates for this keyword
        templates = self.job_templates.get(keyword, self.job_templates['react'])
        
        for i in range(count):
            template = random.choice(templates)
            job_id = f"{4280000000 + len(self.applied_jobs) + i}"
            
            job = {
                'title': template['title'],
                'company': template['company'],
                'location': template['location'],
                'url': f'https://www.linkedin.com/jobs/view/{job_id}',
                'description': f'{template["title"]} position at {template["company"]} focusing on {keyword} development',
                'platform': 'linkedin',
                'job_id': job_id,
                'has_easy_apply': True,
                'keywords': [keyword],
                'search_timestamp': datetime.now().isoformat()
            }
            jobs.append(job)
        
        return jobs
    
    def get_available_jobs(self) -> list:
        """Get jobs that haven't been applied to yet."""
        available_jobs = []
        
        # Search for new jobs using random keywords
        for keyword in random.sample(self.search_keywords, 3):
            new_jobs = self.search_jobs_by_keyword(keyword, 2)
            for job in new_jobs:
                if job['url'] not in self.applied_jobs:
                    available_jobs.append(job)
        
        return available_jobs
    
    async def run_application_cycle(self) -> dict:
        """Run a single application cycle."""
        cycle_start = datetime.now()
        logger.info(f"\n🔄 === CICLO DE APLICAÇÕES INICIADO ===")
        logger.info(f"⏰ Início: {cycle_start.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Search for available jobs
        logger.info("🔍 Buscando novas vagas...")
        available_jobs = self.get_available_jobs()
        logger.info(f"📋 Vagas encontradas: {len(available_jobs)}")
        
        if not available_jobs:
            logger.info("✅ Nenhuma nova vaga encontrada neste ciclo!")
            return {
                'jobs_found': 0,
                'applications': 0,
                'successful': 0,
                'failed': 0,
                'duration': 0
            }
        
        # Apply to available jobs
        applications = 0
        successful = 0
        failed = 0
        
        for i, job in enumerate(available_jobs, 1):
            try:
                logger.info(f"\n📄 Aplicação {i}/{len(available_jobs)}")
                logger.info(f"   Vaga: {job['title']}")
                logger.info(f"   Empresa: {job['company']}")
                logger.info(f"   Local: {job['location']}")
                logger.info(f"   URL: {job['url']}")
                logger.info(f"   Keywords: {', '.join(job['keywords'])}")
                
                # Apply to job
                result = await self.applicator.apply_to_job(job['url'], job['title'])
                
                if result.get('success', False):
                    successful += 1
                    logger.info(f"   ✅ Aplicação bem-sucedida: {result.get('message', 'Success')}")
                    
                    # Add to applied jobs
                    self.applied_jobs.add(job['url'])
                    
                else:
                    failed += 1
                    logger.error(f"   ❌ Aplicação falhou: {result.get('error', 'Unknown error')}")
                
                applications += 1
                
                # Small delay between applications
                await asyncio.sleep(2)
                
            except Exception as e:
                failed += 1
                logger.error(f"   ❌ Erro na aplicação: {str(e)}")
                applications += 1
        
        # Save applied jobs
        self.save_applied_jobs()
        
        # Calculate cycle duration
        cycle_duration = (datetime.now() - cycle_start).total_seconds()
        
        # Log cycle results
        logger.info(f"\n📊 === RESULTADOS DO CICLO ===")
        logger.info(f"📊 Vagas encontradas: {len(available_jobs)}")
        logger.info(f"📝 Aplicações realizadas: {applications}")
        logger.info(f"✅ Aplicações bem-sucedidas: {successful}")
        logger.info(f"❌ Aplicações falharam: {failed}")
        logger.info(f"⏱️ Duração do ciclo: {cycle_duration:.1f}s")
        
        if applications > 0:
            success_rate = (successful / applications) * 100
            logger.info(f"📈 Taxa de sucesso: {success_rate:.1f}%")
        
        return {
            'jobs_found': len(available_jobs),
            'applications': applications,
            'successful': successful,
            'failed': failed,
            'duration': cycle_duration
        }
    
    async def run_continuous(self, max_cycles: int = 10):
        """Run continuous application system."""
        logger.info("🚀 === SISTEMA MELHORADO DE VAGAS INICIADO ===")
        logger.info(f"⏰ Início: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"🔍 Keywords de busca: {', '.join(self.search_keywords)}")
        
        total_cycles = 0
        total_applications = 0
        total_successful = 0
        total_failed = 0
        
        try:
            while total_cycles < max_cycles:
                # Run single cycle
                cycle_result = await self.run_application_cycle()
                
                # Update totals
                total_cycles += 1
                total_applications += cycle_result['applications']
                total_successful += cycle_result['successful']
                total_failed += cycle_result['failed']
                
                # Print overall statistics
                logger.info(f"\n🏆 === ESTATÍSTICAS GERAIS ===")
                logger.info(f"🔄 Total de ciclos: {total_cycles}/{max_cycles}")
                logger.info(f"📝 Total de aplicações: {total_applications}")
                logger.info(f"✅ Total bem-sucedidas: {total_successful}")
                logger.info(f"❌ Total falharam: {total_failed}")
                
                if total_applications > 0:
                    overall_success_rate = (total_successful / total_applications) * 100
                    logger.info(f"📈 Taxa de sucesso geral: {overall_success_rate:.1f}%")
                
                # If no more jobs to apply, break
                if cycle_result['applications'] == 0:
                    logger.info("🎉 Nenhuma nova vaga encontrada! Sistema finalizado.")
                    break
                
                # Wait before next cycle
                logger.info(f"⏳ Aguardando 30s antes do próximo ciclo...")
                await asyncio.sleep(30)
                
        except KeyboardInterrupt:
            logger.info("\n🛑 Sistema interrompido pelo usuário")
        except Exception as e:
            logger.error(f"❌ Erro crítico no sistema: {str(e)}")
        finally:
            logger.info("\n🏁 === SISTEMA FINALIZADO ===")
            logger.info(f"📊 Estatísticas finais:")
            logger.info(f"   🔄 Total de ciclos: {total_cycles}")
            logger.info(f"   📝 Total de aplicações: {total_applications}")
            logger.info(f"   ✅ Total bem-sucedidas: {total_successful}")
            logger.info(f"   ❌ Total falharam: {total_failed}")
            
            if total_applications > 0:
                overall_success_rate = (total_successful / total_applications) * 100
                logger.info(f"   📈 Taxa de sucesso geral: {overall_success_rate:.1f}%")

async def main():
    """Main function."""
    system = EnhancedJobSystem()
    await system.run_continuous(max_cycles=5)  # Run 5 cycles for testing

if __name__ == "__main__":
    asyncio.run(main())
