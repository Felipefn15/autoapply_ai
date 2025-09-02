#!/usr/bin/env python3
"""
LinkedIn Unified System
Sistema unificado para Easy Apply e análise de posts
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

from app.automation.linkedin_easy_apply import LinkedInEasyApply
from app.automation.linkedin_post_analyzer import LinkedInPostAnalyzer
from app.automation.linkedin_application_executor import LinkedInApplicationExecutor
from app.main import load_config

class LinkedInUnifiedSystem:
    """Sistema unificado para LinkedIn."""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config = load_config(config_path)
        
        # Initialize components
        self.easy_apply = LinkedInEasyApply(self.config)
        self.post_analyzer = LinkedInPostAnalyzer(self.config)
        self.application_executor = LinkedInApplicationExecutor(self.config)
        
        # Statistics
        self.total_cycles = 0
        self.total_easy_apply = 0
        self.total_post_applications = 0
        self.total_successful = 0
        self.total_failed = 0
    
    async def run_cycle(self) -> dict:
        """Run a single cycle of LinkedIn applications."""
        cycle_start = datetime.now()
        logger.info(f"\n🔄 === CICLO LINKEDIN {self.total_cycles + 1} INICIADO ===")
        logger.info(f"⏰ Início: {cycle_start.strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # 1. Easy Apply Applications
            logger.info("🚀 1. Buscando e aplicando Easy Apply...")
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
            # Search for Easy Apply jobs
            keywords = ['react', 'python', 'javascript', 'frontend', 'backend', 'fullstack']
            jobs = await self.easy_apply.search_easy_apply_jobs(keywords)
            
            if not jobs:
                logger.info("ℹ️ Nenhuma vaga Easy Apply encontrada")
                return {'applications': 0, 'successful': 0, 'failed': 0}
            
            logger.info(f"📋 Encontradas {len(jobs)} vagas Easy Apply")
            
            # Apply to jobs
            applications = 0
            successful = 0
            failed = 0
            
            for job in jobs[:5]:  # Limit to 5 applications per cycle
                try:
                    logger.info(f"🚀 Aplicando Easy Apply: {job['title']} - {job['company']}")
                    
                    result = await self.easy_apply.apply_to_easy_apply_job(
                        job['url'], 
                        job['title']
                    )
                    
                    if result.get('success', False):
                        successful += 1
                        logger.info(f"✅ Easy Apply bem-sucedido: {result.get('message', 'Success')}")
                    else:
                        failed += 1
                        logger.error(f"❌ Easy Apply falhou: {result.get('error', 'Unknown error')}")
                    
                    applications += 1
                    
                    # Delay between applications
                    await asyncio.sleep(5)
                    
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
            # Search for hiring posts
            keywords = ['react', 'python', 'javascript', 'frontend', 'backend', 'fullstack']
            posts = await self.post_analyzer.search_hiring_posts(keywords)
            
            if not posts:
                logger.info("ℹ️ Nenhum post de contratação encontrado")
                return {'applications': 0, 'successful': 0, 'failed': 0}
            
            logger.info(f"📋 Encontrados {len(posts)} posts de contratação")
            
            # Analyze posts
            analysis_results = []
            for post in posts[:10]:  # Limit to 10 posts per cycle
                try:
                    analysis = await self.post_analyzer.analyze_post(post)
                    if not analysis.get('already_analyzed', False):
                        analysis_results.append(analysis)
                except Exception as e:
                    logger.error(f"❌ Erro na análise do post: {e}")
            
            if not analysis_results:
                logger.info("ℹ️ Nenhum post novo para analisar")
                return {'applications': 0, 'successful': 0, 'failed': 0}
            
            logger.info(f"🔍 Analisados {len(analysis_results)} posts")
            
            # Execute applications
            results = await self.application_executor.execute_multiple_applications(analysis_results)
            
            # Count results
            applications = len(results)
            successful = sum(1 for r in results if r.get('success', False))
            failed = applications - successful
            
            return {'applications': applications, 'successful': successful, 'failed': failed}
            
        except Exception as e:
            logger.error(f"❌ Erro no ciclo de análise de posts: {e}")
            return {'applications': 0, 'successful': 0, 'failed': 0}
    
    async def run_continuous(self, max_cycles: int = 10):
        """Run continuous LinkedIn application system."""
        logger.info("🚀 === SISTEMA LINKEDIN UNIFICADO INICIADO ===")
        logger.info(f"⏰ Início: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"🔄 Máximo de ciclos: {max_cycles}")
        
        try:
            while self.total_cycles < max_cycles:
                # Run single cycle
                cycle_result = await self.run_cycle()
                
                # Update totals
                self.total_cycles += 1
                self.total_easy_apply += cycle_result['easy_apply']['applications']
                self.total_post_applications += cycle_result['post_applications']['applications']
                self.total_successful += cycle_result['total_successful']
                self.total_failed += cycle_result['total_failed']
                
                # Print overall statistics
                logger.info(f"\n🏆 === ESTATÍSTICAS GERAIS ===")
                logger.info(f"🔄 Total de ciclos: {self.total_cycles}/{max_cycles}")
                logger.info(f"🚀 Total Easy Apply: {self.total_easy_apply}")
                logger.info(f"📝 Total Posts: {self.total_post_applications}")
                logger.info(f"📊 Total de aplicações: {self.total_successful + self.total_failed}")
                logger.info(f"✅ Total bem-sucedidas: {self.total_successful}")
                logger.info(f"❌ Total falharam: {self.total_failed}")
                
                if (self.total_successful + self.total_failed) > 0:
                    overall_success_rate = (self.total_successful / (self.total_successful + self.total_failed)) * 100
                    logger.info(f"📈 Taxa de sucesso geral: {overall_success_rate:.1f}%")
                
                # If no applications in this cycle, break
                if cycle_result['total_applications'] == 0:
                    logger.info("🎉 Nenhuma nova aplicação encontrada! Sistema finalizado.")
                    break
                
                # Wait before next cycle
                logger.info(f"⏳ Aguardando 60s antes do próximo ciclo...")
                await asyncio.sleep(60)
                
        except KeyboardInterrupt:
            logger.info("\n🛑 Sistema interrompido pelo usuário")
        except Exception as e:
            logger.error(f"❌ Erro crítico no sistema: {str(e)}")
        finally:
            logger.info("\n🏁 === SISTEMA FINALIZADO ===")
            logger.info(f"📊 Estatísticas finais:")
            logger.info(f"   🔄 Total de ciclos: {self.total_cycles}")
            logger.info(f"   🚀 Total Easy Apply: {self.total_easy_apply}")
            logger.info(f"   📝 Total Posts: {self.total_post_applications}")
            logger.info(f"   📊 Total de aplicações: {self.total_successful + self.total_failed}")
            logger.info(f"   ✅ Total bem-sucedidas: {self.total_successful}")
            logger.info(f"   ❌ Total falharam: {self.total_failed}")
            
            if (self.total_successful + self.total_failed) > 0:
                overall_success_rate = (self.total_successful / (self.total_successful + self.total_failed)) * 100
                logger.info(f"   📈 Taxa de sucesso geral: {overall_success_rate:.1f}%")

async def main():
    """Main function."""
    system = LinkedInUnifiedSystem()
    await system.run_continuous(max_cycles=5)  # Run 5 cycles for testing

if __name__ == "__main__":
    asyncio.run(main())
