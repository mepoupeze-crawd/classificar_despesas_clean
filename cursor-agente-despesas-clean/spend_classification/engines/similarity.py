"""
Módulo de similaridade baseado em TF-IDF para classificação de despesas.

Este módulo carrega dados do modelo_despesas_completo.csv e constrói um índice TF-IDF
para encontrar transações similares baseadas em similaridade de cosseno.
"""

import os
import logging
from typing import Optional, Tuple, Dict, Any
import re
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

logger = logging.getLogger(__name__)


class SimilarityClassifier:
    """
    Classificador de similaridade baseado em TF-IDF e similaridade de cosseno.
    
    Carrega dados do modelo_despesas_completo.csv e constrói um índice TF-IDF para
    encontrar transações similares.
    """
    
    def __init__(self, csv_path: str = None, threshold: float = 0.70):
        """
        Inicializa o classificador de similaridade.
        
        Args:
            csv_path: Caminho para o arquivo CSV com dados de treinamento (opcional, usa env var se None)
            threshold: Limite mínimo de similaridade para retornar resultado
        """
        # Usar variável de ambiente se csv_path não for fornecido
        if csv_path is None:
            csv_path = os.getenv('TRAINING_DATA_FILE', 'modelo_despesas_completo.csv')
        
        self.csv_path = csv_path
        self.threshold = float(os.getenv('SIMILARITY_THRESHOLD', threshold))
        self.vectorizer = None
        self.tfidf_matrix = None
        self.data = None
        self.is_loaded = False
        
        # Carregar dados se o arquivo existir
        self._load_data()
    
    def _normalize_description(self, text: str) -> str:
        """
        Normaliza descrição removendo datas, padrões de parcela e prefixos comuns.
        
        Exemplos:
        - "16/06/2025 - Usregen*Ltda" → "usregen*ltda"
        - "31/12/2024 - Amazon" → "amazon"
        - "04/05 Netflix" → "netflix"
        - "Evo*Usregen Ltda (02/03)" → "usregen ltda"
        - "Bkg*Hotel At Booking C" → "hotel at booking c"
        
        Args:
            text: Texto da descrição a ser normalizado
            
        Returns:
            Texto normalizado em minúsculas e sem datas, parcelas e prefixos
        """
        # Remover datas no formato DD/MM/YYYY ou DD/MM
        text = re.sub(r'\d{2}/\d{2}/\d{4}', '', text)
        text = re.sub(r'\d{2}/\d{2}(?!\d)', '', text)
        
        # Remover padrões de parcelas: (02/03), (1/12), etc.
        text = re.sub(r'\([0-9/]+\)', '', text)
        
        # Remover prefixos comuns: Evo*, Bkg*, Htm*, Ifd*, etc.
        text = re.sub(r'^\w+\*', '', text)
        
        # Remover palavras genéricas: pagamento, compra, anuidade, debito, credito, pix
        text = re.sub(r'\b(pagamento|compra|anuidade|debito|credito|pix)\b', '', text, flags=re.IGNORECASE)
        
        # Remover hífens e espaços extras
        text = re.sub(r'^[\s-]+|[\s-]+$', '', text)
        text = re.sub(r'\s+', ' ', text)
        
        # Remover parênteses vazios e outros caracteres especiais residuais
        text = re.sub(r'[()]+', '', text)
        
        return text.lower().strip()
    
    def _load_data(self) -> None:
        """
        Carrega os dados do CSV e constrói o índice TF-IDF.
        """
        try:
            if not os.path.exists(self.csv_path):
                logger.warning(f"Arquivo {self.csv_path} não encontrado")
                return
            
            # Carregar dados
            self.data = pd.read_csv(self.csv_path, encoding='utf-8')
            logger.info(f"Carregados {len(self.data)} registros de {self.csv_path}")
            
            # Verificar se tem as colunas necessárias
            if 'aonde gastou' not in self.data.columns or 'natureza do gasto' not in self.data.columns:
                logger.error("CSV deve conter colunas 'aonde gastou' e 'natureza do gasto'")
                return
            
            # Limpar e preparar textos
            descriptions_raw = self.data['aonde gastou'].fillna('').astype(str)
            
            # Normalizar descrições removendo datas
            descriptions = [self._normalize_description(desc) for desc in descriptions_raw]
            
            categories = self.data['natureza do gasto'].fillna('').astype(str)
            
            # Construir índice TF-IDF
            num_docs = len(descriptions)
            
            # Ajustar parâmetros baseado no tamanho do dataset
            if num_docs == 1:
                # Para um único documento, usar configurações especiais
                min_df_val = 1
                max_df_val = 1.0
                max_features_val = 1000
            elif num_docs <= 10:
                # Para datasets pequenos
                min_df_val = 1
                max_df_val = 1.0
                max_features_val = min(5000, num_docs * 10)
            else:
                # Para datasets maiores
                min_df_val = max(1, int(0.01 * num_docs))
                max_df_val = min(0.95, max(0.5, 1.0 - (2.0 / num_docs)))
                max_features_val = min(10000, num_docs * 2)
            
            self.vectorizer = TfidfVectorizer(
                lowercase=True,
                stop_words=None,  # Não usar stop words em português por padrão
                ngram_range=(1, 2),  # Unigramas e bigramas
                max_features=max_features_val,
                min_df=min_df_val,
                max_df=max_df_val
            )
            
            self.tfidf_matrix = self.vectorizer.fit_transform(descriptions)
            self.is_loaded = True
            
            logger.info(f"Índice TF-IDF construído com {self.tfidf_matrix.shape[1]} features")
            
        except Exception as e:
            logger.error(f"Erro ao carregar dados: {e}")
            self.is_loaded = False
    
    def query(self, text: str) -> Optional[Tuple[str, float]]:
        """
        Busca transação similar ao texto fornecido.
        
        Args:
            text: Texto da transação a ser classificada
            
        Returns:
            Tupla (categoria, score) se encontrar similaridade acima do threshold,
            None caso contrário
        """
        if not self.is_loaded or not text or not text.strip():
            return None
        
        try:
            # Normalizar descrição de entrada
            text_normalized = self._normalize_description(text.strip())
            
            # Usar TF-IDF com descrição normalizada
            text_vector = self.vectorizer.transform([text_normalized])
            
            # Calcular similaridade de cosseno
            similarities = cosine_similarity(text_vector, self.tfidf_matrix)
            
            # Encontrar a maior similaridade
            max_similarity_idx = np.argmax(similarities[0])
            max_similarity_score = similarities[0][max_similarity_idx]
            
            # Verificar se está acima do threshold
            if max_similarity_score >= self.threshold:
                category = self.data.iloc[max_similarity_idx]['natureza do gasto']
                
                # Log detalhado para debugging
                matched_description = self.data.iloc[max_similarity_idx]['aonde gastou']
                logger.debug(f"Similaridade encontrada: '{text}' (normalizado: '{text_normalized}') -> '{matched_description}' "
                           f"(categoria: {category}, score: {max_similarity_score:.3f})")
                
                return category, float(max_similarity_score)
            else:
                logger.debug(f"Similaridade {max_similarity_score:.3f} abaixo do threshold {self.threshold}")
                return None
                
        except Exception as e:
            logger.error(f"Erro na busca de similaridade: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do classificador.
        
        Returns:
            Dicionário com estatísticas
        """
        if not self.is_loaded:
            return {
                'loaded': False,
                'records': 0,
                'features': 0,
                'threshold': self.threshold
            }
        
        return {
            'loaded': True,
            'records': len(self.data),
            'features': self.tfidf_matrix.shape[1] if self.tfidf_matrix is not None else 0,
            'threshold': self.threshold,
            'csv_path': self.csv_path
        }
    
    def reload(self) -> bool:
        """
        Recarrega os dados do CSV.
        
        Returns:
            True se recarregou com sucesso, False caso contrário
        """
        self.is_loaded = False
        self._load_data()
        return self.is_loaded


# Função de conveniência para uso direto
def create_similarity_classifier(csv_path: str = "modelo_despesas_completo.csv", threshold: float = 0.70) -> SimilarityClassifier:
    """
    Cria uma instância do classificador de similaridade.
    
    Args:
        csv_path: Caminho para o arquivo CSV
        threshold: Limite mínimo de similaridade
        
    Returns:
        Instância do SimilarityClassifier
    """
    return SimilarityClassifier(csv_path, threshold)
