from card_pdf_parser.parser.extract import extract_lines_lr_order

lines = extract_lines_lr_order('fatura_cartao_3.pdf')

print("Contexto ao redor das linhas problemáticas (170-195):")
print()
for i in range(170, 195):
    print(f"Linha {i}: {lines[i][:150]}")

