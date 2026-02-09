import pandas as pd
import numpy as np
import re
from datetime import datetime
from spend_classification.engines import ClassificationPipeline
from spend_classification.core.schemas import ExpenseTransaction

# === Inicializa o pipeline de classificação ===
pipeline = ClassificationPipeline()

# === Função para converter DataFrame em transações ===
def df_to_transactions(df):
    """Converte DataFrame em lista de ExpenseTransaction."""
    transactions = []
    
    for _, row in df.iterrows():
        try:
            # Parse da data
            if pd.notna(row.get('data')):
                date_str = str(row['data']).strip()
                try:
                    # Tenta diferentes formatos de data
                    if '/' in date_str:
                        date_obj = datetime.strptime(date_str, '%d/%m/%Y')
                    elif '-' in date_str:
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    else:
                        date_obj = datetime.now()
                except:
                    date_obj = datetime.now()
            else:
                date_obj = datetime.now()
            
            # Parse do valor
            valor_str = str(row.get('valor_r_', row.get('valor', 0))).replace(',', '.')
            try:
                valor = float(valor_str)
                # Garante que o valor seja positivo (schema requirement)
                if valor <= 0:
                    valor = 0.01  # Valor mínimo positivo
            except:
                valor = 0.01  # Valor mínimo positivo
            
            # Cria transação
            transaction = ExpenseTransaction(
                id=str(row.get('id', len(transactions))),
                description=str(row.get('descricao', '')),
                amount=valor,
                date=date_obj,
                card_holder=str(row.get('cartao', '')),
                origin=str(row.get('origem', '')),
                metadata={
                    'original_row': row.to_dict()
                }
            )
            transactions.append(transaction)
            
        except Exception as e:
            print(f"⚠️ Erro ao converter linha {len(transactions)}: {e}")
            continue
    
    return transactions

# === Funções auxiliares ===
def extrair_parcelas(texto):
    match = re.search(r'[\(\[]\s*(\d{1,2})\s*/\s*(\d{1,2})\s*[\)\]]', str(texto))
    return match.groups() if match else (None, None)

def extrair_num(valor):
    valor = str(valor).strip()
    if valor.lower().startswith("duvida"):
        return np.nan
    try:
        return int(valor)
    except ValueError:
        return np.nan

def parse_valor(valor):
    try:
        return float(str(valor).replace(",", "."))
    except:
        return np.nan

# === Leitura do input ===
print("[INFO] Lendo arquivo de entrada...")
df_input = pd.read_csv("outputs/output_fatura_e_extrato.csv")

# Normaliza colunas
df_input.columns = (
    df_input.columns
    .str.strip()
    .str.lower()
    .str.normalize("NFKD")
    .str.encode("ascii", errors="ignore")
    .str.decode("utf-8")
    .str.replace("valor__rs__", "valor_r_", regex=False)
    .str.replace(r"[^a-z0-9_]", "_", regex=True)
)
df_input = df_input.dropna(subset=["descricao"]).reset_index(drop=True)

print(f"[INFO] Processando {len(df_input)} transacoes...")

# === Converte DataFrame em transações ===
transactions = df_to_transactions(df_input)
print(f"[OK] {len(transactions)} transacoes convertidas para o formato do pipeline")

# === Classificação usando o novo pipeline ===
print("[INFO] Iniciando classificacao com o novo pipeline...")
predictions, elapsed_ms = pipeline.predict_batch(transactions)

print(f"[OK] Classificacao concluida em {elapsed_ms:.2f}ms")
print(f"[INFO] Performance: {elapsed_ms/len(transactions):.2f}ms por transacao")

# === Extrai resultados ===
pred_nat = [p.label for p in predictions]
pred_confidences = [p.confidence for p in predictions]
pred_methods = [p.method_used for p in predictions]

# === Processa dados originais para outras colunas ===
descricoes = df_input["descricao"]
cartaos = df_input.get("cartao", [""] * len(df_input))
origens = df_input.get("origem", [""] * len(df_input))

# === Extrai parcelas das descrições ===
final_parcelas, final_no_parcela = [], []
for texto in descricoes:
    no, total = extrair_parcelas(texto)
    final_no_parcela.append(no if no else "")
    final_parcelas.append(total if total else "")

# === Determina tipo baseado em origem ===
pred_tipo = []
for origem in origens:
    origem_norm = str(origem).lower().strip()
    if origem_norm == "fatura":
        pred_tipo.append("crédito")
    elif origem_norm == "extrato":
        pred_tipo.append("débito")
    else:
        pred_tipo.append("crédito")  # Default

# === Determina Comp baseado em cartão ===
pred_comp_final = []
for cartao in cartaos:
    cartao_str = str(cartao).lower()
    
    # Regras simples para Comp
    if "casa" in cartao_str or "angela" in cartao_str:
        pred_comp_final.append("planilha comp")
    elif "aline" in cartao_str:
        pred_comp_final.append("Gastos Aline")
    elif "joao" in cartao_str or "joão" in cartao_str:
        pred_comp_final.append("Gastos Joao")
    else:
        pred_comp_final.append("")

# === Formata "Aonde Gastou" ===
aonde_gastou_formatado = df_input["data"].astype(str).str.strip() + " - " + df_input["descricao"].astype(str).str.strip()

# === Monta dataframe final ===
coluna_valor = next(col for col in df_input.columns if "valor" in col and "r" in col)
df_saida = pd.DataFrame({
    "Aonde Gastou": aonde_gastou_formatado,
    "Natureza do Gasto": pred_nat,
    "Confiança": pred_confidences,
    "Método": pred_methods,
    "Valor Total": df_input[coluna_valor],
    "Parcelas": final_parcelas,
    "No da Parcela": final_no_parcela,
    "Valor Unitário": df_input[coluna_valor],
    "tipo": pred_tipo,
    "Comp": pred_comp_final,
    "cartao": df_input["cartao"]
})

# Multiplicacao e debug
df_saida["Parcelas_num"] = df_saida["Parcelas"].apply(extrair_num)
df_saida["Valor_Unitario_num"] = df_saida["Valor Unitário"].apply(parse_valor)

valores_totais = []
for i, row in df_saida.iterrows():
    parcelas = row["Parcelas_num"]
    unit = row["Valor_Unitario_num"]
    if pd.notna(parcelas) and pd.notna(unit):
        total_calc = parcelas * unit
        total_fmt = f"{total_calc:.2f}".replace(".", ",")
        valores_totais.append(total_fmt)
    else:
        valores_totais.append(row["Valor Total"])

df_saida["Valor Total"] = valores_totais

# Limpa colunas auxiliares
df_saida.drop(columns=["Parcelas_num", "Valor_Unitario_num"], inplace=True)
df_saida = df_saida.astype(str).replace(["nan", "NaN", "None"], "")
df_saida.to_csv("gastos_categorizados.csv", index=False)

# === Estatísticas finais ===
print(f"\n[STATS] ESTATISTICAS FINAIS:")
print(f"   Total de transações: {len(df_saida)}")
print(f"   Tempo total de processamento: {elapsed_ms:.2f}ms")
print(f"   Performance média: {elapsed_ms/len(df_saida):.2f}ms por transação")

# Conta métodos usados
method_counts = {}
for method in pred_methods:
    method_counts[method] = method_counts.get(method, 0) + 1

print(f"\n[METHODS] DISTRIBUICAO DE METODOS:")
for method, count in method_counts.items():
    percentage = (count / len(pred_methods)) * 100
    print(f"   {method}: {count} ({percentage:.1f}%)")

# Conta categorias mais comuns
category_counts = {}
for category in pred_nat:
    if category and category != "duvida":
        category_counts[category] = category_counts.get(category, 0) + 1

print(f"\n[CATEGORIES] CATEGORIAS MAIS COMUNS:")
sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
for category, count in sorted_categories[:5]:  # Top 5
    percentage = (count / len(pred_nat)) * 100
    print(f"   {category}: {count} ({percentage:.1f}%)")

print(f"\n[OK] Arquivo 'gastos_categorizados.csv' criado com sucesso.")
print(f"[INFO] Usando o novo modulo spend_classification com pipeline otimizado!")
