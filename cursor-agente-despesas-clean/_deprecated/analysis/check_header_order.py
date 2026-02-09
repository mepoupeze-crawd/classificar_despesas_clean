from card_pdf_parser.parser.extract import extract_lines_lr_order
import re

lines = extract_lines_lr_order('fatura_cartao_3.pdf')

CARD_HEADER_PATTERN = re.compile(r"aline i de sousa\s*\(final\s*(\d{4})\)", re.IGNORECASE)
TRANSACTION_PATTERN = re.compile(r"(\d{2}/\d{2})(.*?)(-?\d{1,3}(?:\.\d{3})*,\d{2})")

# Procurar por transações problemáticas e cabeçalhos próximos
problem_items = [
    ("12/08", "ORGANICO OSCAR FREIRE", "92,66"),
    ("12/08", "APPLE.COM/BILL", "64,90"),
    ("12/08", "CAFE ZINN", "69,30"),
    ("12/08", "EC PINHEIROS", "3,00"),
    ("13/08", "EC PINHEIROS", "3,00"),
    ("13/08", "ESPORTE CLUBE PINHEIRO", "16,60"),
    ("13/08", "SmartBreak", "11,99"),
]

print("Procurando por transações problemáticas e cabeçalhos próximos...")
print()

for i, line in enumerate(lines):
    normalized = line.lower()
    
    # Verificar se é um cabeçalho de cartão
    header_match = CARD_HEADER_PATTERN.search(normalized)
    if header_match:
        last4 = header_match.group(1)
        print(f"Linha {i}: CABEÇALHO CARTÃO {last4}")
        print(f"  {line[:120]}")
        print()
    
    # Verificar se é uma transação problemática
    for date, desc, amount in problem_items:
        if date in line and desc.lower() in normalized and amount in line:
            print(f"Linha {i}: TRANSAÇÃO PROBLEMÁTICA - {date} {desc} {amount}")
            print(f"  {line[:150]}")
            # Verificar cabeçalhos próximos (5 linhas antes e depois)
            print("  Cabeçalhos próximos:")
            for j in range(max(0, i-5), min(len(lines), i+6)):
                if j != i:
                    nearby_line = lines[j]
                    nearby_normalized = nearby_line.lower()
                    nearby_header = CARD_HEADER_PATTERN.search(nearby_normalized)
                    if nearby_header:
                        nearby_last4 = nearby_header.group(1)
                        print(f"    Linha {j} ({'antes' if j < i else 'depois'}): CARTÃO {nearby_last4}")
            print()

