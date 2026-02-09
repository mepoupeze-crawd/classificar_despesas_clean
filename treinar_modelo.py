import os
import re
from collections import Counter

import joblib
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    f1_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import label_binarize
from sklearn.svm import LinearSVC
from sklearn.utils import resample

# Carregar variáveis de ambiente
load_dotenv()

# === Carrega CSV ===
arquivo = os.getenv("TRAINING_DATA_FILE", "modelo_despesas_completo.csv")
df = pd.read_csv(arquivo, encoding="utf-8-sig")
df.columns = df.columns.str.strip().str.lower()  # padroniza os nomes das colunas

# === Determina diretório de saída dos modelos ===
# Prioridade: MODEL_OUTPUT_DIR > MODEL_DIR > default "./modelos"
MODEL_OUTPUT_DIR = os.getenv("MODEL_OUTPUT_DIR") or os.getenv("MODEL_DIR", "./modelos")
os.makedirs(MODEL_OUTPUT_DIR, exist_ok=True)


def limpar_texto(texto: str) -> str:
    """Normaliza texto, preservando termos discriminativos (e.g. Restaurante)."""

    texto = str(texto)
    # Remove datas no formato dd/mm/aaaa ou semelhante
    texto = re.sub(r"\b(\d{2,4})[/-](\d{1,2})[/-](\d{2,4})\b", "", texto)
    # Remove tokens de cartão/identificadores pouco discriminativos
    texto = re.sub(
        r"\b(pagamento|compra|anuidade|debito|credito|pix|cartao)\b",
        "",
        texto,
        flags=re.IGNORECASE,
    )
    # Mantém termos específicos como nomes de estabelecimento para diferenciar classes
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


df["aonde gastou"] = df["aonde gastou"].apply(limpar_texto)


def oversample_minority(X: pd.Series, y: pd.Series, min_frac: float = 0.7):
    """Faz oversampling leve para classes abaixo de um percentual do maior grupo."""

    counts = y.value_counts()
    max_count = counts.max()
    target = int(max_count * min_frac)

    X_resampled = [X]
    y_resampled = [y]

    for label, count in counts.items():
        if count < target:
            n_samples = target - count
            X_up, y_up = resample(
                X[y == label],
                y[y == label],
                replace=True,
                n_samples=n_samples,
                random_state=42,
            )
            X_resampled.append(X_up)
            y_resampled.append(y_up)

    X_balanced = pd.concat(X_resampled)
    y_balanced = pd.concat(y_resampled)
    return X_balanced, y_balanced


def relatorio_calibracao(y_true, proba, classes):
    y_true_bin = label_binarize(y_true, classes=classes)
    # Brier multi-classe (média dos erros quadráticos por classe)
    brier = np.mean((proba - y_true_bin) ** 2)

    # AUC por classe (One-vs-Rest)
    auc_por_classe = roc_auc_score(y_true_bin, proba, average=None)

    return brier, dict(zip(classes, auc_por_classe))


def avaliar_modelo(modelo_nome, pipeline, X_test, y_test):
    y_pred = pipeline.predict(X_test)
    relatorio = classification_report(
        y_test, y_pred, zero_division=0, output_dict=True
    )

    # Probabilidades calibradas
    proba = pipeline.predict_proba(X_test)
    brier, auc_por_classe = relatorio_calibracao(
        y_test, proba, pipeline.classes_
    )

    f1_macro = f1_score(y_test, y_pred, average="macro")

    print(f"\n[RESULTADOS - HOLD-OUT] {modelo_nome}")
    print(classification_report(y_test, y_pred, zero_division=0))
    print(f"Brier score (quanto menor melhor): {brier:.4f}")
    print("AUC por classe:")
    for classe, auc in auc_por_classe.items():
        print(f"  - {classe}: {auc:.4f}")

    return {
        "nome": modelo_nome,
        "f1_macro": f1_macro,
        "brier": brier,
        "auc_por_classe": auc_por_classe,
        "relatorio": relatorio,
        "pipeline": pipeline,
        "y_pred": y_pred,
    }


def cross_validate_modelo(modelo_nome, estimador, X, y, n_splits=5):
    """Executa validação cruzada estratificada e retorna métricas médias."""

    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    f1_scores = []
    briers = []
    aucs_por_classe = {}
    classes_modelo = None

    for fold, (train_idx, val_idx) in enumerate(skf.split(X, y), start=1):
        X_train_fold = X.iloc[train_idx]
        y_train_fold = y.iloc[train_idx]
        X_val_fold = X.iloc[val_idx]
        y_val_fold = y.iloc[val_idx]

        vectorizer = TfidfVectorizer(ngram_range=(1, 2))
        pipeline = Pipeline([("tfidf", vectorizer), ("clf", estimador)])
        pipeline.fit(X_train_fold, y_train_fold)

        if classes_modelo is None:
            classes_modelo = pipeline.classes_

        y_pred = pipeline.predict(X_val_fold)
        proba = pipeline.predict_proba(X_val_fold)
        brier, auc_dict = relatorio_calibracao(
            y_val_fold, proba, pipeline.classes_
        )

        f1_scores.append(f1_score(y_val_fold, y_pred, average="macro"))
        briers.append(brier)

        for classe, auc in auc_dict.items():
            aucs_por_classe.setdefault(classe, []).append(auc)

        print(
            f"[CV] {modelo_nome} - Fold {fold}/{n_splits}: "
            f"F1-macro={f1_scores[-1]:.4f}, Brier={brier:.4f}"
        )

    aucs_medios = {cls: float(np.mean(vals)) for cls, vals in aucs_por_classe.items()}

    return {
        "nome": modelo_nome,
        "cv_f1_macro": float(np.mean(f1_scores)),
        "cv_brier": float(np.mean(briers)),
        "cv_auc_por_classe": aucs_medios,
        "classes": classes_modelo,
    }


def treinar_linear_models(X_train, y_train, X_test, y_test):
    modelos = [
        (
            "LogisticRegression (balanced)",
            LogisticRegression(
                max_iter=2000,
                class_weight="balanced",
                n_jobs=-1,
            ),
        ),
        (
            "Calibrated LinearSVC (balanced)",
            CalibratedClassifierCV(
                estimator=LinearSVC(class_weight="balanced"),
                cv=StratifiedKFold(
                    n_splits=3, shuffle=True, random_state=42
                ),
                method="sigmoid",
            ),
        ),
    ]

    resultados = []
    for nome, modelo in modelos:
        print(f"\n[INFO] Validando modelo {nome} com StratifiedKFold...")
        cv_metricas = cross_validate_modelo(nome, modelo, X_train, y_train)

        vectorizer = TfidfVectorizer(ngram_range=(1, 2))
        pipeline = Pipeline([("tfidf", vectorizer), ("clf", modelo)])
        pipeline.fit(X_train, y_train)

        avaliacao_holdout = avaliar_modelo(nome, pipeline, X_test, y_test)

        resultados.append({**cv_metricas, **avaliacao_holdout})

        print(
            f"[RESUMO CV] {nome}: F1-macro médio={cv_metricas['cv_f1_macro']:.4f}, "
            f"Brier médio={cv_metricas['cv_brier']:.4f}"
        )

    return resultados


def registrar_matriz_confusao(y_true, y_pred, classes_destacadas=None):
    matriz = confusion_matrix(y_true, y_pred, labels=classes_destacadas)
    print("\n[MATRIZ DE CONFUSAO - classes destacadas]")
    print(pd.DataFrame(matriz, index=classes_destacadas, columns=classes_destacadas))


def treinar_modelo_basico(nome_coluna, incluir_cartao=False, apenas_completos=False):
    """Treina modelos auxiliares (linear balanceado) para outras colunas."""

    print(f"\n[INFO] Treinando modelo para coluna: {nome_coluna}")

    coluna_alvo = nome_coluna.strip().lower()
    if coluna_alvo not in df.columns:
        print(f"[ERROR] Coluna '{coluna_alvo}' nao encontrada.")
        return

    dados = df.dropna(subset=[coluna_alvo]) if apenas_completos else df.copy()

    X = dados["aonde gastou"].fillna("")
    if incluir_cartao and "cartao" in dados.columns:
        X = X + " [cartao: " + dados["cartao"].fillna("") + "]"

    y = dados[coluna_alvo].astype(str)

    estratificar = y if y.value_counts().min() >= 2 else None

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=estratificar
    )

    pipeline = Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2))),
            (
                "clf",
                LogisticRegression(
                    max_iter=1500,
                    class_weight="balanced",
                    n_jobs=-1,
                ),
            ),
        ]
    )

    pipeline.fit(X_train, y_train)
    nome_modelo = coluna_alvo.replace(" ", "_")
    joblib.dump(pipeline, os.path.join(MODEL_OUTPUT_DIR, f"modelo_{nome_modelo}.pkl"))

    y_pred = pipeline.predict(X_test)
    print(f"[OK] Modelo '{nome_coluna}' treinado e salvo.")
    print(classification_report(y_test, y_pred, zero_division=0))


# === Treina os modelos auxiliares ===
treinar_modelo_basico("comp", incluir_cartao=True)
treinar_modelo_basico("parcelas")
treinar_modelo_basico("no da parcela")
treinar_modelo_basico("tipo")

# === Treina modelo principal para ModelAdapter ===
print(
    "\n[INFO] Treinando modelo principal com validação estratificada e calibração..."
)

dados_principais = df.dropna(subset=["natureza do gasto"])
X_principal = dados_principais["aonde gastou"].fillna("")
y_principal = dados_principais["natureza do gasto"].astype(str)

contagens_principais = y_principal.value_counts()
raras = contagens_principais[contagens_principais < 2].index
if len(raras) > 0:
    print(
        f"[WARN] Removendo classes raras com apenas 1 exemplo: "
        f"{list(raras)}"
    )
    filtro = ~y_principal.isin(raras)
    X_principal = X_principal[filtro]
    y_principal = y_principal[filtro]

X_train, X_test, y_train, y_test = train_test_split(
    X_principal,
    y_principal,
    test_size=0.2,
    random_state=42,
    stratify=y_principal,
)

# Oversampling leve apenas no treino
X_train_bal, y_train_bal = oversample_minority(X_train, y_train, min_frac=0.7)
print("Distribuição antes do oversampling:", Counter(y_train))
print("Distribuição após oversampling leve:", Counter(y_train_bal))

resultados = treinar_linear_models(X_train_bal, y_train_bal, X_test, y_test)

# Seleciona melhor modelo pelo F1 macro médio na validação cruzada
melhor = max(resultados, key=lambda r: r["cv_f1_macro"])
melhor_pipeline = melhor["pipeline"]

# Salva vectorizer e classifier separadamente
vectorizer = melhor_pipeline.named_steps["tfidf"]
classifier = melhor_pipeline.named_steps["clf"]
joblib.dump(vectorizer, os.path.join(MODEL_OUTPUT_DIR, "vectorizer.pkl"))
joblib.dump(classifier, os.path.join(MODEL_OUTPUT_DIR, "classifier.pkl"))
joblib.dump(melhor_pipeline, os.path.join(MODEL_OUTPUT_DIR, "modelo_natureza_do_gasto.pkl"))

print(
    f"[OK] Melhor modelo: {melhor['nome']} | "
    f"F1-macro={melhor['f1_macro']:.4f} | Brier={melhor['brier']:.4f}"
)
print(
    f"[OK] Artefatos salvos em {MODEL_OUTPUT_DIR}: "
    "vectorizer.pkl, classifier.pkl e modelo_natureza_do_gasto.pkl"
)

registrar_matriz_confusao(
    y_test,
    melhor["y_pred"],
    classes_destacadas=["Restaurante", "Gastos Pessoais"],
)

# === Teste de diagnóstico para casos específicos ===
test_cases = [
    ("Hb - Imares (04/04)", "Carro (Manutenção/ IPVA/ Seguro)"),
    ("Raiadrogasilsa", "Farmácia"),
    ("Ifd*Drogaria Penamar L", "Farmácia"),
    ("CREDITO DE SALARIO CNPJ 007526557000100", "Salário"),
]

print("\n[TESTE] Verificando predições para casos específicos:")
for test_text, expected_category in test_cases:
    cleaned = limpar_texto(test_text)
    prediction = melhor_pipeline.predict([cleaned])[0]
    proba = melhor_pipeline.predict_proba([cleaned])[0]
    max_confidence = np.max(proba)

    print(f"\n  Input: {test_text}")
    print(f"  Cleaned: {cleaned}")
    print(f"  Predicted: {prediction}")
    print(f"  Confidence: {max_confidence:.3f}")
    print(f"  Expected: {expected_category}")
    print(f"  Match: {prediction == expected_category}")
