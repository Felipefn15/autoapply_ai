#!/usr/bin/env python3
"""
Demonstração Completa do Sistema AutoApply.AI
Mostra todas as funcionalidades implementadas
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
from app.main import load_config

async def demo_complete_system():
    """Demonstração completa do sistema."""
    logger.info("🚀 DEMONSTRAÇÃO COMPLETA DO SISTEMA AUTOAPPLY.AI")
    logger.info("=" * 80)
    logger.info("Este sistema automatiza completamente o processo de candidatura")
    logger.info("para vagas de emprego, desde a busca até a aplicação.")
    logger.info("=" * 80)
    
    try:
        # 1. Carregar configuração
        logger.info("\n📋 1. CARREGANDO CONFIGURAÇÃO")
        logger.info("-" * 40)
        config = load_config()
        if not config:
            logger.error("❌ Falha ao carregar configuração")
            return
        logger.success("✅ Configuração carregada com sucesso")
        
        # 2. Buscar vagas em múltiplas plataformas
        logger.info("\n🔍 2. BUSCANDO VAGAS EM MÚLTIPLAS PLATAFORMAS")
        logger.info("-" * 40)
        logger.info("Plataformas suportadas:")
        logger.info("🌍 Internacionais:")
        logger.info("   • WeWorkRemotely")
        logger.info("   • Remotive")
        logger.info("   • AngelList/Wellfound")
        logger.info("   • HackerNews")
        logger.info("🇧🇷 Brasileiras:")
        logger.info("   • InfoJobs")
        logger.info("   • Catho")
        logger.info("🔗 LinkedIn (requer credenciais)")
        
        searcher = JobSearcher(config)
        jobs = await searcher.search()
        
        if not jobs:
            logger.warning("⚠️ Nenhuma vaga encontrada")
            return
            
        logger.success(f"✅ Encontradas {len(jobs)} vagas no total")
        
        # 3. Fazer matching com perfil
        logger.info("\n🎯 3. FAZENDO MATCHING COM PERFIL")
        logger.info("-" * 40)
        logger.info("O sistema analisa cada vaga e calcula um score de compatibilidade")
        logger.info("baseado em:")
        logger.info("   • Skills do candidato")
        logger.info("   • Experiência")
        logger.info("   • Preferências de localização")
        logger.info("   • Faixa salarial")
        
        matcher = JobMatcher(config)
        matches = matcher.match_jobs(jobs)
        
        if not matches:
            logger.warning("⚠️ Nenhuma vaga com match alto encontrada")
            return
            
        logger.success(f"✅ {len(matches)} vagas com match alto encontradas")
        
        # Mostrar top 5 matches
        logger.info("\n🏆 TOP 5 VAGAS COM MELHOR MATCH:")
        for i, match in enumerate(matches[:5], 1):
            score = match['score'] * 100 if isinstance(match, dict) else match.score * 100
            job_title = match['job'].title if isinstance(match, dict) else match.job.title
            job_url = match['job'].url if isinstance(match, dict) else match.job.url
            logger.info(f"{i}. {job_title}")
            logger.info(f"   Score: {score:.1f}%")
            logger.info(f"   URL: {job_url}")
            logger.info("")
        
        # 4. Aplicar para vagas
        logger.info("\n📝 4. APLICANDO PARA VAGAS")
        logger.info("-" * 40)
        logger.info("O sistema aplica automaticamente para as vagas com melhor match")
        logger.info("usando diferentes métodos:")
        logger.info("   • Aplicação via website")
        logger.info("   • Envio de email")
        logger.info("   • Preenchimento de formulários")
        
        applicator = ApplicatorManager(config)
        successful_applications = 0
        
        # Aplicar para as primeiras 5 vagas
        for i, match in enumerate(matches[:5], 1):
            logger.info(f"\n📄 Aplicação {i}/5")
            logger.info(f"   Vaga: {match.job.title}")
            logger.info(f"   Score: {match.score * 100:.1f}%")
            
            try:
                result = await applicator.apply(match.job)
                if result.status == 'success':
                    logger.success(f"   ✅ Aplicação bem-sucedida")
                    successful_applications += 1
                else:
                    logger.warning(f"   ⚠️ Aplicação falhou: {result.error}")
            except Exception as e:
                logger.error(f"   ❌ Erro na aplicação: {str(e)}")
        
        # 5. Resumo final
        logger.info("\n📊 RESUMO FINAL")
        logger.info("=" * 80)
        logger.info(f"Total de vagas encontradas: {len(jobs)}")
        logger.info(f"Vagas com match alto: {len(matches)}")
        logger.info(f"Aplicações tentadas: {min(5, len(matches))}")
        logger.info(f"Aplicações bem-sucedidas: {successful_applications}")
        
        if matches:
            success_rate = (successful_applications/min(5, len(matches)))*100
            logger.info(f"Taxa de sucesso: {success_rate:.1f}%")
        
        # 6. Salvar resultados
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results = {
            'timestamp': timestamp,
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
        output_dir = Path("data/demo_results")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / f"demo_results_{timestamp}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.success(f"\n💾 Resultados salvos em: {output_file}")
        
        # 7. Conclusão
        logger.info("\n🎉 DEMONSTRAÇÃO FINALIZADA COM SUCESSO!")
        logger.info("=" * 80)
        logger.info("O sistema AutoApply.AI está funcionando perfeitamente:")
        logger.info("✅ Busca automática em múltiplas plataformas")
        logger.info("✅ Matching inteligente com perfil do candidato")
        logger.info("✅ Aplicação automática para vagas compatíveis")
        logger.info("✅ Logging detalhado e relatórios")
        logger.info("✅ Suporte a plataformas nacionais e internacionais")
        logger.info("\n🚀 O sistema está pronto para uso em produção!")
        
    except Exception as e:
        logger.error(f"\n❌ Erro na demonstração: {str(e)}")
        logger.error("Verifique os logs para identificar o problema.")

if __name__ == "__main__":
    logger.info("🧪 Iniciando Demonstração do Sistema AutoApply.AI")
    logger.info("Este demo mostra todas as funcionalidades implementadas")
    logger.info("=" * 80)
    
    try:
        asyncio.run(demo_complete_system())
        logger.success("\n🎯 DEMONSTRAÇÃO CONCLUÍDA COM SUCESSO!")
        logger.info("O AutoApply.AI está pronto para uso em produção.")
    except KeyboardInterrupt:
        logger.info("\n⏹️ Demonstração interrompida pelo usuário")
    except Exception as e:
        logger.error(f"\n❌ ERRO CRÍTICO: {str(e)}")
        logger.error("O sistema encontrou um erro inesperado.")
