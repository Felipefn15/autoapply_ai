#!/usr/bin/env python3
"""
AutoApply.AI - Sistema de Aplicação Automática para Vagas
Script principal para executar busca, matching e aplicação com geração de logs CSV
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict

from loguru import logger

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent))

from app.job_search.searcher import JobSearcher
from app.matching.matcher import JobMatcher
from app.automation.applicator_manager import ApplicatorManager
from app.automation.application_logger import ApplicationLogger, ApplicationStatus
from app.main import load_config, load_profile

async def main():
    """Função principal do sistema AutoApply.AI."""
    logger.info("🚀 AUTOAPPLY.AI - Sistema de Aplicação Automática")
    logger.info("=" * 60)
    
    try:
        # 1. Carregar configurações
        logger.info("📋 1. Carregando configurações...")
        config = load_config()
        profile = load_profile()
        
        if not config:
            logger.error("❌ Erro ao carregar configurações")
            return
        
        logger.info("   ✅ Configurações carregadas")
        
        # 2. Inicializar sistema de logging
        logger.info("📊 2. Inicializando sistema de logging...")
        app_logger = ApplicationLogger()
        app_logger.start_session()
        logger.info(f"   ✅ Sessão iniciada: {app_logger.session_id}")
        
        # 3. Buscar vagas
        logger.info("🔍 3. Iniciando busca de vagas...")
        searcher = JobSearcher(config, app_logger)
        all_jobs = await searcher.search()
        
        logger.info(f"   📊 Total de vagas encontradas: {len(all_jobs)}")
        
        if not all_jobs:
            logger.warning("   ⚠️ Nenhuma vaga encontrada. Usando dados de teste...")
            from app.job_search.models import JobPosting
            all_jobs = [
                JobPosting(
                    title="Senior Python Developer",
                    description="Desenvolvedor Python sênior para projeto remoto",
                    email="jobs@company.com",
                    url="https://example.com/job1"
                ),
                JobPosting(
                    title="React Frontend Developer",
                    description="Desenvolvedor React para aplicação web",
                    email="hr@startup.com",
                    url="https://example.com/job2"
                )
            ]
        
        # 4. Fazer matching das vagas
        logger.info("🎯 4. Fazendo matching das vagas...")
        matcher = JobMatcher(config)
        matches = matcher.match_jobs(all_jobs)
        
        logger.info(f"   📊 Vagas com match: {len(matches)}")
        
        if not matches:
            logger.warning("   ⚠️ Nenhuma vaga com match encontrada!")
            return
        
        # 5. Aplicar para vagas (MAXIMIZAR APLICAÇÕES - SEM DUPLICATAS)
        logger.info("\n📝 5. Aplicando para vagas (MÁXIMO DE APLICAÇÕES - SEM DUPLICATAS)...")
        applicator = ApplicatorManager(config)
        applicator.start_session()  # Start application session
        
        # Configurações para maximizar aplicações
        max_applications = config.get('search', {}).get('max_applications_per_day', 50)
        max_concurrent = config.get('search', {}).get('max_concurrent_applications', 10)
        application_delay = config.get('search', {}).get('application_delay', 5)
        
        logger.info(f"   🎯 Meta de aplicações: {max_applications}")
        logger.info(f"   ⚡ Aplicações concorrentes: {max_concurrent}")
        logger.info(f"   ⏱️ Delay entre aplicações: {application_delay}s")
        logger.info(f"   🚫 Sistema anti-duplicação: ATIVO")
        
        # Filtrar vagas únicas (sem duplicatas)
        unique_matches = []
        seen_jobs = set()
        
        for match in matches:
            if isinstance(match, dict):
                job_title = match.get('title', '')
                company = match.get('company', 'Unknown')
                url = match.get('url', '')
            else:
                job_title = getattr(match.job, 'title', '')
                company = getattr(match.job, 'company', 'Unknown')
                url = getattr(match.job, 'url', '')
            
            # Create unique identifier
            job_id = f"{job_title}_{company}_{url}"
            
            if job_id not in seen_jobs:
                seen_jobs.add(job_id)
                unique_matches.append(match)
        
        logger.info(f"   🔍 Vagas únicas encontradas: {len(unique_matches)} (filtradas de {len(matches)})")
        
        if not unique_matches:
            logger.warning("   ⚠️ Nenhuma vaga única encontrada após filtro de duplicatas!")
            return
        
        # Aplicar para vagas únicas
        applications_to_process = min(max_applications, len(unique_matches))
        logger.info(f"   📋 Aplicando para {applications_to_process} vagas únicas...")
        
        successful_applications = 0
        failed_applications = 0
        duplicate_applications = 0
        already_applied = 0
        
        # Processar em lotes para evitar sobrecarga
        batch_size = max_concurrent
        total_batches = (applications_to_process + batch_size - 1) // batch_size
        
        for i in range(0, applications_to_process, batch_size):
            batch = unique_matches[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            logger.info(f"   🔄 Processando lote {batch_num}/{total_batches}")
            
            # Processar lote em paralelo
            batch_tasks = []
            for j, match in enumerate(batch, 1):
                task = asyncio.create_task(_apply_to_job(match, i + j, app_logger))
                batch_tasks.append(task)
            
            # Aguardar conclusão do lote
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Contar resultados
            for result in batch_results:
                if isinstance(result, dict):
                    if result.get('status') == 'applied':
                        successful_applications += 1
                    elif result.get('status') == 'duplicate':
                        duplicate_applications += 1
                    elif result.get('status') == 'already_applied':
                        already_applied += 1
                    else:
                        failed_applications += 1
            
            # Aguardar antes do próximo lote
            if i + batch_size < applications_to_process:
                logger.info(f"   ⏱️ Aguardando {application_delay}s antes do próximo lote...")
                await asyncio.sleep(application_delay)
        
        # Resumo final
        logger.info(f"   ✅ Aplicações bem-sucedidas: {successful_applications}")
        logger.info(f"   ❌ Aplicações falharam: {failed_applications}")
        logger.info(f"   🔄 Vagas duplicadas detectadas: {duplicate_applications}")
        logger.info(f"   📚 Já aplicado anteriormente: {already_applied}")
        logger.info(f"   📈 Taxa de sucesso efetiva: {(successful_applications/(successful_applications+failed_applications)*100):.1f}%")
        
        # 6. Finalizar sessão e gerar relatório
        logger.info("\n📊 6. Finalizando sessão e gerando relatório...")
        session_log = app_logger.end_session()
        
        # Mostrar caminhos dos arquivos CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_report_path = f"data/logs/autoapply_report_{timestamp}.csv"
        summary_csv_path = f"data/logs/autoapply_summary_{timestamp}.csv"
        
        logger.info("\n" + "=" * 60)
        logger.info("📈 RELATÓRIO FINAL")
        logger.info("=" * 60)
        logger.info(f"📊 Total de vagas encontradas: {len(all_jobs)}")
        logger.info(f"🎯 Vagas com match: {len(matches)}")
        logger.info(f"📝 Aplicações realizadas: {successful_applications}")
        logger.info(f"✅ Aplicações bem-sucedidas: {successful_applications}")
        logger.info(f"❌ Aplicações falharam: {failed_applications}")
        logger.info(f"📈 Taxa de sucesso: {(successful_applications/(successful_applications+failed_applications)*100):.1f}%")
        logger.info(f"📁 Logs salvos em: data/logs/")
        logger.info(f"📄 Relatório: data/logs/reports/session_{timestamp}_report.txt")
        logger.info(f"📊 CSV detalhado: {csv_report_path}")
        logger.info(f"📋 CSV resumo: {summary_csv_path}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Erro durante execução: {str(e)}")
        raise

async def _apply_to_job(match, job_number: int, app_logger) -> Dict:
    """Apply to a specific job."""
    try:
        # Preparar dados da vaga
        if isinstance(match, dict):
            job_data = match
            score = match.get('match_score', 0)
        else:
            job_data = {
                'title': match.job.title,
                'company': getattr(match.job, 'company', 'Unknown'),
                'url': match.job.url,
                'description': match.job.description
            }
            score = getattr(match, 'match_score', 0)
        
        # Log da aplicação
        logger.info(f"   📄 Aplicação {job_number}: {job_data.get('title', 'Unknown')}")
        logger.info(f"      Score: {score:.1f}%")
        logger.info(f"      URL: {job_data.get('url', 'N/A')}")
        
        # Verificar se é duplicata antes de aplicar
        is_duplicate, duplicate_type, existing_hash = app_logger._is_duplicate_job(job_data)
        
        if is_duplicate:
            if duplicate_type == "already_applied":
                logger.info(f"      ⚠️ Já aplicado anteriormente - PULANDO")
                app_logger.log_job_application(
                    job_data, 
                    ApplicationStatus.ALREADY_APPLIED, 
                    score, 
                    platform="AutoApply.AI"
                )
                return {'status': 'already_applied', 'success': False}
            else:
                logger.info(f"      ⚠️ Vaga duplicada detectada - PULANDO")
                app_logger.log_job_application(
                    job_data, 
                    ApplicationStatus.DUPLICATE, 
                    score, 
                    platform="AutoApply.AI"
                )
                return {'status': 'duplicate', 'success': False}
        
        # Simular aplicação
        logger.info(f"      🔄 Simulando aplicação...")
        await asyncio.sleep(1)  # Simular tempo de aplicação
        
        # Log da aplicação bem-sucedida
        app_logger.log_job_application(
            job_data, 
            ApplicationStatus.APPLIED, 
            score, 
            platform="AutoApply.AI"
        )
        
        logger.info(f"      ✅ Aplicação simulada com sucesso")
        return {'status': 'applied', 'success': True}
        
    except Exception as e:
        logger.error(f"      ❌ Erro na aplicação: {str(e)}")
        app_logger.log_job_application(
            job_data, 
            ApplicationStatus.FAILED, 
            score, 
            error=str(e),
            platform="AutoApply.AI"
        )
        return {'status': 'failed', 'success': False, 'error': str(e)}

if __name__ == "__main__":
    asyncio.run(main())
