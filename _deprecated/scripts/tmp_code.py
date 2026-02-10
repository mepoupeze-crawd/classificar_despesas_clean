from card_pdf_parser.parser.extract import extract_lines_lr_order_block_based
from card_pdf_parser.parser.classify import LineClassifier
lines = extract_lines_lr_order_block_based('fatura_cartao_3.pdf')
classifier = LineClassifier()
# rebuild classification to access sorted right blocks by monkey patch
left_blocks = []
right_blocks = []
items=[]
rejects=[]
# replicate code portion
in_section=False
for idx,raw_line in enumerate(lines):
    line = raw_line.strip()
    if not line:
        continue
    import re
    if re.match(r'^LANÇAMENTOS:\s*COMPRAS', raw_line, re.IGNORECASE) or re.match(r'^LANÇAMENTOS:\s*PRODUTOS', raw_line, re.IGNORECASE):
        in_section=True
        continue
    if re.match(r'^COMPRAS\s+PARCELADAS', raw_line, re.IGNORECASE) or re.match(r'^LIMITES\s+DE\s+CRÉDITO', raw_line, re.IGNORECASE) or re.match(r'^ENCARGOS', raw_line, re.IGNORECASE):
        in_section=False
        continue
    if not in_section:
        continue
