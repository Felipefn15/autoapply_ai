#!/usr/bin/env python3
"""
Script melhorado para iniciar o sistema contínuo AutoApply.AI
Com melhor controle de shutdown e monitoramento
"""

import os
import sys
import signal
import asyncio
from pathlib import Path
from continuous_autoapply import ContinuousAutoApplySystem

def signal_handler(signum, frame):
    """Handler para sinais de interrupção."""
    print(f"\n🛑 Sinal {signum} recebido. Parando sistema...")
    sys.exit(0)

def check_environment():
    """Verifica se o ambiente está configurado corretamente."""
    print("🔍 Verificando ambiente...")
    
    # Verificar arquivos necessários
    required_files = [
        "config/config.yaml",
        "config/profile.yaml", 
        "config/continuous_config.yaml",
        "config/credentials.yaml"
    ]
    
    for file_path in required_files:
        if not Path(file_path).exists():
            print(f"❌ Arquivo não encontrado: {file_path}")
            return False
        print(f"✅ {file_path}")
    
    # Verificar diretórios
    required_dirs = ["data", "data/logs", "data/applications", "data/matches", "data/jobs"]
    for dir_path in required_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✅ {dir_path}")
    
    return True

async def main():
    """Função principal."""
    print("🚀 SISTEMA CONTÍNUO AUTOAPPLY.AI - VERSÃO MELHORADA")
    print("=" * 60)
    
    # Verificar ambiente
    if not check_environment():
        print("❌ Ambiente não configurado corretamente")
        return
    
    # Configurar handlers de sinal
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Inicializar sistema
        print("\n🔄 Inicializando sistema...")
        system = ContinuousAutoApplySystem()
        
        print("✅ Sistema inicializado com sucesso!")
        print(f"⏰ Intervalo de busca: {system.system_config.search_interval}s")
        print(f"📊 Máx aplicações por ciclo: {system.system_config.max_applications_per_cycle}")
        print(f"🤖 Groq AI: {'Habilitado' if system.groq_ai else 'Desabilitado'}")
        
        print("\n" + "=" * 60)
        print("🎯 SISTEMA RODANDO - Pressione Ctrl+C para parar")
        print("=" * 60)
        
        # Executar sistema
        await system.run_continuous()
        
    except KeyboardInterrupt:
        print("\n🛑 Sistema interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro crítico: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n👋 Sistema finalizado")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Sistema finalizado pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        sys.exit(1)
