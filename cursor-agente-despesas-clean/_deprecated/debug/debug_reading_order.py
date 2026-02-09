import json
from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.rules import detect_card_marker

pdf_path = 'fatura_cartao_3.pdf'
lines = extract_lines_lr_order(pdf_path)

# Verificar linhas 174-185 em detalhe
print("=== Análise detalhada das linhas 174-185 ===\n")
for i in range(174, min(186, len(lines))):
    line = lines[i]
    marker = detect_card_marker(line)
    marker_str = f" [MARCADOR: {marker}]" if marker else ""
    print(f"Linha {i}: {line}{marker_str}")

# Verificar qual cartão está ativo após cada linha
print("\n=== Simulação do processamento ===\n")
current_card = "9826"  # Assumindo que começamos com 9826
for i in range(174, min(186, len(lines))):
    line = lines[i]
    marker = detect_card_marker(line)
    
    if marker:
        kind, card = marker
        if kind == "total":
            print(f"Linha {i}: Marcador 'total' para cartão {card}")
            print(f"  Cartão atual ANTES: {current_card}")
            # Não resetar imediatamente - manter até próximo "start"
            print(f"  Cartão atual DEPOIS: {current_card} (mantido)")
        elif kind == "start":
            print(f"Linha {i}: Marcador 'start' para cartão {card}")
            print(f"  Cartão atual ANTES: {current_card}")
            # Se há transação na linha, processar com cartão anterior primeiro
            # Depois mudar para o novo cartão
            print(f"  Transação na linha deve ser processada com: {current_card}")
            current_card = card
            print(f"  Cartão atual DEPOIS: {current_card} (mudado para {card})")
    else:
        print(f"Linha {i}: Sem marcador - será processada com cartão: {current_card}")


