"""Project paths and constants."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RAW_DATA = DATA_DIR / "Telco-Customer-Churn.csv"
CLEAN_DATA = DATA_DIR / "telco_churn_cleaned.csv"
PROCESSED_DIR = DATA_DIR / "processed"
FIGURES_DIR = ROOT / "figures"
MODELS_DIR = ROOT / "models"
OUTPUTS_DIR = ROOT / "outputs"

TARGET = "Churn"
ID_COL = "customerID"
RANDOM_STATE = 42
TEST_SIZE = 0.2

# Features that should not leak into training after label encoding of target
LEAKAGE_SAFE_DROP = [ID_COL]

CATEGORICAL_COLS = [
    "gender",
    "Partner",
    "Dependents",
    "PhoneService",
    "MultipleLines",
    "InternetService",
    "OnlineSecurity",
    "OnlineBackup",
    "DeviceProtection",
    "TechSupport",
    "StreamingTV",
    "StreamingMovies",
    "Contract",
    "PaperlessBilling",
    "PaymentMethod",
]

NUMERIC_COLS = ["SeniorCitizen", "tenure", "MonthlyCharges", "TotalCharges"]
