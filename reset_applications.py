#!/usr/bin/env python3
"""
Reset Applications - Reset the application history to test again
"""

import json
from pathlib import Path

def reset_applications():
    """Reset all application history."""
    print("🔄 RESETANDO HISTÓRICO DE APLICAÇÕES")
    print("=" * 50)
    
    # Files to reset
    files_to_reset = [
        "data/logs/simple_applied_jobs.json",
        "data/logs/real_jobs_applied.json",
        "data/logs/application_history.json"
    ]
    
    for file_path in files_to_reset:
        try:
            file_obj = Path(file_path)
            if file_obj.exists():
                file_obj.unlink()
                print(f"✅ Removido: {file_path}")
            else:
                print(f"ℹ️  Não encontrado: {file_path}")
        except Exception as e:
            print(f"❌ Erro ao remover {file_path}: {e}")
    
    print(f"\n🎉 Reset concluído! Agora você pode testar novamente.")
    print(f"💡 Execute: python run_real_jobs_system.py")

if __name__ == "__main__":
    reset_applications()
