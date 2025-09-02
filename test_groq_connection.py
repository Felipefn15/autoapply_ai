#!/usr/bin/env python3
"""
Teste de Conexão com Groq AI
Testa se a API key do Groq está funcionando corretamente
"""

import yaml
import sys
from pathlib import Path

def load_groq_api_key():
    """Carrega API key do Groq do arquivo credentials.yaml."""
    try:
        credentials_path = Path("config/credentials.yaml")
        if not credentials_path.exists():
            print("❌ Arquivo config/credentials.yaml não encontrado")
            return None
        
        with open(credentials_path, 'r') as f:
            credentials = yaml.safe_load(f)
            groq_config = credentials.get('groq', {})
            api_key = groq_config.get('api_key')
            
            if api_key:
                print(f"✅ API key encontrada: {api_key[:10]}...")
                return api_key
            else:
                print("❌ API key não encontrada em config/credentials.yaml")
                return None
                
    except Exception as e:
        print(f"❌ Erro ao carregar credentials.yaml: {e}")
        return None

def test_groq_connection(api_key):
    """Testa conexão com Groq AI."""
    try:
        import groq
        print("✅ Biblioteca Groq importada com sucesso")
        
        # Criar cliente
        client = groq.Groq(api_key=api_key)
        print("✅ Cliente Groq criado")
        
        # Teste simples
        print("🧪 Testando conexão...")
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": "Hello, this is a test. Please respond with 'Connection successful!'"}],
            model="llama-3.1-8b-instant",
            max_tokens=20,
            temperature=0.1
        )
        
        if response.choices and response.choices[0].message.content:
            print("✅ Resposta recebida:")
            print(f"   {response.choices[0].message.content}")
            return True
        else:
            print("❌ Resposta inválida da API")
            return False
            
    except ImportError:
        print("❌ Biblioteca Groq não instalada")
        print("📦 Execute: pip install groq")
        return False
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        return False

def test_job_matching():
    """Testa funcionalidade de matching de vagas."""
    try:
        from continuous_autoapply import GroqAIEnhancer
        
        api_key = load_groq_api_key()
        if not api_key:
            return False
        
        print("\n🎯 Testando matching de vagas...")
        
        # Criar enhancer
        enhancer = GroqAIEnhancer(api_key, "llama-3.1-8b-instant")
        
        # Dados de teste
        job_description = """
        We are looking for a Senior Full Stack Developer with experience in:
        - React and Node.js
        - Python and Django
        - AWS and Docker
        - 5+ years of experience
        - Remote work available
        """
        
        profile = {
            'personal': {'name': 'Felipe França Nogueira'},
            'experience': {'years': 7},
            'core_technologies': ['React', 'Node.js', 'Python', 'Django'],
            'skills': ['React', 'Node.js', 'Python', 'Django', 'AWS', 'Docker']
        }
        
        # Testar matching
        import asyncio
        result = asyncio.run(enhancer.enhance_job_matching(job_description, profile))
        
        print("✅ Matching testado com sucesso:")
        print(f"   Score: {result.get('score', 'N/A')}")
        print(f"   Recomendação: {result.get('recommendation', 'N/A')}")
        print(f"   Pontos fortes: {', '.join(result.get('strengths', []))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de matching: {e}")
        return False

def main():
    """Função principal."""
    print("🤖 TESTE DE CONEXÃO COM GROQ AI")
    print("=" * 50)
    
    # Carregar API key
    api_key = load_groq_api_key()
    if not api_key:
        print("\n❌ Não foi possível carregar API key")
        return 1
    
    # Testar conexão
    print("\n🔗 Testando conexão...")
    if not test_groq_connection(api_key):
        print("\n❌ Teste de conexão falhou")
        return 1
    
    # Testar matching
    print("\n🎯 Testando funcionalidade de matching...")
    if not test_job_matching():
        print("\n⚠️ Teste de matching falhou (mas conexão OK)")
    
    print("\n🎉 TESTE CONCLUÍDO COM SUCESSO!")
    print("✅ Groq AI está funcionando corretamente")
    print("✅ Sistema contínuo pode usar Groq AI")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
