import subprocess
import sys
import time
from datetime import datetime

def log_step(step_num, description):
    """Log com timestamp para cada etapa."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"\n[{timestamp}] [STEP] Etapa {step_num}: {description}")

def run_script(script_name, description):
    """Executa um script Python com tratamento de erro."""
    try:
        print(f"   Executando: python {script_name}")
        result = subprocess.run([sys.executable, script_name], check=True, capture_output=True, text=True)
        print(f"   [OK] {description} - Concluido com sucesso")
        if result.stdout.strip():
            print(f"   [OUTPUT] {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   [ERROR] Erro ao executar {script_name}: {e}")
        if e.stdout:
            print(f"   [OUTPUT] {e.stdout}")
        if e.stderr:
            print(f"   [ERROR] {e.stderr}")
        return False

def main():
    """Pipeline principal usando o novo módulo spend_classification."""
    start_time = time.time()
    
    print("=" * 80)
    print("PIPELINE DE GASTOS - USANDO SPEND_CLASSIFICATION")
    print("=" * 80)
    
    # Etapa 1: Preparar dados base
    log_step(1, "Unindo modelo base com feedbacks...")
    if not run_script("unir_modelo_e_feedback.py", "Uniao de modelo e feedbacks"):
        print("[ERROR] Falha na Etapa 1. Pipeline interrompido.")
        return False
    
    # Etapa 2: Treinar modelos
    log_step(2, "Treinando modelos com dados completos...")
    if not run_script("treinar_modelo.py", "Treinamento de modelos"):
        print("[ERROR] Falha na Etapa 2. Pipeline interrompido.")
        return False
    
    # Etapa 3: Converter fatura bancaria
    log_step(3, "Convertendo fatura bancaria em input_formatado.csv...")
    if not run_script("transformar_outputbanco.py", "Conversao de fatura bancaria"):
        print("[ERROR] Falha na Etapa 3. Pipeline interrompido.")
        return False
    
    # Etapa 4: Converter extrato bancario
    log_step(4, "Convertendo extrato bancario em extrato_formatado.csv...")
    if not run_script("extrato_xls_em_csv.py", "Conversao de extrato bancario"):
        print("[ERROR] Falha na Etapa 4. Pipeline interrompido.")
        return False
    
    # Etapa 5: Unir extrato com fatura
    log_step(5, "Unindo extrato com input_formatado.csv...")
    if not run_script("unir_extrato_com_fatura.py", "Uniao de extrato e fatura"):
        print("[ERROR] Falha na Etapa 5. Pipeline interrompido.")
        return False
    
    # Etapa 6: Classificacao usando o novo modulo
    log_step(6, "Classificando despesas usando spend_classification...")
    print("   [INFO] Usando o novo pipeline de classificacao otimizado")
    print("   [INFO] Pipeline: Rules Engine -> Similarity -> Model Adapter -> Fallback")
    if not run_script("classificar_despesas.py", "Classificacao de despesas"):
        print("[ERROR] Falha na Etapa 6. Pipeline interrompido.")
        return False
    
    # Etapa 7: Consolidar resultados
    log_step(7, "Juntando as novas despesas no consolidado geral...")
    if not run_script("unir_gasto_formatado_com_tabela_completa.py", "Consolidacao geral"):
        print("[ERROR] Falha na Etapa 7. Pipeline interrompido.")
        return False
    
    # Estatisticas finais
    end_time = time.time()
    total_time = end_time - start_time
    
    print("\n" + "=" * 80)
    print("[SUCCESS] PIPELINE CONCLUIDA COM SUCESSO!")
    print("=" * 80)
    print(f"[TIME] Tempo total: {total_time:.2f} segundos")
    print(f"[MODULE] Modulo utilizado: spend_classification")
    print(f"[OUTPUT] Arquivo gerado: gastos_categorizados.csv")
    print("=" * 80)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
