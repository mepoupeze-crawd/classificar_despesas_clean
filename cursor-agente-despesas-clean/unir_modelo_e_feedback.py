import pandas as pd
import glob
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Carrega base principal
df_base = pd.read_csv("modelo_despesas_completo.csv")
df_base.columns = df_base.columns.str.strip().str.lower().str.replace("ã", "a")
if "cartao" not in df_base.columns:
    df_base["cartao"] = ""
df_base["origem"] = "base"

# Define colunas essenciais (baseadas no arquivo base)
essential_columns = list(df_base.columns)
print(f"[INFO] Colunas essenciais definidas: {essential_columns}")

# Carrega feedbacks
feedback_files = glob.glob(os.path.join("feedbacks", "feedback_*.csv"))
df_feedbacks = []

for f in feedback_files:
    print(f"[INFO] Processando arquivo: {f}")
    df = pd.read_csv(f)
    df.columns = df.columns.str.strip().str.lower().str.replace("ã", "a")
    
    print(f"[INFO] Colunas originais do feedback: {list(df.columns)}")
    
    # CORREÇÃO: Garantir que apenas colunas essenciais sejam mantidas
    for col in essential_columns:
        if col not in df.columns:
            df[col] = ""  # Adiciona coluna com valor vazio se não existir
            print(f"[INFO] Adicionada coluna faltante: {col}")
    
    # CORREÇÃO: Remover colunas extras que não existem no arquivo base
    df = df[essential_columns]  # Manter apenas colunas essenciais
    print(f"[INFO] Colunas finais do feedback: {list(df.columns)}")
    
    df_feedbacks.append(df)

# Junta tudo (agora com estrutura idêntica)
df_total = pd.concat([df_base] + df_feedbacks, ignore_index=True)

# Salva dataset final usando variável de ambiente
output_file = os.getenv('TRAINING_DATA_FILE', 'modelo_despesas_completo.csv')
df_total.to_csv(output_file, index=False)
print(f"[OK] '{output_file}' criado com base em modelo + feedbacks.")
print(f"[INFO] Colunas finais: {list(df_total.columns)}")
print(f"[INFO] Total de registros: {len(df_total)}")
