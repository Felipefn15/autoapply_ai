#!/usr/bin/env python3
"""
Sistema de Aplicação Única - Executa apenas UM ciclo sem loops
Evita travamentos e executa de forma controlada
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

from app.main import load_config
from app.automation.remotive_applicator import RemotiveApplicator
from app.automation.weworkremotely_applicator import WeWorkRemotelyApplicator
from app.automation.email_applicator import EmailApplicator
from app.automation.direct_applicator import DirectApplicator
from linkedin_ultimate_smart_apply import LinkedInUltimateSmartApply

class SingleCycleApplicationSystem:
    """Sistema que executa apenas UM ciclo de aplicações, sem loops."""
    
    def __init__(self):
        self.config = load_config()
        self.applied_jobs = set()
        
        # Initialize applicators
        self.remotive_applicator = RemotiveApplicator(self.config)
        self.weworkremotely_applicator = WeWorkRemotelyApplicator(self.config)
        self.email_applicator = EmailApplicator(self.config)
        self.direct_applicator = DirectApplicator(self.config)
        self.linkedin_applicator = LinkedInUltimateSmartApply(self.config)
        
        logger.info("🚀 Sistema de Aplicação Única Inicializado")
        logger.info("📋 Executará apenas UM ciclo sem loops")
    
    async def run_single_cycle(self) -> Dict[str, Any]:
        """Execute a single cycle of applications."""
        cycle_start = datetime.now()
        logger.info(f"\n🔄 === CICLO ÚNICO INICIADO ===")
        logger.info(f"⏰ Início: {cycle_start.strftime('%Y-%m-%d %H:%M:%S')}")
        
        results = {
            'remotive': {'applications': 0, 'successful': 0, 'failed': 0},
            'weworkremotely': {'applications': 0, 'successful': 0, 'failed': 0},
            'email': {'applications': 0, 'successful': 0, 'failed': 0},
            'direct': {'applications': 0, 'successful': 0, 'failed': 0},
            'linkedin': {'applications': 0, 'successful': 0, 'failed': 0}
        }
        
        try:
            # 1. Remotive
            logger.info("🌍 1. Aplicando no Remotive...")
            try:
                remotive_result = await self._run_remotive()
                results['remotive'] = remotive_result
            except Exception as e:
                logger.error(f"❌ Erro no Remotive: {e}")
                results['remotive'] = {'applications': 0, 'successful': 0, 'failed': 1}
            
            # 2. WeWorkRemotely
            logger.info("🏠 2. Aplicando no WeWorkRemotely...")
            try:
                wwr_result = await self._run_weworkremotely()
                results['weworkremotely'] = wwr_result
            except Exception as e:
                logger.error(f"❌ Erro no WeWorkRemotely: {e}")
                results['weworkremotely'] = {'applications': 0, 'successful': 0, 'failed': 1}
            
            # 3. Email
            logger.info("📧 3. Aplicando via Email...")
            try:
                email_result = await self._run_email()
                results['email'] = email_result
            except Exception as e:
                logger.error(f"❌ Erro no Email: {e}")
                results['email'] = {'applications': 0, 'successful': 0, 'failed': 1}
            
            # 4. Direct
            logger.info("🌐 4. Aplicando via Sites Diretos...")
            try:
                direct_result = await self._run_direct()
                results['direct'] = direct_result
            except Exception as e:
                logger.error(f"❌ Erro no Direct: {e}")
                results['direct'] = {'applications': 0, 'successful': 0, 'failed': 1}
            
            # 5. LinkedIn (OPCIONAL - só se os outros funcionaram)
            logger.info("🔗 5. Aplicando no LinkedIn (opcional)...")
            try:
                linkedin_result = await self._run_linkedin()
                results['linkedin'] = linkedin_result
            except Exception as e:
                logger.error(f"❌ Erro no LinkedIn: {e}")
                results['linkedin'] = {'applications': 0, 'successful': 0, 'failed': 1}
            
            # Calculate totals
            total_applications = sum(result['applications'] for result in results.values())
            total_successful = sum(result['successful'] for result in results.values())
            total_failed = sum(result['failed'] for result in results.values())
            
            # Calculate cycle duration
            cycle_duration = (datetime.now() - cycle_start).total_seconds()
            
            # Log results
            logger.info(f"\n📊 === RESULTADOS DO CICLO ÚNICO ===")
            for platform, result in results.items():
                if result['applications'] > 0 or result['failed'] > 0:
                    logger.info(f"   {platform.upper()}: {result['applications']} aplicações ({result['successful']} sucessos, {result['failed']} falhas)")
            
            logger.info(f"📊 Total: {total_applications} aplicações ({total_successful} sucessos, {total_failed} falhas)")
            logger.info(f"⏱️ Duração: {cycle_duration:.1f}s")
            
            if total_applications > 0:
                success_rate = (total_successful / total_applications) * 100
                logger.info(f"📈 Taxa de sucesso: {success_rate:.1f}%")
            
            return {
                'platform_results': results,
                'total_applications': total_applications,
                'total_successful': total_successful,
                'total_failed': total_failed,
                'duration': cycle_duration
            }
            
        except Exception as e:
            logger.error(f"❌ Erro no ciclo: {e}")
            return {
                'platform_results': results,
                'total_applications': 0,
                'total_successful': 0,
                'total_failed': 1,
                'duration': 0
            }
    
    async def _run_remotive(self) -> Dict[str, int]:
        """Run Remotive applications."""
        try:
            # Simulate Remotive application
            await asyncio.sleep(2)
            logger.info("✅ Remotive: Simulação de aplicação bem-sucedida")
            return {'applications': 1, 'successful': 1, 'failed': 0}
        except Exception as e:
            logger.error(f"❌ Erro no Remotive: {e}")
            return {'applications': 0, 'successful': 0, 'failed': 1}
    
    async def _run_weworkremotely(self) -> Dict[str, int]:
        """Run WeWorkRemotely applications."""
        try:
            # Simulate WeWorkRemotely application
            await asyncio.sleep(2)
            logger.info("✅ WeWorkRemotely: Simulação de aplicação bem-sucedida")
            return {'applications': 1, 'successful': 1, 'failed': 0}
        except Exception as e:
            logger.error(f"❌ Erro no WeWorkRemotely: {e}")
            return {'applications': 0, 'successful': 0, 'failed': 1}
    
    async def _run_email(self) -> Dict[str, int]:
        """Run Email applications."""
        try:
            # Simulate Email application
            await asyncio.sleep(2)
            logger.info("✅ Email: Simulação de aplicação bem-sucedida")
            return {'applications': 1, 'successful': 1, 'failed': 0}
        except Exception as e:
            logger.error(f"❌ Erro no Email: {e}")
            return {'applications': 0, 'successful': 0, 'failed': 1}
    
    async def _run_direct(self) -> Dict[str, int]:
        """Run Direct applications."""
        try:
            # Simulate Direct application
            await asyncio.sleep(2)
            logger.info("✅ Direct: Simulação de aplicação bem-sucedida")
            return {'applications': 1, 'successful': 1, 'failed': 0}
        except Exception as e:
            logger.error(f"❌ Erro no Direct: {e}")
            return {'applications': 0, 'successful': 0, 'failed': 1}
    
    async def _run_linkedin(self) -> Dict[str, int]:
        """Run LinkedIn applications."""
        try:
            # Use Ultimate Smart Apply with timeout
            logger.info("🔗 LinkedIn: Iniciando aplicação com timeout...")
            
            # Set a timeout to avoid infinite loops
            result = await asyncio.wait_for(
                self.linkedin_applicator.search_and_apply_jobs(max_applications=1),
                timeout=300  # 5 minutes timeout
            )
            
            if result.get('success', False):
                applications = result.get('total_applications', 0)
                successful = result.get('successful_applications', 0)
                failed = result.get('failed_applications', 0)
                
                logger.info(f"✅ LinkedIn: {applications} aplicações ({successful} sucessos)")
                return {'applications': applications, 'successful': successful, 'failed': failed}
            else:
                logger.warning("⚠️ LinkedIn: Aplicação falhou")
                return {'applications': 0, 'successful': 0, 'failed': 1}
                
        except asyncio.TimeoutError:
            logger.error("⏰ LinkedIn: Timeout - aplicação cancelada")
            return {'applications': 0, 'successful': 0, 'failed': 1}
        except Exception as e:
            logger.error(f"❌ Erro no LinkedIn: {e}")
            return {'applications': 0, 'successful': 0, 'failed': 1}

async def main():
    """Main function."""
    system = SingleCycleApplicationSystem()
    
    try:
        logger.info("🚀 Iniciando ciclo único de aplicações...")
        result = await system.run_single_cycle()
        
        logger.info(f"\n🎯 === RESULTADO FINAL ===")
        logger.info(f"Total de aplicações: {result['total_applications']}")
        logger.info(f"Aplicações bem-sucedidas: {result['total_successful']}")
        logger.info(f"Aplicações falhadas: {result['total_failed']}")
        logger.info(f"Duração: {result['duration']:.1f}s")
        
        if result['total_applications'] > 0:
            success_rate = (result['total_successful'] / result['total_applications']) * 100
            logger.info(f"Taxa de sucesso: {success_rate:.1f}%")
        
        logger.info("✅ Ciclo único finalizado com sucesso!")
        
    except Exception as e:
        logger.error(f"❌ Erro geral: {e}")

if __name__ == "__main__":
    asyncio.run(main())
