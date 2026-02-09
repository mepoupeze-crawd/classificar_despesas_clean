import json
from pathlib import Path

result = json.loads(Path('out3.json').read_text(encoding='utf-8'))
print(f'Total de itens: {len(result["items"])}')
print(f'Stats matched: {result["stats"]["matched"]}')
print(f'Cards: {list(result["stats"]["by_card"].keys())}')

