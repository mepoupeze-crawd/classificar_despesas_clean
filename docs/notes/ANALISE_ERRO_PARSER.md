# Análise do Erro no Parser Itaú

## Problema Identificado

O erro ocorre na função `extract_lines_lr_order` em `card_pdf_parser/parser/extract.py` quando o PDF é processado como bytes ou BytesIO.

### Causa Raiz

1. **Fluxo do código:**
   - `parse_itau_fatura()` recebe bytes do PDF
   - Converte bytes para `BytesIO` na linha 83 de `itau_cartao_parser.py`
   - Chama `extract_lines_lr_order(pdf_input)` onde `pdf_input` é um `BytesIO`

2. **O problema acontece em `extract_lines_lr_order`:**
   - Linha 536: `pdfplumber.open(pdf_path)` abre e **consome** o BytesIO
   - Se `words` está vazio, entra no fallback (linhas 544-557)
   - Linha 548: Tenta chamar `extract_chars_from_pdf(pdf_path)` 
   - **ERRO**: O BytesIO já foi consumido na primeira leitura e não pode ser reaberto sem resetar o ponteiro

3. **Por que isso acontece:**
   - Um objeto `BytesIO` mantém um ponteiro interno que avança conforme é lido
   - Após `pdfplumber.open()` ler o conteúdo, o ponteiro está no final
   - Quando `extract_chars_from_pdf()` tenta abrir novamente, o BytesIO já está "esgotado"
   - `pdfplumber.open()` não consegue ler um BytesIO que já foi totalmente consumido

### Localização do Bug

**Arquivo:** `card_pdf_parser/parser/extract.py`
**Função:** `extract_lines_lr_order()` 
**Linhas problemáticas:** 544-557 (especialmente linha 548)

```python
# Linha 536: Primeira leitura (consome o BytesIO)
with pdfplumber.open(pdf_path) as pdf:
    for page in pdf.pages:
        words = page.extract_words(...)
        if words:
            # Processa normalmente
        else:
            # FALLBACK - PROBLEMA AQUI
            if chars_cache is None:
                # Linha 548: Tenta reabrir o mesmo BytesIO que já foi consumido
                chars_cache = extract_chars_from_pdf(pdf_path)
```

### Solução Implementada

A solução foi extrair os caracteres **diretamente das páginas já abertas** em vez de tentar reabrir o PDF. Isso evita o problema de consumir o BytesIO.

**Mudança no código:**
- Antes: Tentava chamar `extract_chars_from_pdf(pdf_path)` no fallback, o que falhava com BytesIO consumido
- Agora: Extrai caracteres diretamente de `page.chars` quando `page.extract_words()` retorna vazio

**Código corrigido (linhas 550-572):**
```python
else:
    # Fallback: extrair caracteres diretamente da página já aberta
    # Isso evita o problema de tentar reabrir um BytesIO consumido
    page_chars: List[Char] = []
    page_chars_data = page.chars
    for char_data in page_chars_data:
        page_chars.append(Char(...))
    
    if page_chars:
        split_x = detect_column_split(page_chars, page.page_number)
        # ... processar normalmente
```

Esta solução funciona para:
- ✅ Arquivos (string path)
- ✅ Bytes (convertidos para BytesIO)
- ✅ BytesIO (mesmo após consumo parcial)

