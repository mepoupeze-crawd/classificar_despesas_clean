#!/usr/bin/env python3
"""Teste direto do endpoint parse_itau"""

import requests

files = {'file': open('fatura_cartao.pdf', 'rb')}
try:
    r = requests.post('http://localhost:8081/parse_itau', files=files)
    print(f'Status: {r.status_code}')
    if r.status_code == 200:
        data = r.json()
        print(f'Items: {len(data.get("items", []))}')
        print(f'Total lines: {data.get("stats", {}).get("total_lines", 0)}')
        print(f'Matched: {data.get("stats", {}).get("matched", 0)}')
        print(f'Rejected: {data.get("stats", {}).get("rejected", 0)}')
        if data.get("items"):
            print(f'\nPrimeiro item:')
            print(f'  Date: {data["items"][0].get("date")}')
            print(f'  Description: {data["items"][0].get("description")}')
            print(f'  Amount: {data["items"][0].get("amount")}')
    else:
        print(f'Erro: {r.text}')
finally:
    files['file'].close()

