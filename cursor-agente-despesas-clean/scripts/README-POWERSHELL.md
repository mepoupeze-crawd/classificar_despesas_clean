# Scripts PowerShell para Testes da API

Scripts PowerShell nativos (sem dependência de `jq`) para testar a API de Classificação de Despesas.

## 📋 Scripts Disponíveis

### 1. `test-health.ps1`
Testa o endpoint `/healthz` da API.

```powershell
.\scripts\test-health.ps1
```

**Variáveis de ambiente:**
- `API_URL`: URL da API (padrão: `http://localhost:8081`)

### 2. `test-classify.ps1`
Testa o endpoint `/v1/classify` com uma transação única.

```powershell
.\scripts\test-classify.ps1
```

**Variáveis de ambiente:**
- `API_URL`: URL da API (padrão: `http://localhost:8081`)

### 3. `test-classify-batch.ps1`
Testa o endpoint `/v1/classify` com múltiplas transações (lote).

```powershell
.\scripts\test-classify-batch.ps1
```

**Variáveis de ambiente:**
- `API_URL`: URL da API (padrão: `http://localhost:8081`)

### 4. `test-from-file.ps1`
Testa o endpoint `/v1/classify` usando um arquivo JSON.

```powershell
# Usar arquivo padrão (app/samples/tx_single.json)
.\scripts\test-from-file.ps1

# Especificar arquivo
.\scripts\test-from-file.ps1 app\samples\tx_batch.json
```

**Parâmetros:**
- `$args[0]`: Caminho do arquivo JSON (opcional, padrão: `app/samples/tx_single.json`)

**Variáveis de ambiente:**
- `API_URL`: URL da API (padrão: `http://localhost:8081`)

### 5. `test-api-powershell.ps1`
Script completo que testa health check e classificação.

```powershell
.\scripts\test-api-powershell.ps1
```

**Variáveis de ambiente:**
- `API_URL`: URL da API (padrão: `http://localhost:8081`)

### 6. `test-parse-itau.ps1`
Testa o endpoint `/parse_itau` para parsing de PDFs Itaú (equivalente ao `curl -F "file=@./fatura_cartao.pdf" http://localhost:8081/parse_itau | jq .`).

```powershell
# Usar arquivo padrão (./fatura_cartao.pdf)
.\scripts\test-parse-itau.ps1

# Especificar arquivo PDF
$env:PDF_PATH = "caminho/para/fatura.pdf"
.\scripts\test-parse-itau.ps1
```

**Variáveis de ambiente:**
- `API_URL`: URL da API (padrão: `http://localhost:8081`)
- `PDF_PATH`: Caminho do arquivo PDF (padrão: `./fatura_cartao.pdf`)

**Nota:** Este endpoint requer que o módulo `card_pdf_parser` esteja implementado e configurado.

## 🚀 Como Usar

### Executar script individual

```powershell
# Health check
.\scripts\test-health.ps1

# Classificação única
.\scripts\test-classify.ps1

# Classificação em lote
.\scripts\test-classify-batch.ps1

# Usar arquivo JSON
.\scripts\test-from-file.ps1 app\samples\tx_single.json
```

### Executar com URL customizada

```powershell
$env:API_URL = "http://localhost:8081"
.\scripts\test-health.ps1
```

### Executar todos os testes

```powershell
# Health check
.\scripts\test-health.ps1

# Classificação única
.\scripts\test-classify.ps1

# Classificação em lote
.\scripts\test-classify-batch.ps1

# Testar com arquivos de exemplo
.\scripts\test-from-file.ps1 app\samples\tx_single.json
.\scripts\test-from-file.ps1 app\samples\tx_batch.json

# Testar parsing de PDF (se endpoint disponível)
.\scripts\test-parse-itau.ps1
```

## ✅ Validações Realizadas

Todos os scripts verificam:

- ✅ **Health check**: Status da API
- ✅ **Estrutura da resposta**: Campos obrigatórios presentes
- ✅ **Confidence**: Valores no range [0, 1]
- ✅ **Labels**: Predições válidas
- ✅ **Métodos**: Method usado na classificação
- ✅ **Tempos**: Elapsed time presente

## 🔧 Requisitos

- **PowerShell 5.1+** ou **PowerShell Core 7+**
- **API rodando** na porta 8081 (ou URL especificada)
- **Acesso de rede** para a API

## 📝 Exemplos de Saída

### Health Check
```
🏥 Testando health check...
URL: http://localhost:8081/healthz

✅ Health check OK
Resposta: {"status":"ok"}

🎉 API está funcionando corretamente!
```

### Classificação
```
🧪 Testando classificação de transações
========================================
API URL: http://localhost:8081

1️⃣ Testando health check...
✅ Health check OK

2️⃣ Preparando payload de teste...
Payload: [{"description":"Netflix Com","amount":44.90,"date":"2024-01-01T00:00:00"}]

3️⃣ Enviando requisição de classificação...
✅ Classificação realizada com sucesso!

📊 Resposta completa:
{
  "predictions": [
    {
      "label": "Gastos com mensalidades (Gympass, Spotfy, Unicef e Rappi)",
      "confidence": 0.95,
      "method_used": "model_adapter",
      "elapsed_ms": 5.2
    }
  ],
  "total_transactions": 1,
  "elapsed_ms": 15.2
}

🔍 Verificando campos...
  ✅ Predictions encontradas: 1
  Label: Gastos com mensalidades (Gympass, Spotfy, Unicef e Rappi)
  Confidence: 0.95
  Method: model_adapter
  Elapsed: 5.2ms
  ✅ Confidence válido (0-1)

🎉 Teste concluído com sucesso!
```

## 🐛 Troubleshooting

### Erro: "Cannot connect to the remote server"
- Verifique se a API está rodando
- Verifique se a porta está correta (8081 para Docker Compose)
- Verifique se o firewall permite a conexão

### Erro: "The remote server returned an error: (404) Not Found"
- Verifique se a URL da API está correta
- Verifique se o endpoint existe (`/healthz` ou `/v1/classify`)

### Erro: "The remote server returned an error: (500) Internal Server Error"
- Verifique os logs da API
- Verifique se os modelos estão carregados corretamente
- Verifique se as variáveis de ambiente estão configuradas

## 📚 Scripts Relacionados

- `test-single.ps1`: Script original (pode requerer `jq`)
- `test-batch.ps1`: Script original (pode requerer `jq`)
- `test-api.ps1`: Script original (pode requerer `jq`)

Os scripts neste diretório (`test-*.ps1`) são versões melhoradas que **não requerem `jq`** e usam apenas comandos PowerShell nativos.

