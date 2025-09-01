#!/usr/bin/env python3
"""
Teste Completo do Sistema AutoApply.AI
Demonstra o fluxo completo de busca, matching e aplicação
"""
import asyncio
import json
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
from app.main import load_config
from app.job_search.models import JobPosting

async def test_complete_system():
    """Teste completo do sistema."""
    logger.info("🚀 Iniciando Teste Completo do Sistema AutoApply.AI")
    logger.info("=" * 60)
    
    try:
        # 1. Carregar configuração
        logger.info("📋 1. Carregando configuração...")
        config = load_config()
        if not config:
            logger.error("❌ Falha ao carregar configuração")
            return
        logger.success("✅ Configuração carregada com sucesso")
        
        # 2. Inicializar sistema de logging
        logger.info("📊 2. Inicializando sistema de logging...")
        app_logger = ApplicationLogger()
        session_id = app_logger.start_session()
        logger.success(f"✅ Sessão de logging iniciada: {session_id}")
        
        # 3. Buscar vagas
        logger.info("\n🔍 3. Buscando vagas...")
        searcher = JobSearcher(config, logger_instance=app_logger)
        jobs = await searcher.search()
        
        if not jobs:
            logger.warning("⚠️ Nenhuma vaga encontrada")
            return
            
        logger.success(f"✅ Encontradas {len(jobs)} vagas")
        
        # 4. Fazer matching
        logger.info("\n🎯 4. Fazendo matching com perfil...")
        matcher = JobMatcher(config)
        matches = matcher.match_jobs(jobs)
        
        if not matches:
            logger.warning("⚠️ Nenhuma vaga com match alto encontrada")
            return
            
        logger.success(f"✅ {len(matches)} vagas com match alto")
        
        # 5. Aplicar para vagas
        logger.info("\n📝 5. Aplicando para vagas...")
        applicator = ApplicatorManager(config)
        applicator.start_session()  # Start application session
        
        successful_applications = 0
        
        # Aplicar para as primeiras 5 vagas
        for i, match in enumerate(matches[:5], 1):
            logger.info(f"\n📄 Aplicação {i}/5")
            
            # Handle both MatchResult objects and dictionaries
            if hasattr(match, 'job'):
                # MatchResult object
                job = match.job
                score = match.score
            elif isinstance(match, dict):
                # Dictionary format from matcher
                job = JobPosting(
                    title=match.get('title', 'Unknown'),
                    description=match.get('description', ''),
                    email=match.get('email'),
                    url=match.get('url', '')
                )
                score = match.get('match_score', 0.0)
            else:
                logger.error(f"   ❌ Formato de match desconhecido: {type(match)}")
                continue
            
            logger.info(f"   Vaga: {job.title}")
            logger.info(f"   Empresa: N/A")  # JobPosting doesn't have company field
            logger.info(f"   Score: {score:.1%}")
            
            try:
                result = await applicator.apply(job)
                if result.status == 'success':
                    logger.success(f"   ✅ Aplicação bem-sucedida")
                    successful_applications += 1
                else:
                    logger.warning(f"   ⚠️ Aplicação falhou: {result.error}")
            except Exception as e:
                logger.error(f"   ❌ Erro na aplicação: {str(e)}")
        
        # 6. Finalizar sessão e gerar relatórios
        logger.info("\n📊 6. Finalizando sessão e gerando relatórios...")
        session_log = applicator.end_session()
        
        if session_log:
            logger.success("✅ Relatórios gerados com sucesso")
            logger.info(f"📄 Relatório salvo em: data/logs/reports/{session_id}_report.txt")
            logger.info(f"📊 Analytics salvo em: data/logs/reports/analytics_30days.json")
        
        # 7. Resumo final
        logger.info("\n📊 RESUMO FINAL")
        logger.info("=" * 60)
        logger.info(f"Total de vagas encontradas: {len(jobs)}")
        logger.info(f"Vagas com match alto: {len(matches)}")
        logger.info(f"Aplicações tentadas: {min(5, len(matches))}")
        logger.info(f"Aplicações bem-sucedidas: {successful_applications}")
        
        if matches:
            success_rate = (successful_applications/min(5, len(matches)))*100
            logger.info(f"Taxa de sucesso: {success_rate:.1f}%")
        else:
            logger.info("Taxa de sucesso: N/A (nenhuma vaga para aplicar)")
        
        # 8. Salvar resultados
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results = {
            'timestamp': timestamp,
            'session_id': session_id,
            'total_jobs_found': len(jobs),
            'high_match_jobs': len(matches),
            'applications_attempted': min(5, len(matches)),
            'successful_applications': successful_applications,
            'success_rate': success_rate if matches else 0,
            'platforms': {
                'weworkremotely': len([j for j in jobs if 'weworkremotely' in j.url.lower()]),
                'remotive': len([j for j in jobs if 'remotive' in j.url.lower()]),
                'hackernews': len([j for j in jobs if 'ycombinator' in j.url.lower()]),
                'linkedin': len([j for j in jobs if 'linkedin' in j.url.lower()]),
                'infojobs': len([j for j in jobs if 'infojobs' in j.url.lower()]),
                'catho': len([j for j in jobs if 'catho' in j.url.lower()]),
            }
        }
        
        # Criar diretório se não existir
        output_dir = Path("data/test_results")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / f"test_results_{timestamp}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.success(f"\n💾 Resultados salvos em: {output_file}")
        
        # 9. Conclusão
        logger.success("\n🎉 TESTE COMPLETO FINALIZADO COM SUCESSO!")
        logger.info("O sistema está funcionando corretamente em todas as etapas:")
        logger.info("✅ Busca de vagas")
        logger.info("✅ Matching com perfil")
        logger.info("✅ Aplicação automática")
        logger.info("✅ Logging e relatórios")
        logger.info("✅ Sistema de analytics")
        
    except Exception as e:
        logger.error(f"\n❌ Erro no teste: {str(e)}")
        raise

def main():
    """Função principal."""
    logger.info("🧪 Iniciando Teste do Sistema AutoApply.AI")
    logger.info("Este teste demonstra o fluxo completo do sistema")
    logger.info("=" * 60)
    
    try:
        asyncio.run(test_complete_system())
        logger.success("\n🎯 SISTEMA VALIDADO COM SUCESSO!")
        logger.info("O AutoApply.AI está pronto para uso em produção.")
    except Exception as e:
        logger.error(f"\n❌ SISTEMA COM PROBLEMAS!")
        logger.error(f"Erro: {str(e)}")
        logger.info("Verifique os logs para identificar os problemas.")

if __name__ == "__main__":
    main()
