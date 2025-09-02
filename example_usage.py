#!/usr/bin/env python3
"""
Exemplo de Uso do Sistema Contínuo AutoApply.AI
Demonstra como usar o sistema programaticamente
"""

import asyncio
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent))

from continuous_autoapply import ContinuousAutoApplySystem, SystemConfig

async def example_basic_usage():
    """Exemplo básico de uso do sistema."""
    print("🚀 Exemplo Básico - Sistema Contínuo AutoApply.AI")
    print("=" * 60)
    
    # Configuração personalizada
    custom_config = SystemConfig(
        search_interval=60,  # 1 minuto para teste
        max_applications_per_cycle=5,
        max_concurrent_applications=2,
        application_delay=10,
        enable_groq_ai=False,  # Desabilitar para teste
        platforms=["remotive", "weworkremotely"]
    )
    
    # Inicializar sistema
    system = ContinuousAutoApplySystem()
    system.system_config = custom_config
    
    print(f"⏰ Intervalo de busca: {custom_config.search_interval}s")
    print(f"📊 Máx aplicações por ciclo: {custom_config.max_applications_per_cycle}")
    print(f"🤖 Groq AI: {'Habilitado' if custom_config.enable_groq_ai else 'Desabilitado'}")
    
    # Executar apenas um ciclo para demonstração
    print("\n🔄 Executando um ciclo de demonstração...")
    result = await system._run_application_cycle()
    
    print(f"\n📊 Resultado do ciclo:")
    print(f"   📝 Aplicações: {result.get('total_applications', 0)}")
    print(f"   ✅ Sucessos: {result.get('successful_applications', 0)}")
    print(f"   ❌ Falhas: {result.get('failed_applications', 0)}")

async def example_with_groq_ai():
    """Exemplo usando Groq AI."""
    print("\n🤖 Exemplo com Groq AI")
    print("=" * 60)
    
    # Verificar se Groq AI está disponível
    import os
    groq_key = os.getenv("GROQ_API_KEY")
    
    if not groq_key:
        print("⚠️ GROQ_API_KEY não configurada")
        print("Execute: python setup_groq.py")
        return
    
    # Configuração com Groq AI
    custom_config = SystemConfig(
        search_interval=120,
        max_applications_per_cycle=3,
        enable_groq_ai=True,
        groq_api_key=groq_key,
        groq_model="llama3-8b-8192",
        min_match_score=75.0  # Score mais alto para melhor qualidade
    )
    
    # Inicializar sistema
    system = ContinuousAutoApplySystem()
    system.system_config = custom_config
    
    print("🤖 Groq AI habilitado")
    print(f"📊 Score mínimo: {custom_config.min_match_score}")
    print(f"🧠 Modelo: {custom_config.groq_model}")
    
    # Executar ciclo com AI
    print("\n🔄 Executando ciclo com Groq AI...")
    result = await system._run_application_cycle()
    
    print(f"\n📊 Resultado com AI:")
    print(f"   📝 Aplicações: {result.get('total_applications', 0)}")
    print(f"   ✅ Sucessos: {result.get('successful_applications', 0)}")
    print(f"   ❌ Falhas: {result.get('failed_applications', 0)}")

async def example_custom_platforms():
    """Exemplo com plataformas personalizadas."""
    print("\n🌐 Exemplo com Plataformas Personalizadas")
    print("=" * 60)
    
    # Configuração focada em plataformas específicas
    custom_config = SystemConfig(
        search_interval=180,
        max_applications_per_cycle=10,
        platforms=["remotive", "email"],  # Apenas 2 plataformas
        application_delay=15,
        enable_groq_ai=False
    )
    
    system = ContinuousAutoApplySystem()
    system.system_config = custom_config
    
    print(f"🌐 Plataformas: {', '.join(custom_config.platforms)}")
    print(f"⏱️ Delay entre aplicações: {custom_config.application_delay}s")
    
    # Executar ciclo
    print("\n🔄 Executando ciclo com plataformas personalizadas...")
    result = await system._run_application_cycle()
    
    print(f"\n📊 Resultado:")
    print(f"   📝 Aplicações: {result.get('total_applications', 0)}")
    print(f"   ✅ Sucessos: {result.get('successful_applications', 0)}")
    print(f"   ❌ Falhas: {result.get('failed_applications', 0)}")

async def example_monitoring():
    """Exemplo de monitoramento."""
    print("\n📊 Exemplo de Monitoramento")
    print("=" * 60)
    
    # Simular sistema em execução
    system = ContinuousAutoApplySystem()
    
    # Simular algumas aplicações
    system.total_applications = 25
    system.successful_applications = 20
    system.failed_applications = 5
    system.cycle_count = 3
    
    print("📈 Estatísticas simuladas:")
    print(f"   🔄 Ciclos: {system.cycle_count}")
    print(f"   📝 Total aplicações: {system.total_applications}")
    print(f"   ✅ Sucessos: {system.successful_applications}")
    print(f"   ❌ Falhas: {system.failed_applications}")
    
    if system.total_applications > 0:
        success_rate = (system.successful_applications / system.total_applications) * 100
        print(f"   📈 Taxa de sucesso: {success_rate:.1f}%")

def show_configuration_examples():
    """Mostra exemplos de configuração."""
    print("\n⚙️ EXEMPLOS DE CONFIGURAÇÃO")
    print("=" * 60)
    
    print("1. Configuração Básica (sem AI):")
    print("""
    config = SystemConfig(
        search_interval=3600,  # 1 hora
        max_applications_per_cycle=20,
        enable_groq_ai=False
    )
    """)
    
    print("2. Configuração com Groq AI:")
    print("""
    config = SystemConfig(
        search_interval=1800,  # 30 minutos
        max_applications_per_cycle=15,
        enable_groq_ai=True,
        groq_api_key="gsk_...",
        min_match_score=80.0
    )
    """)
    
    print("3. Configuração Agressiva:")
    print("""
    config = SystemConfig(
        search_interval=600,   # 10 minutos
        max_applications_per_cycle=50,
        max_concurrent_applications=10,
        application_delay=5
    )
    """)
    
    print("4. Configuração Conservadora:")
    print("""
    config = SystemConfig(
        search_interval=7200,  # 2 horas
        max_applications_per_cycle=5,
        max_concurrent_applications=1,
        application_delay=60
    )
    """)

async def main():
    """Função principal com exemplos."""
    print("📚 EXEMPLOS DE USO - SISTEMA CONTÍNUO AUTOAPPLY.AI")
    print("=" * 80)
    
    try:
        # Exemplo 1: Uso básico
        await example_basic_usage()
        
        # Exemplo 2: Com Groq AI (se disponível)
        await example_with_groq_ai()
        
        # Exemplo 3: Plataformas personalizadas
        await example_custom_platforms()
        
        # Exemplo 4: Monitoramento
        await example_monitoring()
        
        # Mostrar exemplos de configuração
        show_configuration_examples()
        
        print("\n🎉 EXEMPLOS CONCLUÍDOS!")
        print("=" * 80)
        print("Para usar o sistema completo:")
        print("1. python setup_groq.py          # Configurar Groq AI")
        print("2. python start_continuous_system.py  # Iniciar sistema")
        print("3. python monitor_system.py      # Monitorar sistema")
        
    except Exception as e:
        print(f"\n❌ Erro nos exemplos: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
