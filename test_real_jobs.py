#!/usr/bin/env python3
"""
Test Real Jobs - Test with the real LinkedIn jobs you found
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

async def test_real_jobs():
    """Test with real LinkedIn jobs."""
    try:
        from app.automation.real_linkedin_applicator import RealLinkedInApplicator
        from app.main import load_config
        
        print("🚀 TESTANDO APLICAÇÕES REAIS NO LINKEDIN")
        print("=" * 50)
        
        # Load config
        config = load_config("config/config.yaml")
        
        # Real jobs you found
        real_jobs = [
            {
                'title': 'Desenvolvedor Front-end Pleno',
                'company': 'Flexge - Global English',
                'location': 'Foz do Iguaçu, Paraná, Brazil',
                'url': 'https://www.linkedin.com/jobs/view/4294117359',
                'description': 'Desenvolvedor Front-end Pleno com experiência em React, React Native e TypeScript',
                'platform': 'linkedin',
                'job_id': '4294117359',
                'has_easy_apply': True
            },
            {
                'title': 'PP - Fullstack Web Engineer',
                'company': 'Thaloz',
                'location': 'Brazil',
                'url': 'https://www.linkedin.com/jobs/view/4283401866',
                'description': 'Senior Fullstack Web Developer para desenvolvimento de aplicações web',
                'platform': 'linkedin',
                'job_id': '4283401866',
                'has_easy_apply': True
            }
        ]
        
        print(f"📋 Testando com {len(real_jobs)} vagas reais:")
        for i, job in enumerate(real_jobs, 1):
            print(f"   {i}. {job['title']} - {job['company']}")
            print(f"      URL: {job['url']}")
        
        # Initialize applicator
        applicator = RealLinkedInApplicator(config)
        
        # Test applying to first job
        print(f"\n🚀 Aplicando para primeira vaga...")
        result = await applicator.apply_to_linkedin_job(
            real_jobs[0]['url'],
            real_jobs[0]['title']
        )
        
        print(f"\n📊 RESULTADO:")
        print(f"   Sucesso: {'✅' if result.get('success') else '❌'}")
        print(f"   Método: {result.get('method', 'N/A')}")
        print(f"   Mensagem: {result.get('message', 'N/A')}")
        if result.get('error'):
            print(f"   Erro: {result.get('error')}")
        
        print(f"\n✅ Teste concluído!")
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_real_jobs())
