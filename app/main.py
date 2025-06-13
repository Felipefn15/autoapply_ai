#!/usr/bin/env python3
"""
AutoApply.AI - Main Application Script
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

def load_config(config_path: str) -> Dict:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to config file
        
    Returns:
        Configuration dictionary
    """
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            logger.info("Loaded configuration")
            return config
    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
        raise

def run_script(script_name: str, *args) -> None:
    """
    Run a Python script with arguments.
    
    Args:
        script_name: Name of the script to run
        *args: Additional arguments to pass to the script
    """
    try:
        cmd = ['python', f'scripts/{script_name}.py'] + list(args)
        logger.info(f"Running {script_name}")
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
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

def main():
    """Main function."""
    try:
        # Load configuration
        config = load_config('config/config.yaml')
        
        # Set up logging
        os.makedirs('logs', exist_ok=True)
        logger.add(
            'logs/autoapply.log',
            rotation='1 day',
            retention='1 week',
            level=config['logging']['level']
        )
        
        # Print menu
        while True:
            print("\nAutoApply.AI - Automatização de Candidaturas")
            print("=" * 40)
            print("1. Buscar Vagas")
            print("2. Combinar Vagas com Perfil")
            print("3. Candidatar-se às Vagas")
            print("4. Visualizar Análise de Vagas")
            print("5. Executar Fluxo Completo")
            print("6. Sair")
            print("=" * 40)
            
            choice = input("\nDigite sua escolha (1-6): ")
            
            if choice == '1':
                run_script('search_jobs')
                
            elif choice == '2':
                run_script('match_jobs')
                
            elif choice == '3':
                run_script('apply_jobs', 
                    '--config', 'config/config.yaml',
                    '--resume', config['resume']['path'],
                    '--matches-dir', 'data/matches'
                )
                
            elif choice == '4':
                run_script('analyze_jobs')
                
            elif choice == '5':
                logger.info("Executando fluxo completo")
                try:
                    # Run search_jobs
                    run_script('search_jobs')
                    
                    # Run match_jobs
                    run_script('match_jobs')
                    
                    # Run apply_jobs
                    run_script('apply_jobs',
                        '--config', 'config/config.yaml',
                        '--resume', config['resume']['path'],
                        '--matches-dir', 'data/matches'
                    )
                    
                    # Run analyze_jobs
                    run_script('analyze_jobs')
                    
                except Exception as e:
                    logger.error("Falha nas candidaturas")
                    raise
                    
            elif choice == '6':
                print("Saindo...")
                break
                
            else:
                print("Opção inválida!")
                
    except KeyboardInterrupt:
        logger.info("Aplicação interrompida pelo usuário")
    except Exception as e:
        logger.error(f"Erro: {str(e)}")
        raise

if __name__ == "__main__":
    main() 