from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.rules import detect_card_marker, extract_date, extract_value
import re
from decimal import Decimal

lines = extract_lines_lr_order('fatura_cartao_3.pdf')

# Encontrar linha do total do 9826
for i, line in enumerate(lines):
    marker = detect_card_marker(line)
    if marker and marker[0] == 'total' and marker[1] == '9826':
        print(f"Linha do total: {line}")
        
        # Extrair todos os valores
        value_matches = list(re.finditer(r'-?\s*\d{1,3}(?:\.\d{3})*,\d{2}', line))
        print(f"\nValores encontrados na linha do total:")
        for match in value_matches:
            val_str = match.group(0).replace('.', '').replace(',', '.').replace(' ', '').lstrip('-')
            try:
                val = Decimal(val_str)
                if match.group(0).strip().startswith('-'):
                    val = -val
                print(f"  -> {val} (posição {match.start()}-{match.end()})")
            except:
                pass
        
        # Verificar se há uma transação na linha do total
        invoice_year = 2025
        date = extract_date(line, default_year=invoice_year)
        value_first = extract_value(line, prefer_last=False)
        value_last = extract_value(line, prefer_last=True)
        
        print(f"\nData: {date}")
        print(f"Valor (prefer_last=False): {value_first}")
        print(f"Valor (prefer_last=True): {value_last}")
        
        # O subtotal do PDF é 9139.39
        # Se há uma transação com valor 10.80, o total deveria ser 9139.39 + 10.80 = 9150.19
        # Mas o subtotal é 9139.39, então a transação de 10.80 já está incluída no subtotal
        # Isso significa que precisamos contar a transação da linha do total também
        
        break

