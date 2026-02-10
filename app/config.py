#!/usr/bin/env python3
"""
Módulo de configuração centralizado para diretórios de dados.

Este módulo centraliza a lógica de configuração de diretórios, suportando
DATA_DIR como base opcional para facilitar configuração em produção.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()


def get_data_dir() -> str:
    """
    Obtém o diretório base de dados (DATA_DIR).
    
    Returns:
        Caminho do diretório base ou string vazia se não configurado
    """
    return os.getenv("DATA_DIR", "").strip()


def get_model_dir() -> str:
    """
    Obtém o diretório de modelos, com suporte a DATA_DIR.
    
    Lógica:
    - Se MODEL_DIR estiver setado, usa ele
    - Se DATA_DIR estiver setado e MODEL_DIR não, usa ${DATA_DIR}/models
    - Caso contrário, usa default ./modelos
    
    Returns:
        Caminho do diretório de modelos
    """
    model_dir = os.getenv("MODEL_DIR", "").strip()
    
    if model_dir:
        return model_dir
    
    data_dir = get_data_dir()
    if data_dir:
        return os.path.join(data_dir, "models")
    
    return "./modelos"


def get_feedback_dir() -> str:
    """
    Obtém o diretório de feedbacks, com suporte a DATA_DIR.
    
    Lógica:
    - Se FEEDBACK_DIR estiver setado, usa ele
    - Se DATA_DIR estiver setado e FEEDBACK_DIR não, usa ${DATA_DIR}/feedbacks
    - Caso contrário, usa default ./feedbacks
    
    Returns:
        Caminho do diretório de feedbacks
    """
    feedback_dir = os.getenv("FEEDBACK_DIR", "").strip()
    
    if feedback_dir:
        return feedback_dir
    
    data_dir = get_data_dir()
    if data_dir:
        return os.path.join(data_dir, "feedbacks")
    
    return "./feedbacks"


def ensure_directories_exist():
    """
    Garante que os diretórios necessários existem.
    
    Cria MODEL_DIR e FEEDBACK_DIR se não existirem.
    """
    model_dir = get_model_dir()
    feedback_dir = get_feedback_dir()
    
    os.makedirs(model_dir, exist_ok=True)
    os.makedirs(feedback_dir, exist_ok=True)
    
    return {
        "model_dir": model_dir,
        "feedback_dir": feedback_dir
    }


def bootstrap_model_from_bundled(bundled_model_path: str = "/models/modelo_natureza_do_gasto.pkl") -> bool:
    """
    Copia modelo bundled para diretório persistente se necessário.
    
    Esta função é chamada no startup para garantir que o primeiro deploy
    "semeia" o volume persistente com o modelo da imagem.
    
    Args:
        bundled_model_path: Caminho do modelo na imagem Docker
        
    Returns:
        True se modelo foi copiado, False caso contrário
    """
    import shutil
    
    model_dir = get_model_dir()
    target_path = os.path.join(model_dir, "modelo_natureza_do_gasto.pkl")
    
    # Só fazer bootstrap se:
    # 1. MODEL_DIR aponta para /data/models (ou similar, volume persistente)
    # 2. Modelo bundled existe
    # 3. Modelo alvo ainda não existe
    
    if not os.path.exists(bundled_model_path):
        return False
    
    if os.path.exists(target_path):
        return False
    
    # Verificar se estamos em ambiente de produção (volume montado)
    # Se MODEL_DIR contém "/data" ou está fora de "./modelos", assumir produção
    is_production = "/data" in model_dir or (not model_dir.startswith("./") and model_dir != "modelos" and not model_dir.endswith("/modelos"))
    
    if not is_production:
        return False
    
    try:
        # Copiar modelo bundled para destino persistente
        os.makedirs(model_dir, exist_ok=True)
        shutil.copy2(bundled_model_path, target_path)
        
        # Copiar também outros modelos se existirem
        bundled_dir = os.path.dirname(bundled_model_path)
        if os.path.isdir(bundled_dir):
            for filename in ["vectorizer.pkl", "classifier.pkl", "modelo_comp.pkl", "modelo_parcelas.pkl"]:
                bundled_file = os.path.join(bundled_dir, filename)
                target_file = os.path.join(model_dir, filename)
                if os.path.exists(bundled_file) and not os.path.exists(target_file):
                    shutil.copy2(bundled_file, target_file)
        
        print(f"INFO: Modelo bootstrap concluído: {bundled_model_path} -> {target_path}")
        return True
    except Exception as e:
        print(f"WARN: Erro ao fazer bootstrap do modelo: {str(e)}")
        return False

