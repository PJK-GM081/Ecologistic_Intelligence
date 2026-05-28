import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

# ============================================================
# PROJECT PATHS (Relative to project root)
# ============================================================

# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent


def project_path(env_name: str, default: str) -> Path:
    """Resolve a path from .env or fall back to a project-relative default."""
    value = os.getenv(env_name, default)
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path

# Data Paths
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_PATH = project_path("RAW_DATA_PATH", "data/raw/DataCoSupplyChainDataset.csv")
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# Model & Artifacts
MODELS_DIR = PROJECT_ROOT / "models"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
MODEL_PATH = project_path("MODEL_PATH", "models/random_forest_model.pkl")
PREPROCESSOR_PATH = project_path("PREPROCESSOR_PATH", "artifacts/encoders/preprocessor.pkl")
ENCODERS_DIR = ARTIFACTS_DIR / "encoders"
METADATA_DIR = project_path("METADATA_PATH", "artifacts/metadata/preprocessing_metadata.pkl").parent

# Processed Data Paths
X_TRAIN_PATH = PROCESSED_DATA_DIR / "X_train.csv"
X_TEST_PATH = PROCESSED_DATA_DIR / "X_test.csv"
Y_TRAIN_PATH = PROCESSED_DATA_DIR / "y_train.csv"
Y_TEST_PATH = PROCESSED_DATA_DIR / "y_test.csv"

# ============================================================
# FEATURE CONFIGURATION
# ============================================================

TARGET = "late_delivery_risk"

# Raw Input Features (from raw dataset)
RAW_FEATURES = [
    "days_for_shipment_(scheduled)",
    "benefit_per_order",
    "category_name",
    "customer_id",
    "customer_segment",
    "market",
    "order_date_(dateorders)",
    "order_id",
    "order_item_quantity",
    "sales",
    "order_region",
    "shipping_mode"
]

# Categorical Features (for preprocessing)
CATEGORICAL_FEATURES = [
    "category_name",
    "customer_segment",
    "market",
    "order_region",
    "shipping_mode"
]

# Numerical Features (for preprocessing)
NUMERICAL_FEATURES = [
    "days_for_shipment_(scheduled)",
    "benefit_per_order",
    "order_item_quantity",
    "sales",
    "order_month",
    "order_dayofweek",
    "is_weekend_order",
    "shipping_mode_risk",
    "avg_delay_by_region",
    "category_delay_risk",
    "customer_order_count",
    "customer_late_rate",
]

# Features used for aggregations (require train-only computation)
AGGREGATION_FEATURES = [
    "customer_id",
    "order_region",
    "shipping_mode",
    "category_name"
]

# ============================================================
# FEATURE ENGINEERING PARAMETERS
# ============================================================

# Bayesian Smoothing Parameters
SMOOTHING_FACTOR = 10  # For customer_late_rate smoothing

# Train/Test Split
TEST_SIZE = 0.2
RANDOM_STATE = 42
GROUPBY_COLUMN = "customer_id"  # For group-aware stratification

# ============================================================
# MODEL HYPERPARAMETERS
# ============================================================

# Random Forest Configuration (PRODUCTION MODEL)
RF_PARAMS = {
    "n_estimators": 200,
    "max_depth": 12,
    "min_samples_split": 10,
    "min_samples_leaf": 4,
    "random_state": RANDOM_STATE,
    "n_jobs": -1
}

# ============================================================
# INTERPRETATION PARAMETERS
# ============================================================

# SHAP Configuration
SHAP_SAMPLE_SIZE = 17000  # Number of samples for SHAP computation (for efficiency)
SHAP_SEED = RANDOM_STATE

# Risk Categorization Thresholds (for decision support)
RISK_THRESHOLDS = {
    "LOW": (0.0, 0.4),
    "MEDIUM": (0.4, 0.7),
    "HIGH": (0.7, 1.0)
}

# ============================================================
# PREPROCESSING CONFIGURATION
# ============================================================

# Imputation Strategies
CATEGORICAL_IMPUTATION_STRATEGY = "most_frequent"
NUMERICAL_IMPUTATION_STRATEGY = "median"

# One-Hot Encoding
ONEHOT_HANDLE_UNKNOWN = "ignore"  # Silently drop unknown categories

# Data Types
CSV_ENCODING = "utf-8"

# ============================================================
# LOGGING CONFIGURATION
# ============================================================

LOG_DIR = PROJECT_ROOT / "logs"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
