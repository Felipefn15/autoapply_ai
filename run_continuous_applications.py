#!/usr/bin/env python3
"""
Sistema de Aplicações Contínuas - Loop Infinito
Aplica para vagas continuamente até não haver mais resultados
"""

import asyncio
import logging
import time
from datetime import datetime
from pathlib import Path
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/continuous_applications.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import after setting up logging
from app.job_search.searcher import JobSearcher
from app.matching.matcher import JobMatcher
from app.automation.application_logger import ApplicationLogger, ApplicationStatus
from app.automation.direct_applicator import DirectApplicator
from app.automation.real_linkedin_applicator import RealLinkedInApplicator
from app.automation.real_linkedin_searcher import RealLinkedInSearcher
from simple_linkedin_applicator import SimpleLinkedInApplicator
from app.main import load_config

class ContinuousApplicationSystem:
    """Sistema de aplicações contínuas em loop infinito."""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config = load_config(config_path)
        self.searcher = JobSearcher(self.config)
        self.matcher = JobMatcher(self.config)
        self.direct_applicator = DirectApplicator(self.config)
        self.real_linkedin_applicator = RealLinkedInApplicator(self.config)
        self.real_linkedin_searcher = RealLinkedInSearcher(self.config)
        self.simple_linkedin_applicator = SimpleLinkedInApplicator()
        self.app_logger = ApplicationLogger()
        
        # Statistics
        self.total_cycles = 0
        self.total_applications = 0
        self.total_successful = 0
        self.total_failed = 0
        self.start_time = datetime.now()
        
        # Rate limiting
        self.min_cycle_interval = 300  # 5 minutes between cycles
        self.max_applications_per_cycle = 50
        
        # Duplicate detection
        self.applied_job_ids = set()
        self.load_applied_jobs()
    
    def load_applied_jobs(self):
        """Load previously applied job IDs to avoid duplicates."""
        try:
            history_file = Path("data/logs/application_history.json")
            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                    # Handle both list and dict formats
                    if isinstance(history, list):
                        self.applied_job_ids = set([job.get('job_id', '') for job in history if isinstance(job, dict) and job.get('job_id')])
                    elif isinstance(history, dict):
                        # If it's a dict, try to extract job IDs from values
                        self.applied_job_ids = set()
                        for key, value in history.items():
                            if isinstance(value, dict) and 'job_id' in value:
                                self.applied_job_ids.add(value['job_id'])
                logger.info(f"📚 Carregados {len(self.applied_job_ids)} jobs já aplicados")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar histórico: {e}")
            self.applied_job_ids = set()
    
    def is_job_already_applied(self, job_data: dict) -> bool:
        """Check if job was already applied to."""
        job_id = self._generate_job_id(job_data)
        return job_id in self.applied_job_ids
    
    def _generate_job_id(self, job_data: dict) -> str:
        """Generate unique job ID."""
        return f"{job_data.get('platform', 'unknown')}_{job_data.get('url', '')}_{job_data.get('title', '')}"
    
    async def run_single_cycle(self) -> dict:
        """Run a single application cycle."""
        cycle_start = datetime.now()
        logger.info(f"\n🔄 === CICLO {self.total_cycles + 1} INICIADO ===")
        logger.info(f"⏰ Início: {cycle_start.strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # 1. Search for real LinkedIn jobs
            logger.info("🔍 1. Buscando vagas REAIS no LinkedIn...")
            linkedin_jobs = await self.real_linkedin_searcher.search_linkedin_jobs()
            logger.info(f"📊 Total de vagas LinkedIn encontradas: {len(linkedin_jobs)}")
            
            # Also search other platforms
            logger.info("🔍 2. Buscando vagas em outras plataformas...")
            other_jobs = await self.searcher.search()
            logger.info(f"📊 Total de vagas outras plataformas: {len(other_jobs)}")
            
            # Combine all jobs
            all_jobs = linkedin_jobs + other_jobs
            logger.info(f"📊 Total de vagas encontradas: {len(all_jobs)}")
            
            if not all_jobs:
                logger.warning("⚠️ Nenhuma vaga encontrada neste ciclo")
                return {
                    'jobs_found': 0,
                    'applications': 0,
                    'successful': 0,
                    'failed': 0,
                    'duration': 0
                }
            
            # 3. Match jobs
            logger.info("🎯 3. Fazendo matching...")
            matches = self.matcher.match_jobs(all_jobs)
            logger.info(f"🎯 Vagas com match: {len(matches)}")
            
            # 4. Filter out already applied jobs
            new_matches = []
            for match in matches:
                if isinstance(match, dict):
                    if not self.is_job_already_applied(match):
                        new_matches.append(match)
                    else:
                        logger.debug(f"⏭️ Job já aplicado: {match.get('title', 'Unknown')}")
            
            logger.info(f"🆕 Novas vagas para aplicar: {len(new_matches)}")
            
            if not new_matches:
                logger.info("✅ Todas as vagas já foram aplicadas")
                return {
                    'jobs_found': len(all_jobs),
                    'applications': 0,
                    'successful': 0,
                    'failed': 0,
                    'duration': 0
                }
            
            # 5. Apply to jobs
            logger.info("📝 5. Aplicando para vagas...")
            applications = 0
            successful = 0
            failed = 0
            
            # Limit applications per cycle
            jobs_to_apply = new_matches[:self.max_applications_per_cycle]
            logger.info(f"🎯 Aplicando para {len(jobs_to_apply)} vagas (limite: {self.max_applications_per_cycle})")
            
            for i, match in enumerate(jobs_to_apply, 1):
                try:
                    logger.info(f"\n📄 Aplicação {i}/{len(jobs_to_apply)}")
                    logger.info(f"   Vaga: {match.get('title', 'Unknown')}")
                    logger.info(f"   Empresa: {match.get('company', 'Unknown')}")
                    logger.info(f"   Score: {match.get('match_score', 0):.1f}%")
                    logger.info(f"   URL: {match.get('url', 'N/A')}")
                    logger.info(f"   Plataforma: {match.get('platform', 'Unknown')}")
                    
                    # Create JobPosting object
                    from app.job_search.models import JobPosting
                    job_posting = JobPosting(
                        title=match.get('title', 'Unknown'),
                        description=match.get('description', ''),
                        url=match.get('url', ''),
                        email=match.get('email')
                    )
                    
                    # Apply to job
                    logger.info("   🚀 Aplicando diretamente...")
                    
                    # Use simple LinkedIn applicator for LinkedIn jobs
                    if match.get('platform', '').lower() == 'linkedin':
                        result = await self.simple_linkedin_applicator.apply_to_job(
                            match.get('url', ''),
                            match.get('title', 'Unknown')
                        )
                    else:
                        result = await self.direct_applicator.apply_to_job(job_posting)
                    
                    if result.get('success', False):
                        successful += 1
                        logger.info(f"   ✅ Aplicação bem-sucedida: {result.get('message', 'Success')}")
                        
                        # Log successful application
                        self.app_logger.log_job_application(
                            job_title=match.get('title', 'Unknown'),
                            company=match.get('company', 'Unknown'),
                            url=match.get('url', ''),
                            status=ApplicationStatus.APPLIED,
                            match_score=match.get('match_score', 0),
                            platform=match.get('platform', 'Unknown')
                        )
                        
                        # Add to applied jobs
                        job_id = self._generate_job_id(match)
                        self.applied_job_ids.add(job_id)
                        
                    else:
                        failed += 1
                        logger.error(f"   ❌ Aplicação falhou: {result.get('error', 'Unknown error')}")
                        
                        # Log failed application
                        self.app_logger.log_job_application(
                            job_title=match.get('title', 'Unknown'),
                            company=match.get('company', 'Unknown'),
                            url=match.get('url', ''),
                            status=ApplicationStatus.FAILED,
                            match_score=match.get('match_score', 0),
                            platform=match.get('platform', 'Unknown')
                        )
                    
                    applications += 1
                    
                    # Small delay between applications
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    failed += 1
                    logger.error(f"   ❌ Erro na aplicação: {str(e)}")
                    applications += 1
            
            # 5. Save applied jobs
            self.save_applied_jobs()
            
            # 6. Calculate cycle duration
            cycle_duration = (datetime.now() - cycle_start).total_seconds()
            
            # 7. Update statistics
            self.total_cycles += 1
            self.total_applications += applications
            self.total_successful += successful
            self.total_failed += failed
            
            # 8. Log cycle results
            logger.info(f"\n📊 === RESULTADOS DO CICLO {self.total_cycles} ===")
            logger.info(f"📊 Vagas encontradas: {len(all_jobs)}")
            logger.info(f"🎯 Vagas com match: {len(matches)}")
            logger.info(f"🆕 Novas vagas: {len(new_matches)}")
            logger.info(f"📝 Aplicações realizadas: {applications}")
            logger.info(f"✅ Aplicações bem-sucedidas: {successful}")
            logger.info(f"❌ Aplicações falharam: {failed}")
            logger.info(f"⏱️ Duração do ciclo: {cycle_duration:.1f}s")
            
            if applications > 0:
                success_rate = (successful / applications) * 100
                logger.info(f"📈 Taxa de sucesso: {success_rate:.1f}%")
            
            return {
                'jobs_found': len(all_jobs),
                'applications': applications,
                'successful': successful,
                'failed': failed,
                'duration': cycle_duration
            }
            
        except Exception as e:
            logger.error(f"❌ Erro no ciclo {self.total_cycles + 1}: {str(e)}")
            return {
                'jobs_found': 0,
                'applications': 0,
                'successful': 0,
                'failed': 0,
                'duration': 0
            }
    
    def save_applied_jobs(self):
        """Save applied job IDs to file."""
        try:
            applied_file = Path("data/logs/applied_jobs.json")
            applied_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(applied_file, 'w', encoding='utf-8') as f:
                json.dump(list(self.applied_job_ids), f, indent=2)
                
        except Exception as e:
            logger.warning(f"⚠️ Erro ao salvar jobs aplicados: {e}")
    
    def print_overall_statistics(self):
        """Print overall statistics."""
        total_time = (datetime.now() - self.start_time).total_seconds()
        hours = total_time // 3600
        minutes = (total_time % 3600) // 60
        
        logger.info(f"\n🏆 === ESTATÍSTICAS GERAIS ===")
        logger.info(f"🔄 Total de ciclos: {self.total_cycles}")
        logger.info(f"📝 Total de aplicações: {self.total_applications}")
        logger.info(f"✅ Total bem-sucedidas: {self.total_successful}")
        logger.info(f"❌ Total falharam: {self.total_failed}")
        logger.info(f"⏱️ Tempo total: {hours:.0f}h {minutes:.0f}m")
        
        if self.total_applications > 0:
            overall_success_rate = (self.total_successful / self.total_applications) * 100
            logger.info(f"📈 Taxa de sucesso geral: {overall_success_rate:.1f}%")
        
        if self.total_cycles > 0:
            avg_applications_per_cycle = self.total_applications / self.total_cycles
            logger.info(f"📊 Média de aplicações por ciclo: {avg_applications_per_cycle:.1f}")
    
    async def run_continuous(self):
        """Run continuous application system."""
        logger.info("🚀 === SISTEMA DE APLICAÇÕES CONTÍNUAS INICIADO ===")
        logger.info(f"⏰ Início: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"🔄 Intervalo entre ciclos: {self.min_cycle_interval}s")
        logger.info(f"📝 Máximo de aplicações por ciclo: {self.max_applications_per_cycle}")
        
        consecutive_empty_cycles = 0
        max_empty_cycles = 3  # Stop after 3 consecutive empty cycles
        
        try:
            while True:
                # Run single cycle
                cycle_result = await self.run_single_cycle()
                
                # Check if cycle had no new applications
                if cycle_result['applications'] == 0:
                    consecutive_empty_cycles += 1
                    logger.info(f"⚠️ Ciclo vazio {consecutive_empty_cycles}/{max_empty_cycles}")
                    
                    if consecutive_empty_cycles >= max_empty_cycles:
                        logger.info(f"🛑 {max_empty_cycles} ciclos vazios consecutivos. Parando sistema.")
                        break
                else:
                    consecutive_empty_cycles = 0
                
                # Print overall statistics
                self.print_overall_statistics()
                
                # Wait before next cycle
                logger.info(f"⏳ Aguardando {self.min_cycle_interval}s antes do próximo ciclo...")
                await asyncio.sleep(self.min_cycle_interval)
                
        except KeyboardInterrupt:
            logger.info("\n🛑 Sistema interrompido pelo usuário")
        except Exception as e:
            logger.error(f"❌ Erro crítico no sistema: {str(e)}")
        finally:
            logger.info("\n🏁 === SISTEMA FINALIZADO ===")
            self.print_overall_statistics()
            
            # Save final statistics
            self.save_applied_jobs()
            logger.info("💾 Dados salvos com sucesso")

async def main():
    """Main function."""
    system = ContinuousApplicationSystem()
    await system.run_continuous()

if __name__ == "__main__":
    asyncio.run(main())
