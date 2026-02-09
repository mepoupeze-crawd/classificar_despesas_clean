import pandas as pd
import sys
import os

# Diretórios
input_dir = "inputs"
output_dir = "outputs"

# Certifica que a pasta de saída existe
os.makedirs(output_dir, exist_ok=True)

# Caminhos de entrada e saída
xls_file = os.path.join(input_dir, "planilhaExtrato.xls")
csv_bruto = os.path.join(output_dir, "extrato_bruto.csv")
csv_formatado = os.path.join(output_dir, "extrato_formatado.csv")

# 1️⃣ Leitura do Excel
try:
    df_raw = pd.read_excel(xls_file, header=None, engine="xlrd")
except ImportError:
    print("[ERROR] xlrd nao esta instalado. Instale com: pip install xlrd")
    sys.exit(1)
except FileNotFoundError:
    print(f"[ERROR] Arquivo '{xls_file}' nao encontrado.")
    sys.exit(1)

# 2️⃣ Salva CSV bruto para verificação
df_raw.to_csv(csv_bruto, index=False, header=False)
print(f"[INFO] Arquivo bruto salvo como '{csv_bruto}'")

# 3️⃣ Encontrar "Data" na coluna A
linha_inicio = df_raw[df_raw.iloc[:, 0].astype(str).str.strip().str.upper() == "DATA"].index.min()
if pd.isna(linha_inicio):
    raise ValueError("[ERROR] A palavra 'Data' nao foi encontrada na coluna A.")

# 4️⃣ Trabalhar com dados reais
df = df_raw.iloc[linha_inicio + 1:].copy().reset_index(drop=True)

# 5️⃣ Encontrar e remover a linha "Total", a anterior e todas abaixo
linha_total = df[df[0].astype(str).str.strip().str.upper().str.contains("TOTAL")].index.min()
if not pd.isna(linha_total) and linha_total >= 1:
    df = df.iloc[:linha_total - 1]

# 6️⃣ Função para conversão BR
def br_to_float(valor):
    if isinstance(valor, str):
        valor = valor.replace(".", "").replace(",", ".")
    return pd.to_numeric(valor, errors="coerce")

# 7️⃣ Preencher coluna 3 com valores de colunas 5 e 6
valores_formatados = []
for i, row in df.iterrows():
    val5 = br_to_float(row[4]) if len(row) > 4 else None
    val6 = br_to_float(row[5]) if len(row) > 5 else None
    valor = None
    if pd.notna(val5):
        valor = -abs(val5)
    elif pd.notna(val6):
        valor = abs(val6)
    if valor is not None:
        valor_str = f"{valor:.2f}".replace(".", ",")
    else:
        valor_str = ""
    valores_formatados.append(valor_str)

df.iloc[:, 2] = valores_formatados

# 8️⃣ Coluna 4 = "CC - data_inicial a data_final"
coluna_datas = pd.to_datetime(df[0], dayfirst=True, errors="coerce")
data_inicial = coluna_datas[coluna_datas.first_valid_index()].strftime("%d/%m/%Y")
data_final = coluna_datas[coluna_datas.last_valid_index()].strftime("%d/%m/%Y")
texto_cc = f"CC - {data_inicial} a {data_final}"
df.iloc[:, 3] = texto_cc

# 9️⃣ Zerar a quinta coluna
df.iloc[:, 4] = ""

# 🔟 Manter apenas as 5 primeiras colunas
df = df.iloc[:, :5]

# 11️⃣ Exportar CSV final
df.to_csv(csv_formatado, index=False, header=False)
print(f"[OK] Arquivo final salvo como '{csv_formatado}' com virgula como separador decimal na coluna de valores.")
