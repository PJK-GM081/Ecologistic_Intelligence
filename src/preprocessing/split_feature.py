from pathlib import Path
from typing import Optional, Tuple

import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

from src.preprocessing.feature_engineering import (
    build_preprocessing_pipeline,
    create_bayesian_smoothed_features,
    create_frequency_features,
    create_target_encodings,
    create_temporal_features,
    drop_temporary_columns,
    fit_and_transform_data,
    separate_features_target,
)
from src.preprocessing.pipeline import save_processed_data
from src.utils.config import GROUPBY_COLUMN, RANDOM_STATE, RAW_FEATURES, TARGET, TEST_SIZE
from src.utils.helpers import (
    get_target_distribution,
    load_raw_data,
    normalize_columns,
    validate_data_shape,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


# LOAD AND SELECT FEATURES
def load_and_select_features(file_path: Optional[Path] = None) -> pd.DataFrame:
    logger.info("=" * 60)
    logger.info("STEP 1: LOAD AND SELECT FEATURES")
    logger.info("=" * 60)
    
    # Load data
    df = load_raw_data(file_path)
    
    # Normalize column names
    df = normalize_columns(df)
    logger.info(f"Column names normalized: {df.columns.tolist()}")
    
    # Select features + target
    selected_cols = RAW_FEATURES + [TARGET]
    validate_data_shape(df, selected_cols, "Raw data")
    
    df = df[selected_cols].copy()
    logger.info(f"Selected {len(RAW_FEATURES)} features + target. Shape: {df.shape}")
    
    # Log target distribution
    target_dist = get_target_distribution(df[TARGET])
    logger.info(f"Target imbalance ratio: {target_dist['imbalance_ratio']:.2f}")
    
    return df


# TRAIN/TEST SPLIT (BEFORE AGGREGATIONS)
# Split dataset into train/test using GroupShuffleSplit on customer_id.
def split_dataset(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    logger.info("=" * 60)
    logger.info("STEP 3: TRAIN/TEST SPLIT (GROUP-AWARE)")
    logger.info("=" * 60)
    
    if GROUPBY_COLUMN not in df.columns:
        raise ValueError(f"Grouping column '{GROUPBY_COLUMN}' not found")
    
    # GroupShuffleSplit by customer_id to prevent leakage
    gss = GroupShuffleSplit(
        n_splits=1,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE
    )
    
    train_idx, test_idx = next(
        gss.split(df, groups=df[GROUPBY_COLUMN])
    )
    
    train_df = df.iloc[train_idx].copy()
    test_df = df.iloc[test_idx].copy()
    
    logger.info(f"Train size: {len(train_df)} ({len(train_df)/len(df)*100:.1f}%)")
    logger.info(f"Test size: {len(test_df)} ({len(test_df)/len(df)*100:.1f}%)")
    
    # Validate no customer overlap
    train_customers = set(train_df[GROUPBY_COLUMN].unique())
    test_customers = set(test_df[GROUPBY_COLUMN].unique())
    overlap = train_customers.intersection(test_customers)
    
    if overlap:
        logger.warning(f"Customer overlap detected: {len(overlap)} customers in both sets")
    else:
        logger.info("No customer leakage: train and test sets have different customers")
    
    # Log target distribution
    logger.info(f"Train target balance: {train_df[TARGET].mean():.3f}")
    logger.info(f"Test target balance: {test_df[TARGET].mean():.3f}")
    
    return train_df, test_df


def run_full_preprocessing(input_file: Optional[Path] = None) -> None:
    """Run preprocessing while keeping transformation logic split by module."""
    logger.info("Starting full preprocessing pipeline")

    df = load_and_select_features(input_file)
    df = create_temporal_features(df)
    train_df, test_df = split_dataset(df)
    train_df, test_df, global_means = create_target_encodings(train_df, test_df)
    train_df, test_df = create_frequency_features(train_df, test_df)
    train_df, test_df = create_bayesian_smoothed_features(train_df, test_df)
    train_df, test_df = drop_temporary_columns(train_df, test_df)
    X_train, y_train, X_test, y_test = separate_features_target(train_df, test_df)
    preprocessor = build_preprocessing_pipeline()
    X_train_transformed, X_test_transformed, feature_names = fit_and_transform_data(
        X_train,
        X_test,
        preprocessor,
    )
    save_processed_data(
        X_train_transformed,
        X_test_transformed,
        y_train,
        y_test,
        feature_names,
        preprocessor,
        global_means,
    )

    logger.info("Preprocessing pipeline completed")
