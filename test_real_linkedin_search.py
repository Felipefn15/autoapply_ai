#!/usr/bin/env python3
"""
Test Real LinkedIn Search - Test the real LinkedIn job searcher
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

async def test_real_linkedin_search():
    """Test the real LinkedIn job searcher."""
    try:
        from app.automation.real_linkedin_searcher import RealLinkedInSearcher
        from app.main import load_config
        
        print("🚀 TESTANDO BUSCADOR REAL DO LINKEDIN")
        print("=" * 50)
        
        # Load config
        config = load_config("config/config.yaml")
        
        # Initialize searcher
        searcher = RealLinkedInSearcher(config)
        
        # Test search
        print("🔍 Buscando vagas reais no LinkedIn...")
        jobs = await searcher.search_linkedin_jobs(["react", "python"])
        
        print(f"\n📊 RESULTADOS:")
        print(f"   Total de vagas encontradas: {len(jobs)}")
        
        if jobs:
            print(f"\n📋 PRIMEIRAS 5 VAGAS:")
            for i, job in enumerate(jobs[:5], 1):
                print(f"\n   {i}. {job.get('title', 'Unknown')}")
                print(f"      Empresa: {job.get('company', 'Unknown')}")
                print(f"      Local: {job.get('location', 'Unknown')}")
                print(f"      URL: {job.get('url', 'N/A')}")
                print(f"      Easy Apply: {'✅' if job.get('has_easy_apply') else '❌'}")
                print(f"      Keyword: {job.get('keyword', 'Unknown')}")
        
        print(f"\n✅ Teste concluído com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_real_linkedin_search())
