"""Data preprocessing pipeline for logistic delay risk prediction.

This module contains the complete data preprocessing pipeline including:
- Feature selection
- Temporal feature engineering
- Target encoding (train-only aggregations)
- Frequency encoding
- Bayesian smoothing
- Data preprocessing (imputation + encoding)
- Train/test splitting with group awareness
"""

import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from typing import Tuple, Dict, Any, Optional
from sklearn.model_selection import GroupShuffleSplit
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

from src.utils.config import (
    RAW_FEATURES,
    CATEGORICAL_FEATURES,
    NUMERICAL_FEATURES,
    TARGET,
    TEST_SIZE,
    RANDOM_STATE,
    GROUPBY_COLUMN,
    SMOOTHING_FACTOR,
    CATEGORICAL_IMPUTATION_STRATEGY,
    NUMERICAL_IMPUTATION_STRATEGY,
    ONEHOT_HANDLE_UNKNOWN,
    PROCESSED_DATA_DIR,
    ENCODERS_DIR,
    METADATA_DIR,
)
from src.utils.helpers import (
    load_raw_data,
    normalize_columns,
    validate_data_shape,
    get_target_distribution,
    ensure_directories_exist,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


# TEMPORAL FEATURE ENGINEERING
# Create temporal features from order_date column.
def create_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("=" * 60)
    logger.info("CREATE TEMPORAL FEATURES")
    logger.info("=" * 60)
    
    df = df.copy()
    
    # Convert to datetime
    date_col = "order_date_(dateorders)"
    if date_col not in df.columns:
        raise ValueError(f"Column '{date_col}' not found")
    
    df[date_col] = pd.to_datetime(df[date_col])
    
    # Extract temporal features
    df["order_month"] = df[date_col].dt.month
    df["order_dayofweek"] = df[date_col].dt.dayofweek
    df["is_weekend_order"] = (df["order_dayofweek"].isin([5, 6])).astype(int)
    
    logger.info("Created 3 temporal features: order_month, order_dayofweek, is_weekend_order")
    logger.info(f"DataFrame shape after temporal engineering: {df.shape}")
    
    return df


# TARGET ENCODINGS (TRAIN-ONLY AGGREGATIONS)
def create_target_encodings( # target-encoded features from train data only.
    train_df: pd.DataFrame,
    test_df: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, float]]:
    logger.info("=" * 60)
    logger.info("TARGET ENCODINGS (TRAIN-ONLY)")
    logger.info("=" * 60)
    
    train_df = train_df.copy()
    test_df = test_df.copy()
    
    # Calculate global mean (baseline for unknowns)
    global_mean = train_df[TARGET].mean()
    global_means = {"global_mean": global_mean}
    
    logger.info(f"Global delay rate (train): {global_mean:.4f}")
    
    # 1. SHIPPING MODE RISK
    shipping_mode_risk = train_df.groupby("shipping_mode")[TARGET].mean()
    global_means["shipping_mode_risk"] = shipping_mode_risk.to_dict()
    
    train_df["shipping_mode_risk"] = train_df["shipping_mode"].map(shipping_mode_risk)
    test_df["shipping_mode_risk"] = test_df["shipping_mode"].map(shipping_mode_risk).fillna(global_mean)
    logger.info(f"Created shipping_mode_risk. Unique modes: {len(shipping_mode_risk)}")
    
    # 2. REGION RISK
    region_risk = train_df.groupby("order_region")[TARGET].mean()
    global_means["region_risk"] = region_risk.to_dict()
    
    train_df["avg_delay_by_region"] = train_df["order_region"].map(region_risk)
    test_df["avg_delay_by_region"] = test_df["order_region"].map(region_risk).fillna(global_mean)
    logger.info(f"Created avg_delay_by_region. Unique regions: {len(region_risk)}")
    
    # 3. CATEGORY RISK
    category_risk = train_df.groupby("category_name")[TARGET].mean()
    global_means["category_risk"] = category_risk.to_dict()
    
    train_df["category_delay_risk"] = train_df["category_name"].map(category_risk)
    test_df["category_delay_risk"] = test_df["category_name"].map(category_risk).fillna(global_mean)
    logger.info(f"Created category_delay_risk. Unique categories: {len(category_risk)}")
    
    logger.info(f"Target encodings created successfully")
    
    return train_df, test_df, global_means


# FREQUENCY ENCODINGS
# frequency-based features (count of orders per customer)
def create_frequency_features(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    logger.info("=" * 60)
    logger.info("FREQUENCY ENCODINGS")
    logger.info("=" * 60)
    
    train_df = train_df.copy()
    test_df = test_df.copy()
    
    # Customer order count (from training set only)
    customer_order_count = train_df.groupby("customer_id")["order_id"].count()
    
    train_df["customer_order_count"] = train_df["customer_id"].map(customer_order_count)
    test_df["customer_order_count"] = test_df["customer_id"].map(customer_order_count).fillna(0)
    
    logger.info(f"Created customer_order_count. Unique customers in train: {len(customer_order_count)}")
    logger.info(f"Min order count: {customer_order_count.min()}, Max: {customer_order_count.max()}")
    
    # Log unseen customers in test
    unseen_customers = test_df[test_df["customer_order_count"] == 0].shape[0]
    if unseen_customers > 0:
        logger.warning(f"Unseen customers in test: {unseen_customers} ({unseen_customers/len(test_df)*100:.1f}%)")
    
    return train_df, test_df


# BAYESIAN SMOOTHED FEATURES
def create_bayesian_smoothed_features( # Create Bayesian smoothed customer late rate to handle sparse data.
    train_df: pd.DataFrame,
    test_df: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    logger.info("=" * 60)
    logger.info("BAYESIAN SMOOTHED FEATURES")
    logger.info("=" * 60)
    
    train_df = train_df.copy()
    test_df = test_df.copy()
    
    # Global late rate
    global_rate = train_df[TARGET].mean()
    logger.info(f"Global late rate: {global_rate:.4f}")
    logger.info(f"Smoothing factor (k): {SMOOTHING_FACTOR}")
    
    # Customer statistics
    customer_stats = train_df.groupby("customer_id")[TARGET].agg(
        n_transactions="size",
        raw_late_rate="mean",
    )
    
    # Apply Bayesian smoothing
    # smoothed_rate = (n * raw_rate + k * global_rate) / (n + k)
    customer_stats["customer_late_rate"] = (
        (customer_stats["n_transactions"] * customer_stats["raw_late_rate"]) +
        (SMOOTHING_FACTOR * global_rate)
    ) / (customer_stats["n_transactions"] + SMOOTHING_FACTOR)
    
    # Verify smoothing effect
    logger.info(f"Smoothing effect:")
    logger.info(f"  Raw rate range: [{customer_stats['raw_late_rate'].min():.4f}, {customer_stats['raw_late_rate'].max():.4f}]")
    logger.info(f"  Smoothed rate range: [{customer_stats['customer_late_rate'].min():.4f}, {customer_stats['customer_late_rate'].max():.4f}]")
    
    # Map to train and test
    train_df["customer_late_rate"] = train_df["customer_id"].map(
        customer_stats["customer_late_rate"]
    )
    test_df["customer_late_rate"] = test_df["customer_id"].map(
        customer_stats["customer_late_rate"]
    ).fillna(global_rate)
    
    logger.info(f"Bayesian smoothed customer_late_rate created")
    
    return train_df, test_df


# DROP TEMPORARY COLUMNS
def drop_temporary_columns(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    logger.info("=" * 60)
    logger.info("DROP TEMPORARY COLUMNS")
    logger.info("=" * 60)
    
    cols_to_drop = [GROUPBY_COLUMN, "order_id", "order_date_(dateorders)"]
    existing_cols = [col for col in cols_to_drop if col in train_df.columns]
    
    if existing_cols:
        train_df = train_df.drop(columns=existing_cols)
        test_df = test_df.drop(columns=existing_cols)
        logger.info(f"Dropped columns: {existing_cols}")
    
    return train_df, test_df


# SEPARATE FEATURES AND TARGET
# Separate features and target variables
def separate_features_target(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
    logger.info("=" * 60)
    logger.info("SEPARATE FEATURES AND TARGET")
    logger.info("=" * 60)
    
    X_train = train_df.drop(columns=[TARGET])
    y_train = train_df[TARGET]
    
    X_test = test_df.drop(columns=[TARGET])
    y_test = test_df[TARGET]
    
    logger.info(f"X_train shape: {X_train.shape}")
    logger.info(f"y_train shape: {y_train.shape}")
    logger.info(f"X_test shape: {X_test.shape}")
    logger.info(f"y_test shape: {y_test.shape}")
    
    return X_train, y_train, X_test, y_test


# PREPROCESSING PIPELINE
# Build scikit-learn preprocessing pipeline for categorical and numerical features.
def build_preprocessing_pipeline() -> ColumnTransformer:
    logger.info("=" * 60)
    logger.info("BUILD PREPROCESSING PIPELINE")
    logger.info("=" * 60)
    
    # Categorical preprocessing
    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy=CATEGORICAL_IMPUTATION_STRATEGY)),
            ("encoder", OneHotEncoder(handle_unknown=ONEHOT_HANDLE_UNKNOWN, sparse_output=False))
        ]
    )
    
    # Numerical preprocessing
    numerical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy=NUMERICAL_IMPUTATION_STRATEGY))
        ]
    )
    
    # Combine
    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", categorical_transformer, CATEGORICAL_FEATURES),
            ("num", numerical_transformer, NUMERICAL_FEATURES)
        ]
    )
    
    logger.info("Preprocessing pipeline created")
    return preprocessor


# FIT AND TRANSFORM DATA
# Fit preprocessor on training data and transform both train and test.
def fit_and_transform_data(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    preprocessor: ColumnTransformer
) -> Tuple[np.ndarray, np.ndarray, list]:
    logger.info("=" * 60)
    logger.info("FIT AND TRANSFORM DATA")
    logger.info("=" * 60)
    
    # Fit on train, transform both
    X_train_transformed = preprocessor.fit_transform(X_train)
    X_test_transformed = preprocessor.transform(X_test)
    
    logger.info(f"X_train transformed shape: {X_train_transformed.shape}")
    logger.info(f"X_test transformed shape: {X_test_transformed.shape}")
    
    # Get feature names (for interpretation)
    feature_names = get_feature_names(preprocessor, X_train)
    logger.info(f"Total features after preprocessing: {len(feature_names)}")
    
    return X_train_transformed, X_test_transformed, feature_names


def get_feature_names(preprocessor: ColumnTransformer, X_train: pd.DataFrame) -> list:
    """Extract feature names from preprocessor."""
    feature_names = []
    
    for name, transformer, columns in preprocessor.transformers_:
        if name == "cat":
            # Get one-hot encoded feature names
            encoder = transformer.named_steps["encoder"]
            encoded_names = encoder.get_feature_names_out(columns)
            feature_names.extend(encoded_names)
        else:  # numerical
            feature_names.extend(columns)
    
    return feature_names
