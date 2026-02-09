import json
from pathlib import Path

result = json.loads(Path('out_fatura2.json').read_text(encoding='utf-8'))
print(f'Total de itens: {len(result["items"])}')
print(f'Stats matched: {result["stats"]["matched"]}')
print(f'Cards: {list(result["stats"]["by_card"].keys())}')
print(f'\nResumo por cartão:')
for card, data in result["stats"]["by_card"].items():
    print(f'  {card}: control_total={data["control_total"]}, calculated_total={data["calculated_total"]}, delta={data["delta"]}')

