"""
End-to-end Telco Customer Churn ML lifecycle runner.
Produces cleaned data, EDA figures, trained models, metrics, and insights JSON.
Does NOT generate the formal academic report.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.config import (
    FIGURES_DIR,
    MODELS_DIR,
    OUTPUTS_DIR,
    PROCESSED_DIR,
    TARGET,
    DATA_DIR,
)
from src.preprocess import (
    load_raw,
    clean_dataframe,
    build_feature_frame,
    engineer_features,
    save_cleaned,
    data_quality_report,
    get_feature_columns,
)
from src.train import train_all_models, select_best_model, save_model
from src.evaluate import (
    evaluate_classifier,
    plot_confusion_matrix,
    plot_roc,
    estimate_business_impact,
    save_json,
)

sns.set_theme(style="whitegrid", context="notebook")
plt.rcParams["figure.facecolor"] = "white"


def ensure_dirs() -> None:
    for d in [FIGURES_DIR, MODELS_DIR, OUTPUTS_DIR, PROCESSED_DIR, DATA_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def run_eda(df: pd.DataFrame) -> dict:
    """Create EDA plots and return key statistical insights."""
    insights = {}

    # 1) Target distribution
    fig, ax = plt.subplots(figsize=(6, 4))
    counts = df[TARGET].value_counts().rename({0: "No Churn", 1: "Churn"})
    sns.barplot(
        x=counts.index,
        y=counts.values,
        hue=counts.index,
        ax=ax,
        palette=["#2a9d8f", "#e76f51"],
        legend=False,
    )
    ax.set_title("Churn Distribution")
    ax.set_ylabel("Customers")
    for i, v in enumerate(counts.values):
        ax.text(i, v + 40, f"{v} ({v/len(df):.1%})", ha="center")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "01_churn_distribution.png", dpi=150)
    plt.close(fig)
    insights["churn_rate"] = float(df[TARGET].mean())

    # 2) Numeric distributions by churn
    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    for ax, col in zip(axes, ["tenure", "MonthlyCharges", "TotalCharges"]):
        sns.kdeplot(data=df, x=col, hue=TARGET, fill=True, common_norm=False, ax=ax)
        ax.set_title(f"{col} by Churn")
        ax.legend(title="Churn", labels=["No", "Yes"])
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "02_numeric_by_churn.png", dpi=150)
    plt.close(fig)

    # 3) Contract vs churn rate
    fig, ax = plt.subplots(figsize=(7, 4))
    contract_churn = df.groupby("Contract")[TARGET].mean().sort_values(ascending=False)
    sns.barplot(x=contract_churn.index, y=contract_churn.values, ax=ax, color="#264653")
    ax.set_title("Churn Rate by Contract Type")
    ax.set_ylabel("Churn Rate")
    ax.set_ylim(0, 1)
    for i, v in enumerate(contract_churn.values):
        ax.text(i, v + 0.02, f"{v:.1%}", ha="center")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "03_churn_by_contract.png", dpi=150)
    plt.close(fig)
    insights["churn_by_contract"] = {k: float(v) for k, v in contract_churn.items()}

    # 4) Internet service vs churn
    fig, ax = plt.subplots(figsize=(7, 4))
    inet = df.groupby("InternetService")[TARGET].mean().sort_values(ascending=False)
    sns.barplot(x=inet.index, y=inet.values, ax=ax, color="#e9c46a")
    ax.set_title("Churn Rate by Internet Service")
    ax.set_ylabel("Churn Rate")
    ax.set_ylim(0, 1)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "04_churn_by_internet.png", dpi=150)
    plt.close(fig)
    insights["churn_by_internet"] = {k: float(v) for k, v in inet.items()}

    # 5) Payment method vs churn
    fig, ax = plt.subplots(figsize=(9, 4))
    pay = df.groupby("PaymentMethod")[TARGET].mean().sort_values(ascending=False)
    sns.barplot(y=pay.index, x=pay.values, ax=ax, color="#f4a261")
    ax.set_title("Churn Rate by Payment Method")
    ax.set_xlabel("Churn Rate")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "05_churn_by_payment.png", dpi=150)
    plt.close(fig)
    insights["churn_by_payment"] = {k: float(v) for k, v in pay.items()}

    # 6) Correlation heatmap (numeric + target)
    num_cols = ["SeniorCitizen", "tenure", "MonthlyCharges", "TotalCharges", "AvgChargesPerMonth", "AddonCount", "HasStreamingBundle", "IsAutoPay", TARGET]
    num_cols = [c for c in num_cols if c in df.columns]
    corr = df[num_cols].corr()
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdBu_r", center=0, ax=ax)
    ax.set_title("Numeric Feature Correlations")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "06_correlation_heatmap.png", dpi=150)
    plt.close(fig)
    insights["corr_with_churn"] = {
        k: float(v) for k, v in corr[TARGET].drop(TARGET).sort_values().items()
    }

    # 7) Tenure group churn
    fig, ax = plt.subplots(figsize=(7, 4))
    tg = df.groupby("TenureGroup")[TARGET].mean().reindex(["0-12", "13-24", "25-48", "49-72"])
    sns.barplot(x=tg.index, y=tg.values, ax=ax, color="#2a9d8f")
    ax.set_title("Churn Rate by Tenure Group")
    ax.set_ylabel("Churn Rate")
    ax.set_ylim(0, 1)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "07_churn_by_tenure_group.png", dpi=150)
    plt.close(fig)
    insights["churn_by_tenure_group"] = {str(k): float(v) for k, v in tg.items()}

    # 8) Boxplots for outlier view
    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    for ax, col in zip(axes, ["tenure", "MonthlyCharges", "TotalCharges"]):
        sns.boxplot(data=df, y=col, x=df[TARGET].map({0: "No", 1: "Yes"}), ax=ax)
        ax.set_xlabel("Churn")
        ax.set_title(col)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "08_boxplots_outliers.png", dpi=150)
    plt.close(fig)

    # Basic stats table
    stats = df[["tenure", "MonthlyCharges", "TotalCharges"]].describe().round(2)
    stats.to_csv(OUTPUTS_DIR / "numeric_describe.csv")
    insights["numeric_describe"] = stats.to_dict()

    return insights


def outlier_summary(df: pd.DataFrame) -> dict:
    summary = {}
    for col in ["tenure", "MonthlyCharges", "TotalCharges", "AvgChargesPerMonth"]:
        q1, q3 = df[col].quantile(0.25), df[col].quantile(0.75)
        iqr = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        n = int(((df[col] < lower) | (df[col] > upper)).sum())
        summary[col] = {
            "q1": float(q1),
            "q3": float(q3),
            "iqr": float(iqr),
            "lower": float(lower),
            "upper": float(upper),
            "outlier_count": n,
            "outlier_pct": float(n / len(df)),
        }
    return summary


def feature_importance_plot(pipeline, feature_frame: pd.DataFrame, top_n: int = 20) -> list[tuple[str, float]]:
    """Extract importances from tree model if available; else LR coefficients."""
    pre = pipeline.named_steps["preprocess"]
    model = pipeline.named_steps["model"]
    numeric_cols, categorical_cols = get_feature_columns(feature_frame)

    num_names = numeric_cols
    cat_names = list(
        pre.named_transformers_["cat"]
        .named_steps["onehot"]
        .get_feature_names_out(categorical_cols)
    )
    feature_names = num_names + cat_names

    if hasattr(model, "feature_importances_"):
        importances = model.feature_importances_
    elif hasattr(model, "coef_"):
        importances = np.abs(model.coef_.ravel())
    else:
        return []

    pairs = sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True)[:top_n]
    names, vals = zip(*pairs)

    fig, ax = plt.subplots(figsize=(9, 7))
    sns.barplot(x=list(vals), y=list(names), ax=ax, color="#264653")
    ax.set_title(f"Top {top_n} Feature Importances / |Coefficients|")
    ax.set_xlabel("Importance")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "09_feature_importance.png", dpi=150)
    plt.close(fig)
    return [(n, float(v)) for n, v in pairs]


def write_business_insights(path: Path, eda: dict, metrics: dict, impact: dict, top_feats: list) -> None:
    lines = [
        "# Business Insights & Recommendations",
        "",
        "## Problem",
        "Predict which telecom customers are likely to churn so retention teams can act early.",
        "",
        "## Key Data Insights",
        f"- Overall churn rate: **{eda['churn_rate']:.1%}**",
        f"- Highest-risk contract: Month-to-month (~{eda['churn_by_contract'].get('Month-to-month', 0):.1%})",
        f"- Fiber optic internet has elevated churn (~{eda['churn_by_internet'].get('Fiber optic', 0):.1%})",
        f"- Electronic check payers churn more (~{eda['churn_by_payment'].get('Electronic check', 0):.1%})",
        f"- New customers (0-12 months) churn most (~{eda['churn_by_tenure_group'].get('0-12', 0):.1%})",
        "",
        "## Model Performance (hold-out test)",
        f"- Accuracy: {metrics['accuracy']:.3f}",
        f"- Precision: {metrics['precision']:.3f}",
        f"- Recall: {metrics['recall']:.3f}",
        f"- F1: {metrics['f1']:.3f}",
        f"- ROC-AUC: {metrics['roc_auc']:.3f}",
        "",
        "## Retention Campaign Sketch (test set)",
        f"- Flagged customers: {impact['customers_flagged']}",
        f"- True churners caught: {impact['true_churners_flagged']}",
        f"- Est. customers saved: {impact['est_customers_saved']:.1f}",
        f"- Est. annual revenue retained: ${impact['est_annual_revenue_retained']:,.0f}",
        f"- Campaign cost: ${impact['campaign_cost']:,.0f}",
        f"- Est. net annual value: ${impact['est_net_annual_value']:,.0f}",
        "",
        "## Actionable Recommendations",
        "1. Prioritize retention offers for month-to-month customers in first 12 months.",
        "2. Investigate Fiber optic service quality / pricing friction (high churn segment).",
        "3. Push autopay / card / bank transfer onboarding to reduce electronic-check risk.",
        "4. Bundle security + support add-ons; higher AddonCount correlates with lower churn.",
        "5. Use model scores weekly to feed a ranked outreach list to the CRM team.",
        "",
        "## Top Drivers",
    ]
    for name, val in top_feats[:10]:
        lines.append(f"- {name}: {val:.4f}")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    print("1) Loading raw data...")
    raw = load_raw()

    print("2) Cleaning...")
    clean = clean_dataframe(raw)
    clean = build_feature_frame(clean)
    quality = data_quality_report(raw, clean.assign(**{c: raw[c] for c in []}) if False else clean)
    # rebuild quality with proper cleaned frame that still has same row count semantics
    quality = {
        "raw_rows": int(len(raw)),
        "clean_rows": int(len(clean)),
        "raw_cols": int(raw.shape[1]),
        "clean_cols": int(clean.shape[1]),
        "duplicate_rows_removed": int(raw.duplicated().sum()),
        "total_charges_blank_fixed": int(
            (raw["TotalCharges"].astype(str).str.strip() == "").sum()
        ),
        "missing_after_clean": {
            k: int(v) for k, v in clean.isna().sum().items() if v > 0
        },
        "churn_rate": float(clean[TARGET].mean()),
        "churn_counts": {str(k): int(v) for k, v in clean[TARGET].value_counts().items()},
    }

    print("3) Feature engineering...")
    featured = engineer_features(clean)
    save_cleaned(featured, DATA_DIR / "telco_churn_cleaned.csv")
    featured.to_csv(PROCESSED_DIR / "modeling_frame.csv", index=False)

    outliers = outlier_summary(featured)
    save_json(outliers, OUTPUTS_DIR / "outlier_summary.json")
    save_json(quality, OUTPUTS_DIR / "data_quality_report.json")

    print("4) EDA figures...")
    eda_insights = run_eda(featured)
    save_json(eda_insights, OUTPUTS_DIR / "eda_insights.json")

    print("5) Training models (LR, RF, GBM) with stratified split + 5-fold CV...")
    train_results = train_all_models(featured)

    comparison = {}
    best_test_metrics = {}
    for name, payload in train_results.items():
        metrics = evaluate_classifier(payload["pipeline"], payload["X_test"], payload["y_test"])
        comparison[name] = {
            "cv_roc_auc_mean": payload["cv_roc_auc_mean"],
            "cv_roc_auc_std": payload["cv_roc_auc_std"],
            "test_accuracy": metrics["accuracy"],
            "test_precision": metrics["precision"],
            "test_recall": metrics["recall"],
            "test_f1": metrics["f1"],
            "test_roc_auc": metrics["roc_auc"],
            "confusion_matrix": metrics["confusion_matrix"],
        }
        save_model(payload["pipeline"], f"{name}.joblib")
        plot_confusion_matrix(
            metrics["confusion_matrix"],
            f"Confusion Matrix — {name}",
            FIGURES_DIR / f"cm_{name}.png",
        )
        plot_roc(
            payload["pipeline"],
            payload["X_test"],
            payload["y_test"],
            f"ROC — {name}",
            FIGURES_DIR / f"roc_{name}.png",
        )
        best_test_metrics[name] = metrics

    save_json(comparison, OUTPUTS_DIR / "model_comparison.json")
    pd.DataFrame(comparison).T.to_csv(OUTPUTS_DIR / "model_comparison.csv")

    best_name, best_pipe = select_best_model(train_results)
    save_model(best_pipe, "best_model.joblib")
    best_metrics = best_test_metrics[best_name]
    print(f"Best model by CV ROC-AUC: {best_name}")

    # Comparison bar chart
    fig, ax = plt.subplots(figsize=(8, 4))
    names = list(comparison.keys())
    aucs = [comparison[n]["test_roc_auc"] for n in names]
    sns.barplot(x=names, y=aucs, ax=ax, color="#2a9d8f")
    ax.set_ylim(0.5, 1.0)
    ax.set_title("Test ROC-AUC by Model")
    ax.set_ylabel("ROC-AUC")
    for i, v in enumerate(aucs):
        ax.text(i, v + 0.01, f"{v:.3f}", ha="center")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "10_model_comparison_auc.png", dpi=150)
    plt.close(fig)

    top_feats = feature_importance_plot(best_pipe, featured)

    impact = estimate_business_impact(
        train_results[best_name]["y_test"].values,
        best_metrics["y_prob"],
        avg_monthly_revenue=float(featured["MonthlyCharges"].mean()),
    )
    save_json(impact, OUTPUTS_DIR / "business_impact.json")
    save_json(
        {
            "best_model": best_name,
            "metrics": {k: v for k, v in best_metrics.items() if k not in {"y_pred", "y_prob"}},
            "top_features": top_feats,
        },
        OUTPUTS_DIR / "best_model_report.json",
    )
    write_business_insights(
        OUTPUTS_DIR / "business_insights.md",
        eda_insights,
        best_metrics,
        impact,
        top_feats,
    )

    # Data dictionary
    dictionary = [
        {"column": "customerID", "type": "ID", "description": "Unique customer identifier (dropped before modeling to avoid leakage)"},
        {"column": "gender", "type": "categorical", "description": "Customer gender"},
        {"column": "SeniorCitizen", "type": "binary", "description": "1 if senior citizen, else 0"},
        {"column": "Partner", "type": "categorical", "description": "Whether customer has a partner"},
        {"column": "Dependents", "type": "categorical", "description": "Whether customer has dependents"},
        {"column": "tenure", "type": "numeric", "description": "Months with the company"},
        {"column": "PhoneService", "type": "categorical", "description": "Has phone service"},
        {"column": "MultipleLines", "type": "categorical", "description": "Multiple phone lines status"},
        {"column": "InternetService", "type": "categorical", "description": "DSL / Fiber optic / No"},
        {"column": "OnlineSecurity", "type": "categorical", "description": "Online security add-on"},
        {"column": "OnlineBackup", "type": "categorical", "description": "Online backup add-on"},
        {"column": "DeviceProtection", "type": "categorical", "description": "Device protection add-on"},
        {"column": "TechSupport", "type": "categorical", "description": "Tech support add-on"},
        {"column": "StreamingTV", "type": "categorical", "description": "Streaming TV add-on"},
        {"column": "StreamingMovies", "type": "categorical", "description": "Streaming movies add-on"},
        {"column": "Contract", "type": "categorical", "description": "Month-to-month / One year / Two year"},
        {"column": "PaperlessBilling", "type": "categorical", "description": "Paperless billing flag"},
        {"column": "PaymentMethod", "type": "categorical", "description": "Payment method"},
        {"column": "MonthlyCharges", "type": "numeric", "description": "Current monthly bill amount"},
        {"column": "TotalCharges", "type": "numeric", "description": "Total amount charged to date"},
        {"column": "Churn", "type": "target", "description": "1 = churned, 0 = retained"},
        {"column": "AvgChargesPerMonth", "type": "engineered", "description": "TotalCharges / tenure"},
        {"column": "TenureGroup", "type": "engineered", "description": "Binned tenure groups"},
        {"column": "HasStreamingBundle", "type": "engineered", "description": "Both streaming TV and movies"},
        {"column": "AddonCount", "type": "engineered", "description": "Count of security/support add-ons"},
        {"column": "IsAutoPay", "type": "engineered", "description": "Automatic payment method flag"},
    ]
    pd.DataFrame(dictionary).to_csv(DATA_DIR / "data_dictionary.csv", index=False)

    summary = {
        "dataset": "IBM Telco Customer Churn",
        "source": "https://github.com/IBM/telco-customer-churn-on-icp4d",
        "problem": "Binary classification — predict customer churn",
        "rows": quality["clean_rows"],
        "best_model": best_name,
        "test_roc_auc": comparison[best_name]["test_roc_auc"],
        "test_f1": comparison[best_name]["test_f1"],
        "figures_dir": str(FIGURES_DIR),
        "models_dir": str(MODELS_DIR),
        "outputs_dir": str(OUTPUTS_DIR),
    }
    save_json(summary, OUTPUTS_DIR / "run_summary.json")
    print(json.dumps(summary, indent=2))
    print("\nDone. Formal report NOT generated (as requested).")


if __name__ == "__main__":
    main()
