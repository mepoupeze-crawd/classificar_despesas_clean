import pandas as pd
import re
import os

# Diretórios
input_dir = "inputs"
output_dir = "outputs"

# Certifica que a pasta de saída existe
os.makedirs(output_dir, exist_ok=True)

# Arquivos
arquivo_entrada = os.path.join(input_dir, "input_fatura_banco.csv")
arquivo_saida = os.path.join(output_dir, "output_fatura_formatado.csv")

# Carrega o arquivo bruto
df_raw = pd.read_csv(arquivo_entrada)

# Colunas: A = Data, B = Descrição, D = Valor
df = df_raw.iloc[:, [0, 1, 3]].copy()
df.columns = ["Data", "Descricao", "Valor (R$)"]

# Inicializa controle
cartao_atual = None
linhas_processadas = []
ignorar_linhas = 0

for i in range(len(df)):
    texto = str(df.loc[i, "Descricao"]).strip()
    valor = str(df.loc[i, "Valor (R$)"]).strip()
    data = str(df.loc[i, "Data"]).strip()

    # Ignorar linhas após "Resumo de despesas"
    if "resumo de despesas" in texto.lower():
        if linhas_processadas:
            linhas_processadas.pop()  # remove a linha anterior
        break

    # Ignorar linhas marcadas após "Final XXXX"
    if ignorar_linhas > 0:
        ignorar_linhas -= 1
        continue

    # Ignorar linhas com "Subtotal"
    if texto.lower().startswith("subtotal"):
        continue

    # Captura "Final XXXX" e nome do cartão
    match = re.match(r"Final (\d{4})", texto)
    if match:
        final = match.group(0)
        if i + 1 < len(df):
            nome = str(df.loc[i + 1, "Descricao"]).strip()
            cartao_atual = f"{final} - {nome}"
        ignorar_linhas = 2
        continue

    # Adiciona linha válida
    if texto:
        linhas_processadas.append({
            "Data": data,
            "Descrição": texto,
            "Valor (R$)": valor,
            "cartao": cartao_atual
        })

# Cria DataFrame final
df_formatado = pd.DataFrame(linhas_processadas)

# Salva como novo CSV
df_formatado.to_csv(arquivo_saida, index=False)
print(f"[OK] Arquivo '{arquivo_saida}' gerado com sucesso!")
