#!/usr/bin/env python3
"""
Script de Configuração do Groq AI
Ajuda a configurar a API key do Groq para o sistema contínuo
"""

import os
import sys
from pathlib import Path

def check_groq_installation():
    """Verifica se o Groq está instalado."""
    try:
        import groq
        print("✅ Groq package instalado")
        return True
    except ImportError:
        print("❌ Groq package não instalado")
        print("📦 Instalando...")
        try:
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "groq>=0.4.0"])
            print("✅ Groq package instalado com sucesso")
            return True
        except subprocess.CalledProcessError:
            print("❌ Erro ao instalar Groq package")
            return False

def get_groq_api_key():
    """Obtém a API key do Groq do usuário."""
    print("\n🔑 Configuração da API Key do Groq")
    print("=" * 50)
    print("Para usar o Groq AI, você precisa de uma API key.")
    print("1. Acesse: https://console.groq.com/")
    print("2. Crie uma conta ou faça login")
    print("3. Gere uma nova API key")
    print("4. Cole a chave abaixo")
    print("=" * 50)
    
    while True:
        api_key = input("\n🔑 Digite sua API key do Groq (ou 'skip' para pular): ").strip()
        
        if api_key.lower() == 'skip':
            print("⚠️ Groq AI será desabilitado")
            return None
        
        if not api_key:
            print("❌ API key não pode estar vazia")
            continue
        
        if not api_key.startswith('gsk_'):
            print("⚠️ API key do Groq geralmente começa com 'gsk_'")
            confirm = input("Deseja continuar mesmo assim? (s/N): ").lower()
            if confirm not in ['s', 'sim', 'y', 'yes']:
                continue
        
        # Testar a API key
        if test_groq_api_key(api_key):
            return api_key
        else:
            print("❌ API key inválida ou erro de conexão")
            retry = input("Deseja tentar novamente? (s/N): ").lower()
            if retry not in ['s', 'sim', 'y', 'yes']:
                return None

def test_groq_api_key(api_key: str) -> bool:
    """Testa se a API key do Groq funciona."""
    try:
        import groq
        
        print("🧪 Testando API key...")
        client = groq.Groq(api_key=api_key)
        
        # Fazer uma requisição simples
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": "Hello, this is a test."}],
            model="llama3-8b-8192",
            max_tokens=10
        )
        
        if response.choices and response.choices[0].message.content:
            print("✅ API key válida e funcionando")
            return True
        else:
            print("❌ Resposta inválida da API")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao testar API key: {e}")
        return False

def save_api_key_to_env(api_key: str):
    """Salva a API key no arquivo .env."""
    env_file = Path(".env")
    
    # Ler arquivo .env existente
    env_content = {}
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    env_content[key] = value
    
    # Adicionar/atualizar GROQ_API_KEY
    env_content['GROQ_API_KEY'] = api_key
    
    # Salvar arquivo .env
    with open(env_file, 'w') as f:
        for key, value in env_content.items():
            f.write(f"{key}={value}\n")
    
    print(f"✅ API key salva em {env_file}")

def update_continuous_config(enable_groq: bool):
    """Atualiza a configuração contínua."""
    config_file = Path("config/continuous_config.yaml")
    
    if not config_file.exists():
        print("⚠️ Arquivo de configuração contínua não encontrado")
        return
    
    try:
        import yaml
        
        # Ler configuração
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # Atualizar configuração do Groq
        config['enable_groq_ai'] = enable_groq
        
        # Salvar configuração
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
        
        print(f"✅ Configuração atualizada em {config_file}")
        
    except Exception as e:
        print(f"❌ Erro ao atualizar configuração: {e}")

def show_usage_instructions():
    """Mostra instruções de uso."""
    print("\n📖 INSTRUÇÕES DE USO:")
    print("=" * 60)
    print("1. A API key será salva no arquivo .env")
    print("2. O sistema contínuo será configurado automaticamente")
    print("3. Para iniciar o sistema: python start_continuous_system.py")
    print("4. Para monitorar: python monitor_system.py")
    print("5. Para desabilitar Groq AI: edite config/continuous_config.yaml")
    print("=" * 60)

def main():
    """Função principal."""
    print("🤖 CONFIGURAÇÃO DO GROQ AI")
    print("=" * 60)
    print("Este script ajuda a configurar o Groq AI para o sistema contínuo")
    print("=" * 60)
    
    # Verificar instalação do Groq
    if not check_groq_installation():
        print("❌ Não foi possível instalar o Groq package")
        return 1
    
    # Obter API key
    api_key = get_groq_api_key()
    
    if api_key:
        # Salvar API key
        save_api_key_to_env(api_key)
        
        # Atualizar configuração
        update_continuous_config(True)
        
        print("\n🎉 CONFIGURAÇÃO CONCLUÍDA!")
        print("✅ Groq AI habilitado e configurado")
        print("✅ API key salva com segurança")
        print("✅ Sistema contínuo configurado")
        
    else:
        # Desabilitar Groq AI
        update_continuous_config(False)
        
        print("\n⚠️ CONFIGURAÇÃO CONCLUÍDA (SEM GROQ AI)")
        print("⚠️ Groq AI desabilitado")
        print("✅ Sistema contínuo configurado para funcionar sem AI")
    
    show_usage_instructions()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
