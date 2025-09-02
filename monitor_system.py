#!/usr/bin/env python3
"""
Monitor do Sistema Contínuo AutoApply.AI
Monitora o status e performance do sistema em execução
"""

import os
import sys
import json
import time
try:
    import psutil
except ImportError:
    print("❌ psutil não instalado. Execute: pip install psutil")
    sys.exit(1)
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

def get_system_stats() -> Dict:
    """Obtém estatísticas do sistema."""
    try:
        # Estatísticas do processo
        process = psutil.Process()
        
        # Estatísticas de memória
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()
        
        # Estatísticas de CPU
        cpu_percent = process.cpu_percent()
        
        # Estatísticas de arquivos abertos
        open_files = len(process.open_files())
        
        # Tempo de execução
        create_time = process.create_time()
        uptime = time.time() - create_time
        
        return {
            'pid': process.pid,
            'memory_mb': round(memory_info.rss / 1024 / 1024, 2),
            'memory_percent': round(memory_percent, 2),
            'cpu_percent': round(cpu_percent, 2),
            'open_files': open_files,
            'uptime_seconds': round(uptime, 2),
            'uptime_human': str(timedelta(seconds=int(uptime))),
            'status': process.status(),
            'create_time': datetime.fromtimestamp(create_time).isoformat()
        }
    except Exception as e:
        return {'error': str(e)}

def get_log_stats() -> Dict:
    """Obtém estatísticas dos logs."""
    try:
        log_dir = Path("data/logs")
        if not log_dir.exists():
            return {'error': 'Log directory not found'}
        
        # Encontrar arquivos de log
        log_files = list(log_dir.glob("*.log"))
        continuous_logs = list(log_dir.glob("continuous_autoapply*.log"))
        
        # Estatísticas dos logs
        total_size = sum(f.stat().st_size for f in log_files)
        continuous_size = sum(f.stat().st_size for f in continuous_logs)
        
        # Última modificação
        latest_log = max(log_files, key=lambda x: x.stat().st_mtime) if log_files else None
        
        return {
            'total_log_files': len(log_files),
            'continuous_log_files': len(continuous_logs),
            'total_size_mb': round(total_size / 1024 / 1024, 2),
            'continuous_size_mb': round(continuous_size / 1024 / 1024, 2),
            'latest_log': latest_log.name if latest_log else None,
            'latest_log_time': datetime.fromtimestamp(latest_log.stat().st_mtime).isoformat() if latest_log else None
        }
    except Exception as e:
        return {'error': str(e)}

def get_application_stats() -> Dict:
    """Obtém estatísticas das aplicações."""
    try:
        # Procurar por arquivos de estatísticas
        stats_files = list(Path("data/logs").glob("final_stats_*.json"))
        
        if not stats_files:
            return {'error': 'No application stats found'}
        
        # Carregar estatísticas mais recentes
        latest_stats_file = max(stats_files, key=lambda x: x.stat().st_mtime)
        
        with open(latest_stats_file, 'r') as f:
            stats = json.load(f)
        
        return {
            'stats_file': latest_stats_file.name,
            'total_cycles': stats.get('total_cycles', 0),
            'total_applications': stats.get('total_applications', 0),
            'successful_applications': stats.get('successful_applications', 0),
            'failed_applications': stats.get('failed_applications', 0),
            'applied_jobs_count': stats.get('applied_jobs_count', 0),
            'shutdown_time': stats.get('shutdown_time'),
            'success_rate': round((stats.get('successful_applications', 0) / max(stats.get('total_applications', 1), 1)) * 100, 2)
        }
    except Exception as e:
        return {'error': str(e)}

def get_recent_logs(lines: int = 20) -> List[str]:
    """Obtém as últimas linhas do log contínuo."""
    try:
        log_dir = Path("data/logs")
        continuous_logs = list(log_dir.glob("continuous_autoapply*.log"))
        
        if not continuous_logs:
            return ["Nenhum log contínuo encontrado"]
        
        # Pegar o log mais recente
        latest_log = max(continuous_logs, key=lambda x: x.stat().st_mtime)
        
        with open(latest_log, 'r') as f:
            all_lines = f.readlines()
        
        return all_lines[-lines:] if len(all_lines) > lines else all_lines
    except Exception as e:
        return [f"Erro ao ler logs: {e}"]

def check_system_health() -> Dict:
    """Verifica a saúde do sistema."""
    try:
        # Verificar se o processo está rodando
        process_found = False
        process_name = "continuous_autoapply.py"
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['cmdline'] and any(process_name in cmd for cmd in proc.info['cmdline']):
                    process_found = True
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Verificar uso de recursos
        system_stats = get_system_stats()
        
        # Verificar logs recentes
        recent_logs = get_recent_logs(5)
        has_recent_activity = any("CICLO" in log for log in recent_logs)
        
        return {
            'process_running': process_found,
            'system_stats': system_stats,
            'has_recent_activity': has_recent_activity,
            'health_status': 'HEALTHY' if process_found and has_recent_activity else 'UNHEALTHY'
        }
    except Exception as e:
        return {'error': str(e), 'health_status': 'ERROR'}

def print_dashboard():
    """Imprime dashboard do sistema."""
    print("\n" + "="*80)
    print("📊 AUTOAPPLY.AI - DASHBOARD DO SISTEMA")
    print("="*80)
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Verificar saúde do sistema
    health = check_system_health()
    
    if health.get('health_status') == 'HEALTHY':
        print("🟢 STATUS: SISTEMA FUNCIONANDO")
    elif health.get('health_status') == 'UNHEALTHY':
        print("🟡 STATUS: SISTEMA COM PROBLEMAS")
    else:
        print("🔴 STATUS: SISTEMA COM ERRO")
    
    print("\n📈 ESTATÍSTICAS DO SISTEMA:")
    print("-" * 40)
    
    system_stats = health.get('system_stats', {})
    if 'error' not in system_stats:
        print(f"🆔 PID: {system_stats.get('pid', 'N/A')}")
        print(f"💾 Memória: {system_stats.get('memory_mb', 0)} MB ({system_stats.get('memory_percent', 0)}%)")
        print(f"⚡ CPU: {system_stats.get('cpu_percent', 0)}%")
        print(f"📁 Arquivos abertos: {system_stats.get('open_files', 0)}")
        print(f"⏱️ Uptime: {system_stats.get('uptime_human', 'N/A')}")
        print(f"📅 Iniciado em: {system_stats.get('create_time', 'N/A')}")
    else:
        print(f"❌ Erro: {system_stats['error']}")
    
    print("\n📊 ESTATÍSTICAS DE APLICAÇÕES:")
    print("-" * 40)
    
    app_stats = get_application_stats()
    if 'error' not in app_stats:
        print(f"🔄 Ciclos executados: {app_stats.get('total_cycles', 0)}")
        print(f"📝 Total de aplicações: {app_stats.get('total_applications', 0)}")
        print(f"✅ Aplicações bem-sucedidas: {app_stats.get('successful_applications', 0)}")
        print(f"❌ Aplicações falhadas: {app_stats.get('failed_applications', 0)}")
        print(f"📈 Taxa de sucesso: {app_stats.get('success_rate', 0)}%")
        print(f"📋 Vagas únicas aplicadas: {app_stats.get('applied_jobs_count', 0)}")
    else:
        print(f"ℹ️ {app_stats['error']}")
    
    print("\n📋 ESTATÍSTICAS DE LOGS:")
    print("-" * 40)
    
    log_stats = get_log_stats()
    if 'error' not in log_stats:
        print(f"📄 Total de arquivos de log: {log_stats.get('total_log_files', 0)}")
        print(f"🔄 Logs contínuos: {log_stats.get('continuous_log_files', 0)}")
        print(f"💾 Tamanho total: {log_stats.get('total_size_mb', 0)} MB")
        print(f"📝 Tamanho logs contínuos: {log_stats.get('continuous_size_mb', 0)} MB")
        print(f"📅 Último log: {log_stats.get('latest_log', 'N/A')}")
    else:
        print(f"ℹ️ {log_stats['error']}")
    
    print("\n📝 ATIVIDADE RECENTE:")
    print("-" * 40)
    
    recent_logs = get_recent_logs(10)
    for log_line in recent_logs[-5:]:  # Mostrar apenas as últimas 5 linhas
        print(f"   {log_line.strip()}")
    
    print("\n" + "="*80)

def main():
    """Função principal."""
    try:
        while True:
            # Limpar tela
            os.system('clear' if os.name == 'posix' else 'cls')
            
            # Mostrar dashboard
            print_dashboard()
            
            # Aguardar próxima atualização
            print("\n🔄 Atualizando em 30 segundos... (Ctrl+C para sair)")
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\n🛑 Monitor interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro no monitor: {e}")

if __name__ == "__main__":
    main()
