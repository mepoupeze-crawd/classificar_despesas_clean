import pdfplumber
from card_pdf_parser.parser.extract import _group_words_by_rows, _detect_column_split_from_rows, _rows_to_text

pdf_path = 'fatura_cartao_3.pdf'
with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[0]  # Assumindo que a linha 178 está na primeira página
    words = page.extract_words(use_text_flow=False, keep_blank_chars=False)
    rows = _group_words_by_rows(words)
    split_x = _detect_column_split_from_rows(rows)
    
    # Encontrar a linha que contém "EC PINHEIROS 3,00"
    for i, row in enumerate(rows):
        row_text = " ".join(w.get("text", "") for w in sorted(row, key=lambda w: w["x0"])).strip()
        if "EC PINHEIROS" in row_text and "3,00" in row_text:
            print(f"Linha {i}: {row_text}")
            print(f"Split X: {split_x}")
            print(f"Palavras na linha:")
            for word in sorted(row, key=lambda w: w["x0"]):
                print(f"  '{word.get('text', '')}' - x0={word.get('x0', 0)}, x1={word.get('x1', 0)}")
            break


