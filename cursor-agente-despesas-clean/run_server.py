#!/usr/bin/env python3
"""
Script para iniciar o servidor da API de classificação.
"""

import sys
import os
import uvicorn

# Adiciona o diretório atual ao path do Python
sys.path.insert(0, '.')

def main():
    """Inicia o servidor da API."""
    try:
        from app.main import app
        port = int(os.getenv("PORT", "8081"))
        print("Iniciando servidor da API de classificacao...")
        print(f"URL: http://127.0.0.1:{port}")
        print(f"Documentacao: http://127.0.0.1:{port}/docs")
        print(f"Health Check: http://127.0.0.1:{port}/healthz")
        print(f"Endpoint: http://127.0.0.1:{port}/v1/classify")
        print(f"Parse Itau: http://127.0.0.1:{port}/parse_itau")
        print("\nPressione Ctrl+C para parar o servidor")
        print("-" * 50)
        
        # Usar reload apenas em desenvolvimento para garantir código atualizado
        # Em produção, remover reload para melhor performance
        reload = os.getenv("RELOAD", "false").lower() == "true"
        
        if reload:
            # Para reload funcionar, precisa passar como string de importação
            uvicorn.run("app.main:app", host='0.0.0.0', port=port, log_level='info', reload=True)
        else:
            # Sem reload, pode passar o objeto diretamente
            uvicorn.run(app, host='0.0.0.0', port=port, log_level='info', reload=False)
        
    except ImportError as e:
        print(f"Erro ao importar modulos: {e}")
        print("Certifique-se de que esta no diretorio correto do projeto")
        sys.exit(1)
    except Exception as e:
        print(f"Erro ao iniciar servidor: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
