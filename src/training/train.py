import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from typing import Tuple, Dict, Any, Optional
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay
)
import matplotlib.pyplot as plt

from src.utils.config import (
    RF_PARAMS,
    RANDOM_STATE,
    MODELS_DIR,
    X_TRAIN_PATH,
    X_TEST_PATH,
    Y_TRAIN_PATH,
    Y_TEST_PATH,
    MODEL_PATH,
)
from src.utils.helpers import ensure_directories_exist
from src.utils.logger import get_logger

logger = get_logger(__name__)

# LOAD PROCESSED DATA
def load_processed_data() -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    logger.info("=" * 60)
    logger.info("STEP 1: LOAD PROCESSED DATA")
    logger.info("=" * 60)
    
    try:
        X_train = pd.read_csv(X_TRAIN_PATH)
        X_test = pd.read_csv(X_TEST_PATH)
        y_train = pd.read_csv(Y_TRAIN_PATH).squeeze()
        y_test = pd.read_csv(Y_TEST_PATH).squeeze()
        
        logger.info(f"X_train shape: {X_train.shape}")
        logger.info(f"X_test shape: {X_test.shape}")
        logger.info(f"y_train distribution: {y_train.value_counts().to_dict()}")
        logger.info(f"y_test distribution: {y_test.value_counts().to_dict()}")
        
        return X_train.values, X_test.values, y_train.values, y_test.values
        
    except FileNotFoundError as e:
        logger.error(f"Processed data not found: {e}")
        logger.error("Please run preprocessing pipeline first: src.preprocessing.split_feature.run_full_preprocessing()")
        raise

# TRAIN MODEL
def train_random_forest(
    X_train: np.ndarray,
    y_train: np.ndarray,
    hyperparams: Optional[Dict[str, Any]] = None
) -> RandomForestClassifier:
    logger.info("=" * 60)
    logger.info("TRAIN RANDOM FOREST MODEL")
    logger.info("=" * 60)
    
    params = hyperparams if hyperparams else RF_PARAMS
    
    logger.info(f"Hyperparameters:")
    for key, value in params.items():
        logger.info(f"  {key}: {value}")
    
    # Create and train model
    model = RandomForestClassifier(**params)
    logger.info("Training RandomForest...")
    model.fit(X_train, y_train)
    
    logger.info(f"Model trained successfully")
    logger.info(f"Number of trees: {model.n_estimators}")
    logger.info(f"Number of features: {model.n_features_in_}")
    
    return model


# ============================================================
# STEP 3: EVALUATE MODEL
# ============================================================

def evaluate_model(
    model: RandomForestClassifier,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray
) -> Dict[str, Dict[str, float]]:
    logger.info("=" * 60)
    logger.info("STEP 3: EVALUATE MODEL")
    logger.info("=" * 60)
    
    # Predictions
    y_train_pred = model.predict(X_train)
    y_test_pred = model.predict(X_test)
    
    # Metrics
    metrics = {}
    
    # Train metrics
    metrics["train"] = {
        "accuracy": accuracy_score(y_train, y_train_pred),
        "precision": precision_score(y_train, y_train_pred),
        "recall": recall_score(y_train, y_train_pred),
        "f1": f1_score(y_train, y_train_pred),
        "roc_auc": roc_auc_score(y_train, y_train_pred),
    }
    
    # Test metrics
    metrics["test"] = {
        "accuracy": accuracy_score(y_test, y_test_pred),
        "precision": precision_score(y_test, y_test_pred),
        "recall": recall_score(y_test, y_test_pred),
        "f1": f1_score(y_test, y_test_pred),
        "roc_auc": roc_auc_score(y_test, y_test_pred),
    }
    
    # Gap analysis (train - test)
    metrics["gap"] = {}
    for metric_name in metrics["train"].keys():
        gap = metrics["train"][metric_name] - metrics["test"][metric_name]
        metrics["gap"][metric_name] = gap
    
    # Log metrics
    logger.info("\nTRAIN METRICS:")
    logger.info("-" * 40)
    for metric, value in metrics["train"].items():
        logger.info(f"  {metric.upper():15s}: {value:.4f}")
    
    logger.info("\nTEST METRICS:")
    logger.info("-" * 40)
    for metric, value in metrics["test"].items():
        logger.info(f"  {metric.upper():15s}: {value:.4f}")
    
    logger.info("\nTRAIN-TEST GAP (overfitting indicator):")
    logger.info("-" * 40)
    for metric, gap in metrics["gap"].items():
        status = "HIGH" if gap > 0.1 else "OK"
        logger.info(f"  {metric.upper():15s}: {gap:.4f} {status}")
    
    # Classification report
    logger.info("\nCLASSIFICATION REPORT (Test Set):")
    logger.info("-" * 40)
    logger.info("\n" + classification_report(y_test, y_test_pred))
    
    return metrics, y_test_pred

# FEATURE IMPORTANCE
def get_feature_importance(
    model: RandomForestClassifier,
    X_train: pd.DataFrame,
    top_n: int = 20
) -> pd.DataFrame:
    """
    Get feature importance from trained model.
    
    Args:
        model: Trained RandomForestClassifier
        X_train: Training features (used to get feature names)
        top_n: Number of top features to return
        
    Returns:
        DataFrame with features and importance scores
    """
    logger.info("=" * 60)
    logger.info("STEP 4: FEATURE IMPORTANCE")
    logger.info("=" * 60)
    
    feature_importance = pd.DataFrame({
        "feature": X_train.columns if hasattr(X_train, 'columns') else range(model.n_features_in_),
        "importance": model.feature_importances_
    }).sort_values("importance", ascending=False)
    
    logger.info(f"\nTOP {top_n} MOST IMPORTANT FEATURES:")
    logger.info("-" * 40)
    for idx, row in feature_importance.head(top_n).iterrows():
        logger.info(f"  {str(row['feature']):30s}: {row['importance']:.6f}")
    
    return feature_importance

# SAVE MODEL
def save_model(
    model: RandomForestClassifier,
    output_path: Optional[Path] = None,
    metrics: Optional[Dict] = None
) -> Path:
    logger.info("=" * 60)
    logger.info("STEP 5: SAVE MODEL")
    logger.info("=" * 60)
    
    output_path = Path(output_path) if output_path else Path(MODEL_PATH)
    ensure_directories_exist([output_path.parent])
    
    joblib.dump(model, output_path)
    logger.info(f"Model saved to: {output_path}")
    
    # Also save metrics
    if metrics:
        metrics_path = output_path.parent / "model_metrics.pkl"
        joblib.dump(metrics, metrics_path)
        logger.info(f"Metrics saved to: {metrics_path}")
    
    return output_path

# LOAD MODEL
def load_model(model_path: Optional[Path] = None) -> RandomForestClassifier:
    model_path = Path(model_path) if model_path else Path(MODEL_PATH)
    
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found at {model_path}")
    
    logger.info(f"Loading model from {model_path}")
    model = joblib.load(model_path)
    logger.info(f"Model loaded successfully")
    
    return model


# MAIN TRAINING PIPELINE
def run_full_training() -> RandomForestClassifier:
    logger.info("\n" + "=" * 70)
    logger.info("STARTING FULL MODEL TRAINING PIPELINE")
    logger.info("=" * 70 + "\n")
    
    try:
        # Step 1: Load data
        X_train, X_test, y_train, y_test = load_processed_data()
        
        # Step 2: Train model
        model = train_random_forest(X_train, y_train)
        
        # Step 3: Evaluate
        metrics, y_test_pred = evaluate_model(model, X_train, y_train, X_test, y_test)
        
        # Step 4: Feature importance
        feature_importance = get_feature_importance(model, X_train)
        
        # Step 5: Save model
        save_model(model, metrics={"metrics": metrics})
        
        logger.info("\n" + "=" * 70)
        logger.info("TRAINING PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("=" * 70 + "\n")
        
        return model
        
    except Exception as e:
        logger.error(f"Training failed: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    run_full_training()
