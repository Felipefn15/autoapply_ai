#!/usr/bin/env python3
"""
Script para verificar aplicações reais do sistema AutoApply.AI
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

def check_application_logs():
    """Verifica logs de aplicações reais."""
    print("🔍 VERIFICANDO APLICAÇÕES REAIS")
    print("=" * 50)
    
    applications_dir = Path("data/applications")
    if not applications_dir.exists():
        print("❌ Diretório de aplicações não encontrado")
        return
    
    # Buscar arquivos de aplicação
    application_files = list(applications_dir.glob("application_*.json"))
    
    if not application_files:
        print("❌ Nenhum arquivo de aplicação encontrado")
        return
    
    print(f"📁 {len(application_files)} arquivos de aplicação encontrados")
    
    # Analisar aplicações
    total_applications = 0
    successful_applications = 0
    failed_applications = 0
    platform_stats = defaultdict(int)
    company_stats = defaultdict(int)
    
    recent_applications = []
    cutoff_time = datetime.now() - timedelta(hours=24)
    
    for app_file in application_files:
        try:
            with open(app_file, 'r') as f:
                app_data = json.load(f)
            
            total_applications += 1
            
            if app_data.get('status') == 'success':
                successful_applications += 1
            else:
                failed_applications += 1
            
            platform = app_data.get('platform', 'unknown')
            company = app_data.get('company', 'unknown')
            platform_stats[platform] += 1
            company_stats[company] += 1
            
            # Verificar aplicações recentes
            app_time = datetime.fromisoformat(app_data.get('timestamp', ''))
            if app_time > cutoff_time:
                recent_applications.append(app_data)
                
        except Exception as e:
            print(f"⚠️ Erro ao processar {app_file}: {e}")
    
    # Estatísticas gerais
    print(f"\n📊 ESTATÍSTICAS GERAIS")
    print(f"   📝 Total de aplicações: {total_applications}")
    print(f"   ✅ Sucessos: {successful_applications}")
    print(f"   ❌ Falhas: {failed_applications}")
    
    if total_applications > 0:
        success_rate = (successful_applications / total_applications) * 100
        print(f"   📈 Taxa de sucesso: {success_rate:.1f}%")
    
    # Estatísticas por plataforma
    print(f"\n🌐 APLICAÇÕES POR PLATAFORMA")
    for platform, count in sorted(platform_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"   {platform}: {count} aplicações")
    
    # Top empresas
    print(f"\n🏢 TOP EMPRESAS")
    for company, count in sorted(company_stats.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   {company}: {count} aplicações")
    
    # Aplicações recentes (últimas 24h)
    print(f"\n⏰ APLICAÇÕES RECENTES (últimas 24h)")
    print(f"   📝 {len(recent_applications)} aplicações")
    
    for app in recent_applications[-5:]:  # Últimas 5
        timestamp = app.get('timestamp', 'N/A')
        job_title = app.get('job_title', 'N/A')
        company = app.get('company', 'N/A')
        platform = app.get('platform', 'N/A')
        status = app.get('status', 'N/A')
        
        print(f"   📄 {job_title} - {company} ({platform}) - {status}")
        print(f"      ⏰ {timestamp}")

def check_system_stats():
    """Verifica estatísticas do sistema."""
    print(f"\n📈 ESTATÍSTICAS DO SISTEMA")
    print("=" * 50)
    
    logs_dir = Path("data/logs")
    if not logs_dir.exists():
        print("❌ Diretório de logs não encontrado")
        return
    
    # Buscar arquivos de estatísticas finais
    stats_files = list(logs_dir.glob("final_stats_*.json"))
    
    if stats_files:
        latest_stats = max(stats_files, key=lambda x: x.stat().st_mtime)
        print(f"📁 Arquivo mais recente: {latest_stats}")
        
        try:
            with open(latest_stats, 'r') as f:
                stats = json.load(f)
            
            print(f"   🔄 Total de ciclos: {stats.get('total_cycles', 0)}")
            print(f"   📝 Total de aplicações: {stats.get('total_applications', 0)}")
            print(f"   ✅ Sucessos: {stats.get('successful_applications', 0)}")
            print(f"   ❌ Falhas: {stats.get('failed_applications', 0)}")
            print(f"   📅 Shutdown: {stats.get('shutdown_time', 'N/A')}")
            
        except Exception as e:
            print(f"⚠️ Erro ao ler estatísticas: {e}")
    else:
        print("❌ Nenhum arquivo de estatísticas encontrado")

def check_job_search_logs():
    """Verifica logs de busca de vagas."""
    print(f"\n🔍 LOGS DE BUSCA DE VAGAS")
    print("=" * 50)
    
    jobs_dir = Path("data/jobs")
    if not jobs_dir.exists():
        print("❌ Diretório de vagas não encontrado")
        return
    
    job_files = list(jobs_dir.glob("jobs_*.json"))
    
    if job_files:
        latest_jobs = max(job_files, key=lambda x: x.stat().st_mtime)
        print(f"📁 Arquivo mais recente: {latest_jobs}")
        
        try:
            with open(latest_jobs, 'r') as f:
                jobs = json.load(f)
            
            print(f"   📊 {len(jobs)} vagas encontradas")
            
            # Estatísticas por plataforma
            platform_stats = defaultdict(int)
            for job in jobs:
                platform = job.get('platform', 'unknown')
                platform_stats[platform] += 1
            
            print(f"   🌐 Vagas por plataforma:")
            for platform, count in sorted(platform_stats.items(), key=lambda x: x[1], reverse=True):
                print(f"      {platform}: {count}")
                
        except Exception as e:
            print(f"⚠️ Erro ao ler vagas: {e}")
    else:
        print("❌ Nenhum arquivo de vagas encontrado")

def main():
    """Função principal."""
    print("🚀 AUTOAPPLY.AI - VERIFICADOR DE APLICAÇÕES")
    print("=" * 60)
    
    check_application_logs()
    check_system_stats()
    check_job_search_logs()
    
    print(f"\n✅ Verificação concluída!")
    print(f"💡 Para ver logs em tempo real: tail -f logs/continuous_autoapply.log")

if __name__ == "__main__":
    main()
