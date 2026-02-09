import json
from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.rules import extract_value, extract_date
from card_pdf_parser.parser.classify import LineClassifier
import re

pdf_path = 'fatura_cartao_2.pdf'
lines = extract_lines_lr_order(pdf_path)

print("=== Procurando 'SEG CARTAO PROTEGIDO' no PDF ===\n")

# Procurar linhas que contêm a descrição
for i, line in enumerate(lines):
    line_clean = line.strip()
    if not line_clean:
        continue
    
    if "seg" in line_clean.lower() and "cartao" in line_clean.lower():
        print(f"Linha {i+1}: '{line_clean}'")
        print(f"  Tamanho: {len(line_clean)}")
        
        # Verificar todos os padrões de data
        date_patterns = list(re.finditer(r'(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?', line_clean))
        print(f"\n  Padrões de data encontrados:")
        for match in date_patterns:
            print(f"    '{match.group()}' na posição {match.start()}")
        
        # Verificar valores monetários
        value_patterns = list(re.finditer(r'\d{1,3}(?:\.\d{3})*,\d{2}|\d+,\d{2}', line_clean))
        print(f"\n  Valores monetários encontrados:")
        for match in value_patterns:
            print(f"    '{match.group()}' na posição {match.start()}")
        
        # Tentar extrair data e valor
        date = extract_date(line_clean)
        value = extract_value(line_clean)
        
        print(f"\n  Data extraída: {date}")
        print(f"  Valor extraído: {value}")
        
        # Verificar se seria classificada como transação
        if date and value:
            print(f"  Status: TEM DATA E VALOR - deveria ser classificada")
        elif date:
            print(f"  Status: TEM DATA mas SEM VALOR")
        elif value:
            print(f"  Status: TEM VALOR mas SEM DATA")
        else:
            print(f"  Status: SEM DATA E SEM VALOR - seria rejeitada")
        
        print("-" * 80 + "\n")

# Agora processar completo e ver o que foi rejeitado
print("\n=== Processando PDF completo e verificando rejeições ===\n")
classifier = LineClassifier()
items, rejects = classifier.classify_lines(lines)

# Procurar nas rejeições
print(f"Total de itens extraídos: {len(items)}")
print(f"Total de linhas rejeitadas: {len(rejects)}\n")

print("Linhas rejeitadas que contêm 'seg' ou 'cartao':")
for reject in rejects:
    if "seg" in reject.line.lower() or "cartao" in reject.line.lower():
        print(f"  Linha: '{reject.line}'")
        print(f"  Motivo: {reject.reason}\n")

# Procurar nos itens extraídos
print("\nItens extraídos que contêm 'seg' ou 'cartao':")
for item in items:
    if "seg" in item.description.lower() or "cartao" in item.description.lower():
        print(f"  Descrição: {item.description}")
        print(f"  Data: {item.date}")
        print(f"  Valor: {item.amount}")
        print(f"  last4: {item.last4}\n")

