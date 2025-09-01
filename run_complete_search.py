#!/usr/bin/env python3
"""
Script para Executar Busca Completa e Gerar Logs Detalhados
Executa todo o processo de busca, matching e aplicação com logging completo
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

from loguru import logger

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent))

from app.job_search.searcher import JobSearcher
from app.matching.matcher import JobMatcher
from app.automation.applicator_manager import ApplicatorManager
from app.automation.application_logger import ApplicationLogger, ApplicationStatus
from app.automation.direct_applicator import DirectApplicator
from app.main import load_config

async def run_complete_search():
    """Executar busca completa com logging detalhado."""
    logger.info("🚀 INICIANDO BUSCA COMPLETA COM LOGGING DETALHADO")
    logger.info("=" * 60)
    
    try:
        # 1. Carregar configurações
        logger.info("📋 1. Carregando configurações...")
        config = load_config()
        logger.info("   ✅ Configurações carregadas")
        
        # 2. Inicializar logger de aplicações
        logger.info("📊 2. Inicializando sistema de logging...")
        app_logger = ApplicationLogger()
        session_id = app_logger.start_session()
        logger.info(f"   ✅ Sessão iniciada: {session_id}")
        
        # 3. Buscar vagas
        logger.info("🔍 3. Iniciando busca de vagas...")
        searcher = JobSearcher(config, app_logger)
        
        # Buscar em todas as plataformas usando o método search()
        logger.info("   🔍 Buscando em todas as plataformas...")
        all_jobs = await searcher.search()
        
        logger.info(f"   📊 Total de vagas encontradas: {len(all_jobs)}")
        
        if not all_jobs:
            logger.warning("   ⚠️ Nenhuma vaga encontrada. Usando dados de teste...")
            # Criar algumas vagas de teste
            from app.job_search.models import JobPosting
            all_jobs = [
                JobPosting(
                    title="Senior Python Developer",
                    description="Desenvolvedor Python sênior para projeto remoto",
                    url="https://example.com/job1",
                    email="hr@example.com"
                ),
                JobPosting(
                    title="Full Stack Engineer",
                    description="Engenheiro full stack com experiência em React e Node.js",
                    url="https://example.com/job2",
                    email="jobs@example.com"
                ),
                JobPosting(
                    title="Data Scientist",
                    description="Cientista de dados para análise de big data",
                    url="https://example.com/job3",
                    email="careers@example.com"
                )
            ]
        
        # 4. Fazer matching das vagas
        logger.info("🎯 4. Fazendo matching das vagas...")
        matcher = JobMatcher(config)
        matches = matcher.match_jobs(all_jobs)
        
        logger.info(f"   📊 Vagas com match: {len(matches)}")
        
        # Mostrar top 5 matches
        logger.info("\n🏆 TOP 5 VAGAS COM MELHOR MATCH:")
        for i, match in enumerate(matches[:5], 1):
            if isinstance(match, dict):
                score = match.get('match_score', 0.0) * 100
                job_title = match.get('title', 'Unknown')
                job_url = match.get('url', '')
            else:
                score = match.score * 100
                job_title = match.job.title
                job_url = match.job.url
            
            logger.info(f"{i}. {job_title}")
            logger.info(f"   Score: {score:.1f}%")
            logger.info(f"   URL: {job_url}")
            logger.info("")
        
        # 5. Aplicar para vagas usando sistema direto
        logger.info("📝 5. Aplicando para vagas usando sistema direto...")
        
        # Inicializar sistema de aplicações diretas
        direct_applicator = DirectApplicator(config)
        
        successful_applications = 0
        failed_applications = 0
        total_applications = min(len(matches), 50)  # Aplicar para até 50 vagas
        
        logger.info(f"🎯 Aplicando para {total_applications} vagas com melhor match...")
        
        for i, match in enumerate(matches[:total_applications], 1):
            logger.info(f"\n📄 Aplicação {i}/{total_applications}")
            
            # Preparar dados da vaga
            if isinstance(match, dict):
                job_data = {
                    'title': match.get('title', 'Unknown'),
                    'description': match.get('description', ''),
                    'url': match.get('url', ''),
                    'email': match.get('email'),
                    'company': match.get('company', 'Unknown'),
                    'platform': match.get('platform', 'Unknown')
                }
                score = match.get('match_score', 0.0)
            else:
                job_data = {
                    'title': match.job.title,
                    'description': match.job.description,
                    'url': match.job.url,
                    'email': match.job.email,
                    'company': 'Unknown',
                    'platform': 'Unknown'
                }
                score = match.score
            
            logger.info(f"   Vaga: {job_data['title']}")
            logger.info(f"   Empresa: {job_data['company']}")
            logger.info(f"   Score: {score:.1%}")
            logger.info(f"   URL: {job_data['url']}")
            logger.info(f"   Plataforma: {job_data['platform']}")
            
            # Aplicar para a vaga usando sistema direto
            logger.info("   🚀 Aplicando diretamente...")
            
            try:
                # Criar objeto JobPosting para o aplicador direto
                from app.job_search.models import JobPosting
                job_posting = JobPosting(
                    title=job_data['title'],
                    description=job_data['description'],
                    url=job_data['url'],
                    email=job_data.get('email')
                )
                
                # Aplicar para a vaga
                result = await direct_applicator.apply_to_job(job_posting)
                
                if result.get('success', False):
                    logger.info(f"   ✅ Aplicação bem-sucedida: {result.get('message', '')}")
                    successful_applications += 1
                    
                    # Log da aplicação bem-sucedida
                    app_logger.log_job_application(
                        job_data=job_data,
                        status=ApplicationStatus.APPLIED,
                        match_score=score,
                        platform=job_data['platform']
                    )
                else:
                    logger.warning(f"   ⚠️ Aplicação falhou: {result.get('error', 'Erro desconhecido')}")
                    failed_applications += 1
                    
                    # Log da aplicação falhada
                    app_logger.log_job_application(
                        job_data=job_data,
                        status=ApplicationStatus.FAILED,
                        match_score=score,
                        platform=job_data['platform']
                    )
                
            except Exception as e:
                logger.error(f"   ❌ Erro na aplicação: {str(e)}")
                failed_applications += 1
                
                # Log do erro
                app_logger.log_job_application(
                    job_data=job_data,
                    status=ApplicationStatus.FAILED,
                    match_score=score,
                    platform=job_data['platform']
                )
            
            # Delay entre aplicações para evitar rate limiting
            await asyncio.sleep(1)  # Reduzido para 1 segundo
        
        # 6. Mostrar estatísticas do sistema direto
        logger.info("\n📊 6. Estatísticas do sistema de aplicações diretas...")
        direct_stats = direct_applicator.get_application_stats()
        logger.info(f"   📈 Total de aplicações diretas: {direct_stats.get('total_applications', 0)}")
        logger.info(f"   ✅ Aplicações bem-sucedidas: {direct_stats.get('successful_applications', 0)}")
        logger.info(f"   ❌ Aplicações falharam: {direct_stats.get('failed_applications', 0)}")
        logger.info(f"   📊 Taxa de sucesso: {direct_stats.get('success_rate', 0)}%")
        logger.info(f"   🌐 Plataformas usadas: {', '.join(direct_stats.get('platforms_used', []))}")
        logger.info(f"   🔧 Métodos usados: {', '.join(direct_stats.get('methods_used', []))}")
        
        # 7. Finalizar sessão e gerar relatório
        logger.info("\n📊 7. Finalizando sessão e gerando relatório...")
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
        logger.info(f"📝 Aplicações realizadas: {successful_applications + failed_applications}")
        logger.info(f"✅ Aplicações bem-sucedidas: {successful_applications}")
        logger.info(f"❌ Aplicações falharam: {failed_applications}")
        
        if successful_applications + failed_applications > 0:
            success_rate = (successful_applications / (successful_applications + failed_applications)) * 100
            logger.info(f"📈 Taxa de sucesso: {success_rate:.1f}%")
        else:
            logger.info(f"📈 Taxa de sucesso: 0.0%")
        logger.info(f"📁 Logs salvos em: data/logs/")
        logger.info(f"📄 Relatório: data/logs/reports/session_{timestamp}_report.txt")
        logger.info(f"📊 CSV Detalhado: {csv_report_path}")
        logger.info(f"📈 CSV Resumo: {summary_csv_path}")
        
        logger.info("\n🎉 Busca completa finalizada com sucesso!")
        
    except Exception as e:
        logger.error(f"❌ Erro durante a busca completa: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(run_complete_search())
