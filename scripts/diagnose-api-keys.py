#!/usr/bin/env python3
"""
Script de diagnóstico para verificar API keys do AI Fallback.
Execute dentro do container para verificar se as chaves estão sendo carregadas.
"""

import os
import sys
from pathlib import Path

def check_env_file(path):
    """Verifica se um arquivo .env existe e tem as chaves."""
    if not os.path.exists(path):
        return False, f"Arquivo não existe: {path}"
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            has_openai = 'OPENAI_API_KEY' in content
            has_serpapi = 'SERPAPI_API_KEY' in content
            has_anthropic = 'ANTHROPIC_API_KEY' in content
            
            # Verificar se não está vazio
            lines = [line.strip() for line in content.split('\n') if line.strip() and not line.strip().startswith('#')]
            openai_value = None
            serpapi_value = None
            
            for line in lines:
                if line.startswith('OPENAI_API_KEY='):
                    openai_value = line.split('=', 1)[1].strip().strip('"').strip("'")
                elif line.startswith('SERPAPI_API_KEY='):
                    serpapi_value = line.split('=', 1)[1].strip().strip('"').strip("'")
            
            return True, {
                'exists': True,
                'has_openai': has_openai,
                'has_serpapi': has_serpapi,
                'has_anthropic': has_anthropic,
                'openai_value_length': len(openai_value) if openai_value else 0,
                'serpapi_value_length': len(serpapi_value) if serpapi_value else 0,
                'openai_empty': not openai_value or len(openai_value) == 0,
                'serpapi_empty': not serpapi_value or len(serpapi_value) == 0
            }
    except Exception as e:
        return False, f"Erro ao ler arquivo: {e}"

def main():
    print("=" * 60)
    print("DIAGNÓSTICO DE API KEYS - AI FALLBACK")
    print("=" * 60)
    print()
    
    # 1. Verificar variáveis de ambiente
    print("1. VARIÁVEIS DE AMBIENTE (os.environ):")
    print("-" * 60)
    openai_in_env = 'OPENAI_API_KEY' in os.environ
    serpapi_in_env = 'SERPAPI_API_KEY' in os.environ
    anthropic_in_env = 'ANTHROPIC_API_KEY' in os.environ
    
    print(f"  OPENAI_API_KEY in os.environ: {openai_in_env}")
    if openai_in_env:
        value = os.getenv('OPENAI_API_KEY', '')
        print(f"    Valor presente: {'Sim' if value else 'Não'}")
        print(f"    Tamanho: {len(value)} caracteres")
        print(f"    Primeiros 10 chars: {value[:10]}..." if len(value) > 10 else f"    Valor: {value}")
    
    print(f"  SERPAPI_API_KEY in os.environ: {serpapi_in_env}")
    if serpapi_in_env:
        value = os.getenv('SERPAPI_API_KEY', '')
        print(f"    Valor presente: {'Sim' if value else 'Não'}")
        print(f"    Tamanho: {len(value)} caracteres")
        print(f"    Primeiros 10 chars: {value[:10]}..." if len(value) > 10 else f"    Valor: {value}")
    
    print(f"  ANTHROPIC_API_KEY in os.environ: {anthropic_in_env}")
    print()
    
    # 2. Verificar os.getenv() (após load_dotenv)
    print("2. VALORES VIA os.getenv() (após load_dotenv):")
    print("-" * 60)
    from dotenv import load_dotenv
    
    # Tentar carregar de múltiplos locais
    env_paths = ['.env', '/app/.env', os.path.join(os.getcwd(), '.env')]
    loaded = False
    for env_path in env_paths:
        if os.path.exists(env_path):
            load_dotenv(env_path, override=False)
            print(f"  Carregado .env de: {env_path}")
            loaded = True
            break
    
    if not loaded:
        load_dotenv(override=False)
        print("  Tentativa de carregar .env do diretório padrão")
    
    openai_value = os.getenv('OPENAI_API_KEY')
    serpapi_value = os.getenv('SERPAPI_API_KEY')
    anthropic_value = os.getenv('ANTHROPIC_API_KEY')
    
    print(f"  OPENAI_API_KEY: {'Presente' if openai_value and openai_value.strip() else 'Ausente ou vazio'}")
    if openai_value:
        print(f"    Tamanho: {len(openai_value)} caracteres")
        print(f"    Após strip: {len(openai_value.strip())} caracteres")
    
    print(f"  SERPAPI_API_KEY: {'Presente' if serpapi_value and serpapi_value.strip() else 'Ausente ou vazio'}")
    if serpapi_value:
        print(f"    Tamanho: {len(serpapi_value)} caracteres")
        print(f"    Após strip: {len(serpapi_value.strip())} caracteres")
    
    print(f"  ANTHROPIC_API_KEY: {'Presente' if anthropic_value and anthropic_value.strip() else 'Ausente ou vazio'}")
    print()
    
    # 3. Verificar arquivos .env
    print("3. ARQUIVOS .env:")
    print("-" * 60)
    env_files = ['.env', '.env.production', '/app/.env']
    for env_file in env_files:
        exists = os.path.exists(env_file)
        print(f"  {env_file}: {'Existe' if exists else 'Não existe'}")
        if exists:
            success, info = check_env_file(env_file)
            if success and isinstance(info, dict):
                print(f"    OPENAI_API_KEY definido: {info['has_openai']}")
                print(f"    OPENAI_API_KEY vazio: {info['openai_empty']}")
                print(f"    SERPAPI_API_KEY definido: {info['has_serpapi']}")
                print(f"    SERPAPI_API_KEY vazio: {info['serpapi_empty']}")
            else:
                print(f"    {info}")
    print()
    
    # 4. Diretório atual
    print("4. INFORMAÇÕES DO SISTEMA:")
    print("-" * 60)
    print(f"  Diretório atual: {os.getcwd()}")
    print(f"  __file__ diretório: {os.path.dirname(__file__) if '__file__' in globals() else 'N/A'}")
    print(f"  PATH: {os.environ.get('PATH', 'N/A')[:100]}...")
    print()
    
    # 5. Resumo
    print("5. RESUMO:")
    print("-" * 60)
    openai_ok = bool(openai_value and openai_value.strip())
    serpapi_ok = bool(serpapi_value and serpapi_value.strip())
    anthropic_ok = bool(anthropic_value and anthropic_value.strip())
    
    print(f"  OPENAI_API_KEY válida: {'✅ SIM' if openai_ok else '❌ NÃO'}")
    print(f"  SERPAPI_API_KEY válida: {'✅ SIM' if serpapi_ok else '❌ NÃO'}")
    print(f"  ANTHROPIC_API_KEY válida: {'✅ SIM' if anthropic_ok else '❌ NÃO'}")
    print(f"  AI Fallback pode funcionar: {'✅ SIM' if (openai_ok or anthropic_ok) else '❌ NÃO'}")
    print()
    print("=" * 60)

if __name__ == '__main__':
    main()





