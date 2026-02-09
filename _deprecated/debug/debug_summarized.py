from services.pdf.itau_cartao_parser import ItauCartaoParser

parser = ItauCartaoParser()
result = parser.parse('fatura_cartao_3.pdf')

# Verificar itens problemáticos
problem_items = [
    ("2025-08-12", "APPLE.COM/BILL", "64.90"),
    ("2025-08-12", "CAFE ZINN", "69.30"),
    ("2025-08-12", "EC PINHEIROS", "3.00"),
    ("2025-08-12", "ORGANICO OSCAR FREIRE", "92.66"),
    ("2025-08-13", "EC PINHEIROS", "3.00"),
    ("2025-08-13", "ESPORTE CLUBE PINHEIRO", "16.60"),
    ("2025-08-13", "SmartBreak", "11.99"),
]

print("Verificando itens problemáticos:")
for date, desc, amount in problem_items:
    found = [i for i in result['items'] if i.get('date') == date and i.get('description') == desc and i.get('amount') == amount]
    if found:
        item = found[0]
        print(f"  {date} {desc} {amount}: last4 = {item.get('last4')}")
    else:
        print(f"  {date} {desc} {amount}: NÃO ENCONTRADO")

