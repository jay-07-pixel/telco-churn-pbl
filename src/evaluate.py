"""Model evaluation and business metric helpers."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
    RocCurveDisplay,
    ConfusionMatrixDisplay,
)
import matplotlib.pyplot as plt

from .config import FIGURES_DIR, OUTPUTS_DIR, TARGET


def evaluate_classifier(pipeline, X_test, y_test) -> dict[str, Any]:
    y_pred = pipeline.predict(X_test)
    y_prob = pipeline.predict_proba(X_test)[:, 1]
    cm = confusion_matrix(y_test, y_pred)
    return {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred)),
        "recall": float(recall_score(y_test, y_pred)),
        "f1": float(f1_score(y_test, y_pred)),
        "roc_auc": float(roc_auc_score(y_test, y_prob)),
        "confusion_matrix": cm.tolist(),
        "classification_report": classification_report(
            y_test, y_pred, target_names=["No Churn", "Churn"], output_dict=True
        ),
        "y_pred": y_pred,
        "y_prob": y_prob,
    }


def plot_confusion_matrix(cm, title: str, save_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(5, 4))
    disp = ConfusionMatrixDisplay(confusion_matrix=np.array(cm), display_labels=["No", "Yes"])
    disp.plot(ax=ax, cmap="Blues", colorbar=False)
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)


def plot_roc(pipeline, X_test, y_test, title: str, save_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(5, 4))
    RocCurveDisplay.from_estimator(pipeline, X_test, y_test, ax=ax)
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)


def estimate_business_impact(
    y_test,
    y_prob,
    avg_monthly_revenue: float = 65.0,
    retention_cost: float = 25.0,
    retention_success_rate: float = 0.35,
    threshold: float = 0.5,
) -> dict[str, float]:
    """
    Simple retention campaign ROI sketch.
    Flag customers with P(churn) >= threshold, offer retention offer.
    """
    flagged = y_prob >= threshold
    true_churners_flagged = ((y_test == 1) & flagged).sum()
    false_alarms = ((y_test == 0) & flagged).sum()

    customers_saved = true_churners_flagged * retention_success_rate
    revenue_retained = customers_saved * avg_monthly_revenue * 12  # annualized
    campaign_cost = flagged.sum() * retention_cost
    net_value = revenue_retained - campaign_cost

    return {
        "threshold": float(threshold),
        "customers_flagged": int(flagged.sum()),
        "true_churners_flagged": int(true_churners_flagged),
        "false_alarms": int(false_alarms),
        "est_customers_saved": float(customers_saved),
        "est_annual_revenue_retained": float(revenue_retained),
        "campaign_cost": float(campaign_cost),
        "est_net_annual_value": float(net_value),
    }


def save_json(obj: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    def _default(o):
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating,)):
            return float(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
        raise TypeError(type(o))

    # Drop non-serializable arrays from nested dicts if present
    clean = {}
    for k, v in obj.items():
        if k in {"y_pred", "y_prob"}:
            continue
        clean[k] = v
    path.write_text(json.dumps(clean, indent=2, default=_default), encoding="utf-8")
