#!/usr/bin/env python3
"""
Test LinkedIn System - Test the unified LinkedIn system
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

async def test_linkedin_system():
    """Test the LinkedIn unified system."""
    try:
        from linkedin_unified_system import LinkedInUnifiedSystem
        
        print("🚀 TESTANDO SISTEMA LINKEDIN UNIFICADO")
        print("=" * 50)
        
        # Initialize system
        system = LinkedInUnifiedSystem()
        
        # Run single cycle for testing
        print("🔄 Executando ciclo de teste...")
        result = await system.run_cycle()
        
        print(f"\n📊 RESULTADOS DO TESTE:")
        print(f"   🚀 Easy Apply: {result['easy_apply']['applications']} aplicações")
        print(f"   📝 Posts: {result['post_applications']['applications']} aplicações")
        print(f"   📊 Total: {result['total_applications']} aplicações")
        print(f"   ✅ Sucessos: {result['total_successful']}")
        print(f"   ❌ Falhas: {result['total_failed']}")
        print(f"   ⏱️ Duração: {result['duration']:.1f}s")
        
        if result['total_applications'] > 0:
            success_rate = (result['total_successful'] / result['total_applications']) * 100
            print(f"   📈 Taxa de sucesso: {success_rate:.1f}%")
        
        print(f"\n✅ Teste concluído!")
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_linkedin_system())
