# Dockerfile para Microserviço de Classificação de Despesas
# Otimizado para build local e publicação no GCP

FROM python:3.11-slim

# Instalar build essentials mínimos para sklearn e limpar cache
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Criar usuário não-root para segurança
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Definir diretório de trabalho
WORKDIR /app

# Copiar requirements.txt e instalar dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY app/ ./app/
COPY spend_classification/ ./spend_classification/
COPY card_pdf_parser/ ./card_pdf_parser/
COPY services/ ./services/

# Copiar arquivo CSV de dados de treinamento
COPY modelo_despesas_completo.csv ./

# Copiar script de treinamento
COPY treinar_modelo.py ./

# Copiar modelos para diretório /models (paridade com Cloud Run)
COPY modelos/ /models/

# Criar diretórios necessários
RUN mkdir -p /models /app/feedbacks

# Definir variáveis de ambiente padrão
# Nota: Valores serão sobrescritos por docker-compose.yml ou variáveis de ambiente se necessário
ENV PORT=8080
# AI Fallback - Habilitado por padrão
# Para desabilitar: ENABLE_FALLBACK_AI=false
# Requer pelo menos uma API key: OPENAI_API_KEY ou ANTHROPIC_API_KEY
# Opcional: SERPAPI_API_KEY para melhorar qualidade da classificação
ENV ENABLE_FALLBACK_AI=true
ENV SIMILARITY_THRESHOLD=0.9
ENV MODEL_THRESHOLD=0.70
ENV MODEL_DIR=/models
ENV TRAINING_DATA_FILE=/app/modelo_despesas_completo.csv
ENV FEEDBACK_DIR=/app/feedbacks
ENV FEEDBACK_FILENAME_TEMPLATE=feedback_%Y-%m-%d.csv

# Mudar propriedade dos arquivos para o usuário não-root
RUN chown -R appuser:appuser /app /models /app/feedbacks

# Mudar para usuário não-root
USER appuser

# Expor porta
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/healthz')"

# Comando para executar o serviço
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1"]
