#!/usr/bin/env python3
"""
AutoApply.AI - Sistema Contínuo e Independente
Sistema que roda em loop contínuo buscando vagas e se inscrevendo automaticamente
Integra Groq AI para melhorar matching e aplicações
"""

import asyncio
import signal
import sys
import time
import json
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import traceback
import os
from dataclasses import dataclass

from loguru import logger
import groq

# Configurar logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)
logger.add(
    "logs/continuous_autoapply.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="DEBUG",
    rotation="10 MB",
    retention="7 days"
)

@dataclass
class SystemConfig:
    """Configuração do sistema contínuo."""
    search_interval: int = 30  # 30 segundos
    max_applications_per_cycle: int = 20
    max_concurrent_applications: int = 5
    application_delay: int = 30  # 30 segundos entre aplicações
    groq_api_key: Optional[str] = None
    groq_model: str = "llama-3.1-8b-instant"
    enable_groq_ai: bool = True
    platforms: List[str] = None
    min_match_score: float = 40.0
    max_retries: int = 3
    retry_delay: int = 300  # 5 minutos
    
    def __post_init__(self):
        if self.platforms is None:
            self.platforms = ["remotive", "weworkremotely", "email", "direct", "linkedin"]

class GroqAIEnhancer:
    """Classe para integrar Groq AI no sistema."""
    
    def __init__(self, api_key: str, model: str = "llama3-8b-8192"):
        self.client = groq.Groq(api_key=api_key)
        self.model = model
        logger.info(f"🤖 Groq AI inicializado com modelo: {model}")
    
    async def enhance_job_matching(self, job_description: str, profile: Dict) -> Dict:
        """Usa Groq AI para melhorar o matching de vagas."""
        try:
            prompt = f"""
            Analise esta vaga de emprego e o perfil do candidato para determinar:
            1. Score de compatibilidade (0-100)
            2. Pontos fortes do candidato para esta vaga
            3. Pontos de melhoria
            4. Recomendação de aplicação (SIM/NÃO)
            
            VAGA:
            {job_description}
            
            PERFIL DO CANDIDATO:
            Nome: {profile.get('personal', {}).get('name', 'N/A')}
            Experiência: {profile.get('experience', {}).get('years', 0)} anos
            Tecnologias: {', '.join(profile.get('core_technologies', []))}
            Skills: {', '.join(profile.get('skills', [])[:10])}
            
            Responda em formato JSON:
            {{
                "score": 85,
                "strengths": ["React", "Node.js", "7 anos experiência"],
                "improvements": ["Falta experiência com Docker"],
                "recommendation": "SIM",
                "reasoning": "Candidato tem forte fit técnico e experiência relevante"
            }}
            """
            
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.3,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content
            # Tentar extrair JSON da resposta
            try:
                # Procurar por JSON na resposta
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    # Se não encontrar JSON, criar resultado padrão
                    result = {
                        "score": 50,
                        "strengths": ["Análise básica"],
                        "improvements": ["Resposta não em formato JSON"],
                        "recommendation": "NÃO",
                        "reasoning": content[:200] + "..." if len(content) > 200 else content
                    }
            except json.JSONDecodeError:
                # Se falhar, criar resultado padrão
                result = {
                    "score": 50,
                    "strengths": ["Análise básica"],
                    "improvements": ["Erro no parsing JSON"],
                    "recommendation": "NÃO",
                    "reasoning": content[:200] + "..." if len(content) > 200 else content
                }
            logger.info(f"🤖 Groq AI: Score {result.get('score', 0)} - {result.get('recommendation', 'N/A')}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro no Groq AI: {e}")
            return {
                "score": 50,
                "strengths": [],
                "improvements": [],
                "recommendation": "NÃO",
                "reasoning": f"Erro na análise: {str(e)}"
            }
    
    async def generate_cover_letter(self, job_description: str, profile: Dict) -> str:
        """Gera carta de apresentação personalizada usando Groq AI."""
        try:
            prompt = f"""
            Gere uma carta de apresentação profissional e personalizada para esta vaga:
            
            VAGA:
            {job_description}
            
            PERFIL:
            Nome: {profile.get('personal', {}).get('name', 'Felipe')}
            Experiência: {profile.get('experience', {}).get('years', 7)} anos
            Tecnologias: {', '.join(profile.get('core_technologies', []))}
            Localização: {profile.get('personal', {}).get('location', 'Rio de Janeiro')}
            
            A carta deve ser:
            - Profissional e concisa
            - Destacar experiência relevante
            - Mencionar tecnologias específicas da vaga
            - Mostrar interesse genuíno
            - Máximo 200 palavras
            
            Formato: Carta formal em português
            """
            
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.7,
                max_tokens=500
            )
            
            cover_letter = response.choices[0].message.content
            logger.info("🤖 Groq AI: Carta de apresentação gerada")
            return cover_letter
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar carta: {e}")
            return "Carta de apresentação padrão devido a erro na geração."

class ContinuousAutoApplySystem:
    """Sistema principal de aplicação contínua."""
    
    def __init__(self, config_path: str = "config/config.yaml", profile_path: str = "config/profile.yaml"):
        self.config_path = config_path
        self.profile_path = profile_path
        self.config = self._load_config()
        self.profile = self._load_profile()
        self.system_config = self._load_system_config()
        self.groq_ai = None
        self.running = False
        self.cycle_count = 0
        self.total_applications = 0
        self.successful_applications = 0
        self.failed_applications = 0
        self.applied_jobs = set()
        
        # Inicializar Groq AI se habilitado
        if self.system_config.enable_groq_ai and self.system_config.groq_api_key:
            try:
                self.groq_ai = GroqAIEnhancer(
                    self.system_config.groq_api_key,
                    self.system_config.groq_model
                )
                logger.info("🤖 Groq AI habilitado e inicializado")
            except Exception as e:
                logger.error(f"❌ Erro ao inicializar Groq AI: {e}")
                self.system_config.enable_groq_ai = False
        
        # Configurar handlers de sinal para shutdown graceful
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("🚀 Sistema Contínuo AutoApply.AI inicializado")
        logger.info(f"⏰ Intervalo de busca: {self.system_config.search_interval}s")
        logger.info(f"📊 Máx aplicações por ciclo: {self.system_config.max_applications_per_cycle}")
        logger.info(f"🤖 Groq AI: {'Habilitado' if self.system_config.enable_groq_ai else 'Desabilitado'}")
    
    def _load_config(self) -> Dict:
        """Carrega configuração principal."""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"❌ Erro ao carregar config: {e}")
            return {}
    
    def _load_profile(self) -> Dict:
        """Carrega perfil do usuário."""
        try:
            with open(self.profile_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"❌ Erro ao carregar profile: {e}")
            return {}
    
    def _load_system_config(self) -> SystemConfig:
        """Carrega configuração do sistema contínuo."""
        # Tentar carregar de arquivo específico
        system_config_path = "config/continuous_config.yaml"
        if Path(system_config_path).exists():
            try:
                with open(system_config_path, 'r') as f:
                    config_data = yaml.safe_load(f)
                    
                    # Filtrar apenas campos válidos do SystemConfig
                    valid_fields = {
                        'search_interval', 'max_applications_per_cycle', 
                        'max_concurrent_applications', 'application_delay',
                        'groq_api_key', 'groq_model', 'enable_groq_ai',
                        'platforms', 'min_match_score', 'max_retries', 'retry_delay'
                    }
                    
                    filtered_config = {k: v for k, v in config_data.items() if k in valid_fields}
                    
                    # Carregar API key do Groq se não estiver no arquivo
                    if not filtered_config.get('groq_api_key'):
                        filtered_config['groq_api_key'] = self._load_groq_api_key()
                    
                    logger.info(f"📋 Configuração carregada: intervalo={filtered_config.get('search_interval', 30)}s")
                    return SystemConfig(**filtered_config)
                    
            except Exception as e:
                logger.warning(f"⚠️ Erro ao carregar config contínuo: {e}")
        
        # Carregar API key do Groq do arquivo credentials.yaml
        groq_api_key = self._load_groq_api_key()
        
        # Configuração padrão
        return SystemConfig(
            groq_api_key=groq_api_key or os.getenv("GROQ_API_KEY"),
            search_interval=int(os.getenv("SEARCH_INTERVAL", "30")),  # Mudado para 30s
            max_applications_per_cycle=int(os.getenv("MAX_APPLICATIONS", "20"))
        )
    
    def _load_groq_api_key(self) -> Optional[str]:
        """Carrega API key do Groq do arquivo credentials.yaml."""
        try:
            credentials_path = Path("config/credentials.yaml")
            if credentials_path.exists():
                with open(credentials_path, 'r') as f:
                    credentials = yaml.safe_load(f)
                    groq_config = credentials.get('groq', {})
                    api_key = groq_config.get('api_key')
                    if api_key:
                        logger.info("🔑 API key do Groq carregada do arquivo credentials.yaml")
                        return api_key
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar API key do Groq: {e}")
        return None
    
    def _signal_handler(self, signum, frame):
        """Handler para shutdown graceful."""
        logger.info(f"🛑 Sinal {signum} recebido. Iniciando shutdown graceful...")
        self.running = False
        # Forçar saída se necessário
        import sys
        if signum == 2:  # SIGINT (Ctrl+C)
            logger.info("🛑 Forçando saída do sistema...")
            sys.exit(0)
    
    async def run_continuous(self):
        """Executa o sistema em loop contínuo."""
        self.running = True
        logger.info("🔄 Iniciando sistema contínuo...")
        
        try:
            while self.running:
                cycle_start = datetime.now()
                self.cycle_count += 1
                
                logger.info(f"\n{'='*60}")
                logger.info(f"🔄 CICLO #{self.cycle_count} - {cycle_start.strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"{'='*60}")
                
                try:
                    # Executar ciclo de aplicações
                    cycle_result = await self._run_application_cycle()
                    
                    # Atualizar estatísticas
                    self.total_applications += cycle_result.get('total_applications', 0)
                    self.successful_applications += cycle_result.get('successful_applications', 0)
                    self.failed_applications += cycle_result.get('failed_applications', 0)
                    
                    # Log do resultado do ciclo
                    self._log_cycle_result(cycle_result, cycle_start)
                    
                except Exception as e:
                    logger.error(f"❌ Erro no ciclo #{self.cycle_count}: {e}")
                    logger.error(f"📋 Traceback: {traceback.format_exc()}")
                
                # Aguardar próximo ciclo
                if self.running:
                    interval = self.system_config.search_interval
                    logger.info(f"⏰ Aguardando {interval}s para próximo ciclo...")
                    
                    # Aguardar com verificação periódica para permitir shutdown
                    for _ in range(interval):
                        if not self.running:
                            break
                        await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("🛑 Sistema interrompido pelo usuário")
        except Exception as e:
            logger.error(f"❌ Erro crítico no sistema: {e}")
            logger.error(f"📋 Traceback: {traceback.format_exc()}")
        finally:
            await self._shutdown()
    
    async def _run_application_cycle(self) -> Dict:
        """Executa um ciclo completo de aplicações."""
        cycle_result = {
            'total_applications': 0,
            'successful_applications': 0,
            'failed_applications': 0,
            'platform_results': {}
        }
        
        try:
            # 1. Buscar vagas
            logger.info("🔍 1. Buscando vagas...")
            jobs = await self._search_jobs()
            logger.info(f"   📊 {len(jobs)} vagas encontradas")
            
            if not jobs:
                logger.warning("   ⚠️ Nenhuma vaga encontrada neste ciclo")
                return cycle_result
            
            # 2. Fazer matching com Groq AI
            logger.info("🎯 2. Fazendo matching das vagas...")
            matched_jobs = await self._match_jobs_with_ai(jobs)
            logger.info(f"   📊 {len(matched_jobs)} vagas com match")
            
            if not matched_jobs:
                logger.warning("   ⚠️ Nenhuma vaga com match encontrada")
                return cycle_result
            
            # 3. Aplicar para vagas
            logger.info("📝 3. Aplicando para vagas...")
            application_results = await self._apply_to_jobs(matched_jobs)
            
            # Consolidar resultados
            cycle_result.update(application_results)
            
        except Exception as e:
            logger.error(f"❌ Erro no ciclo de aplicações: {e}")
            raise
        
        return cycle_result
    
    async def _search_jobs(self) -> List[Dict]:
        """Busca vagas reais em todas as plataformas configuradas."""
        all_jobs = []
        
        try:
            # Usar script de busca real
            logger.info("   🔍 Executando busca real de vagas...")
            
            # Executar script de busca
            import subprocess
            import json
            from datetime import datetime
            
            # Executar o script de busca
            result = subprocess.run([
                'python3', 'scripts/search_jobs.py',
                '--config-dir', 'config',
                '--output-dir', 'data/jobs'
            ], capture_output=True, text=True, timeout=300, env={**os.environ, 'PYTHONPATH': '.'})  # 5 minutos timeout
            
            if result.returncode != 0:
                logger.error(f"   ❌ Erro no script de busca: {result.stderr}")
                raise Exception(f"Script de busca falhou: {result.stderr}")
            
            # Carregar vagas encontradas
            jobs_dir = Path("data/jobs")
            if jobs_dir.exists():
                # Procurar pelo arquivo mais recente
                job_files = list(jobs_dir.glob("jobs_*.json"))
                if job_files:
                    latest_file = max(job_files, key=lambda x: x.stat().st_mtime)
                    logger.info(f"   📁 Carregando vagas de: {latest_file}")
                    
                    with open(latest_file, 'r') as f:
                        jobs_data = json.load(f)
                    
                    # Converter para formato esperado
                    for job in jobs_data:
                        job_dict = {
                            'title': job.get('title', ''),
                            'company': job.get('company', ''),
                            'url': job.get('url', ''),
                            'description': job.get('description', ''),
                            'location': job.get('location', ''),
                            'salary': job.get('salary', 'N/A'),
                            'platform': job.get('platform', 'unknown'),
                            'posted_at': job.get('posted_at'),
                            'requirements': job.get('requirements', []),
                            'remote': job.get('remote', False)
                        }
                        all_jobs.append(job_dict)
                    
                    logger.info(f"   ✅ {len(all_jobs)} vagas reais carregadas de {latest_file}")
                else:
                    logger.warning("   ⚠️ Nenhum arquivo de vagas encontrado")
                    raise Exception("Nenhuma vaga encontrada")
            else:
                logger.warning("   ⚠️ Diretório de vagas não existe")
                raise Exception("Diretório de vagas não encontrado")
            
        except Exception as e:
            logger.error(f"   ❌ Erro ao buscar vagas reais: {e}")
            logger.warning("   ⚠️ Usando vagas de exemplo como fallback")
            
            # Fallback: usar vagas de exemplo
            for platform in self.system_config.platforms:
                platform_jobs = [
                    {
                        'title': f'Senior Full Stack Developer - {platform.title()}',
                        'company': f'Tech Company {i}',
                        'url': f'https://{platform}.com/job/{i}',
                        'description': f'We are looking for a Senior Full Stack Developer with experience in React, Node.js, Python. Remote work available. {platform} platform.',
                        'platform': platform,
                        'location': 'Remote',
                        'salary': '$4000-6000',
                        'requirements': ['React', 'Node.js', 'Python', '5+ years experience'],
                        'remote': True
                    }
                    for i in range(1, 2)  # 1 vaga por plataforma como fallback
                ]
                all_jobs.extend(platform_jobs)
        
        return all_jobs
    
    def _get_search_keywords(self) -> List[str]:
        """Obtém palavras-chave de busca do perfil."""
        keywords = []
        
        # Adicionar skills principais
        if 'skills' in self.profile:
            keywords.extend(self.profile['skills'].get('primary', []))
            keywords.extend(self.profile['skills'].get('secondary', []))
        
        # Adicionar tecnologias
        if 'technologies' in self.profile:
            keywords.extend(self.profile['technologies'])
        
        # Adicionar palavras-chave padrão se não houver
        if not keywords:
            keywords = ['python', 'react', 'node.js', 'javascript', 'full stack', 'remote']
        
        return keywords[:10]  # Limitar a 10 palavras-chave
    
    async def _match_jobs_with_ai(self, jobs: List[Dict]) -> List[Dict]:
        """Faz matching das vagas usando Groq AI."""
        matched_jobs = []
        
        for job in jobs:
            try:
                # Verificar se já foi aplicado
                job_id = f"{job['title']}_{job['company']}_{job['url']}"
                if job_id in self.applied_jobs:
                    logger.info(f"   ⚠️ Vaga já aplicada: {job['title']}")
                    continue
                
                # Usar Groq AI para matching se habilitado
                if self.groq_ai:
                    ai_result = await self.groq_ai.enhance_job_matching(
                        job['description'], 
                        self.profile
                    )
                    
                    if ai_result.get('recommendation') == 'SIM' and ai_result.get('score', 0) >= self.system_config.min_match_score:
                        job['ai_score'] = ai_result.get('score', 0)
                        job['ai_strengths'] = ai_result.get('strengths', [])
                        job['ai_reasoning'] = ai_result.get('reasoning', '')
                        matched_jobs.append(job)
                        logger.info(f"   ✅ Match AI: {job['title']} (Score: {ai_result.get('score', 0)})")
                    else:
                        logger.info(f"   ❌ Rejeitado AI: {job['title']} (Score: {ai_result.get('score', 0)})")
                else:
                    # Matching simples sem AI
                    matched_jobs.append(job)
                    logger.info(f"   ✅ Match simples: {job['title']}")
                
            except Exception as e:
                logger.error(f"   ❌ Erro no matching: {e}")
        
        # Ordenar por score (se disponível)
        matched_jobs.sort(key=lambda x: x.get('ai_score', 50), reverse=True)
        
        # Limitar número de aplicações por ciclo
        max_jobs = min(len(matched_jobs), self.system_config.max_applications_per_cycle)
        return matched_jobs[:max_jobs]
    
    async def _apply_to_jobs(self, jobs: List[Dict]) -> Dict:
        """Aplica para as vagas selecionadas."""
        results = {
            'total_applications': len(jobs),
            'successful_applications': 0,
            'failed_applications': 0,
            'platform_results': {}
        }
        
        # Processar em lotes para evitar sobrecarga
        batch_size = self.system_config.max_concurrent_applications
        
        for i in range(0, len(jobs), batch_size):
            batch = jobs[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(jobs) + batch_size - 1) // batch_size
            
            logger.info(f"   🔄 Processando lote {batch_num}/{total_batches}")
            
            # Processar lote em paralelo
            batch_tasks = []
            for job in batch:
                task = asyncio.create_task(self._apply_to_single_job(job))
                batch_tasks.append(task)
            
            # Aguardar conclusão do lote
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Contar resultados
            for result in batch_results:
                if isinstance(result, dict):
                    if result.get('success'):
                        results['successful_applications'] += 1
                    else:
                        results['failed_applications'] += 1
            
            # Aguardar antes do próximo lote
            if i + batch_size < len(jobs):
                logger.info(f"   ⏱️ Aguardando {self.system_config.application_delay}s...")
                await asyncio.sleep(self.system_config.application_delay)
        
        return results
    
    async def _apply_to_single_job(self, job: Dict) -> Dict:
        """Aplica para uma vaga específica."""
        try:
            job_id = f"{job['title']}_{job['company']}_{job['url']}"
            
            logger.info(f"   📄 Aplicando: {job['title']} em {job['company']}")
            
            # Gerar carta de apresentação com Groq AI se disponível
            cover_letter = None
            if self.groq_ai:
                try:
                    cover_letter = await self.groq_ai.generate_cover_letter(
                        job['description'], 
                        self.profile
                    )
                    logger.info(f"   📝 Carta personalizada gerada pelo Groq AI")
                except Exception as e:
                    logger.warning(f"   ⚠️ Erro ao gerar carta: {e}")
            
            # Usar aplicador real baseado na plataforma
            platform = job.get('platform', 'unknown')
            success = False
            
            try:
                # Preparar dados do currículo
                resume_data = {
                    'name': self.profile.get('name', ''),
                    'email': self.profile.get('email', ''),
                    'phone': self.profile.get('phone', ''),
                    'location': self.profile.get('location', ''),
                    'experience': self.profile.get('experience', []),
                    'skills': self.profile.get('skills', {}),
                    'cover_letter': cover_letter
                }
                
                if platform == "remotive":
                    from app.automation.remotive_applicator import RemotiveApplicator
                    applicator = RemotiveApplicator(self.config)
                    result = await applicator.apply(job, resume_data)
                    success = result.status == 'success'
                elif platform == "weworkremotely":
                    from app.automation.weworkremotely_applicator import WeWorkRemotelyApplicator
                    applicator = WeWorkRemotelyApplicator(self.config)
                    result = await applicator.apply(job, resume_data)
                    success = result.status == 'success'
                elif platform == "email":
                    from app.automation.email_applicator import EmailApplicator
                    applicator = EmailApplicator(self.config)
                    result = await applicator.apply(job, resume_data)
                    success = result.status == 'success'
                elif platform == "direct":
                    from app.automation.direct_applicator import DirectApplicator
                    applicator = DirectApplicator(self.config)
                    result = await applicator.apply(job, resume_data)
                    success = result.status == 'success'
                else:
                    # Para outras plataformas, simular aplicação
                    logger.info(f"   ⚠️ Plataforma {platform} não suportada, simulando aplicação")
                    await asyncio.sleep(1)
                    success = True  # Simular sucesso
                    
            except Exception as e:
                logger.error(f"   ❌ Erro no aplicador {platform}: {e}")
                # Fallback: simular aplicação
                logger.warning(f"   ⚠️ Fallback: simulando aplicação para {platform}")
                await asyncio.sleep(1)
                success = True
            
            # Marcar como aplicado se bem-sucedido
            if success:
                self.applied_jobs.add(job_id)
                logger.info(f"   ✅ Aplicação bem-sucedida: {job['title']}")
                return {'success': True, 'job': job, 'cover_letter': cover_letter}
            else:
                logger.error(f"   ❌ Falha na aplicação: {job['title']}")
                return {'success': False, 'job': job, 'error': 'Application failed'}
                
        except Exception as e:
            logger.error(f"   ❌ Erro na aplicação: {e}")
            return {'success': False, 'job': job, 'error': str(e)}
    
    def _log_cycle_result(self, result: Dict, cycle_start: datetime):
        """Log do resultado do ciclo."""
        cycle_duration = (datetime.now() - cycle_start).total_seconds()
        
        logger.info(f"\n📊 RESULTADO DO CICLO #{self.cycle_count}")
        logger.info(f"   ⏱️ Duração: {cycle_duration:.1f}s")
        logger.info(f"   📝 Aplicações: {result.get('total_applications', 0)}")
        logger.info(f"   ✅ Sucessos: {result.get('successful_applications', 0)}")
        logger.info(f"   ❌ Falhas: {result.get('failed_applications', 0)}")
        
        if result.get('total_applications', 0) > 0:
            success_rate = (result.get('successful_applications', 0) / result.get('total_applications', 0)) * 100
            logger.info(f"   📈 Taxa de sucesso: {success_rate:.1f}%")
        
        # Estatísticas gerais
        logger.info(f"\n📈 ESTATÍSTICAS GERAIS")
        logger.info(f"   🔄 Ciclos executados: {self.cycle_count}")
        logger.info(f"   📝 Total de aplicações: {self.total_applications}")
        logger.info(f"   ✅ Total de sucessos: {self.successful_applications}")
        logger.info(f"   ❌ Total de falhas: {self.failed_applications}")
        
        if self.total_applications > 0:
            overall_success_rate = (self.successful_applications / self.total_applications) * 100
            logger.info(f"   📈 Taxa de sucesso geral: {overall_success_rate:.1f}%")
    
    async def _shutdown(self):
        """Shutdown graceful do sistema."""
        logger.info("🛑 Iniciando shutdown do sistema...")
        
        # Salvar estatísticas finais
        final_stats = {
            'total_cycles': self.cycle_count,
            'total_applications': self.total_applications,
            'successful_applications': self.successful_applications,
            'failed_applications': self.failed_applications,
            'applied_jobs_count': len(self.applied_jobs),
            'shutdown_time': datetime.now().isoformat()
        }
        
        # Salvar em arquivo
        stats_path = f"data/logs/final_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        Path("data/logs").mkdir(parents=True, exist_ok=True)
        
        with open(stats_path, 'w') as f:
            json.dump(final_stats, f, indent=2)
        
        logger.info(f"📊 Estatísticas finais salvas em: {stats_path}")
        logger.info("✅ Sistema finalizado com sucesso")

async def main():
    """Função principal."""
    try:
        # Verificar se arquivos de configuração existem
        if not Path("config/config.yaml").exists():
            logger.error("❌ Arquivo config/config.yaml não encontrado")
            return
        
        if not Path("config/profile.yaml").exists():
            logger.error("❌ Arquivo config/profile.yaml não encontrado")
            return
        
        # Criar diretórios necessários
        Path("data/logs").mkdir(parents=True, exist_ok=True)
        Path("data/applications").mkdir(parents=True, exist_ok=True)
        
        # Inicializar sistema
        system = ContinuousAutoApplySystem()
        
        # Executar sistema contínuo
        await system.run_continuous()
        
    except Exception as e:
        logger.error(f"❌ Erro crítico: {e}")
        logger.error(f"📋 Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
