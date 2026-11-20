"""Model training utilities."""
from __future__ import annotations

from typing import Any

import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline

from .config import RANDOM_STATE, TEST_SIZE, TARGET, MODELS_DIR
from .preprocess import build_preprocessor, get_feature_columns


def split_xy(df: pd.DataFrame):
    X = df.drop(columns=[TARGET])
    y = df[TARGET]
    return X, y


def make_train_test(df: pd.DataFrame):
    X, y = split_xy(df)
    return train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )


def get_candidate_models() -> dict[str, Any]:
    return {
        "logistic_regression": LogisticRegression(
            max_iter=2000, class_weight="balanced", random_state=RANDOM_STATE
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            min_samples_leaf=5,
            class_weight="balanced",
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
        "gradient_boosting": GradientBoostingClassifier(
            n_estimators=150,
            learning_rate=0.08,
            max_depth=3,
            random_state=RANDOM_STATE,
        ),
    }


def build_model_pipeline(estimator, numeric_cols, categorical_cols) -> Pipeline:
    return Pipeline(
        steps=[
            ("preprocess", build_preprocessor(numeric_cols, categorical_cols)),
            ("model", estimator),
        ]
    )


def train_all_models(df: pd.DataFrame) -> dict[str, Any]:
    X_train, X_test, y_train, y_test = make_train_test(df)
    numeric_cols, categorical_cols = get_feature_columns(df)

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    results = {}

    for name, estimator in get_candidate_models().items():
        pipe = build_model_pipeline(estimator, numeric_cols, categorical_cols)
        cv_scores = cross_val_score(
            pipe, X_train, y_train, cv=cv, scoring="roc_auc", n_jobs=-1
        )
        pipe.fit(X_train, y_train)
        results[name] = {
            "pipeline": pipe,
            "cv_roc_auc_mean": float(cv_scores.mean()),
            "cv_roc_auc_std": float(cv_scores.std()),
            "X_test": X_test,
            "y_test": y_test,
            "X_train": X_train,
            "y_train": y_train,
        }
    return results


def select_best_model(train_results: dict[str, Any]) -> tuple[str, Any]:
    best_name = max(train_results, key=lambda k: train_results[k]["cv_roc_auc_mean"])
    return best_name, train_results[best_name]["pipeline"]


def save_model(pipeline, name: str = "best_model.joblib") -> str:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    path = MODELS_DIR / name
    joblib.dump(pipeline, path)
    return str(path)
