import pandas as pd
import os
import re
from datetime import datetime

# Caminhos locais
caminho_base = "E:\Documentos\IA"
caminho_gastos = os.path.join(caminho_base, "agente_despesas", "gastos_categorizados.csv")
caminho_consolidado = os.path.join(caminho_base, "sugestoes", "Consolidado Geral - Consolidado.csv")

# Leitura dos arquivos
df_gastos = pd.read_csv(caminho_gastos)
df_consolidado = pd.read_csv(caminho_consolidado)

# Remove a coluna 'cartao' se existir
if 'cartao' in df_gastos.columns:
    df_gastos = df_gastos.drop(columns=['cartao'])

# Garante que as colunas I (Data texto), J (mês numérico) e K (ano numérico) existam
df_gastos['Data'] = ''
df_gastos['mês'] = ''
df_gastos['ano'] = ''

# Regex para identificar datas no formato dd/mm/yyyy ou similar
def extrair_data_do_texto(texto):
    match = re.search(r'\d{2}/\d{2}/\d{4}', texto)
    if match:
        try:
            return datetime.strptime(match.group(), "%d/%m/%Y")
        except:
            return None
    return None

# Aplica a extração nas descrições (primeira coluna)
primeira_coluna = df_gastos.columns[0]
datas_extraidas = df_gastos[primeira_coluna].apply(extrair_data_do_texto)

# Constrói as colunas I, J, K com base nas datas extraídas
def formatar_data(dt):
    if pd.isna(dt):
        return ('', '', '')
    try:
        col_i = dt.strftime('%b./%y').lower()
        col_j = dt.month
        col_k = dt.strftime('%y')
        return (col_i, col_j, col_k)
    except:
        return ('', '', '')

df_gastos[['Data', 'mês', 'ano']] = pd.DataFrame(
    datas_extraidas.apply(formatar_data).tolist(),
    index=df_gastos.index
)

# Junta os dados ao consolidado
df_atualizado = pd.concat([df_consolidado, df_gastos], ignore_index=True)

# Salva o novo arquivo sobrescrevendo o consolidado
df_atualizado.to_csv(caminho_consolidado, index=False, encoding='utf-8-sig')

print("[OK] Consolidado atualizado com as novas linhas, coluna 'cartao' removida, e colunas I, J, K preenchidas.")
