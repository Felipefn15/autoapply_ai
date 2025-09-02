#!/usr/bin/env python3
"""
Test Real Dynamic System - Test the real dynamic LinkedIn system
"""

import asyncio
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

async def test_real_dynamic_system():
    """Test the real dynamic LinkedIn system."""
    try:
        from linkedin_real_dynamic_system import LinkedInRealDynamicSystem
        
        print("🚀 TESTANDO SISTEMA LINKEDIN DINÂMICO REAL")
        print("=" * 60)
        
        # Initialize system
        system = LinkedInRealDynamicSystem()
        
        # Run single cycle for testing
        print("🔄 Executando ciclo de teste...")
        result = await system.run_cycle()
        
        print(f"\n📊 RESULTADOS DO TESTE:")
        print(f"   🚀 Busca Dinâmica Real: {result['dynamic_search']['applications']} aplicações")
        print(f"   📝 Posts: {result['post_applications']['applications']} aplicações")
        print(f"   📊 Total: {result['total_applications']} aplicações")
        print(f"   ✅ Sucessos: {result['total_successful']}")
        print(f"   ❌ Falhas: {result['total_failed']}")
        print(f"   ⏱️ Duração: {result['duration']:.1f}s")
        
        if result['total_applications'] > 0:
            success_rate = (result['total_successful'] / result['total_applications']) * 100
            print(f"   📈 Taxa de sucesso: {success_rate:.1f}%")
        
        print(f"\n✅ Teste concluído!")
        
        # Show detailed results
        if result['dynamic_search']['applications'] > 0:
            print(f"\n🔍 DETALHES DA BUSCA DINÂMICA:")
            print(f"   📋 Aplicações: {result['dynamic_search']['applications']}")
            print(f"   ✅ Sucessos: {result['dynamic_search']['successful']}")
            print(f"   ❌ Falhas: {result['dynamic_search']['failed']}")
        
        if result['post_applications']['applications'] > 0:
            print(f"\n📝 DETALHES DOS POSTS:")
            print(f"   📋 Aplicações: {result['post_applications']['applications']}")
            print(f"   ✅ Sucessos: {result['post_applications']['successful']}")
            print(f"   ❌ Falhas: {result['post_applications']['failed']}")
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()

async def test_dynamic_searcher_only():
    """Test only the dynamic searcher component."""
    try:
        from app.automation.linkedin_dynamic_searcher import LinkedInDynamicSearcher
        from app.main import load_config
        
        print("🔍 TESTANDO APENAS O BUSCADOR DINÂMICO")
        print("=" * 50)
        
        # Load config
        config = load_config("config/config.yaml")
        
        # Initialize searcher
        searcher = LinkedInDynamicSearcher(config)
        
        # Test search
        print("🔍 Iniciando busca dinâmica...")
        jobs = await searcher.search_jobs_dynamically(max_jobs=10)
        
        print(f"\n📊 RESULTADOS DA BUSCA:")
        print(f"   📋 Vagas encontradas: {len(jobs)}")
        
        if jobs:
            print(f"\n📝 PRIMEIRAS 5 VAGAS:")
            for i, job in enumerate(jobs[:5], 1):
                print(f"   {i}. {job['title']} - {job['company']}")
                print(f"      📍 {job['location']}")
                print(f"      🔍 Keyword: {job['keyword']}")
                print(f"      ⚡ Easy Apply: {'✅' if job.get('has_easy_apply') else '❌'}")
                print(f"      🔗 URL: {job['url']}")
                print()
        
        print(f"✅ Teste do buscador concluído!")
        
    except Exception as e:
        print(f"❌ Erro no teste do buscador: {e}")
        import traceback
        traceback.print_exc()

async def test_easy_apply_only():
    """Test only the Easy Apply component."""
    try:
        from app.automation.linkedin_easy_apply import LinkedInEasyApply
        from app.main import load_config
        
        print("⚡ TESTANDO APENAS O EASY APPLY")
        print("=" * 40)
        
        # Load config
        config = load_config("config/config.yaml")
        
        # Initialize Easy Apply
        easy_apply = LinkedInEasyApply(config)
        
        # Test search for Easy Apply jobs
        print("🔍 Buscando vagas Easy Apply...")
        jobs = await easy_apply.search_easy_apply_jobs(["react", "python"])
        
        print(f"\n📊 RESULTADOS DA BUSCA EASY APPLY:")
        print(f"   📋 Vagas Easy Apply encontradas: {len(jobs)}")
        
        if jobs:
            print(f"\n📝 PRIMEIRAS 3 VAGAS EASY APPLY:")
            for i, job in enumerate(jobs[:3], 1):
                print(f"   {i}. {job['title']} - {job['company']}")
                print(f"      📍 {job['location']}")
                print(f"      🔍 Keyword: {job['keyword']}")
                print(f"      ⚡ Easy Apply: {'✅' if job.get('has_easy_apply') else '❌'}")
                print(f"      🔗 URL: {job['url']}")
                print()
        
        print(f"✅ Teste do Easy Apply concluído!")
        
    except Exception as e:
        print(f"❌ Erro no teste do Easy Apply: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Main test function."""
    print("🧪 ESCOLHA O TESTE:")
    print("1. Sistema completo dinâmico real")
    print("2. Apenas buscador dinâmico")
    print("3. Apenas Easy Apply")
    print("4. Todos os testes")
    
    choice = input("\nDigite sua escolha (1-4): ").strip()
    
    if choice == "1":
        await test_real_dynamic_system()
    elif choice == "2":
        await test_dynamic_searcher_only()
    elif choice == "3":
        await test_easy_apply_only()
    elif choice == "4":
        print("\n🧪 EXECUTANDO TODOS OS TESTES")
        print("=" * 50)
        
        print("\n1️⃣ Testando buscador dinâmico...")
        await test_dynamic_searcher_only()
        
        print("\n2️⃣ Testando Easy Apply...")
        await test_easy_apply_only()
        
        print("\n3️⃣ Testando sistema completo...")
        await test_real_dynamic_system()
        
        print("\n✅ Todos os testes concluídos!")
    else:
        print("❌ Escolha inválida!")

if __name__ == "__main__":
    asyncio.run(main())
