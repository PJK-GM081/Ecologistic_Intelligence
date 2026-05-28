"""Persistence helpers for processed data and preprocessing artifacts."""

from pathlib import Path
from typing import Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer

from src.utils.config import ENCODERS_DIR, METADATA_DIR, PROCESSED_DATA_DIR
from src.utils.helpers import ensure_directories_exist
from src.utils.logger import get_logger

logger = get_logger(__name__)


# SAVE PROCESSED DATA
# Save processed datasets, preprocessor, and metadata.
def save_processed_data(
    X_train: np.ndarray,
    X_test: np.ndarray,
    y_train: pd.Series,
    y_test: pd.Series,
    feature_names: list,
    preprocessor: ColumnTransformer,
    global_means: dict,
    output_dir: Optional[Path] = None
) -> None:
    logger.info("=" * 60)
    logger.info("SAVE PROCESSED DATA")
    logger.info("=" * 60)
    
    output_dir = Path(output_dir) if output_dir else Path(PROCESSED_DATA_DIR)
    ensure_directories_exist([output_dir, Path(ENCODERS_DIR), Path(METADATA_DIR)])
    
    # Convert arrays to DataFrames for CSV storage
    X_train_df = pd.DataFrame(X_train, columns=feature_names)
    X_test_df = pd.DataFrame(X_test, columns=feature_names)
    
    # Save data
    X_train_df.to_csv(output_dir / "X_train.csv", index=False)
    X_test_df.to_csv(output_dir / "X_test.csv", index=False)
    y_train.to_csv(output_dir / "y_train.csv", index=False)
    y_test.to_csv(output_dir / "y_test.csv", index=False)
    
    logger.info(f"Saved X_train: {output_dir / 'X_train.csv'}")
    logger.info(f"Saved X_test: {output_dir / 'X_test.csv'}")
    logger.info(f"Saved y_train: {output_dir / 'y_train.csv'}")
    logger.info(f"Saved y_test: {output_dir / 'y_test.csv'}")
    
    # Save preprocessor
    joblib.dump(preprocessor, Path(ENCODERS_DIR) / "preprocessor.pkl")
    logger.info(f"Saved preprocessor: {Path(ENCODERS_DIR) / 'preprocessor.pkl'}")
    
    # Save metadata
    metadata = {
        "feature_names": feature_names,
        "global_means": global_means,
        "n_features": len(feature_names),
        "n_train": len(X_train_df),
        "n_test": len(X_test_df),
    }
    joblib.dump(metadata, Path(METADATA_DIR) / "preprocessing_metadata.pkl")
    logger.info(f"Saved metadata: {Path(METADATA_DIR) / 'preprocessing_metadata.pkl'}")

