from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.rules import detect_card_marker, extract_date, extract_value
import re
from decimal import Decimal

lines = extract_lines_lr_order('fatura_cartao_3.pdf')

# Verificar linha específica que pode ter problema
print("=== Verificando linha 62 ===")
line_62 = lines[62]
print(f"Linha 62: {line_62}")

date_matches = list(re.finditer(r'\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b', line_62))
value_matches = list(re.finditer(r'-?\s*\d{1,3}(?:\.\d{3})*,\d{2}', line_62))

print(f"Datas encontradas: {len(date_matches)}")
for match in date_matches:
    print(f"  -> {match.group(0)}")

print(f"Valores encontrados: {len(value_matches)}")
for match in value_matches:
    print(f"  -> {match.group(0)}")

# Verificar se esta linha é concatenada ou não
is_concatenated = len(date_matches) >= 2 and len(value_matches) >= 2
print(f"É concatenada: {is_concatenated}")

# Verificar linha 105 também
print("\n=== Verificando linha 105 ===")
line_105 = lines[105]
print(f"Linha 105: {line_105}")

date_matches_105 = list(re.finditer(r'\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b', line_105))
value_matches_105 = list(re.finditer(r'-?\s*\d{1,3}(?:\.\d{3})*,\d{2}', line_105))

print(f"Datas encontradas: {len(date_matches_105)}")
for match in date_matches_105:
    print(f"  -> {match.group(0)}")

print(f"Valores encontrados: {len(value_matches_105)}")
for match in value_matches_105:
    print(f"  -> {match.group(0)}")

is_concatenated_105 = len(date_matches_105) >= 2 and len(value_matches_105) >= 2
print(f"É concatenada: {is_concatenated_105}")

# Verificar se há um padrão: talvez algumas linhas que parecem não concatenadas
# na verdade sejam concatenadas mas com datas no formato diferente
print("\n=== Verificando padrões de datas ===")
# Linha 62: "03/06 ZARA BRASIL LTDA 03/05 135,50"
# Isso parece ter duas datas mas apenas um valor
# Talvez "03/05" seja parte da descrição ou seja um padrão de parcelas?

# Verificar se "03/05" pode ser um padrão de parcelas
parcela_pattern = re.compile(r'(\d{1,2})/(\d{1,2})')
matches_62 = parcela_pattern.findall(line_62)
print(f"Padrões DD/MM na linha 62: {matches_62}")

# Verificar se há valores que não estão sendo contabilizados
# Talvez o problema seja que precisamos contar valores de parcelas também
print("\n=== Verificando se há valores de parcelas ===")
# Verificar se há padrões como "05/10" que podem ser parcelas
for i in range(48, 175):
    line = lines[i]
    # Procurar padrões que podem ser parcelas
    parcela_matches = re.findall(r'(\d{1,2})/(\d{1,2})(?:\s|$)', line)
    value_matches = list(re.finditer(r'-?\s*\d{1,3}(?:\.\d{3})*,\d{2}', line))
    
    # Se há múltiplos padrões DD/MM mas apenas um valor, pode ser uma transação com parcelas
    if len(parcela_matches) >= 2 and len(value_matches) == 1:
        # Verificar se o segundo padrão pode ser parcela
        first_date = parcela_matches[0]
        second_pattern = parcela_matches[1]
        
        # Se o segundo padrão tem primeiro número <= 12 e segundo <= 31, pode ser data ou parcela
        if int(second_pattern[0]) <= 12 and int(second_pattern[1]) <= 31:
            # Pode ser uma data ou parcela
            # Se está próximo ao valor, pode ser parcela
            val_str = value_matches[0].group(0).replace('.', '').replace(',', '.').replace(' ', '').lstrip('-')
            try:
                val = Decimal(val_str)
                if val > 100:  # Valores significativos
                    print(f"Linha {i}: possível parcela ou data extra - '{line[:70]}'")
                    print(f"  -> Padrões: {parcela_matches}, Valor: {val}")
            except:
                pass

