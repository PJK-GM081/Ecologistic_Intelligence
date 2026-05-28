import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from typing import Dict, Tuple, Optional, Union, List
from dataclasses import dataclass

from src.utils.config import (
    MODEL_PATH,
    ENCODERS_DIR,
    METADATA_DIR,
    RISK_THRESHOLDS,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


# DATA CLASSES
@dataclass
class PredictionResult:
    """Container for prediction output."""
    probability: float
    risk_level: str
    risk_score: int
    explanation: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "probability": float(self.probability),
            "risk_level": self.risk_level,
            "risk_score": self.risk_score,
            "explanation": self.explanation
        }


@dataclass
class UserSimulationInput:
    """Container for user simulation input."""
    region: str
    shipping_mode: str
    category: str
    quantity: int
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "region": self.region,
            "shipping_mode": self.shipping_mode,
            "category": self.category,
            "quantity": self.quantity
        }


# MODEL & PREPROCESSOR LOADING
class PredictionPipeline:
    """Production prediction pipeline."""
    
    def __init__(self, model_path: Optional[Path] = None, preprocessor_path: Optional[Path] = None):
        self.model_path = Path(model_path) if model_path else Path(MODEL_PATH) # Initialize prediction pipeline with model and preprocessor.
        self.preprocessor_path = Path(preprocessor_path) if preprocessor_path else Path(ENCODERS_DIR) / "preprocessor.pkl"
        self.metadata_path = Path(METADATA_DIR) / "preprocessing_metadata.pkl"
        
        # Load components
        self.model = self._load_model()
        self.preprocessor = self._load_preprocessor()
        self.metadata = self._load_metadata()
        self.feature_names = self.metadata.get("feature_names", [])
        self.global_means = self.metadata.get("global_means", {})
        
        logger.info(f"Prediction pipeline initialized with {len(self.feature_names)} features")
    
    def _load_model(self):
        """Load trained model."""
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found at {self.model_path}")
        logger.info(f"Loading model from {self.model_path}")
        return joblib.load(self.model_path)
    
    def _load_preprocessor(self):
        """Load preprocessing pipeline."""
        if not self.preprocessor_path.exists():
            raise FileNotFoundError(f"Preprocessor not found at {self.preprocessor_path}")
        logger.info(f"Loading preprocessor from {self.preprocessor_path}")
        return joblib.load(self.preprocessor_path)
    
    def _load_metadata(self) -> Dict:
        """Load preprocessing metadata."""
        if not self.metadata_path.exists():
            logger.warning(f"Metadata not found at {self.metadata_path}")
            return {"feature_names": [], "global_means": {}}
        logger.info(f"Loading metadata from {self.metadata_path}")
        return joblib.load(self.metadata_path)
    
    # preprocess a single sample or batch.
    def preprocess_single_sample(self, X: pd.DataFrame) -> np.ndarray:
        return self.preprocessor.transform(X)
    
    #  predict for a single sample.
    def predict_single(self, X: pd.DataFrame) -> Tuple[float, float]:
        X_processed = self.preprocess_single_sample(X)
        pred_class = self.model.predict(X_processed)[0]
        pred_proba = self.model.predict_proba(X_processed)[0, 1]  # Probability of class 1 (delay)
        
        return int(pred_class), float(pred_proba)
    
    # predict for multiple samples
    def predict_batch(self, X: pd.DataFrame) -> np.ndarray:
        X_processed = self.preprocess_single_sample(X)
        pred_proba = self.model.predict_proba(X_processed)[:, 1]  # Probability of class 1
        
        return pred_proba
    
    #  classify probability into risk level (LOW, MEDIUM, HIGH)
    def get_risk_level(self, probability: float) -> str:
        for level, (low, high) in RISK_THRESHOLDS.items():
            if low <= probability < high:
                return level
        return "HIGH"  # Default if above all thresholds
    
    # generate human-readable explanation for prediction
    def explain_prediction(self, probability: float, risk_level: str) -> str:
        if risk_level == "HIGH":
            return f"High risk of shipment delay ({probability*100:.1f}%). Recommend review and mitigation."
        elif risk_level == "MEDIUM":
            return f"Moderate risk of shipment delay ({probability*100:.1f}%). Monitor closely."
        else:
            return f"Low risk of shipment delay ({probability*100:.1f}%). Shipment appears on track."


# PREDICTION INTERFACE
def make_prediction(
    features_df: pd.DataFrame,
    model_path: Optional[Path] = None,
    preprocessor_path: Optional[Path] = None
) -> Union[PredictionResult, List[Dict]]:
    pipeline = PredictionPipeline(model_path, preprocessor_path) # Make prediction on input features.
    
    if len(features_df) == 1:
        # Single prediction
        pred_class, probability = pipeline.predict_single(features_df)
        risk_level = pipeline.get_risk_level(probability)
        risk_score = int(probability * 100)
        explanation = pipeline.explain_prediction(probability, risk_level)
        
        return PredictionResult(
            probability=probability,
            risk_level=risk_level,
            risk_score=risk_score,
            explanation=explanation
        )
    else:
        # Batch prediction
        probabilities = pipeline.predict_batch(features_df)
        
        results = []
        for i, probability in enumerate(probabilities):
            risk_level = pipeline.get_risk_level(probability)
            risk_score = int(probability * 100)
            explanation = pipeline.explain_prediction(probability, risk_level)
            
            result = PredictionResult(
                probability=probability,
                risk_level=risk_level,
                risk_score=risk_score,
                explanation=explanation
            )
            results.append(result.to_dict())
        
        return results


# USER SIMULATION
# Simulate a shipment prediction from user inputs.
def simulate_shipment_prediction(
    region: str,
    shipping_mode: str,
    category: str,
    quantity: int,
    days_for_shipment: int = 1,
    sales: float = 100.0,
    model_path: Optional[Path] = None
) -> Dict:
    """
    Example:
        region: Shipping region (e.g., "Western Europe")
        shipping_mode: Shipping mode (e.g., "Flight", "Ship")
        category: Product category (e.g., "Apparel")
        quantity: Order quantity
        days_for_shipment: Scheduled days for shipment (default 1)
        sales: Order sales amount (default 100.0)
        model_path: Optional path to model
    """
    
    logger.info(f"Simulating shipment: region={region}, mode={shipping_mode}, category={category}, qty={quantity}")
    
    # Load pipeline and metadata
    pipeline = PredictionPipeline(model_path)
    
    # Build input dataframe (must match preprocessor expectations)
    # This is a simplified version - in production, you'd need the exact feature set
    input_data = pd.DataFrame({
        "days_for_shipment_(scheduled)": [days_for_shipment],
        "order_item_quantity": [quantity],
        "sales": [sales],
        "category_name": [category],
        "customer_segment": ["Consumer"],  # Default
        "market": ["Africa"],  # Default
        "order_region": [region],
        "shipping_mode": [shipping_mode],
        
        # Add engineered features using global means
        "order_month": [6],  # Default month
        "order_dayofweek": [2],  # Default day
        "is_weekend_order": [0],  # Default not weekend
        "shipping_mode_risk": [pipeline.global_means.get("global_mean", 0.5)],
        "avg_delay_by_region": [pipeline.global_means.get("global_mean", 0.5)],
        "category_delay_risk": [pipeline.global_means.get("global_mean", 0.5)],
        "customer_order_count": [1],  # Single order
        "customer_late_rate": [pipeline.global_means.get("global_mean", 0.5)],
    })
    
    # Make prediction
    pred_class, probability = pipeline.predict_single(input_data)
    risk_level = pipeline.get_risk_level(probability)
    risk_score = int(probability * 100)
    explanation = pipeline.explain_prediction(probability, risk_level)
    
    logger.info(f"Prediction: risk_level={risk_level}, probability={probability:.3f}")
    
    return {
        "input": {
            "region": region,
            "shipping_mode": shipping_mode,
            "category": category,
            "quantity": quantity,
        },
        "prediction": {
            "probability": float(probability),
            "risk_level": risk_level,
            "risk_score": risk_score,
        },
        "explanation": explanation,
    }


if __name__ == "__main__":
    # Example: Simulate a shipment
    result = simulate_shipment_prediction(
        region="Western Europe",
        shipping_mode="Flight",
        category="Apparel",
        quantity=5
    )
    print("Prediction result:")
    print(result)
