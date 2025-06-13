#!/usr/bin/env python3
"""
AutoApply.AI - Main Application
"""
import os
import sys
import asyncio
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from loguru import logger

def load_config(config_path: str = "config/config.yaml") -> Dict:
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        logger.info("Loaded configuration")
        return config
    except Exception as e:
        logger.error(f"Error loading config: {str(e)}")
        return {}

async def run_script(script_name: str, config_path: str = "config/config.yaml", 
                    resume_path: str = "data/resumes/resume.pdf",
                    matches_dir: str = "data/matches") -> bool:
    """Run a script and handle its output."""
    try:
        logger.info(f"Running {script_name}")
        
        # Ensure required directories exist
        Path("data/matches").mkdir(parents=True, exist_ok=True)
        Path("data/applications").mkdir(parents=True, exist_ok=True)
        Path("data/analysis").mkdir(parents=True, exist_ok=True)
        
        # Build command with arguments
        cmd = ["python", f"scripts/{script_name}.py"]
        
        # Add common arguments
        cmd.extend(["--config", config_path])
        
        # Add script-specific arguments
        if script_name in ["match_jobs", "apply_jobs"]:
            cmd.extend(["--matches-dir", matches_dir])
            
        if script_name == "apply_jobs":
            cmd.extend(["--resume", resume_path])
            
        # Run script and capture output
        process = subprocess.run(
            cmd,
            check=True,
            text=True,
            capture_output=True
        )
        
        # Log output
        if process.stdout:
            logger.info(process.stdout)
        if process.stderr:
            logger.warning(process.stderr)
            
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running {script_name}: {str(e)}")
        if e.output:
            logger.error(e.output)
        if e.stderr:
            logger.error(e.stderr)
        raise
        
    except Exception as e:
        logger.error(f"Error running {script_name}: {str(e)}")
        raise

def save_jobs(jobs: List[Dict], jobs_dir: str) -> str:
    """
    Save jobs to a JSON file.
    
    Args:
        jobs: List of jobs to save
        jobs_dir: Directory to save jobs in
        
    Returns:
        Path to saved jobs file
    """
    try:
        # Create jobs directory if it doesn't exist
        jobs_dir = Path(jobs_dir)
        jobs_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"jobs_{timestamp}.json"
        filepath = jobs_dir / filename
        
        # Save jobs
        with open(filepath, 'w') as f:
            json.dump(jobs, f, indent=2)
            
        logger.info(f"Saved {len(jobs)} jobs to {filepath}")
        return str(filepath)
        
    except Exception as e:
        logger.error(f"Error saving jobs: {str(e)}")
        raise

def print_menu():
    """Print the main menu."""
    print("\nAutoApply.AI - Automatização de Candidaturas")
    print("=" * 40)
    print("1. Buscar Vagas")
    print("2. Combinar Vagas com Perfil")
    print("3. Candidatar-se às Vagas")
    print("4. Visualizar Análise de Vagas")
    print("5. Executar Fluxo Completo")
    print("6. Sair")
    print("=" * 40)

async def run_complete_flow(config: Dict) -> bool:
    """Run the complete application flow."""
    try:
        logger.info("Executando fluxo completo")
        
        # 1. Search for jobs
        logger.info("\n1. Buscando vagas...")
        if not await run_script("search_jobs"):
            logger.error("Falha na busca de vagas")
            return False
        logger.info("✅ Busca de vagas concluída")
            
        # 2. Match jobs with profile
        logger.info("\n2. Combinando vagas com perfil...")
        if not await run_script("match_jobs"):
            logger.error("Falha na combinação de vagas")
            return False
        logger.info("✅ Combinação de vagas concluída")
            
        # 3. Apply to matched jobs
        logger.info("\n3. Candidatando-se às vagas...")
        if not await run_script("apply_jobs"):
            logger.error("Falha nas candidaturas")
            return False
        logger.info("✅ Candidaturas concluídas")
            
        # 4. Analyze results
        logger.info("\n4. Analisando resultados...")
        if not await run_script("analyze_jobs"):
            logger.error("Falha na análise")
            return False
        logger.info("✅ Análise concluída")
            
        logger.info("\n🎉 Fluxo completo executado com sucesso!")
        return True
        
    except Exception as e:
        logger.error(f"Erro no fluxo completo: {str(e)}")
        return False

async def main():
    """Main application function."""
    try:
        # Load configuration
        config = load_config()
        
        while True:
            print_menu()
            choice = input("Digite sua escolha (1-6): ")
            
            try:
                if choice == "1":
                    await run_script("search_jobs")
                    logger.info("Busca de vagas concluída")
                    
                elif choice == "2":
                    await run_script("match_jobs")
                    logger.info("Combinação de vagas concluída")
                    
                elif choice == "3":
                    await run_script("apply_jobs")
                    logger.info("Candidaturas concluídas")
                    
                elif choice == "4":
                    await run_script("analyze_jobs")
                    logger.info("Análise concluída")
                    
                elif choice == "5":
                    logger.info("Executando fluxo completo")
                    if await run_complete_flow(config):
                        logger.info("Fluxo completo concluído com sucesso")
                    else:
                        logger.error("Falha no fluxo completo")
                    
                elif choice == "6":
                    logger.info("Encerrando aplicação")
                    break
                    
                else:
                    print("Opção inválida. Por favor, escolha entre 1-6.")
                    
            except Exception as e:
                logger.error(f"Erro: {str(e)}")
                print("\nOcorreu um erro. Deseja:")
                print("1. Tentar novamente")
                print("2. Voltar ao menu principal")
                retry = input("Escolha (1-2): ")
                
                if retry != "1":
                    continue
                    
    except KeyboardInterrupt:
        logger.info("\nAplicação encerrada pelo usuário")
    except Exception as e:
        logger.error(f"Erro: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 