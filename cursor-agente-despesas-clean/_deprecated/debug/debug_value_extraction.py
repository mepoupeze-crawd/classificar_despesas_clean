import re
from decimal import Decimal

VALUE_PATTERN = re.compile(r'([+-]?\s*\d{1,3}(?:\.\d{3})*,\d{2})')

line = "29/07 TRELA*Pedido Trela - 0,01"
print(f"Linha: {line}")

matches_iter = list(VALUE_PATTERN.finditer(line))
print(f"Matches encontrados: {len(matches_iter)}")

for match in matches_iter:
    raw_value = match.group(0)
    print(f"\nMatch: '{raw_value}'")
    value_str = raw_value.replace(' ', '').replace('\xa0', '')
    print(f"Após remover espaços: '{value_str}'")
    sign = 1
    if value_str.startswith('+'):
        value_str = value_str[1:]
    elif value_str.startswith('-'):
        sign = -1
        value_str = value_str[1:]
    print(f"Após processar sinal: '{value_str}', sign={sign}")
    value_str = value_str.replace('.', '').replace(',', '.')
    print(f"Após converter formato: '{value_str}'")
    try:
        value = Decimal(value_str) * sign
        print(f"Valor final: {value}, abs={abs(value)}")
        print(f"Condição 0.01 <= abs(value): {0.01 <= abs(value)}")
        print(f"Condição abs(value) <= 1000000: {abs(value) <= 1000000}")
        if 0.01 <= abs(value) <= 1000000:
            print("Valor VÁLIDO")
        else:
            print("Valor FILTRADO")
    except Exception as e:
        print(f"Erro: {e}")


