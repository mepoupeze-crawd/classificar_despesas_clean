#!/usr/bin/env python3
"""
Script de anonimização de dados pessoais (PII)
Remove informações sensíveis de CSVs, JSONs e outros arquivos de dados.
"""
import re
import json
import csv
from pathlib import Path
from typing import Dict, List

# Mapeamentos de anonimização
ANONYMIZATION_MAP = {
    # Nomes de titulares
    "JOAO G B CALICE": "USUARIO EXEMPLO",
    "JOAO GUILHERME BERSANI CALICE": "USUARIO EXEMPLO",
    "JOAO GUILHERME B CALICE": "USUARIO EXEMPLO",
    "JOAO GUILHERME BERSANI CA": "USUARIO EXEMPLO",
    "Joao Guilherme Bersani Ca": "Usuario Exemplo",
    "João Guilherme B Calice": "Usuario Exemplo",
    "João": "Usuario1",
    "JOAO CALICE FILHO": "Pessoa T Costa",
    "Joao Calice Filho": "Pessoa T Costa",
    "ALINE I DE SOUSA": "MARIA S EXEMPLO",
    "MARIA A B CALICE": "LUCIA F EXEMPLO",
    "@ JOAO G B CALICE": "@ USUARIO EXEMPLO",
    "@ ALINE I DE SOUSA": "@ MARIA S EXEMPLO",

    # Números de cartão
    "Final 8073": "Final 0001",
    "Final 6064": "Final 0002",
    "Final 4177": "Final 0003",
    "Final 1439": "Final 0004",
    "Final 4038": "Final 0005",
    "Final 0951": "Final 0006",
    "Final 8805": "Final 0007",
    "Final 4147": "Final 0008",
    "Final 9826": "Final 0009",
    "Final 1298": "Final 0010",

    # Conta bancária
    "0992-01.000531.2": "0000-00.000000.0",

    # CNPJs
    "007526557000100": "000000000000000",
    "CNPJ 007526557000100": "CNPJ 000000000000000",

    # Nomes de terceiros em PIX (substituir por genéricos)
    "Bruno Homsi Consolim": "Pessoa A Silva",
    "Mauricio Falcao Teti Filh": "Pessoa B Santos",
    "Miguel Lunetta": "Pessoa C Oliveira",
    "D DOS SANTOS OLIVEIRA AS": "Pessoa D Costa",
    "D dos Santos Oliveira": "Pessoa D Costa",
    "CAROLINE GABRIELA ABDALLA": "Pessoa E Lima",
    "Caroline Gabriela Abdalla": "Pessoa E Lima",
    "Izabel Garcia Duarte": "Pessoa F Souza",
    "Fernando Conde Marcelino": "Pessoa G Pereira",
    "Lukas Carmona Macedo de S": "Pessoa H Rodrigues",
    "Maria Angela Bersani Cali": "Pessoa I Alves",
    "Andres Enrique Bale": "Pessoa J Fernandes",
    "Guillermo Marcelo Bale": "Pessoa K Ribeiro",
    "Isabel Hering": "Pessoa L Carvalho",
    "Beatriz Lord Kreisler": "Pessoa M Gomes",
    "Fernanda Vautier Franco S": "Pessoa N Martins",
    "LUIS ALBERTO FIGUEIREDO D": "Pessoa O Araujo",
    "Luis Alberto Figueiredo D": "Pessoa O Araujo",
    "Eduardo Paes Candeias": "Pessoa P Rocha",
    "Laerth de Jesus Bernardo": "Pessoa Q Almeida",
    "Fernando Henrique Tric": "Pessoa R Dias",
    "Raphael Tricarico": "Pessoa S Cardoso",
    "Giuliana Bersani Calice": "Pessoa U Nascimento",
    "GIULIANA BERSANI CALICE": "PESSOA U NASCIMENTO",

    # Outros padrões sensíveis
    "fin.calice.site": "fin.exemplo.site",
    "BERSANI CALICE": "EXEMPLO SILVA",  # Full name variants
    "Bersani Calice": "Exemplo Silva",
    "BERSANI": "SILVA",
    "Bersani": "Silva",
    "MCALICE": "MEXEMPLO",  # Transaction codes
    "CALICE": "EXEMPLO",    # Other occurrences
    "Calice": "Exemplo",
    "calice": "exemplo",
}

def anonymize_text(text: str) -> str:
    """Substitui dados pessoais no texto por versões anonimizadas."""
    if not isinstance(text, str):
        return text

    result = text
    for original, replacement in ANONYMIZATION_MAP.items():
        result = result.replace(original, replacement)

    return result

def anonymize_csv_file(file_path: Path):
    """Anonimiza um arquivo CSV."""
    print(f"Anonimizando CSV: {file_path}")

    # Ler o arquivo
    with open(file_path, 'r', encoding='utf-8-sig', errors='ignore') as f:
        content = f.read()

    # Anonimizar
    anonymized = anonymize_text(content)

    # Escrever de volta
    with open(file_path, 'w', encoding='utf-8', newline='') as f:
        f.write(anonymized)

    print(f"  [OK] Anonimizado: {file_path.name}")

def anonymize_json_file(file_path: Path):
    """Anonimiza um arquivo JSON."""
    print(f"Anonimizando JSON: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Converter para string, anonimizar, e converter de volta
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        anonymized_str = anonymize_text(json_str)
        anonymized_data = json.loads(anonymized_str)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(anonymized_data, f, ensure_ascii=False, indent=2)

        print(f"  [OK] Anonimizado: {file_path.name}")
    except Exception as e:
        print(f"  [ERRO] Erro ao processar {file_path.name}: {e}")

def main():
    base_dir = Path(__file__).parent

    print("=" * 60)
    print("ANONIMIZACAO DE DADOS PESSOAIS (PII)")
    print("=" * 60)
    print()

    # Lista de arquivos CSV para anonimizar
    csv_files = [
        "modelo_despesas_completo.csv",
        "gastos_categorizados.csv",
        "inputs/input_fatura_banco.csv",
        "outputs/extrato_bruto.csv",
        "outputs/extrato_formatado.csv",
        "feedbacks/feedback_2025-11-02.csv",
        "feedbacks/feedback_2025-11-04.csv",
        "feedbacks/feedback_2025-11-03.csv",
        "feedbacks/feedback_2025-11-17.csv",
        "feedbacks/feedback_2025-11-23.csv",
    ]

    # Lista de arquivos JSON para anonimizar
    json_files = [
        "fat3.json",
        "tests/expected_fatura_itau.json",
        "tests/output_esperado.json",
        "tests/output_esperado2.json",
        "tests/output_esperado3.json",
        "tests/output_fatura3.json",
    ]

    print("FASE 1: Anonimizando arquivos CSV")
    print("-" * 60)
    for csv_file in csv_files:
        file_path = base_dir / csv_file
        if file_path.exists():
            anonymize_csv_file(file_path)
        else:
            print(f"  [AVISO] Arquivo nao encontrado: {csv_file}")

    print()
    print("FASE 2: Anonimizando arquivos JSON")
    print("-" * 60)
    for json_file in json_files:
        file_path = base_dir / json_file
        if file_path.exists():
            anonymize_json_file(file_path)
        else:
            print(f"  [AVISO] Arquivo nao encontrado: {json_file}")

    print()
    print("=" * 60)
    print("[CONCLUIDO] ANONIMIZACAO CONCLUIDA")
    print("=" * 60)
    print()
    print("Próximos passos:")
    print("1. Revisar os arquivos anonimizados")
    print("2. Deletar arquivos deprecated em _deprecated/outputs/")
    print("3. Limpar PII no código-fonte (app/examples_feedback.py)")
    print("4. Criar repositório novo sem histórico Git")

if __name__ == "__main__":
    main()
