# Arquivos de Análise e Verificação Movidos

**Data:** 2025-11-15  
**Categoria:** Scripts de Análise Pontuais  
**Total de arquivos:** ~30+

## Motivo da Realocação

Estes arquivos foram criados para análises específicas durante o desenvolvimento:
- Scripts `check_*.py`: Verificações pontuais de lógica
- Scripts `analyze_*.py`: Análises de dados específicos
- Scripts `find_*.py`: Buscas por padrões específicos
- Scripts `compare_*.py`: Comparações entre outputs
- Scripts `sum_*.py`: Cálculos de totais
- Scripts `final_*.py`: Análises finais de validação
- Scripts `generate_*.py`: Geração de outputs de teste
- Scripts `verify_*.py`: Verificações de padrões

## Evidência de Não Uso

- **Não importados em código de produção:** Verificado via grep
- **Não parte da suíte de testes:** Testes oficiais em `tests/` e `spend_classification/tests/`
- **Propósito pontual:** Criados para resolver problemas específicos já resolvidos
- **Nomes indicam natureza temporária:** Prefixos indicam análises pontuais

## Arquivos Movidos

- `check_*.py` (15 arquivos)
- `analyze_*.py` (vários)
- `find_*.py` (vários)
- `compare_*.py` (vários)
- `sum_*.py` (vários)
- `final_*.py` (vários)
- `generate_*.py` (vários)
- `verify_*.py` (1 arquivo)

## Como Restaurar

```bash
git mv _deprecated/analysis/<arquivo>.py ./<arquivo>.py
```

## Impacto

**Nenhum impacto funcional.** Estes scripts eram apenas para análises pontuais e não são necessários para operação normal do sistema.


