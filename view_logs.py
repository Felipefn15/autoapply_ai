#!/usr/bin/env python3
"""
Visualizador de Logs e Relatórios do AutoApply.AI
Permite visualizar logs de sessões, aplicações e analytics
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

from loguru import logger

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent))

from app.automation.application_logger import ApplicationLogger

class LogViewer:
    """Visualizador de logs e relatórios."""
    
    def __init__(self, log_dir: str = "data/logs"):
        """Initialize the log viewer."""
        self.log_dir = Path(log_dir)
        self.logger = ApplicationLogger(log_dir)
    
    def show_recent_sessions(self, limit: int = 5) -> None:
        """Mostrar sessões recentes."""
        logger.info("📊 SESSÕES RECENTES")
        logger.info("=" * 50)
        
        sessions = self.logger.get_recent_sessions(limit)
        
        if not sessions:
            logger.warning("Nenhuma sessão encontrada")
            return
        
        for i, session in enumerate(sessions, 1):
            logger.info(f"\n{i}. Sessão: {session.session_id}")
            logger.info(f"   Data: {session.start_time[:10]}")
            logger.info(f"   Vagas encontradas: {session.total_jobs_found}")
            logger.info(f"   Aplicações: {session.total_applications}")
            logger.info(f"   Sucessos: {session.successful_applications}")
            logger.info(f"   Taxa de sucesso: {session.success_rate:.1f}%")
            logger.info(f"   Plataformas: {', '.join(session.platforms_searched)}")
    
    def show_session_details(self, session_id: str) -> None:
        """Mostrar detalhes de uma sessão específica."""
        logger.info(f"📋 DETALHES DA SESSÃO: {session_id}")
        logger.info("=" * 60)
        
        sessions = self.logger.get_recent_sessions(limit=100)
        session = next((s for s in sessions if s.session_id == session_id), None)
        
        if not session:
            logger.error(f"Sessão {session_id} não encontrada")
            return
        
        # Resumo
        logger.info("📊 RESUMO")
        logger.info("-" * 20)
        logger.info(f"ID da Sessão: {session.session_id}")
        logger.info(f"Início: {session.start_time}")
        logger.info(f"Fim: {session.end_time}")
        logger.info(f"Total de vagas: {session.total_jobs_found}")
        logger.info(f"Total de aplicações: {session.total_applications}")
        logger.info(f"Aplicações bem-sucedidas: {session.successful_applications}")
        logger.info(f"Aplicações falharam: {session.failed_applications}")
        logger.info(f"Aplicações puladas: {session.skipped_applications}")
        logger.info(f"Taxa de sucesso: {session.success_rate:.1f}%")
        logger.info(f"Plataformas: {', '.join(session.platforms_searched)}")
        
        # Buscas
        logger.info("\n🔍 BUSCAS REALIZADAS")
        logger.info("-" * 20)
        for search_log in session.search_logs:
            logger.info(f"Plataforma: {search_log.platform}")
            logger.info(f"  Keywords: {', '.join(search_log.keywords)}")
            logger.info(f"  Vagas encontradas: {search_log.jobs_found}")
            logger.info(f"  Duração: {search_log.search_duration:.2f}s")
            logger.info(f"  Sucesso: {'✅' if search_log.success else '❌'}")
            if search_log.errors:
                logger.info(f"  Erros: {len(search_log.errors)}")
                for error in search_log.errors:
                    logger.info(f"    - {error}")
            logger.info("")
        
        # Aplicações
        logger.info("📝 APLICAÇÕES REALIZADAS")
        logger.info("-" * 20)
        for app_log in session.application_logs:
            status_emoji = {
                'applied': '✅',
                'failed': '❌',
                'skipped': '⏭️',
                'interview': '🎯',
                'rejected': '❌',
                'accepted': '🎉'
            }
            
            emoji = status_emoji.get(app_log.status.value, '❓')
            logger.info(f"{emoji} {app_log.job_title}")
            logger.info(f"  Empresa: {app_log.company}")
            logger.info(f"  Plataforma: {app_log.platform}")
            logger.info(f"  Método: {app_log.application_method}")
            logger.info(f"  Status: {app_log.status.value}")
            logger.info(f"  Score: {app_log.match_score:.1%}")
            logger.info(f"  Duração: {app_log.application_duration:.2f}s")
            if app_log.error_message:
                logger.info(f"  Erro: {app_log.error_message}")
            logger.info("")
        
        # Erros
        if session.errors:
            logger.info("❌ ERROS ENCONTRADOS")
            logger.info("-" * 20)
            for error in session.errors:
                logger.error(f"  - {error}")
    
    def show_analytics(self, days: int = 30) -> None:
        """Mostrar analytics do período especificado."""
        logger.info(f"📊 ANALYTICS - ÚLTIMOS {days} DIAS")
        logger.info("=" * 50)
        
        analytics = self.logger.generate_analytics_report(days)
        
        if 'error' in analytics:
            logger.error(f"Erro ao gerar analytics: {analytics['error']}")
            return
        
        # Resumo geral
        logger.info("📈 RESUMO GERAL")
        logger.info("-" * 20)
        logger.info(f"Período: {analytics['period_days']} dias")
        logger.info(f"Total de sessões: {analytics['total_sessions']}")
        logger.info(f"Total de vagas encontradas: {analytics['total_jobs_found']}")
        logger.info(f"Total de aplicações: {analytics['total_applications']}")
        logger.info(f"Aplicações bem-sucedidas: {analytics['total_successful_applications']}")
        logger.info(f"Taxa de sucesso média: {analytics['average_success_rate']:.1f}%")
        
        # Estatísticas por plataforma
        logger.info("\n🌍 ESTATÍSTICAS POR PLATAFORMA")
        logger.info("-" * 30)
        for platform, stats in analytics['platform_statistics'].items():
            logger.info(f"📱 {platform}")
            logger.info(f"  Buscas: {stats['searches']}")
            logger.info(f"  Vagas encontradas: {stats['jobs_found']}")
            logger.info(f"  Taxa de sucesso: {stats['success_rate']:.1f}%")
            logger.info("")
        
        # Sessões recentes
        logger.info("📅 SESSÕES RECENTES")
        logger.info("-" * 20)
        for session in analytics['recent_sessions']:
            logger.info(f"📊 {session['session_id']}")
            logger.info(f"  Data: {session['date']}")
            logger.info(f"  Vagas: {session['jobs_found']}")
            logger.info(f"  Aplicações: {session['applications']}")
            logger.info(f"  Sucesso: {session['success_rate']:.1f}%")
            logger.info("")
    
    def list_available_sessions(self) -> List[str]:
        """Listar todas as sessões disponíveis."""
        session_files = list((self.log_dir / "sessions").glob("*.json"))
        session_ids = [f.stem for f in session_files]
        return sorted(session_ids, reverse=True)
    
    def show_help(self) -> None:
        """Mostrar ajuda."""
        logger.info("🔧 VISUALIZADOR DE LOGS - AJUDA")
        logger.info("=" * 50)
        logger.info("Comandos disponíveis:")
        logger.info("  recent [n]     - Mostrar n sessões recentes (padrão: 5)")
        logger.info("  session <id>   - Mostrar detalhes de uma sessão")
        logger.info("  analytics [d]  - Mostrar analytics dos últimos d dias (padrão: 30)")
        logger.info("  list           - Listar todas as sessões disponíveis")
        logger.info("  help           - Mostrar esta ajuda")
        logger.info("  exit           - Sair")
        logger.info("")
        logger.info("Exemplos:")
        logger.info("  recent 10      - Mostrar 10 sessões recentes")
        logger.info("  session session_20250901_120000")
        logger.info("  analytics 7    - Analytics da última semana")

def main():
    """Função principal."""
    logger.info("📊 VISUALIZADOR DE LOGS DO AUTOAPPLY.AI")
    logger.info("=" * 50)
    
    viewer = LogViewer()
    
    if not viewer.log_dir.exists():
        logger.error(f"Diretório de logs não encontrado: {viewer.log_dir}")
        logger.info("Execute primeiro o sistema para gerar logs")
        return
    
    logger.info("Digite 'help' para ver os comandos disponíveis")
    logger.info("Digite 'exit' para sair")
    logger.info("-" * 50)
    
    while True:
        try:
            command = input("\n📊 > ").strip().lower()
            
            if command == 'exit':
                logger.info("👋 Saindo do visualizador de logs")
                break
            elif command == 'help':
                viewer.show_help()
            elif command.startswith('recent'):
                parts = command.split()
                limit = int(parts[1]) if len(parts) > 1 else 5
                viewer.show_recent_sessions(limit)
            elif command.startswith('session'):
                parts = command.split()
                if len(parts) > 1:
                    session_id = parts[1]
                    viewer.show_session_details(session_id)
                else:
                    logger.error("Especifique o ID da sessão")
            elif command.startswith('analytics'):
                parts = command.split()
                days = int(parts[1]) if len(parts) > 1 else 30
                viewer.show_analytics(days)
            elif command == 'list':
                sessions = viewer.list_available_sessions()
                logger.info("📋 SESSÕES DISPONÍVEIS:")
                logger.info("-" * 30)
                for session_id in sessions:
                    logger.info(f"  {session_id}")
            else:
                logger.warning("Comando não reconhecido. Digite 'help' para ver os comandos disponíveis")
                
        except KeyboardInterrupt:
            logger.info("\n👋 Saindo do visualizador de logs")
            break
        except Exception as e:
            logger.error(f"Erro: {str(e)}")

if __name__ == "__main__":
    main()
