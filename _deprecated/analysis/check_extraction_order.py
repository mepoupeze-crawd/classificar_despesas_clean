from card_pdf_parser.parser.extract import extract_lines_lr_order

pdf_path = 'fatura_cartao_3.pdf'
lines = extract_lines_lr_order(pdf_path)

print("=== Ordem de extração das linhas 170-190 ===\n")
for i in range(170, min(191, len(lines))):
    print(f"Linha {i}: {lines[i][:80]}")


