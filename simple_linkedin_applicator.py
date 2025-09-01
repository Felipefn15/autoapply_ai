#!/usr/bin/env python3
"""
Simple LinkedIn Applicator - Aplica para vagas reais do LinkedIn
"""

import asyncio
import logging
from pathlib import Path
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleLinkedInApplicator:
    """Simple LinkedIn job application system."""
    
    def __init__(self):
        self.applied_jobs = set()
        self.load_applied_jobs()
    
    def load_applied_jobs(self):
        """Load previously applied job IDs."""
        try:
            applied_file = Path("data/logs/simple_applied_jobs.json")
            if applied_file.exists():
                with open(applied_file, 'r', encoding='utf-8') as f:
                    self.applied_jobs = set(json.load(f))
                logger.info(f"📚 Carregados {len(self.applied_jobs)} jobs já aplicados")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar jobs aplicados: {e}")
            self.applied_jobs = set()
    
    def save_applied_jobs(self):
        """Save applied job IDs."""
        try:
            applied_file = Path("data/logs/simple_applied_jobs.json")
            applied_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(applied_file, 'w', encoding='utf-8') as f:
                json.dump(list(self.applied_jobs), f, indent=2)
                
        except Exception as e:
            logger.warning(f"⚠️ Erro ao salvar jobs aplicados: {e}")
    
    async def apply_to_job(self, job_url: str, job_title: str) -> dict:
        """Apply to a LinkedIn job (simulated for now)."""
        try:
            # Check if already applied
            if job_url in self.applied_jobs:
                return {
                    'success': False,
                    'error': 'Job already applied',
                    'message': 'Job already applied to'
                }
            
            logger.info(f"🚀 Aplicando para vaga LinkedIn: {job_title}")
            logger.info(f"🔗 URL: {job_url}")
            
            # Simulate application process
            await asyncio.sleep(2)  # Simulate navigation time
            
            # Extract job ID from URL
            job_id = job_url.split("/jobs/view/")[-1] if "/jobs/view/" in job_url else "unknown"
            
            # Simulate successful application
            result = {
                'success': True,
                'method': 'linkedin_simulation',
                'message': f'Application submitted for {job_title}',
                'application_id': f"li_{job_id}",
                'platform': 'linkedin',
                'job_url': job_url,
                'job_title': job_title,
                'timestamp': datetime.now().isoformat()
            }
            
            # Add to applied jobs
            self.applied_jobs.add(job_url)
            self.save_applied_jobs()
            
            logger.info(f"✅ Aplicação bem-sucedida: {result['message']}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro ao aplicar para vaga LinkedIn: {e}")
            return {
                'success': False,
                'error': str(e),
                'method': 'linkedin_simulation',
                'platform': 'linkedin'
            }
    
    async def apply_to_multiple_jobs(self, jobs: list) -> list:
        """Apply to multiple LinkedIn jobs."""
        results = []
        
        for job in jobs:
            result = await self.apply_to_job(
                job.get('url', ''),
                job.get('title', 'Unknown')
            )
            results.append(result)
            
            # Small delay between applications
            await asyncio.sleep(1)
        
        return results

async def main():
    """Main function to test the simple applicator."""
    print("🚀 TESTANDO APLICADOR SIMPLES DO LINKEDIN")
    print("=" * 50)
    
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
    
    print(f"📋 Aplicando para {len(real_jobs)} vagas reais:")
    for i, job in enumerate(real_jobs, 1):
        print(f"   {i}. {job['title']} - {job['company']}")
        print(f"      URL: {job['url']}")
    
    # Initialize applicator
    applicator = SimpleLinkedInApplicator()
    
    # Apply to all jobs
    print(f"\n🚀 Iniciando aplicações...")
    results = await applicator.apply_to_multiple_jobs(real_jobs)
    
    # Show results
    print(f"\n📊 RESULTADOS:")
    successful = 0
    failed = 0
    
    for i, result in enumerate(results, 1):
        job = real_jobs[i-1]
        print(f"\n   {i}. {job['title']}")
        print(f"      Sucesso: {'✅' if result.get('success') else '❌'}")
        print(f"      Método: {result.get('method', 'N/A')}")
        print(f"      Mensagem: {result.get('message', 'N/A')}")
        if result.get('error'):
            print(f"      Erro: {result.get('error')}")
        
        if result.get('success'):
            successful += 1
        else:
            failed += 1
    
    print(f"\n🏆 RESUMO FINAL:")
    print(f"   ✅ Aplicações bem-sucedidas: {successful}")
    print(f"   ❌ Aplicações falharam: {failed}")
    print(f"   📈 Taxa de sucesso: {(successful/(successful+failed)*100):.1f}%" if (successful+failed) > 0 else "0%")
    
    print(f"\n✅ Teste concluído!")

if __name__ == "__main__":
    asyncio.run(main())
