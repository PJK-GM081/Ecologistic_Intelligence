"""Helper functions for data loading, validation, and utility operations."""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Optional
from src.utils.config import RAW_DATA_PATH, CSV_ENCODING
from src.utils.logger import get_logger

logger = get_logger(__name__)


def load_raw_data(file_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load raw dataset from CSV.
    
    Args:
        file_path: Path to CSV file. Defaults to RAW_DATA_PATH from config.
        
    Returns:
        Loaded DataFrame
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file cannot be read
    """
    path = Path(file_path) if file_path else Path(RAW_DATA_PATH)
    
    if not path.exists():
        raise FileNotFoundError(f"Raw data file not found: {path}")
    
    logger.info(f"Loading raw data from {path}")
    last_error = None
    for encoding in (CSV_ENCODING, "latin1", "cp1252"):
        try:
            df = pd.read_csv(path, encoding=encoding)
            logger.info(f"Data loaded: shape {df.shape} using encoding={encoding}")
            return df
        except UnicodeDecodeError as e:
            last_error = e
            logger.warning(f"Failed to load data with encoding={encoding}: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to load data: {str(e)}")
            raise ValueError(f"Cannot read CSV file {path}: {str(e)}")

    raise ValueError(f"Cannot read CSV file {path}: {str(last_error)}")


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize column names to lowercase with underscores.
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with normalized column names
    """
    df.columns = df.columns.str.lower().str.replace(' ', '_')
    return df


def ensure_directories_exist(directories: list) -> None:
    """
    Ensure all directories in list exist, create if not.
    
    Args:
        directories: List of Path objects to create
    """
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Directory ensured: {directory}")


def validate_data_shape(df: pd.DataFrame, expected_columns: list, name: str = "DataFrame") -> None:
    """
    Validate that DataFrame has expected columns.
    
    Args:
        df: DataFrame to validate
        expected_columns: List of column names to check
        name: Name for logging purposes
        
    Raises:
        ValueError: If expected columns are missing
    """
    missing_cols = set(expected_columns) - set(df.columns)
    if missing_cols:
        raise ValueError(f"{name} missing columns: {missing_cols}")
    logger.debug(f"{name} shape validated: {df.shape}")


def handle_missing_values(df: pd.DataFrame, strategy: str = "report") -> pd.DataFrame:
    """
    Handle missing values in DataFrame.
    
    Args:
        df: Input DataFrame
        strategy: "report" (log only), "drop" (drop rows), or "fillna" (fill with median/mode)
        
    Returns:
        DataFrame with handled missing values
    """
    missing_count = df.isnull().sum()
    if missing_count.sum() == 0:
        logger.info("No missing values found")
        return df
    
    logger.warning(f"Missing values found:\n{missing_count[missing_count > 0]}")
    
    if strategy == "report":
        return df
    elif strategy == "drop":
        return df.dropna()
    elif strategy == "fillna":
        # Fill numerical columns with median, categorical with mode
        for col in df.columns:
            if df[col].isnull().sum() > 0:
                if df[col].dtype in [np.float64, np.int64]:
                    df[col].fillna(df[col].median(), inplace=True)
                else:
                    df[col].fillna(df[col].mode()[0] if len(df[col].mode()) > 0 else 'Unknown', inplace=True)
        return df
    else:
        raise ValueError(f"Unknown strategy: {strategy}")


def split_features_target(df: pd.DataFrame, target_column: str) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Split DataFrame into features and target.
    
    Args:
        df: Input DataFrame containing features and target
        target_column: Name of target column
        
    Returns:
        Tuple of (features DataFrame, target Series)
    """
    if target_column not in df.columns:
        raise ValueError(f"Target column '{target_column}' not found in DataFrame")
    
    X = df.drop(columns=[target_column])
    y = df[target_column]
    logger.info(f"Features shape: {X.shape}, Target shape: {y.shape}")
    return X, y


def get_target_distribution(y: pd.Series) -> dict:
    """
    Get distribution of target variable.
    
    Args:
        y: Target series
        
    Returns:
        Dictionary with distribution statistics
    """
    dist = y.value_counts()
    dist_pct = y.value_counts(normalize=True) * 100
    
    result = {
        "counts": dist.to_dict(),
        "percentages": dist_pct.to_dict(),
        "imbalance_ratio": dist.max() / dist.min() if len(dist) > 1 else 1.0
    }
    logger.info(f"Target distribution:\n{dist}\nPercentages:\n{dist_pct}")
    return result
