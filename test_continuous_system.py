#!/usr/bin/env python3
"""
Teste do Sistema Contínuo AutoApply.AI
Verifica se todos os componentes estão funcionando corretamente
"""

import asyncio
import sys
import os
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent))

def test_imports():
    """Testa se todas as importações funcionam."""
    print("🔍 Testando importações...")
    
    try:
        import yaml
        print("   ✅ yaml")
    except ImportError as e:
        print(f"   ❌ yaml: {e}")
        return False
    
    try:
        import groq
        print("   ✅ groq")
    except ImportError as e:
        print(f"   ⚠️ groq: {e} (opcional)")
    
    try:
        import psutil
        print("   ✅ psutil")
    except ImportError as e:
        print(f"   ❌ psutil: {e}")
        return False
    
    try:
        from loguru import logger
        print("   ✅ loguru")
    except ImportError as e:
        print(f"   ❌ loguru: {e}")
        return False
    
    return True

def test_config_files():
    """Testa se os arquivos de configuração existem e são válidos."""
    print("\n📋 Testando arquivos de configuração...")
    
    config_files = [
        "config/config.yaml",
        "config/profile.yaml",
        "config/continuous_config.yaml"
    ]
    
    all_valid = True
    
    for config_file in config_files:
        if Path(config_file).exists():
            try:
                import yaml
                with open(config_file, 'r') as f:
                    yaml.safe_load(f)
                print(f"   ✅ {config_file}")
            except Exception as e:
                print(f"   ❌ {config_file}: {e}")
                all_valid = False
        else:
            print(f"   ❌ {config_file}: arquivo não encontrado")
            all_valid = False
    
    return all_valid

def test_directories():
    """Testa se os diretórios necessários existem."""
    print("\n📁 Testando diretórios...")
    
    directories = [
        "data",
        "data/logs",
        "data/applications",
        "data/matches",
        "data/jobs",
        "data/analysis"
    ]
    
    all_exist = True
    
    for directory in directories:
        if Path(directory).exists():
            print(f"   ✅ {directory}")
        else:
            print(f"   ⚠️ {directory}: criando...")
            Path(directory).mkdir(parents=True, exist_ok=True)
            print(f"   ✅ {directory} criado")
    
    return True

def test_groq_ai():
    """Testa se o Groq AI está configurado."""
    print("\n🤖 Testando Groq AI...")
    
    # Verificar API key do arquivo credentials.yaml
    groq_key = None
    try:
        import yaml
        credentials_path = Path("config/credentials.yaml")
        if credentials_path.exists():
            with open(credentials_path, 'r') as f:
                credentials = yaml.safe_load(f)
                groq_config = credentials.get('groq', {})
                groq_key = groq_config.get('api_key')
                if groq_key:
                    print("   ✅ API key encontrada em config/credentials.yaml")
    except Exception as e:
        print(f"   ⚠️ Erro ao carregar credentials.yaml: {e}")
    
    # Fallback para variável de ambiente
    if not groq_key:
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            print("   ✅ API key encontrada em variável de ambiente")
    
    if not groq_key:
        print("   ⚠️ API key do Groq não encontrada")
        print("   ℹ️ Verifique config/credentials.yaml ou execute: python setup_groq.py")
        return False
    
    try:
        import groq
        client = groq.Groq(api_key=groq_key)
        
        # Teste simples
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": "Hello"}],
            model="llama-3.1-8b-instant",
            max_tokens=5
        )
        
        if response.choices and response.choices[0].message.content:
            print("   ✅ Groq AI funcionando")
            return True
        else:
            print("   ❌ Groq AI: resposta inválida")
            return False
            
    except Exception as e:
        print(f"   ❌ Groq AI: {e}")
        return False

async def test_system_components():
    """Testa os componentes do sistema."""
    print("\n🔧 Testando componentes do sistema...")
    
    try:
        from continuous_autoapply import ContinuousAutoApplySystem, SystemConfig
        
        # Teste de configuração
        config = SystemConfig(
            search_interval=60,
            max_applications_per_cycle=1,
            enable_groq_ai=False
        )
        print("   ✅ SystemConfig")
        
        # Teste de inicialização do sistema
        system = ContinuousAutoApplySystem()
        print("   ✅ ContinuousAutoApplySystem")
        
        # Teste de busca de vagas (simulado)
        jobs = await system._search_jobs()
        print(f"   ✅ Busca de vagas: {len(jobs)} vagas encontradas")
        
        # Teste de matching
        if jobs:
            matched_jobs = await system._match_jobs_with_ai(jobs[:2])  # Apenas 2 para teste
            print(f"   ✅ Matching: {len(matched_jobs)} vagas com match")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Componentes do sistema: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_monitoring():
    """Testa o sistema de monitoramento."""
    print("\n📊 Testando sistema de monitoramento...")
    
    try:
        from monitor_system import get_system_stats, get_log_stats
        
        # Teste de estatísticas do sistema
        stats = get_system_stats()
        if 'error' not in stats:
            print("   ✅ Estatísticas do sistema")
        else:
            print(f"   ⚠️ Estatísticas do sistema: {stats['error']}")
        
        # Teste de estatísticas de logs
        log_stats = get_log_stats()
        if 'error' not in log_stats:
            print("   ✅ Estatísticas de logs")
        else:
            print(f"   ⚠️ Estatísticas de logs: {log_stats['error']}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Sistema de monitoramento: {e}")
        return False

def show_test_summary(results):
    """Mostra resumo dos testes."""
    print("\n" + "="*60)
    print("📊 RESUMO DOS TESTES")
    print("="*60)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    print(f"Total de testes: {total_tests}")
    print(f"Testes aprovados: {passed_tests}")
    print(f"Testes falharam: {total_tests - passed_tests}")
    print(f"Taxa de sucesso: {(passed_tests/total_tests)*100:.1f}%")
    
    print("\nDetalhes:")
    for test_name, result in results.items():
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"   {test_name}: {status}")
    
    if passed_tests == total_tests:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Sistema pronto para uso")
    else:
        print(f"\n⚠️ {total_tests - passed_tests} TESTE(S) FALHARAM")
        print("❌ Verifique os erros acima antes de usar o sistema")
    
    print("="*60)

async def main():
    """Função principal de teste."""
    print("🧪 TESTE DO SISTEMA CONTÍNUO AUTOAPPLY.AI")
    print("="*60)
    
    results = {}
    
    # Executar testes
    results["Importações"] = test_imports()
    results["Arquivos de Configuração"] = test_config_files()
    results["Diretórios"] = test_directories()
    results["Groq AI"] = test_groq_ai()
    results["Componentes do Sistema"] = await test_system_components()
    results["Sistema de Monitoramento"] = test_monitoring()
    
    # Mostrar resumo
    show_test_summary(results)
    
    # Retornar código de saída
    all_passed = all(results.values())
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
