from card_pdf_parser.parser.extract import extract_lines_lr_order
for idx,line in enumerate(extract_lines_lr_order('fatura_cartao.pdf')):
    if idx >= 320 and idx <= 330:
        print(idx, repr(line))
