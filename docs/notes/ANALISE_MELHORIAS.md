# Análise de Melhorias para o Parser de PDF Itaú

## Problemas Identificados

### 1. Campo "flux" Faltando
- **Problema**: O modelo `ParsedItem` não tem o campo `flux` que é esperado no output
- **Solução**: Adicionar campo `flux: str = "Saída"` ao modelo

### 2. Poucas Transações Extraídas
- **Problema**: Apenas 17 items extraídos quando deveria haver ~71 para o cartão 9826
- **Causa Principal**: Validação de ordem de datas está rejeitando transações válidas
  - Exemplo: Encontra transação de 2025-10-06 primeiro, depois rejeita todas as anteriores (04/30, 05/16, etc.)
- **Solução**: 
  - Resetar `last_date_by_card` ao encontrar novo cabeçalho de cartão
  - Melhorar inferência de ano para datas curtas (DD/MM)
  - Permitir que datas sejam inferidas baseadas no contexto (última data conhecida)

### 3. Descrições Mal Limpas
- **Problema**: Descrições contêm datas extras, valores intermediários, códigos
  - Exemplo: `"31/03CLINICA ADRIANA VI06/"` → deveria ser `"CLINICA ADRIANA VI"`
  - Exemplo: `"12/05PG *SHOPGEORGIA 05/05"` → deveria ser `"PG *SHOPGEORGIA"`
  - Exemplo: `"R$ 06/10/"` → deveria ser removido (não é uma transação válida)
- **Solução**: Melhorar função `extract_description` para:
  - Remover todas as datas (não apenas a primeira)
  - Remover valores intermediários que não são o valor da transação
  - Remover códigos como "05/10", "03/03", "04/05" que aparecem nas descrições
  - Remover "R$" e outros símbolos monetários

### 4. Linhas Incompletas
- **Problema**: Muitas linhas têm apenas data ou apenas valor (123 linhas com valor, 90 com data)
- **Causa**: Transações podem estar em múltiplas linhas no PDF
- **Solução**: Melhorar agrupamento de linhas para:
  - Detectar quando uma linha tem apenas data e a próxima tem descrição + valor
  - Agrupar linhas relacionadas (mesma posição Y ou próximas)
  - Considerar que descrições podem estar em múltiplas linhas

### 5. Detecção de Cabeçalhos de Cartão
- **Problema**: Não está detectando todos os cabeçalhos de cartão
  - Padrão esperado: "Lançamentos no cartão (final 9826)"
  - Padrão atual: "XXXX.XXXX.XXXX.9826" ou "(final 9826)"
- **Solução**: Melhorar regex para incluir padrões como:
  - "Lançamentos no cartão (final XXXX)"
  - "ALINE I DE SOUSA (final 9826)"
  - Qualquer linha contendo "(final XXXX)" ou "final XXXX"

### 6. Valores Incorretos
- **Problema**: Alguns valores parecem ser totais (ex: R$ 11426.65, R$ 101252.39)
- **Causa**: Pode estar capturando totais/subtotais como transações individuais
- **Solução**: 
  - Filtrar valores muito grandes (> R$ 10.000) ou que aparecem em linhas de subtotal
  - Validar que valores estão em linhas com descrição de estabelecimento

### 7. Inferência de Ano
- **Problema**: Ano sendo inferido incorretamente para datas curtas (DD/MM)
- **Causa**: Assumindo ano da fatura sem considerar ordem cronológica
- **Solução**: 
  - Inferir ano baseado na última data conhecida para o cartão
  - Se data for anterior à última conhecida, pode ser do ano seguinte (mas precisa validar contexto)
  - Considerar que faturas geralmente têm transações do mês anterior ao mês de vencimento

### 8. Linhas de Categoria
- **Problema**: Linhas como "SAÚDE.SAO PAULO", "VESTUÁRIO SAO ROQUE" não estão sendo ignoradas
- **Solução**: Adicionar padrões de ruído para linhas de categoria

## Melhorias Propostas

### Prioridade Alta
1. ✅ Adicionar campo `flux` ao modelo
2. ✅ Corrigir validação de ordem de datas (reset ao mudar cartão)
3. ✅ Melhorar detecção de cabeçalhos de cartão
4. ✅ Melhorar limpeza de descrições
5. ✅ Melhorar inferência de ano

### Prioridade Média
6. ✅ Melhorar agrupamento de linhas (transações em múltiplas linhas)
7. ✅ Melhorar regex para datas e valores
8. ✅ Filtrar valores muito grandes (totais)

### Prioridade Baixa
9. ✅ Melhorar detecção de linhas de categoria
10. ✅ Melhorar tratamento de linhas incompletas

## Perguntas para o Usuário

1. **Estrutura do PDF**: 
   - As transações estão sempre em uma única linha ou podem estar em múltiplas linhas?
   - Exemplo: Data em uma linha, descrição em outra, valor em outra?

2. **Ordem de Leitura**:
   - A ordem L→R está correta? (esquerda primeiro, depois direita)
   - Dentro de cada coluna, a ordem é topo→baixo?

3. **Ano das Transações**:
   - Como determinar o ano de datas curtas (DD/MM)?
   - A fatura tem uma data de vencimento/emissão que indica o período?

4. **Cabeçalhos de Cartão**:
   - Todos os cabeçalhos seguem o padrão "Lançamentos no cartão (final XXXX)"?
   - Há outros padrões que devo considerar?

5. **Linhas de Categoria**:
   - As linhas como "SAÚDE.SAO PAULO" aparecem sempre abaixo das transações?
   - Devem ser completamente ignoradas?

6. **Valores**:
   - Há algum padrão para identificar totais/subtotais vs transações individuais?
   - Valores muito grandes (> R$ 10.000) são sempre totais?

