#!/usr/bin/env python3
"""
Módulo de rotas para o endpoint de feedback.

Este módulo define as rotas da API para registro de feedbacks do usuário,
incluindo documentação Swagger completa.
"""

import os
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from app.schemas_feedback import (
    FeedbackRequest, 
    FeedbackResponse, 
    FeedbackItem, 
    FeedbackFileInfo
)
from app.services.feedback_store import FeedbackStore
from app.services.feedback_ingestion import FeedbackIngestionService
from app.config import get_feedback_dir

# Configurações do serviço
FEEDBACK_DIR = get_feedback_dir()
FEEDBACK_FILENAME_TEMPLATE = os.getenv("FEEDBACK_FILENAME_TEMPLATE", "feedback_%Y-%m-%d.csv")
TZ = os.getenv("TZ")  # Timezone opcional

# Inicializar serviços
feedback_store = FeedbackStore(
    feedback_dir=FEEDBACK_DIR,
    filename_template=FEEDBACK_FILENAME_TEMPLATE,
    timezone=TZ
)

feedback_ingestion = FeedbackIngestionService(
    feedback_dir=FEEDBACK_DIR,
    base_csv=os.getenv("TRAINING_DATA_FILE", "modelo_despesas_completo.csv")
)

# Router para feedback
router = APIRouter(prefix="/v1", tags=["Feedback"])


@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    status_code=201,
    summary="Registrar feedback de correção",
    description="""
    ## 📝 **Endpoint de Feedback para Correções do Usuário**
    
    Este endpoint permite registrar correções do usuário em transações classificadas.
    Os dados são salvos em arquivos CSV diários para posterior incorporação ao modelo.
    
    ### 🔄 **Funcionalidades**
    
    - **Suporte a lote**: Aceita item único ou array de feedbacks
    - **Persistência segura**: Append com locks para concorrência
    - **Criação automática**: Arquivo e cabeçalho criados automaticamente
    - **Mapeamento inteligente**: Conversão automática para formato CSV
    
    ### 📊 **Mapeamento para CSV**
    
    Os campos são mapeados para as seguintes colunas (nesta ordem):
    
    1. **Aonde Gastou** ← `description`
    2. **Natureza do Gasto** ← `category` (vazio se ausente)
    3. **Valor Total** ← `amount * max(parcelas, 1)`
    4. **Parcelas** ← `parcelas` (default 1 se ausente)
    5. **No da Parcela** ← `numero_parcela` (vazio se ausente)
    6. **Valor Unitário** ← `amount`
    7. **tipo** ← `source`
    8. **Comp** ← `comp`
    9. **Data** ← `date`
    10. **cartao** ← `card`
    11. **transactionId** ← `transactionId`
    12. **modelVersion** ← `modelVersion`
    13. **createdAt** ← `createdAt` (timestamp atual se ausente)
    14. **flux** ← `flux`
    
    ### 🎯 **Campos Obrigatórios**
    
    - `transactionId`: ID único da transação
    - `description`: Descrição da transação
    - `amount`: Valor unitário (deve ser > 0)
    - `date`: Data no formato ISO
    
    ### 📁 **Arquivo de Destino**
    
    Os dados são salvos em: `feedbacks/feedback_YYYY-MM-DD.csv`
    
    ### 🔒 **Comportamento**
    
    - **Sem deduplicação**: TransactionIds repetidos são registrados novamente
    - **Concorrência segura**: Locks por arquivo evitam corrupção
    - **Valores padrão**: Campos opcionais ausentes viram vazio no CSV
    - **Formato decimal**: Valores salvos com ponto decimal (padrão)
    
    ### 🚨 **Códigos de Resposta**
    
    - `201`: Feedback salvo com sucesso
    - `400`: Dados inválidos ou campos obrigatórios ausentes
    - `422`: Erro de validação nos dados
    - `500`: Erro interno do servidor
    """,
    responses={
        201: {
            "description": "Feedback salvo com sucesso",
            "content": {
                "application/json": {
                    "example": {
                        "saved_rows": 3,
                        "file_path": "feedbacks/feedback_2024-01-01.csv",
                        "columns": [
                            "Aonde Gastou",
                            "Natureza do Gasto", 
                            "Valor Total",
                            "Parcelas",
                            "No da Parcela",
                            "Valor Unitário",
                            "tipo",
                            "Comp",
                            "Data",
                            "cartao",
                            "transactionId",
                            "modelVersion",
                            "createdAt",
                            "flux"
                        ]
                    }
                }
            }
        },
        400: {
            "description": "Dados inválidos",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Lista de feedbacks não pode estar vazia"
                    }
                }
            }
        },
        422: {
            "description": "Erro de validação",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "feedback", 0, "amount"],
                                "msg": "ensure this value is greater than 0",
                                "type": "value_error.number.not_gt"
                            }
                        ]
                    }
                }
            }
        },
        500: {
            "description": "Erro interno do servidor",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Erro ao salvar feedbacks: [detalhes do erro]"
                    }
                }
            }
        }
    }
)
async def create_feedback(request: FeedbackRequest):
    """
    🎯 **Registra feedback de correção do usuário**
    
    Salva correções em arquivo CSV diário para posterior incorporação ao modelo.
    """
    try:
        # Normalizar entrada para lista
        if isinstance(request.feedback, FeedbackItem):
            feedback_items = [request.feedback]
        else:
            feedback_items = request.feedback
        
        if not feedback_items:
            raise HTTPException(
                status_code=400, 
                detail="Lista de feedbacks não pode estar vazia"
            )
        
        # Converter Pydantic models para dict
        feedback_dicts = []
        for item in feedback_items:
            # Adicionar timestamp atual se createdAt não especificado
            item_dict = item.dict()
            if not item_dict.get("createdAt"):
                from datetime import datetime
                item_dict["createdAt"] = datetime.now().isoformat()
            
            feedback_dicts.append(item_dict)
        
        # Salvar feedbacks
        result = feedback_store.save_feedbacks(feedback_dicts)
        
        return FeedbackResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao salvar feedbacks: {str(e)}"
        )


@router.get(
    "/feedback/file-info",
    response_model=FeedbackFileInfo,
    summary="Informações sobre arquivo de feedback",
    description="""
    ## 📁 **Informações sobre Arquivo de Feedback**
    
    Retorna informações detalhadas sobre o arquivo de feedback de uma data específica.
    
    ### 📊 **Informações Retornadas**
    
    - **Arquivo**: Nome e caminho do arquivo
    - **Existência**: Se o arquivo existe no sistema
    - **Tamanho**: Tamanho em bytes (se existe)
    - **Modificação**: Data da última modificação (se existe)
    - **Cabeçalho**: Se tem cabeçalho correto (se existe)
    - **Colunas**: Lista das colunas esperadas
    
    ### 🎯 **Parâmetros**
    
    - `date`: Data no formato YYYY-MM-DD (opcional, usa hoje se não especificado)
    
    ### 📝 **Exemplos**
    
    - `GET /v1/feedback/file-info` - Informações do arquivo de hoje
    - `GET /v1/feedback/file-info?date=2024-01-01` - Informações do arquivo de 01/01/2024
    """,
    responses={
        200: {
            "description": "Informações do arquivo",
            "content": {
                "application/json": {
                    "example": {
                        "filename": "feedback_2024-01-01.csv",
                        "file_path": "feedbacks/feedback_2024-01-01.csv",
                        "exists": True,
                        "columns": ["Aonde Gastou", "Natureza do Gasto", "Valor Total"],
                        "size_bytes": 2048,
                        "modified": "2024-01-01T12:00:00",
                        "has_header": True
                    }
                }
            }
        },
        400: {
            "description": "Data inválida",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Data deve estar no formato YYYY-MM-DD"
                    }
                }
            }
        }
    }
)
async def get_feedback_file_info(
    date: Optional[str] = Query(
        None, 
        description="Data no formato YYYY-MM-DD (opcional, usa hoje se não especificado)",
        example="2024-01-01"
    )
):
    """
    📁 **Obtém informações sobre arquivo de feedback**
    
    Retorna detalhes sobre o arquivo de feedback de uma data específica.
    """
    try:
        info = feedback_store.get_feedback_file_info(date)
        return FeedbackFileInfo(**info)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao obter informações do arquivo: {str(e)}"
        )


# =============================================================================
# ENDPOINTS DO PIPELINE DE INGESTÃO E RETREINO
# =============================================================================

@router.get(
    "/feedback/pipeline/status",
    summary="Status do Pipeline de Ingestão",
    description="""
    ## 🔄 **Status do Pipeline de Ingestão de Feedbacks**
    
    Retorna informações sobre o estado atual do pipeline de ingestão e retreino.
    
    ### 📊 **Informações Retornadas**
    
    - **Arquivos de feedback**: Quantidade e status
    - **Arquivos processados**: Lista de arquivos já processados
    - **Modelos**: Timestamps e status dos modelos
    - **Backups**: Informações sobre backups disponíveis
    - **Métricas**: Estatísticas do pipeline
    
    ### 🎯 **Uso**
    
    Use este endpoint para monitorar o estado do sistema antes de executar
    operações de ingestão ou retreino.
    """
)
async def get_pipeline_status():
    """Obtém status completo do pipeline de ingestão"""
    try:
        # Informações sobre arquivos de feedback
        feedback_files = feedback_ingestion.get_feedback_files()
        processed_files = feedback_ingestion.get_processed_files()
        
        # Informações sobre modelos
        model_timestamps = feedback_ingestion.get_model_timestamps()
        
        # Informações sobre backups
        backup_files = feedback_ingestion.get_backup_files()
        
        # Informações sobre dataset base
        base_csv = feedback_ingestion.base_csv
        base_exists = os.path.exists(base_csv)
        base_info = {}
        if base_exists:
            base_info = feedback_ingestion.get_dataset_info(base_csv)
        
        return {
            "pipeline_status": "operational",
            "feedback_files": {
                "total_found": len(feedback_files),
                "files": [str(f) for f in feedback_files],
                "processed_count": len(processed_files),
                "processed_files": list(processed_files),
                "pending_count": len(feedback_files) - len(processed_files)
            },
            "models": {
                "directory": "modelos",
                "count": len(model_timestamps),
                "files": model_timestamps,
                "last_updated": max(model_timestamps.values()) if model_timestamps else None
            },
            "backups": {
                "count": len(backup_files),
                "files": backup_files
            },
            "dataset_base": {
                "file": base_csv,
                "exists": base_exists,
                "info": base_info
            },
            "timestamp": "2024-01-15T12:00:00Z"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter status do pipeline: {str(e)}"
        )


@router.post(
    "/feedback/pipeline/collect",
    summary="Coletar Feedbacks para Processamento",
    description="""
    ## 📥 **Coleta de Feedbacks para Processamento**
    
    Coleta todos os arquivos de feedback não processados e os prepara para
    integração com o dataset principal.
    
    ### 🔄 **Processo**
    
    1. **Lista arquivos**: Encontra todos os arquivos `feedback_*.csv`
    2. **Filtra novos**: Remove arquivos já processados
    3. **Valida estrutura**: Verifica se cada arquivo tem 14 colunas
    4. **Remove duplicatas**: Elimina duplicatas por transactionId
    5. **Marca processados**: Atualiza lista de arquivos processados
    
    ### 📊 **Resposta**
    
    - **Arquivos processados**: Lista de arquivos coletados
    - **Registros coletados**: Total de registros únicos
    - **Duplicatas removidas**: Estatísticas de limpeza
    - **Próximos passos**: Sugestões para continuar o pipeline
    
    ### ⚠️ **Importante**
    
    - Arquivos são marcados como processados após coleta bem-sucedida
    - Use `/feedback/pipeline/clear-processed` para reprocessar arquivos
    - Operação é idempotente (seguro executar múltiplas vezes)
    """
)
async def collect_feedbacks():
    """Coleta feedbacks não processados"""
    try:
        feedbacks = feedback_ingestion.collect_feedbacks_with_control()
        
        total_records = sum(len(df) for df in feedbacks)
        
        return {
            "success": True,
            "operation": "collect_feedbacks",
            "results": {
                "files_collected": len(feedbacks),
                "total_records": total_records,
                "files": [f"feedback_YYYY-MM-DD.csv" for _ in feedbacks]  # Placeholder
            },
            "next_steps": [
                "Execute /feedback/pipeline/merge para integrar ao dataset",
                "Execute /feedback/pipeline/retrain para retreinar modelos"
            ],
            "timestamp": "2024-01-15T12:00:00Z"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro na coleta de feedbacks: {str(e)}"
        )


@router.post(
    "/feedback/pipeline/merge",
    summary="Mesclar Feedbacks com Dataset Principal",
    description="""
    ## 🔗 **Mesclagem de Feedbacks com Dataset Principal**
    
    Integra os feedbacks coletados ao dataset principal para preparar
    dados para retreino dos modelos.
    
    ### 🔄 **Processo**
    
    1. **Carrega dataset base**: Lê arquivo principal de treinamento
    2. **Coleta feedbacks**: Busca feedbacks não processados
    3. **Valida integração**: Verifica compatibilidade e qualidade
    4. **Mescla dados**: Concatena feedbacks ao final do dataset
    5. **Valida resultado**: Confirma estrutura e integridade
    
    ### 📊 **Validações Executadas**
    
    - **Estrutura de colunas**: Compatibilidade entre base e feedbacks
    - **Duplicatas**: Detecção de transactionIds duplicados
    - **Qualidade**: Valores nulos e negativos em campos críticos
    - **Balanceamento**: Análise de distribuição de categorias
    
    ### 📈 **Métricas Retornadas**
    
    - **Registros base**: Quantidade no dataset original
    - **Registros feedback**: Quantidade de feedbacks integrados
    - **Duplicatas encontradas**: TransactionIds já existentes
    - **Problemas de qualidade**: Issues detectados nos dados
    
    ### ⚠️ **Importante**
    
    - Dataset base deve existir e ser válido
    - Operação cria backup automático antes de modificar
    - Use `/feedback/pipeline/backup/list` para ver backups
    """
)
async def merge_feedbacks():
    """Mescla feedbacks com dataset principal"""
    try:
        merged_df = feedback_ingestion.merge_into_model_dataset()
        
        return {
            "success": True,
            "operation": "merge_dataset",
            "results": {
                "total_records": len(merged_df),
                "dataset_file": feedback_ingestion.base_csv,
                "backup_created": True
            },
            "next_steps": [
                "Execute /feedback/pipeline/retrain para retreinar modelos",
                "Execute /feedback/pipeline/validate para validar qualidade"
            ],
            "timestamp": "2024-01-15T12:00:00Z"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro na mesclagem: {str(e)}"
        )


@router.post(
    "/feedback/pipeline/retrain",
    summary="Retreinar Modelos com Dados Atualizados",
    description="""
    ## 🤖 **Retreino de Modelos com Dados Atualizados**
    
    Executa o retreino completo dos modelos usando o dataset atualizado
    com os feedbacks integrados.
    
    ### 🔄 **Processo**
    
    1. **Verifica modelos**: Obtém timestamps dos modelos atuais
    2. **Executa treinamento**: Chama `treinar_modelo.py` com dataset atualizado
    3. **Monitora progresso**: Acompanha execução com timeout de 10min
    4. **Valida resultados**: Verifica se modelos foram atualizados
    5. **Testa qualidade**: Valida funcionalidade dos novos modelos
    
    ### 📊 **Modelos Retreinados**
    
    - **modelo_natureza_do_gasto.pkl**: Classificação de categorias
    - **modelo_comp.pkl**: Classificação de compartilhamento
    - **modelo_parcelas.pkl**: Predição de parcelas
    
    ### 🔍 **Validações de Qualidade**
    
    - **Carregamento**: Modelos podem ser carregados corretamente
    - **Métodos**: Presença de métodos `predict` e `predict_proba`
    - **Teste funcional**: Predições com dados de exemplo
    - **Tamanho**: Verificação de tamanho dos arquivos
    
    ### ⚠️ **Importante**
    
    - Timeout de 10 minutos para evitar travamentos
    - Variáveis de ambiente são configuradas automaticamente
    - Logs detalhados são capturados e retornados
    - Operação pode ser demorada dependendo do tamanho dos dados
    """
)
async def retrain_models():
    """Retreina modelos com dados atualizados"""
    try:
        result = feedback_ingestion.trigger_model_retraining(feedback_ingestion.base_csv)
        
        if result['success']:
            return {
                "success": True,
                "operation": "retrain_models",
                "results": {
                    "updated_models": result['updated_models'],
                    "models_before": result['models_before'],
                    "models_after": result['models_after'],
                    "quality_results": result['quality_results']
                },
                "training_output": result['training_output'],
                "next_steps": [
                    "Modelos atualizados com sucesso",
                    "Execute /feedback/pipeline/validate para validar qualidade",
                    "Execute /feedback/pipeline/status para verificar estado"
                ],
                "timestamp": "2024-01-15T12:00:00Z"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Erro no retreino: {result['error']}"
            )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro no retreino dos modelos: {str(e)}"
        )


@router.post(
    "/feedback/pipeline/run-complete",
    summary="Executar Pipeline Completo",
    description="""
    ## 🚀 **Pipeline Completo de Ingestão e Retreino**
    
    Executa todo o pipeline de ingestão de feedbacks em uma única operação:
    coleta → mesclagem → escrita → retreino.
    
    ### 🔄 **Fluxo Completo**
    
    1. **Coleta**: Busca feedbacks não processados
    2. **Mesclagem**: Integra com dataset principal
    3. **Escrita**: Salva dataset consolidado com backup
    4. **Retreino**: Executa treinamento dos modelos
    5. **Validação**: Confirma qualidade dos resultados
    
    ### 📊 **Métricas Detalhadas**
    
    - **Feedbacks coletados**: Quantidade de arquivos processados
    - **Registros integrados**: Total de registros adicionados
    - **Modelos atualizados**: Lista de modelos retreinados
    - **Tempo de execução**: Duração de cada etapa
    - **Qualidade**: Resultados das validações
    
    ### ⚠️ **Importante**
    
    - **Operação longa**: Pode levar vários minutos para completar
    - **Backup automático**: Dataset original é preservado
    - **Rollback**: Em caso de erro, sistema pode ser restaurado
    - **Monitoramento**: Use `/feedback/pipeline/status` para acompanhar
    
    ### 🎯 **Quando Usar**
    
    - **Integração diária**: Processar feedbacks acumulados
    - **Retreino semanal**: Atualizar modelos regularmente
    - **Deploy**: Preparar sistema para produção
    - **Manutenção**: Operação de manutenção programada
    """
)
async def run_complete_pipeline():
    """Executa pipeline completo de ingestão e retreino"""
    try:
        result = feedback_ingestion.run_complete_pipeline()
        
        return {
            "success": result['success'],
            "operation": "complete_pipeline",
            "steps_completed": result['steps_completed'],
            "errors": result['errors'],
            "metrics": result['metrics'],
            "timestamp": "2024-01-15T12:00:00Z"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro no pipeline completo: {str(e)}"
        )


@router.get(
    "/feedback/pipeline/backup/list",
    summary="Listar Backups Disponíveis",
    description="""
    ## 💾 **Lista de Backups Disponíveis**
    
    Retorna lista de todos os backups de dataset disponíveis,
    ordenados por data de criação (mais recentes primeiro).
    
    ### 📊 **Informações dos Backups**
    
    - **Arquivo**: Nome do arquivo de backup
    - **Data de criação**: Timestamp de quando foi criado
    - **Tamanho**: Tamanho do arquivo em bytes
    - **Status**: Se o arquivo ainda existe
    
    ### 🔧 **Operações Disponíveis**
    
    - **Restaurar**: Use backup para restaurar dataset
    - **Limpar**: Remove backups antigos automaticamente
    - **Validar**: Verifica integridade dos backups
    """
)
async def list_backups():
    """Lista backups disponíveis"""
    try:
        backup_files = feedback_ingestion.get_backup_files()
        
        backup_info = []
        for backup_file in backup_files:
            if os.path.exists(backup_file):
                stat = os.stat(backup_file)
                backup_info.append({
                    "file": backup_file,
                    "created": stat.st_mtime,
                    "size": stat.st_size,
                    "exists": True
                })
            else:
                backup_info.append({
                    "file": backup_file,
                    "created": None,
                    "size": 0,
                    "exists": False
                })
        
        return {
            "success": True,
            "backups": backup_info,
            "count": len(backup_info),
            "timestamp": "2024-01-15T12:00:00Z"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao listar backups: {str(e)}"
        )


@router.post(
    "/feedback/pipeline/clear-processed",
    summary="Limpar Lista de Arquivos Processados",
    description="""
    ## 🗑️ **Limpeza de Arquivos Processados**
    
    Remove a lista de arquivos processados, permitindo reprocessamento
    de todos os arquivos de feedback.
    
    ### ⚠️ **CUIDADO**
    
    Esta operação permite reprocessar arquivos já processados, o que pode
    causar duplicação de dados se executado sem cuidado.
    
    ### 🎯 **Quando Usar**
    
    - **Desenvolvimento**: Durante testes e desenvolvimento
    - **Correção de bugs**: Após correção de problemas no processamento
    - **Manutenção**: Para reprocessar dados com nova lógica
    - **Reset**: Para reiniciar completamente o pipeline
    
    ### 🔄 **Próximos Passos**
    
    Após limpar a lista, execute `/feedback/pipeline/collect` para
    reprocessar todos os arquivos de feedback.
    """
)
async def clear_processed_files():
    """Limpa lista de arquivos processados"""
    try:
        feedback_ingestion.clear_processed_files()
        
        return {
            "success": True,
            "operation": "clear_processed_files",
            "message": "Lista de arquivos processados foi limpa",
            "next_steps": [
                "Execute /feedback/pipeline/collect para reprocessar arquivos",
                "Execute /feedback/pipeline/status para verificar estado"
            ],
            "timestamp": "2024-01-15T12:00:00Z"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao limpar arquivos processados: {str(e)}"
        )
