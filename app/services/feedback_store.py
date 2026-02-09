#!/usr/bin/env python3
"""
Serviço de persistência de feedback para correções do usuário.

Este módulo gerencia a escrita de feedbacks em arquivos CSV diários,
com suporte a concorrência e criação automática de cabeçalhos.
"""

import os
import csv
import threading
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path


class FeedbackStore:
    """
    Serviço para persistir feedbacks em arquivos CSV diários.
    
    Características:
    - Criação automática de arquivos com cabeçalho
    - Append seguro com locks por arquivo
    - Mapeamento de campos para formato CSV
    - Suporte a timezone configurável
    """
    
    def __init__(
        self,
        feedback_dir: str = "feedbacks",
        filename_template: str = "feedback_%Y-%m-%d.csv",
        timezone: Optional[str] = None
    ):
        """
        Inicializa o serviço de feedback.
        
        Args:
            feedback_dir: Diretório para armazenar arquivos de feedback
            filename_template: Template do nome do arquivo (strftime)
            timezone: Timezone para data do arquivo (opcional)
        """
        self.feedback_dir = Path(feedback_dir)
        self.filename_template = filename_template
        self.timezone = timezone
        
        # Criar diretório se não existir
        self.feedback_dir.mkdir(exist_ok=True)
        
        # Locks por arquivo para concorrência
        self._file_locks: Dict[str, threading.Lock] = {}
        self._locks_lock = threading.Lock()
        
        # Colunas do CSV na ordem especificada (devem corresponder ao dataset base)
        self.csv_columns = [
            "aonde gastou",           # Minúsculo para corresponder ao dataset base
            "natureza do gasto",      # Minúsculo para corresponder ao dataset base
            "valor total",            # Minúsculo para corresponder ao dataset base
            "parcelas",
            "no da parcela",
            "valor unitário",
            "tipo",
            "comp",
            "data",
            "cartao",
            "transactionId",
            "modelVersion",
            "createdAt",
            "flux"
        ]
    
    def _get_file_lock(self, filepath: str) -> threading.Lock:
        """Obtém lock para um arquivo específico."""
        with self._locks_lock:
            if filepath not in self._file_locks:
                self._file_locks[filepath] = threading.Lock()
            return self._file_locks[filepath]
    
    def _get_today_filename(self) -> str:
        """Gera nome do arquivo para hoje."""
        now = datetime.now()
        if self.timezone:
            # Se timezone especificado, converter (implementação básica)
            # Para implementação completa, usar pytz ou zoneinfo
            pass
        return now.strftime(self.filename_template)
    
    def _map_feedback_to_csv_row(self, feedback: Dict[str, Any]) -> List[str]:
        """
        Mapeia dados de feedback para linha do CSV.
        
        Args:
            feedback: Dados do feedback
            
        Returns:
            Lista de valores para a linha do CSV
        """
        # Calcular parcelas (default 1 se ausente)
        parcelas = feedback.get("parcelas", 1)
        if parcelas is None:
            parcelas = 1
        
        # Calcular valor total
        amount = float(feedback.get("amount", 0))
        valor_total = amount * parcelas
        
        # Mapear campos para CSV
        row = [
            feedback.get("description", ""),                    # Aonde Gastou
            feedback.get("category", ""),                        # Natureza do Gasto
            str(valor_total),                                   # Valor Total
            str(parcelas),                                       # Parcelas
            str(feedback.get("numero_parcela", "") or ""),       # No da Parcela
            str(amount),                                         # Valor Unitário
            feedback.get("source", ""),                         # tipo
            feedback.get("comp", ""),                            # Comp
            feedback.get("date", ""),                            # Data
            feedback.get("card", ""),                            # cartao
            feedback.get("transactionId", ""),                   # transactionId
            feedback.get("modelVersion", ""),                    # modelVersion
            feedback.get("createdAt", ""),                       # createdAt
            feedback.get("flux", "")                             # flux
        ]
        
        return row
    
    def _file_exists_with_header(self, filepath: Path) -> bool:
        """Verifica se arquivo existe e tem cabeçalho."""
        if not filepath.exists():
            return False
        
        try:
            with open(filepath, 'r', encoding='utf-8', newline='') as f:
                reader = csv.reader(f)
                first_row = next(reader, None)
                return first_row == self.csv_columns
        except Exception:
            return False
    
    def save_feedbacks(self, feedbacks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Salva lista de feedbacks no arquivo CSV do dia.
        
        Args:
            feedbacks: Lista de feedbacks para salvar
            
        Returns:
            Dicionário com resultado da operação
        """
        if not feedbacks:
            return {
                "saved_rows": 0,
                "file_path": "",
                "columns": self.csv_columns
            }
        
        # Gerar nome do arquivo para hoje
        filename = self._get_today_filename()
        filepath = self.feedback_dir / filename
        
        print(f"INFO: Salvando feedbacks em: {filepath}")
        print(f"INFO: Diretório de feedback: {self.feedback_dir}")
        print(f"INFO: Diretório existe: {self.feedback_dir.exists()}")
        
        # Obter lock para o arquivo
        file_lock = self._get_file_lock(str(filepath))
        
        with file_lock:
            # Verificar se arquivo existe com cabeçalho correto
            file_exists = self._file_exists_with_header(filepath)
            
            # Modo de escrita (append se existe, write se não)
            mode = 'a' if file_exists else 'w'
            
            try:
                with open(filepath, mode, encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    
                    # Escrever cabeçalho se arquivo novo
                    if not file_exists:
                        writer.writerow(self.csv_columns)
                    
                    # Escrever linhas de feedback
                    rows_written = 0
                    for feedback in feedbacks:
                        row = self._map_feedback_to_csv_row(feedback)
                        writer.writerow(row)
                        rows_written += 1
                
                print(f"INFO: Feedbacks salvos com sucesso: {rows_written} linhas em {filepath}")
                print(f"INFO: Arquivo existe após salvamento: {filepath.exists()}")
                
                return {
                    "saved_rows": rows_written,
                    "file_path": str(filepath),
                    "columns": self.csv_columns
                }
                
            except Exception as e:
                raise RuntimeError(f"Erro ao salvar feedbacks: {str(e)}")
    
    def get_feedback_file_info(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtém informações sobre arquivo de feedback.
        
        Args:
            date: Data no formato YYYY-MM-DD (opcional, usa hoje se não especificado)
            
        Returns:
            Informações sobre o arquivo
        """
        if date:
            try:
                # Validar formato da data
                datetime.strptime(date, "%Y-%m-%d")
                filename = f"feedback_{date}.csv"
            except ValueError:
                raise ValueError("Data deve estar no formato YYYY-MM-DD")
        else:
            filename = self._get_today_filename()
        
        filepath = self.feedback_dir / filename
        
        info = {
            "filename": filename,
            "file_path": str(filepath),
            "exists": filepath.exists(),
            "columns": self.csv_columns
        }
        
        if filepath.exists():
            try:
                stat = filepath.stat()
                info.update({
                    "size_bytes": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "has_header": self._file_exists_with_header(filepath)
                })
            except Exception as e:
                info["error"] = str(e)
        
        return info
