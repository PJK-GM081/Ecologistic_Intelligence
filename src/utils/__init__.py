"""Utilities module for configuration, logging, and helpers."""

from src.utils.config import (
    PROJECT_ROOT,
    DATA_DIR,
    RAW_DATA_PATH,
    PROCESSED_DATA_DIR,
    MODELS_DIR,
    MODEL_PATH,
    X_TRAIN_PATH,
    X_TEST_PATH,
    Y_TRAIN_PATH,
    Y_TEST_PATH,
    TARGET,
    RAW_FEATURES,
    CATEGORICAL_FEATURES,
    NUMERICAL_FEATURES,
    AGGREGATION_FEATURES,
    TEST_SIZE,
    RANDOM_STATE,
    RF_PARAMS,
)

from src.utils.logger import setup_logger, get_logger
from src.utils.helpers import (
    load_raw_data,
    normalize_columns,
    ensure_directories_exist,
    validate_data_shape,
    handle_missing_values,
    split_features_target,
    get_target_distribution,
)

__all__ = [
    # Config
    "PROJECT_ROOT",
    "RAW_DATA_PATH",
    "MODELS_DIR",
    "MODEL_PATH",
    "TARGET",
    "RAW_FEATURES",
    "CATEGORICAL_FEATURES",
    "NUMERICAL_FEATURES",
    "TEST_SIZE",
    "RANDOM_STATE",
    "RF_PARAMS",
    # Logger
    "setup_logger",
    "get_logger",
    # Helpers
    "load_raw_data",
    "normalize_columns",
    "ensure_directories_exist",
    "validate_data_shape",
    "split_features_target",
]
