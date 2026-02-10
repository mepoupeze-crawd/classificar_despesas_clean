#!/usr/bin/env python3
"""
Serviço de Ingestão de Feedbacks para Retreino

Este módulo fornece funções para coletar feedbacks diários e integrá-los
ao dataset principal para retreino dos modelos. As funções estão documentadas
mas não implementadas, servindo como ganchos para integração futura.

Fluxo esperado:
1. collect_feedbacks() - Coleta todos os arquivos CSV de feedback
2. merge_into_model_dataset() - Mescla feedbacks com dataset base
3. write_merged_dataset() - Escreve dataset consolidado
"""

import os
import pandas as pd
import shutil
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from app.config import get_model_dir


class FeedbackIngestionService:
    """
    Serviço para ingestão e consolidação de feedbacks para retreino.
    
    Este serviço implementa o pipeline de consolidação de feedbacks:
    - Coleta arquivos CSV diários de feedback
    - Mescla com dataset principal
    - Prepara dados para retreino
    """
    
    def __init__(self, feedback_dir: str = "feedbacks", base_csv: str = "modelo_despesas_completo.csv"):
        """
        Inicializa o serviço de ingestão.
        
        Args:
            feedback_dir: Diretório contendo arquivos de feedback
            base_csv: Arquivo CSV base para mesclagem
        """
        self.feedback_dir = Path(feedback_dir)
        self.base_csv = base_csv
        self.processed_file = Path(feedback_dir) / ".processed_files.txt"  # Arquivo de controle
    
    def collect_feedbacks(self, feedback_dir: Optional[str] = None) -> List[pd.DataFrame]:
        """
        Coleta todos os arquivos CSV de feedback do diretório especificado.
        
        Args:
            feedback_dir: Diretório de feedbacks (opcional, usa self.feedback_dir se None)
            
        Returns:
            Lista de DataFrames, um para cada arquivo de feedback encontrado
            
        Invariantes:
            - Cada DataFrame deve ter as 14 colunas padrão do feedback
            - Arquivos vazios ou inválidos são ignorados silenciosamente
            - Ordem dos arquivos é determinística (por nome/data)
            - Duplicatas por transactionId são removidas (mantém última ocorrência)
        """
        target_dir = Path(feedback_dir) if feedback_dir else self.feedback_dir
        
        if not target_dir.exists():
            print(f"AVISO: Diretorio de feedbacks nao existe: {target_dir}")
            return []
        
        # 1. Listar arquivos feedback_*.csv
        feedback_files = list(target_dir.glob("feedback_*.csv"))
        
        if not feedback_files:
            print(f"INFO: Nenhum arquivo de feedback encontrado em {target_dir}")
            return []
        
        # 2. Ordenar por nome (que inclui data)
        feedback_files.sort()
        print(f"INFO: Encontrados {len(feedback_files)} arquivos de feedback")
        
        # 3. Ler cada arquivo como DataFrame
        feedbacks = []
        all_transaction_ids = set()  # Controle de duplicação global
        
        for file_path in feedback_files:
            try:
                print(f"INFO: Processando: {file_path.name}")
                
                # Ler arquivo
                df = pd.read_csv(file_path)
                
                # Validar se arquivo não está vazio
                if df.empty:
                    print(f"AVISO: Arquivo vazio ignorado: {file_path.name}")
                    continue
                
                # 4. Validar estrutura das colunas
                if not self.validate_feedback_structure(df):
                    print(f"ERRO: Estrutura invalida ignorada: {file_path.name}")
                    continue
                
                # 5. Remover duplicatas internas por transactionId
                initial_count = len(df)
                df = df.drop_duplicates(subset=['transactionId'], keep='last')
                removed_internal = initial_count - len(df)
                
                if removed_internal > 0:
                    print(f"INFO: Removidas {removed_internal} duplicatas internas em {file_path.name}")
                
                # 6. Remover duplicatas globais (já processadas em arquivos anteriores)
                df_filtered = df[~df['transactionId'].isin(all_transaction_ids)]
                removed_global = len(df) - len(df_filtered)
                
                if removed_global > 0:
                    print(f"INFO: Removidas {removed_global} duplicatas globais de {file_path.name}")
                
                # Atualizar conjunto de IDs processados
                all_transaction_ids.update(df_filtered['transactionId'].tolist())
                
                if len(df_filtered) > 0:
                    feedbacks.append(df_filtered)
                    print(f"OK: {len(df_filtered)} registros validos de {file_path.name}")
                else:
                    print(f"INFO: Nenhum registro novo em {file_path.name}")
                
            except Exception as e:
                print(f"ERRO: Erro ao processar {file_path.name}: {str(e)}")
                continue
        
        print(f"INFO: Total de feedbacks coletados: {len(feedbacks)} arquivos")
        total_records = sum(len(df) for df in feedbacks)
        print(f"INFO: Total de registros unicos: {total_records}")
        
        return feedbacks
    
    def get_processed_files(self) -> set:
        """
        Retorna conjunto de arquivos já processados.
        
        Returns:
            Set com nomes dos arquivos já processados
        """
        if not self.processed_file.exists():
            return set()
        
        try:
            with open(self.processed_file, 'r', encoding='utf-8') as f:
                return set(line.strip() for line in f if line.strip())
        except Exception as e:
            print(f"ERRO: Erro ao ler arquivo de controle: {str(e)}")
            return set()
    
    def mark_file_as_processed(self, filename: str):
        """
        Marca arquivo como processado.
        
        Args:
            filename: Nome do arquivo a ser marcado como processado
        """
        try:
            # Garantir que o diretório existe
            self.processed_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.processed_file, 'a', encoding='utf-8') as f:
                f.write(f"{filename}\n")
            
            print(f"INFO: Arquivo marcado como processado: {filename}")
        except Exception as e:
            print(f"ERRO: Erro ao marcar arquivo como processado: {str(e)}")
    
    def clear_processed_files(self):
        """
        Limpa lista de arquivos processados (usar com cuidado).
        """
        try:
            if self.processed_file.exists():
                self.processed_file.unlink()
                print(f"INFO: Lista de arquivos processados limpa")
        except Exception as e:
            print(f"ERRO: Erro ao limpar arquivos processados: {str(e)}")
    
    def collect_feedbacks_with_control(self, feedback_dir: Optional[str] = None) -> List[pd.DataFrame]:
        """
        Coleta feedbacks com controle de arquivos já processados.
        
        Args:
            feedback_dir: Diretório de feedbacks (opcional, usa self.feedback_dir se None)
            
        Returns:
            Lista de DataFrames de arquivos não processados anteriormente
        """
        target_dir = Path(feedback_dir) if feedback_dir else self.feedback_dir
        
        if not target_dir.exists():
            print(f"AVISO: Diretorio de feedbacks nao existe: {target_dir}")
            return []
        
        # Obter arquivos já processados
        processed_files = self.get_processed_files()
        print(f"INFO: Arquivos ja processados: {len(processed_files)}")
        
        # Listar todos os arquivos de feedback
        all_feedback_files = list(target_dir.glob("feedback_*.csv"))
        
        # Filtrar apenas arquivos não processados
        new_files = [f for f in all_feedback_files if f.name not in processed_files]
        
        print(f"INFO: Total de arquivos encontrados: {len(all_feedback_files)}")
        print(f"INFO: Arquivos novos para processar: {len(new_files)}")
        
        if not new_files:
            print(f"INFO: Nenhum arquivo novo para processar")
            return []
        
        # Processar apenas arquivos novos
        feedbacks = []
        all_transaction_ids = set()  # Controle de duplicação global
        
        for file_path in new_files:
            try:
                print(f"INFO: Processando arquivo novo: {file_path.name}")
                
                # Ler arquivo
                df = pd.read_csv(file_path)
                
                # Validar se arquivo não está vazio
                if df.empty:
                    print(f"AVISO: Arquivo vazio ignorado: {file_path.name}")
                    self.mark_file_as_processed(file_path.name)
                    continue
                
                # Validar estrutura das colunas
                if not self.validate_feedback_structure(df):
                    print(f"ERRO: Estrutura invalida ignorada: {file_path.name}")
                    self.mark_file_as_processed(file_path.name)
                    continue
                
                # Remover duplicatas internas por transactionId
                initial_count = len(df)
                df = df.drop_duplicates(subset=['transactionId'], keep='last')
                removed_internal = initial_count - len(df)
                
                if removed_internal > 0:
                    print(f"INFO: Removidas {removed_internal} duplicatas internas em {file_path.name}")
                
                # Remover duplicatas globais (já processadas em arquivos anteriores)
                df_filtered = df[~df['transactionId'].isin(all_transaction_ids)]
                removed_global = len(df) - len(df_filtered)
                
                if removed_global > 0:
                    print(f"INFO: Removidas {removed_global} duplicatas globais de {file_path.name}")
                
                # Atualizar conjunto de IDs processados
                all_transaction_ids.update(df_filtered['transactionId'].tolist())
                
                if len(df_filtered) > 0:
                    feedbacks.append(df_filtered)
                    print(f"OK: {len(df_filtered)} registros validos de {file_path.name}")
                else:
                    print(f"INFO: Nenhum registro novo em {file_path.name}")
                
                # Marcar arquivo como processado
                self.mark_file_as_processed(file_path.name)
                
            except Exception as e:
                print(f"ERRO: Erro ao processar {file_path.name}: {str(e)}")
                # Marcar como processado mesmo com erro para evitar reprocessamento
                self.mark_file_as_processed(file_path.name)
                continue
        
        print(f"INFO: Total de feedbacks coletados: {len(feedbacks)} arquivos")
        total_records = sum(len(df) for df in feedbacks)
        print(f"INFO: Total de registros unicos: {total_records}")
        
        return feedbacks
    
    def merge_into_model_dataset(self, base_csv: Optional[str] = None, feedbacks_list: Optional[List[pd.DataFrame]] = None) -> pd.DataFrame:
        """
        Mescla lista de feedbacks com o dataset base para retreino.
        
        Args:
            base_csv: Caminho para arquivo CSV base (opcional, usa self.base_csv se None)
            feedbacks_list: Lista de DataFrames de feedback (opcional, coleta automaticamente se None)
            
        Returns:
            DataFrame mesclado pronto para retreino
            
        Invariantes:
            - Dataset base deve existir e ter estrutura válida
            - Feedbacks são concatenados ao final do dataset base
            - Colunas devem ser compatíveis entre base e feedbacks
            - Não remove duplicatas automaticamente (deixar para análise posterior)
            
        Riscos identificados:
            - Balanceamento: Feedbacks podem desbalancear classes
            - Duplicidade: transactionIds podem aparecer múltiplas vezes
            - Qualidade: Feedbacks podem ter dados inconsistentes
            - Volume: Muitos feedbacks podem impactar performance
            
        Nota:
            Esta função não está implementada - serve como gancho para integração futura.
            Implementação deve:
            1. Carregar dataset base
            2. Concatenar feedbacks ao final
            3. Validar estrutura resultante
            4. Retornar DataFrame consolidado
        """
        # 1. Determinar arquivo base
        target_base_csv = base_csv or self.base_csv
        
        if not os.path.exists(target_base_csv):
            raise FileNotFoundError(f"Dataset base nao encontrado: {target_base_csv}")
        
        print(f"INFO: Carregando dataset base: {target_base_csv}")
        
        # 2. Carregar dataset base
        try:
            base_df = pd.read_csv(target_base_csv)
            print(f"INFO: Dataset base carregado: {len(base_df)} registros")
        except Exception as e:
            raise Exception(f"Erro ao carregar dataset base: {str(e)}")
        
        # 3. Coletar feedbacks se não fornecidos
        if feedbacks_list is None:
            print(f"INFO: Coletando feedbacks automaticamente")
            feedbacks_list = self.collect_feedbacks_with_control()
        
        if not feedbacks_list:
            print(f"INFO: Nenhum feedback para mesclar")
            return base_df
        
        # 4. Concatenar feedbacks
        print(f"INFO: Concatenando {len(feedbacks_list)} arquivos de feedback")
        feedbacks_df = pd.concat(feedbacks_list, ignore_index=True)
        
        # 5. Validações de integração
        validation_result = self.validate_dataset_integration(base_df, feedbacks_df)
        
        if not validation_result['success']:
            raise Exception(f"Validacao de integracao falhou: {validation_result['error']}")
        
        print(f"INFO: Validacao de integracao passou")
        print(f"INFO: Registros base: {validation_result['base_rows']}")
        print(f"INFO: Registros feedback: {validation_result['feedback_rows']}")
        print(f"INFO: Duplicatas encontradas: {validation_result['duplicates']}")
        
        # 6. Mesclar datasets (manter apenas colunas do dataset base)
        # Adicionar colunas faltantes no feedback com valores padrão
        for col in base_df.columns:
            if col not in feedbacks_df.columns:
                feedbacks_df[col] = ''  # Valor padrão vazio
        
        # Filtrar feedbacks para ter apenas as colunas que existem no dataset base
        feedbacks_filtered = feedbacks_df[base_df.columns].copy()
        merged_df = pd.concat([base_df, feedbacks_filtered], ignore_index=True)
        
        print(f"INFO: Dataset mesclado criado: {len(merged_df)} registros total")
        print(f"INFO: Colunas mantidas: {list(base_df.columns)}")
        
        return merged_df
    
    def validate_dataset_integration(self, base_df: pd.DataFrame, feedbacks_df: pd.DataFrame) -> dict:
        """
        Valida se a integração entre base e feedbacks é válida.
        
        Args:
            base_df: DataFrame do dataset base
            feedbacks_df: DataFrame dos feedbacks
            
        Returns:
            Dicionário com resultado da validação
        """
        try:
            # 1. Validar estrutura das colunas essenciais (apenas as que existem no dataset base)
            essential_columns = [
                "aonde gastou", "natureza do gasto", "valor total", "parcelas",
                "no da parcela", "valor unitário", "tipo", "comp", "cartao"
            ]
            
            base_essential = [col for col in essential_columns if col in base_df.columns]
            feedback_essential = [col for col in essential_columns if col in feedbacks_df.columns]
            
            if base_essential != feedback_essential:
                return {
                    'success': False,
                    'error': f'Estrutura de colunas essenciais incompativel entre base e feedbacks. Base: {base_essential}, Feedback: {feedback_essential}'
                }
            
            # 2. Validar se feedbacks têm dados
            if len(feedbacks_df) == 0:
                return {
                    'success': False,
                    'error': 'Nenhum feedback para integrar'
                }
            
            # 3. Verificar duplicatas por transactionId (apenas se a coluna existir)
            duplicates = set()
            if 'transactionId' in base_df.columns and 'transactionId' in feedbacks_df.columns:
                base_ids = set(base_df['transactionId'].dropna())
                feedback_ids = set(feedbacks_df['transactionId'].dropna())
                duplicates = base_ids.intersection(feedback_ids)
            else:
                # Se não há transactionId, usar combinação de campos para detectar duplicatas
                base_combinations = set()
                feedback_combinations = set()
                
                for _, row in base_df.iterrows():
                    combo = f"{row.get('aonde gastou', '')}_{row.get('valor total', '')}_{row.get('tipo', '')}"
                    base_combinations.add(combo)
                
                for _, row in feedbacks_df.iterrows():
                    combo = f"{row.get('aonde gastou', '')}_{row.get('valor total', '')}_{row.get('tipo', '')}"
                    feedback_combinations.add(combo)
                
                duplicates = base_combinations.intersection(feedback_combinations)
            
            # 4. Validar qualidade dos dados
            quality_issues = []
            
            # Verificar valores nulos em campos críticos
            critical_fields = ['Aonde Gastou', 'Valor Unitário', 'Data', 'transactionId']
            for field in critical_fields:
                if field in feedbacks_df.columns:
                    null_count = feedbacks_df[field].isnull().sum()
                    if null_count > 0:
                        quality_issues.append(f"Campo '{field}' tem {null_count} valores nulos")
            
            # Verificar valores negativos em campos numéricos
            numeric_fields = ['Valor Unitário', 'Valor Total', 'Parcelas']
            for field in numeric_fields:
                if field in feedbacks_df.columns:
                    negative_count = (feedbacks_df[field] < 0).sum()
                    if negative_count > 0:
                        quality_issues.append(f"Campo '{field}' tem {negative_count} valores negativos")
            
            # 5. Calcular métricas de balanceamento
            balance_metrics = {}
            if 'Natureza do Gasto' in feedbacks_df.columns:
                base_categories = base_df['Natureza do Gasto'].value_counts()
                feedback_categories = feedbacks_df['Natureza do Gasto'].value_counts()
                
                balance_metrics = {
                    'base_categories': len(base_categories),
                    'feedback_categories': len(feedback_categories),
                    'new_categories': len(set(feedback_categories.index) - set(base_categories.index)),
                    'category_distribution': feedback_categories.to_dict()
                }
            
            return {
                'success': True,
                'base_rows': len(base_df),
                'feedback_rows': len(feedbacks_df),
                'duplicates': len(duplicates),
                'duplicate_ids': list(duplicates),
                'quality_issues': quality_issues,
                'balance_metrics': balance_metrics
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Erro na validacao: {str(e)}'
            }
    
    def write_merged_dataset(self, merged_df: pd.DataFrame, out_csv: Optional[str] = None) -> str:
        """
        Escreve dataset mesclado para arquivo CSV.
        
        Args:
            merged_df: DataFrame mesclado para escrever
            out_csv: Caminho de saída (opcional, usa self.base_csv se None)
            
        Returns:
            Caminho do arquivo escrito
            
        Invariantes:
            - Backup do arquivo original é criado antes da sobrescrita
            - Arquivo é escrito com encoding UTF-8
            - Estrutura de colunas é preservada
            - Timestamp de modificação é registrado
            
        Nota:
            Esta função não está implementada - serve como gancho para integração futura.
            Implementação deve:
            1. Criar backup do arquivo original
            2. Escrever DataFrame com encoding UTF-8
            3. Validar arquivo escrito
            4. Retornar caminho do arquivo
        """
        # 1. Determinar caminho de saída
        output_path = out_csv or self.base_csv
        
        print(f"INFO: Escrevendo dataset mesclado para: {output_path}")
        
        # 2. Criar backup se arquivo já existe
        backup_path = None
        if os.path.exists(output_path):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = f"{output_path}.backup_{timestamp}"
            
            try:
                shutil.copy2(output_path, backup_path)
                print(f"INFO: Backup criado: {backup_path}")
            except Exception as e:
                raise Exception(f"Erro ao criar backup: {str(e)}")
        
        # 3. Escrever dataset mesclado
        try:
            merged_df.to_csv(output_path, index=False, encoding='utf-8')
            print(f"INFO: Dataset escrito com sucesso: {len(merged_df)} registros")
        except Exception as e:
            # Restaurar backup se houver erro
            if backup_path and os.path.exists(backup_path):
                try:
                    shutil.copy2(backup_path, output_path)
                    print(f"INFO: Backup restaurado devido ao erro")
                except:
                    pass
            raise Exception(f"Erro ao escrever dataset: {str(e)}")
        
        # 4. Validar arquivo escrito
        validation_result = self.validate_written_file(output_path, backup_path)
        
        if not validation_result['success']:
            # Restaurar backup se validação falhar
            if backup_path and os.path.exists(backup_path):
                try:
                    shutil.copy2(backup_path, output_path)
                    print(f"INFO: Backup restaurado devido a falha na validacao")
                except:
                    pass
            raise Exception(f"Validacao do arquivo escrito falhou: {validation_result['error']}")
        
        print(f"INFO: Validacao do arquivo escrito passou")
        print(f"INFO: Registros originais: {validation_result['original_rows']}")
        print(f"INFO: Registros finais: {validation_result['final_rows']}")
        print(f"INFO: Novos registros: {validation_result['new_rows']}")
        
        return output_path
    
    def validate_written_file(self, new_file: str, backup_file: Optional[str] = None) -> dict:
        """
        Valida se o arquivo foi escrito corretamente.
        
        Args:
            new_file: Caminho do arquivo escrito
            backup_file: Caminho do arquivo de backup (opcional)
            
        Returns:
            Dicionário com resultado da validação
        """
        try:
            # 1. Verificar se arquivo existe
            if not os.path.exists(new_file):
                return {
                    'success': False,
                    'error': 'Arquivo escrito nao encontrado'
                }
            
            # 2. Ler arquivo escrito
            try:
                new_df = pd.read_csv(new_file)
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Erro ao ler arquivo escrito: {str(e)}'
                }
            
            # 3. Validar estrutura básica
            if len(new_df) == 0:
                return {
                    'success': False,
                    'error': 'Arquivo escrito esta vazio'
                }
            
            # 4. Validar estrutura das colunas (usar apenas as colunas essenciais que realmente existem)
            expected_columns = [
                "aonde gastou", "natureza do gasto", "valor total", "parcelas",
                "no da parcela", "valor unitário", "tipo", "comp", "cartao", "origem"
            ]
            
            if list(new_df.columns) != expected_columns:
                return {
                    'success': False,
                    'error': 'Estrutura de colunas incorreta no arquivo escrito'
                }
            
            # 5. Comparar com backup se disponível
            original_rows = 0
            if backup_file and os.path.exists(backup_file):
                try:
                    backup_df = pd.read_csv(backup_file)
                    original_rows = len(backup_df)
                except:
                    pass
            
            return {
                'success': True,
                'original_rows': original_rows,
                'final_rows': len(new_df),
                'new_rows': len(new_df) - original_rows,
                'file_size': os.path.getsize(new_file)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Erro na validacao: {str(e)}'
            }
    
    def get_backup_files(self, base_file: Optional[str] = None) -> List[str]:
        """
        Lista arquivos de backup disponíveis.
        
        Args:
            base_file: Arquivo base para buscar backups (opcional, usa self.base_csv se None)
            
        Returns:
            Lista de caminhos de arquivos de backup
        """
        target_file = base_file or self.base_csv
        backup_pattern = f"{target_file}.backup_*"
        
        import glob
        backup_files = glob.glob(backup_pattern)
        backup_files.sort(reverse=True)  # Mais recentes primeiro
        
        return backup_files
    
    def cleanup_old_backups(self, base_file: Optional[str] = None, keep_count: int = 5):
        """
        Remove backups antigos, mantendo apenas os mais recentes.
        
        Args:
            base_file: Arquivo base para limpar backups (opcional, usa self.base_csv se None)
            keep_count: Número de backups a manter
        """
        backup_files = self.get_backup_files(base_file)
        
        if len(backup_files) <= keep_count:
            print(f"INFO: Nenhum backup antigo para remover (mantendo {len(backup_files)})")
            return
        
        files_to_remove = backup_files[keep_count:]
        
        for backup_file in files_to_remove:
            try:
                os.remove(backup_file)
                print(f"INFO: Backup antigo removido: {backup_file}")
            except Exception as e:
                print(f"ERRO: Erro ao remover backup {backup_file}: {str(e)}")
        
        print(f"INFO: Limpeza de backups concluida. Mantidos: {keep_count}, Removidos: {len(files_to_remove)}")
    
    def trigger_model_retraining(self, dataset_path: str, output_dir: Optional[str] = None) -> dict:
        """
        Dispara retreino do modelo usando treinar_modelo.py.
        
        Args:
            dataset_path: Caminho para o dataset consolidado
            output_dir: Diretório de saída dos modelos
            
        Returns:
            Dicionário com resultado do retreino
        """
        import subprocess
        import os
        
        # Usar MODEL_DIR configurado se output_dir não foi fornecido
        if output_dir is None:
            output_dir = get_model_dir()
        
        print(f"INFO: Iniciando retreino do modelo")
        print(f"INFO: Dataset: {dataset_path}")
        print(f"INFO: Diretorio de saida: {output_dir}")
        
        # 1. Verificar modelos antes do treinamento
        models_before = self.get_model_timestamps(output_dir)
        
        # 2. Preparar comando
        cmd = [
            'python', 'treinar_modelo.py'
        ]
        
        # 3. Definir variáveis de ambiente
        env = os.environ.copy()
        env['TRAINING_DATA_FILE'] = dataset_path
        env['MODEL_OUTPUT_DIR'] = output_dir
        
        # 4. Executar treinamento
        try:
            print(f"INFO: Executando comando: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minutos timeout
                env=env,
                cwd=os.getcwd()
            )
            
            if result.returncode != 0:
                return {
                    'success': False,
                    'error': f'Erro no treinamento (codigo {result.returncode}): {result.stderr}',
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
            
            # 5. Verificar modelos após treinamento
            models_after = self.get_model_timestamps(output_dir)
            
            # 6. Validar se modelos foram atualizados
            updated_models = []
            expected_models = ['modelo_natureza_do_gasto.pkl', 'modelo_comp.pkl', 'modelo_parcelas.pkl']
            
            for model_name in expected_models:
                if models_after.get(model_name, 0) > models_before.get(model_name, 0):
                    updated_models.append(model_name)
            
            # 7. Validar qualidade dos modelos
            quality_results = {}
            for model_name in updated_models:
                model_path = os.path.join(output_dir, model_name)
                quality_results[model_name] = self.validate_model_quality(model_path)
            
            return {
                'success': True,
                'updated_models': updated_models,
                'models_before': models_before,
                'models_after': models_after,
                'training_output': result.stdout,
                'quality_results': quality_results,
                'execution_time': 'N/A'  # Poderia ser calculado se necessário
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Timeout no treinamento (>10min)',
                'stdout': '',
                'stderr': 'Processo interrompido por timeout'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Erro ao executar treinamento: {str(e)}',
                'stdout': '',
                'stderr': str(e)
            }
    
    def get_model_timestamps(self, models_dir: Optional[str] = None) -> dict:
        """
        Obtém timestamps dos modelos para validação.
        
        Args:
            models_dir: Diretório dos modelos (usa MODEL_DIR configurado se None)
            
        Returns:
            Dicionário com timestamps dos modelos
        """
        if models_dir is None:
            models_dir = get_model_dir()
        
        timestamps = {}
        
        if not os.path.exists(models_dir):
            return timestamps
        
        for model_file in os.listdir(models_dir):
            if model_file.endswith('.pkl'):
                model_path = os.path.join(models_dir, model_file)
                try:
                    timestamps[model_file] = os.path.getmtime(model_path)
                except OSError:
                    timestamps[model_file] = 0
        
        return timestamps
    
    def validate_model_quality(self, model_path: str) -> dict:
        """
        Valida qualidade do modelo treinado.
        
        Args:
            model_path: Caminho para o modelo .pkl
            
        Returns:
            Dicionário com resultado da validação
        """
        try:
            import joblib
            
            # Carregar modelo
            model = joblib.load(model_path)
            
            # Validações básicas
            validations = {
                'model_loaded': model is not None,
                'has_predict_method': hasattr(model, 'predict'),
                'has_predict_proba_method': hasattr(model, 'predict_proba'),
                'model_type': type(model).__name__
            }
            
            # Teste com dados de exemplo se possível
            if hasattr(model, 'predict'):
                try:
                    # Criar dados de teste simples
                    test_data = self.get_test_data_for_model()
                    if test_data is not None:
                        predictions = model.predict(test_data['X'])
                        validations['predictions_generated'] = len(predictions) > 0
                        validations['prediction_quality'] = len(set(predictions)) > 1  # Mais de uma classe
                        validations['test_samples'] = len(test_data['X'])
                except Exception as e:
                    validations['test_error'] = str(e)
            
            return {
                'success': all(validations.values()),
                'validations': validations,
                'model_size': os.path.getsize(model_path) if os.path.exists(model_path) else 0
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Erro na validacao do modelo: {str(e)}',
                'model_size': 0
            }
    
    def get_test_data_for_model(self) -> Optional[dict]:
        """
        Cria dados de teste simples para validar modelos.
        
        Returns:
            Dicionário com dados de teste ou None se não conseguir criar
        """
        try:
            # Dados de teste simples baseados na estrutura esperada
            test_data = {
                'X': [
                    "NETFLIX COM",
                    "SUPERMERCADO ABC",
                    "FARMACIA XYZ",
                    "POSTO SHELL",
                    "RESTAURANTE DEF"
                ]
            }
            
            return test_data
            
        except Exception:
            return None
    
    def run_complete_pipeline(self, base_csv: Optional[str] = None) -> dict:
        """
        Executa pipeline completo: coleta -> mesclagem -> escrita -> retreino.
        
        Args:
            base_csv: Arquivo CSV base (opcional, usa self.base_csv se None)
            
        Returns:
            Dicionário com resultado completo do pipeline
        """
        pipeline_result = {
            'success': False,
            'steps_completed': [],
            'errors': [],
            'metrics': {}
        }
        
        try:
            # Passo 1: Coletar feedbacks
            print(f"INFO: === PASSO 1: Coletando feedbacks ===")
            feedbacks = self.collect_feedbacks_with_control()
            pipeline_result['steps_completed'].append('collect_feedbacks')
            pipeline_result['metrics']['feedbacks_collected'] = len(feedbacks)
            pipeline_result['metrics']['total_feedback_records'] = sum(len(df) for df in feedbacks)
            
            if not feedbacks:
                pipeline_result['errors'].append('Nenhum feedback encontrado para processar')
                return pipeline_result
            
            # Passo 2: Mesclar com dataset base
            print(f"INFO: === PASSO 2: Mesclando com dataset base ===")
            merged_df = self.merge_into_model_dataset(base_csv=base_csv, feedbacks_list=feedbacks)
            pipeline_result['steps_completed'].append('merge_dataset')
            pipeline_result['metrics']['merged_records'] = len(merged_df)
            
            # Passo 3: Escrever dataset consolidado
            print(f"INFO: === PASSO 3: Escrevendo dataset consolidado ===")
            output_path = self.write_merged_dataset(merged_df, out_csv=base_csv)
            pipeline_result['steps_completed'].append('write_dataset')
            pipeline_result['metrics']['output_file'] = output_path
            
            # Passo 4: Retreinar modelos
            print(f"INFO: === PASSO 4: Retreinando modelos ===")
            retraining_result = self.trigger_model_retraining(output_path)
            pipeline_result['steps_completed'].append('retrain_models')
            pipeline_result['metrics']['retraining'] = retraining_result
            
            if retraining_result['success']:
                pipeline_result['success'] = True
                print(f"INFO: === PIPELINE COMPLETO EXECUTADO COM SUCESSO ===")
            else:
                pipeline_result['errors'].append(f"Erro no retreino: {retraining_result['error']}")
                print(f"ERRO: === PIPELINE FALHOU NO RETREINO ===")
            
        except Exception as e:
            pipeline_result['errors'].append(f"Erro no pipeline: {str(e)}")
            print(f"ERRO: === PIPELINE FALHOU: {str(e)} ===")
        
        return pipeline_result
    
    def get_feedback_files(self, feedback_dir: Optional[str] = None) -> List[Path]:
        """
        Lista arquivos de feedback disponíveis.
        
        Args:
            feedback_dir: Diretório de feedbacks (opcional)
            
        Returns:
            Lista de Paths para arquivos feedback_*.csv ordenados por data
        """
        target_dir = Path(feedback_dir) if feedback_dir else self.feedback_dir
        
        if not target_dir.exists():
            return []
        
        # Listar arquivos feedback_*.csv
        feedback_files = list(target_dir.glob("feedback_*.csv"))
        
        # Ordenar por nome (que inclui data)
        feedback_files.sort()
        
        return feedback_files
    
    def validate_feedback_structure(self, df: pd.DataFrame) -> bool:
        """
        Valida se DataFrame tem estrutura esperada de feedback.
        
        Args:
            df: DataFrame para validar
            
        Returns:
            True se estrutura é válida, False caso contrário
        """
        expected_columns = [
            "aonde gastou", "natureza do gasto", "valor total", "parcelas",
            "no da parcela", "valor unitário", "tipo", "comp", "data",
            "cartao", "transactionId", "modelVersion", "createdAt", "flux"
        ]
        
        return list(df.columns) == expected_columns
    
    def get_dataset_info(self, csv_path: str) -> dict:
        """
        Obtém informações sobre dataset CSV.
        
        Args:
            csv_path: Caminho para arquivo CSV
            
        Returns:
            Dicionário com informações do dataset
        """
        if not os.path.exists(csv_path):
            return {"exists": False}
        
        try:
            # Ler apenas primeiras linhas para obter info
            df = pd.read_csv(csv_path, nrows=5)
            
            return {
                "exists": True,
                "columns": list(df.columns),
                "column_count": len(df.columns),
                "sample_rows": len(df),
                "file_size": os.path.getsize(csv_path)
            }
        except Exception as e:
            return {
                "exists": True,
                "error": str(e)
            }


def create_feedback_ingestion_service(feedback_dir: str = "feedbacks", base_csv: str = "modelo_despesas_completo.csv") -> FeedbackIngestionService:
    """
    Factory function para criar instância do serviço de ingestão.
    
    Args:
        feedback_dir: Diretório de feedbacks
        base_csv: Arquivo CSV base
        
    Returns:
        Instância do FeedbackIngestionService
    """
    return FeedbackIngestionService(feedback_dir=feedback_dir, base_csv=base_csv)
