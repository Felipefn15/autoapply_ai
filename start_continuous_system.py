#!/usr/bin/env python3
"""
Script de Inicialização do Sistema Contínuo AutoApply.AI
Verifica dependências e inicia o sistema de aplicação contínua
"""

import os
import sys
import subprocess
import asyncio
from pathlib import Path
from datetime import datetime

def check_dependencies():
    """Verifica se todas as dependências estão instaladas."""
    print("🔍 Verificando dependências...")
    
    required_packages = [
        'groq',
        'loguru',
        'pyyaml',
        'asyncio'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"   ❌ {package} - NÃO INSTALADO")
    
    if missing_packages:
        print(f"\n❌ Pacotes faltando: {', '.join(missing_packages)}")
        print("📦 Instalando pacotes faltantes...")
        
        for package in missing_packages:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"   ✅ {package} instalado com sucesso")
            except subprocess.CalledProcessError:
                print(f"   ❌ Erro ao instalar {package}")
                return False
    
    return True

def check_config_files():
    """Verifica se os arquivos de configuração existem."""
    print("\n📋 Verificando arquivos de configuração...")
    
    required_files = [
        "config/config.yaml",
        "config/profile.yaml",
        "config/continuous_config.yaml"
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"   ✅ {file_path}")
        else:
            missing_files.append(file_path)
            print(f"   ❌ {file_path} - NÃO ENCONTRADO")
    
    if missing_files:
        print(f"\n❌ Arquivos faltando: {', '.join(missing_files)}")
        return False
    
    return True

def check_environment_variables():
    """Verifica variáveis de ambiente necessárias."""
    print("\n🌍 Verificando configurações...")
    
    # Verificar API key do Groq no arquivo credentials.yaml
    groq_key_found = False
    try:
        import yaml
        credentials_path = Path("config/credentials.yaml")
        if credentials_path.exists():
            with open(credentials_path, 'r') as f:
                credentials = yaml.safe_load(f)
                groq_config = credentials.get('groq', {})
                groq_key = groq_config.get('api_key')
                if groq_key:
                    print("   ✅ API key do Groq encontrada em config/credentials.yaml")
                    groq_key_found = True
    except Exception as e:
        print(f"   ⚠️ Erro ao verificar credentials.yaml: {e}")
    
    # Fallback para variável de ambiente
    if not groq_key_found:
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            print("   ✅ GROQ_API_KEY configurada via variável de ambiente")
            groq_key_found = True
    
    if not groq_key_found:
        print("   ⚠️ API key do Groq não encontrada")
        print("      Para habilitar Groq AI, adicione em config/credentials.yaml:")
        print("      groq:")
        print("        api_key: 'sua_chave'")
    
    # Outras variáveis opcionais
    search_interval = os.getenv("SEARCH_INTERVAL")
    if search_interval:
        print(f"   ✅ SEARCH_INTERVAL: {search_interval}s")
    else:
        print("   ℹ️ SEARCH_INTERVAL não definida (usando padrão: 3600s)")
    
    max_applications = os.getenv("MAX_APPLICATIONS")
    if max_applications:
        print(f"   ✅ MAX_APPLICATIONS: {max_applications}")
    else:
        print("   ℹ️ MAX_APPLICATIONS não definida (usando padrão: 20)")
    
    return True

def create_directories():
    """Cria diretórios necessários."""
    print("\n📁 Criando diretórios necessários...")
    
    directories = [
        "data/logs",
        "data/applications", 
        "data/matches",
        "data/jobs",
        "data/analysis"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"   ✅ {directory}")

def show_system_info():
    """Mostra informações do sistema."""
    print("\n" + "="*60)
    print("🚀 AUTOAPPLY.AI - SISTEMA CONTÍNUO")
    print("="*60)
    print(f"📅 Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🐍 Python: {sys.version}")
    print(f"📂 Diretório: {os.getcwd()}")
    print("="*60)

def show_usage_instructions():
    """Mostra instruções de uso."""
    print("\n📖 INSTRUÇÕES DE USO:")
    print("="*60)
    print("1. O sistema rodará em loop contínuo")
    print("2. Buscará vagas a cada intervalo configurado")
    print("3. Aplicará automaticamente para vagas compatíveis")
    print("4. Usará Groq AI para melhorar matching (se habilitado)")
    print("5. Logs serão salvos em data/logs/")
    print("6. Para parar: Ctrl+C")
    print("="*60)

async def start_system():
    """Inicia o sistema contínuo."""
    print("\n🚀 Iniciando sistema contínuo...")
    
    try:
        # Importar e executar o sistema
        from continuous_autoapply import main
        await main()
    except KeyboardInterrupt:
        print("\n🛑 Sistema interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro ao iniciar sistema: {e}")
        return False
    
    return True

def main():
    """Função principal."""
    show_system_info()
    
    # Verificações pré-inicialização
    if not check_dependencies():
        print("\n❌ Falha na verificação de dependências")
        return 1
    
    if not check_config_files():
        print("\n❌ Falha na verificação de arquivos de configuração")
        return 1
    
    check_environment_variables()
    create_directories()
    show_usage_instructions()
    
    # Confirmar inicialização
    print("\n❓ Deseja iniciar o sistema contínuo? (s/N): ", end="")
    response = input().lower().strip()
    
    if response not in ['s', 'sim', 'y', 'yes']:
        print("🛑 Inicialização cancelada")
        return 0
    
    # Iniciar sistema
    try:
        asyncio.run(start_system())
    except Exception as e:
        print(f"\n❌ Erro crítico: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
