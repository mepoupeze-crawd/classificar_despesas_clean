import requests
url = 'http://localhost:8081/parse_itau'
with open('fatura_cartao.pdf', 'rb') as f:
    files = {'file': ('fatura_cartao.pdf', f, 'application/pdf')}
    r = requests.post(url, files=files)
print(r.status_code)
print(r.text[:200])
