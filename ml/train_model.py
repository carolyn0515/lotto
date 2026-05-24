import json
from datetime import datetime
from pathlib import Path

import joblib
import pandas as pd

from sklearn.ensemble import (
    ExtraTreesClassifier,
    GradientBoostingClassifier,
    RandomForestClassifier,
)
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "ml_lotto_dataset.csv"
MODEL_DIR = BASE_DIR / "model"

BEST_MODEL_PATH = MODEL_DIR / "best_lotto_model.joblib"
METADATA_PATH = MODEL_DIR / "model_metadata.json"
EXPERIMENT_RESULTS_PATH = MODEL_DIR / "experiment_results.csv"


FEATURE_COLUMNS = [
    "target_number",
    "recent_5_count",
    "recent_10_count",
    "recent_20_count",
    "total_count",
    "rounds_since_last_seen",
    "is_odd",
    "number_group",
]

TARGET_COLUMN = "label"


def load_dataset():
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_PATH}. "
            "Run `python ml/build_features.py` first."
        )

    df = pd.read_csv(DATA_PATH)

    return df


def split_by_round(df, train_ratio=0.8):
    """
    로또 데이터는 시간 순서가 있는 데이터이므로 random split 대신
    회차 기준으로 앞부분은 train, 뒷부분은 validation으로 나눈다.
    """
    unique_rounds = sorted(df["current_round"].unique())
    split_index = int(len(unique_rounds) * train_ratio)

    train_rounds = set(unique_rounds[:split_index])
    valid_rounds = set(unique_rounds[split_index:])

    train_df = df[df["current_round"].isin(train_rounds)].copy()
    valid_df = df[df["current_round"].isin(valid_rounds)].copy()

    return train_df, valid_df


def get_candidate_models():
    """
    여러 모델 후보를 정의한다.
    각 후보는 이름, 모델 객체로 구성된다.
    """
    models = [
        (
            "logistic_regression",
            Pipeline(
                steps=[
                    ("scaler", StandardScaler()),
                    (
                        "model",
                        LogisticRegression(
                            max_iter=1000,
                            class_weight="balanced",
                            random_state=42,
                        ),
                    ),
                ]
            ),
        ),
        (
            "random_forest",
            RandomForestClassifier(
                n_estimators=300,
                max_depth=8,
                min_samples_leaf=5,
                class_weight="balanced",
                random_state=42,
                n_jobs=-1,
            ),
        ),
        (
            "extra_trees",
            ExtraTreesClassifier(
                n_estimators=300,
                max_depth=8,
                min_samples_leaf=5,
                class_weight="balanced",
                random_state=42,
                n_jobs=-1,
            ),
        ),
        (
            "gradient_boosting",
            GradientBoostingClassifier(
                n_estimators=200,
                learning_rate=0.05,
                max_depth=3,
                random_state=42,
            ),
        ),
    ]

    return models


def evaluate_model(model, X_valid, y_valid):
    """
    모델이 label=1일 확률을 얼마나 잘 점수화하는지 평가한다.
    """
    if not hasattr(model, "predict_proba"):
        raise ValueError("Model must support predict_proba().")

    positive_prob = model.predict_proba(X_valid)[:, 1]

    roc_auc = roc_auc_score(y_valid, positive_prob)
    average_precision = average_precision_score(y_valid, positive_prob)

    return {
        "roc_auc": roc_auc,
        "average_precision": average_precision,
    }


def train_and_select_best_model(train_df, valid_df):
    X_train = train_df[FEATURE_COLUMNS]
    y_train = train_df[TARGET_COLUMN]

    X_valid = valid_df[FEATURE_COLUMNS]
    y_valid = valid_df[TARGET_COLUMN]

    experiment_results = []
    best_model = None
    best_model_name = None
    best_score = -1

    for model_name, model in get_candidate_models():
        print(f"\nTraining model: {model_name}")

        model.fit(X_train, y_train)

        metrics = evaluate_model(model, X_valid, y_valid)

        print(f"ROC-AUC: {metrics['roc_auc']:.4f}")
        print(f"Average Precision: {metrics['average_precision']:.4f}")

        experiment_results.append(
            {
                "model_name": model_name,
                "roc_auc": metrics["roc_auc"],
                "average_precision": metrics["average_precision"],
            }
        )

        # 여기서는 ROC-AUC 기준으로 best model 선택
        if metrics["roc_auc"] > best_score:
            best_score = metrics["roc_auc"]
            best_model = model
            best_model_name = model_name

    return best_model_name, best_model, experiment_results


def save_artifacts(best_model_name, best_model, experiment_results, train_df, valid_df):
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    model_bundle = {
        "model": best_model,
        "feature_columns": FEATURE_COLUMNS,
        "target_column": TARGET_COLUMN,
        "model_name": best_model_name,
        "created_at": datetime.now().isoformat(),
    }

    joblib.dump(model_bundle, BEST_MODEL_PATH)

    experiment_df = pd.DataFrame(experiment_results)
    experiment_df = experiment_df.sort_values("roc_auc", ascending=False)
    experiment_df.to_csv(EXPERIMENT_RESULTS_PATH, index=False)

    best_result = experiment_df.iloc[0].to_dict()

    metadata = {
        "model_name": best_model_name,
        "model_path": str(BEST_MODEL_PATH),
        "feature_columns": FEATURE_COLUMNS,
        "target_column": TARGET_COLUMN,
        "created_at": datetime.now().isoformat(),
        "train_rows": int(len(train_df)),
        "valid_rows": int(len(valid_df)),
        "train_round_min": int(train_df["current_round"].min()),
        "train_round_max": int(train_df["current_round"].max()),
        "valid_round_min": int(valid_df["current_round"].min()),
        "valid_round_max": int(valid_df["current_round"].max()),
        "best_metrics": {
            "roc_auc": float(best_result["roc_auc"]),
            "average_precision": float(best_result["average_precision"]),
        },
        "note": (
            "This model is for MLOps pipeline practice and number recommendation. "
            "It does not guarantee actual lottery winning prediction."
        ),
    }

    with open(METADATA_PATH, "w", encoding="utf-8") as file:
        json.dump(metadata, file, ensure_ascii=False, indent=2)

    print("\nArtifacts saved:")
    print(f"- Best model: {BEST_MODEL_PATH}")
    print(f"- Metadata: {METADATA_PATH}")
    print(f"- Experiment results: {EXPERIMENT_RESULTS_PATH}")


def main():
    df = load_dataset()

    print(f"Dataset rows: {len(df)}")
    print(f"Positive ratio: {df[TARGET_COLUMN].mean():.4f}")

    train_df, valid_df = split_by_round(df)

    print(f"Train rows: {len(train_df)}")
    print(f"Valid rows: {len(valid_df)}")
    print(
        f"Train rounds: {train_df['current_round'].min()} "
        f"~ {train_df['current_round'].max()}"
    )
    print(
        f"Valid rounds: {valid_df['current_round'].min()} "
        f"~ {valid_df['current_round'].max()}"
    )

    best_model_name, best_model, experiment_results = train_and_select_best_model(
        train_df=train_df,
        valid_df=valid_df,
    )

    print(f"\nBest model: {best_model_name}")

    save_artifacts(
        best_model_name=best_model_name,
        best_model=best_model,
        experiment_results=experiment_results,
        train_df=train_df,
        valid_df=valid_df,
    )


if __name__ == "__main__":
    main()