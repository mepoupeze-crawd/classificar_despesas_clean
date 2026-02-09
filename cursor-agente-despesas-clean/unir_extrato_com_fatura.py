import pandas as pd
import os

# Diretório de saída
output_dir = "outputs"

# Caminhos dos arquivos
arquivo_extrato = os.path.join(output_dir, "extrato_formatado.csv")
arquivo_fatura = os.path.join(output_dir, "output_fatura_formatado.csv")
arquivo_saida = os.path.join(output_dir, "output_fatura_e_extrato.csv")

# Lê os arquivos
df_extrato = pd.read_csv(arquivo_extrato, header=None)
df_fatura = pd.read_csv(arquivo_fatura)

# Renomeia colunas do extrato para se adequar ao formato da fatura
df_extrato.columns = ["Data", "Descrição", "Valor (R$)", "cartao", "_descartar"]
df_extrato.drop(columns=["_descartar"], inplace=True)

# Garante a ordem correta das colunas
colunas_padrao = ["Data", "Descrição", "Valor (R$)", "cartao"]
df_extrato = df_extrato[colunas_padrao]
df_fatura = df_fatura[colunas_padrao]

# Marca origem
df_extrato["origem"] = "extrato"
df_fatura["origem"] = "fatura"

# Concatena os dados
df_final = pd.concat([df_fatura, df_extrato], ignore_index=True)

# Salva o arquivo final unificado
df_final.to_csv(arquivo_saida, index=False)
print(f"[OK] Arquivo unificado salvo como '{arquivo_saida}'.")
