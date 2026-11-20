"""Data loading, cleaning, and preprocessing utilities."""
from __future__ import annotations

import pandas as pd
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer

from .config import (
    RAW_DATA,
    CLEAN_DATA,
    TARGET,
    ID_COL,
    CATEGORICAL_COLS,
    NUMERIC_COLS,
)


def load_raw(path=None) -> pd.DataFrame:
    path = path or RAW_DATA
    return pd.read_csv(path)


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Clean Telco churn data: fix TotalCharges, drop ID, encode target, remove dupes."""
    out = df.copy()

    # TotalCharges is stored as object with blank strings for brand-new customers
    out["TotalCharges"] = pd.to_numeric(out["TotalCharges"], errors="coerce")

    # New customers with tenure=0 often have missing TotalCharges → fill with 0
    out["TotalCharges"] = out["TotalCharges"].fillna(0.0)

    # Drop exact duplicate rows if any
    out = out.drop_duplicates()

    # Binary target
    out[TARGET] = out[TARGET].map({"Yes": 1, "No": 0}).astype(int)

    # SeniorCitizen already numeric 0/1
    out["SeniorCitizen"] = out["SeniorCitizen"].astype(int)

    return out


def build_feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Return modeling frame without customerID (keep target)."""
    cols = [c for c in df.columns if c != ID_COL]
    return df[cols].copy()


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create domain features that do not leak the target."""
    out = df.copy()

    # Average revenue per tenure month (avoid div by zero)
    out["AvgChargesPerMonth"] = np.where(
        out["tenure"] > 0,
        out["TotalCharges"] / out["tenure"],
        out["MonthlyCharges"],
    )

    # Tenure buckets (ordinal-ish categories for later encoding)
    out["TenureGroup"] = pd.cut(
        out["tenure"],
        bins=[-1, 12, 24, 48, 72],
        labels=["0-12", "13-24", "25-48", "49-72"],
    ).astype(str)

    # Has both streaming services
    out["HasStreamingBundle"] = (
        (out["StreamingTV"] == "Yes") & (out["StreamingMovies"] == "Yes")
    ).astype(int)

    # Count of add-on security/support services
    addon_map = {"Yes": 1, "No": 0, "No internet service": 0}
    for col in ["OnlineSecurity", "OnlineBackup", "DeviceProtection", "TechSupport"]:
        out[f"{col}_flag"] = out[col].map(addon_map).fillna(0).astype(int)
    out["AddonCount"] = (
        out["OnlineSecurity_flag"]
        + out["OnlineBackup_flag"]
        + out["DeviceProtection_flag"]
        + out["TechSupport_flag"]
    )
    out = out.drop(
        columns=[
            "OnlineSecurity_flag",
            "OnlineBackup_flag",
            "DeviceProtection_flag",
            "TechSupport_flag",
        ]
    )

    # Autopay-like payment methods (business signal for retention)
    out["IsAutoPay"] = out["PaymentMethod"].isin(
        ["Bank transfer (automatic)", "Credit card (automatic)"]
    ).astype(int)

    return out


def get_feature_columns(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    """Infer numeric vs categorical feature columns excluding target."""
    feature_df = df.drop(columns=[TARGET], errors="ignore")
    numeric = feature_df.select_dtypes(include=["number"]).columns.tolist()
    categorical = feature_df.select_dtypes(exclude=["number"]).columns.tolist()
    return numeric, categorical


def build_preprocessor(numeric_cols: list[str], categorical_cols: list[str]) -> ColumnTransformer:
    numeric_pipe = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipe = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("num", numeric_pipe, numeric_cols),
            ("cat", categorical_pipe, categorical_cols),
        ]
    )


def save_cleaned(df: pd.DataFrame, path=None) -> None:
    path = path or CLEAN_DATA
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def data_quality_report(raw: pd.DataFrame, clean: pd.DataFrame) -> dict:
    return {
        "raw_rows": int(len(raw)),
        "clean_rows": int(len(clean)),
        "raw_cols": int(raw.shape[1]),
        "clean_cols": int(clean.shape[1]),
        "duplicate_rows_removed": int(raw.duplicated().sum()),
        "total_charges_blank_fixed": int(
            (raw["TotalCharges"].astype(str).str.strip() == "").sum()
        ),
        "missing_after_clean": {k: int(v) for k, v in clean.isna().sum().items() if v > 0},
        "churn_rate": float(clean[TARGET].mean()),
        "churn_counts": clean[TARGET].value_counts().to_dict(),
    }
