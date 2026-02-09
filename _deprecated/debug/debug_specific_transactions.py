import json
from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.classify import LineClassifier
from card_pdf_parser.parser.rules import extract_date, extract_value, extract_description

pdf_path = 'fatura_cartao_3.pdf'
lines = extract_lines_lr_order(pdf_path)

print("=== Procurando transações específicas mencionadas ===\n")

# Transações esperadas para cartão 7430
expected_7430 = [
    ("2025-03-13", "PURA VIDA", "69.52"),
    ("2025-04-29", "PURA VIDA", "311.02"),
    ("2025-04-30", "CLINICA ADRIANA VI", "2048.50"),
    ("2025-05-12", "PG *SHOPGEORGIA", "356.68"),
    ("2025-05-16", "FRATEX INDUSTRIA E", "111.96"),
    ("2025-05-17", "CABANA CRAFTS", "211.36"),
    ("2025-05-21", "ZARA BRASIL LTDA", "143.50"),
    ("2025-06-03", "GALLERIST COM IMP", "125.82"),
    ("2025-06-03", "PASSARO AZUL COMER", "266.35"),
    ("2025-06-03", "ZARA BRASIL LTDA", "135.50"),
    ("2025-06-12", "SEPHORA CIDJARDIN", "83.00"),
    ("2025-06-17", "MTKS JOIAS", "107.50"),
    ("2025-07-01", "BRUNA CUTAIT", "487.74"),
    ("2025-07-23", "DROGASIL1255", "160.10"),
    ("2025-08-14", "SEG CARTAO PROTEGIDO", "10.19"),
]

# Transações esperadas para cartão 9826
expected_9826 = [
    ("2025-07-01", "BRUNA CUTAIT", "-0.18"),  # Estorno
    ("2025-08-12", "ESPORTE CLUBE PINHEIRO", "10.80"),
    ("2025-08-12", "ORGANICO OSCAR FREIRE", "92.66"),
]

# Processar PDF
classifier = LineClassifier()
items, rejects = classifier.classify_lines(lines)

print("=== Verificando transações do cartão 7430 ===\n")
for exp_date, exp_desc, exp_amount in expected_7430:
    found = False
    for item in items:
        if item.last4 and "7430" in item.last4:
            if exp_date in item.date and exp_desc.upper() in item.description.upper():
                amount_str = str(item.amount)
                if abs(float(amount_str) - float(exp_amount)) < 0.01:
                    found = True
                    print(f"[OK] {exp_date} - {exp_desc} - {exp_amount}")
                    break
    if not found:
        print(f"[FALTA] {exp_date} - {exp_desc} - {exp_amount}")

print("\n=== Verificando transações do cartão 9826 ===\n")
for exp_date, exp_desc, exp_amount in expected_9826:
    found = False
    for item in items:
        if item.last4 and "9826" in item.last4:
            if exp_date in item.date and exp_desc.upper() in item.description.upper():
                amount_str = str(item.amount)
                exp_abs = abs(float(exp_amount))
                if abs(float(amount_str) - exp_abs) < 0.01:
                    found = True
                    print(f"[OK] {exp_date} - {exp_desc} - {exp_amount} (flux={item.flux})")
                    break
    if not found:
        print(f"[FALTA] {exp_date} - {exp_desc} - {exp_amount}")

# Procurar linhas específicas no PDF
print("\n=== Procurando linhas específicas no PDF ===\n")
search_terms = [
    "PURA VIDA",
    "CABANA CRAFTS",
    "ORGANICO OSCAR FREIRE",
    "BRUNA CUTAIT.*-.*0,18",
    "ESPORTE CLUBE PINHEIRO.*10,80"
]

for term in search_terms:
    import re
    pattern = re.compile(term, re.IGNORECASE)
    for i, line in enumerate(lines):
        if pattern.search(line):
            print(f"Linha {i}: {line[:100]}...")
            break


