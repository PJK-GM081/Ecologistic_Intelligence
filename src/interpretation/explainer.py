import numpy as np
import pandas as pd
import joblib
import shap
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

from src.utils.config import (
    MODEL_PATH,
    ENCODERS_DIR,
    METADATA_DIR,
    SHAP_SAMPLE_SIZE,
    SHAP_SEED,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)

s
# DATA CLASSES
@dataclass
class ShipmentExplanation:
    """Explanation for a single shipment prediction."""
    risk_probability: float
    risk_level: str
    top_contributing_factors: List[Tuple[str, float]]  # [(feature_name, shap_value), ...]
    dominant_driver: str
    explanation_text: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "risk_probability": float(self.risk_probability),
            "risk_level": self.risk_level,
            "top_factors": [
                {"feature": f[0], "contribution": float(f[1])}
                for f in self.top_contributing_factors
            ],
            "dominant_driver": self.dominant_driver,
            "explanation": self.explanation_text,
        }


@dataclass
class RegionalRiskAnalysis:
    """Risk analysis for a specific region."""
    region: str
    average_risk_score: float
    top_risk_factors: List[Tuple[str, float]]
    risk_summary: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "region": self.region,
            "average_risk_score": float(self.average_risk_score),
            "top_factors": [
                {"feature": f[0], "impact": float(f[1])}
                for f in self.top_risk_factors
            ],
            "summary": self.risk_summary,
        }


# SHAP EXPLAINER
# Initialize SHAP explainer.
class ShapExplainer:
    """SHAP-based model explainer."""
    def __init__(
        self,
        model_path: Optional[Path] = None,
        metadata_path: Optional[Path] = None,
        sample_size: int = SHAP_SAMPLE_SIZE
    ):
        self.model_path = Path(model_path) if model_path else Path(MODEL_PATH)
        self.metadata_path = Path(metadata_path) if metadata_path else Path(METADATA_DIR) / "preprocessing_metadata.pkl"
        self.sample_size = sample_size
        
        # Load model and metadata
        self.model = self._load_model()
        self.metadata = self._load_metadata()
        self.feature_names = self.metadata.get("feature_names", [])
        
        # Initialize explainer (will be created on first use)
        self.explainer = None
        self.shap_values_cache = None
        self.background_data = None
        
        logger.info(f"ShapExplainer initialized with {len(self.feature_names)} features")
    
    def _load_model(self):
        """Load trained model."""
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found at {self.model_path}")
        logger.info(f"Loading model from {self.model_path}")
        return joblib.load(self.model_path)
    
    def _load_metadata(self) -> Dict:
        """Load metadata."""
        if not self.metadata_path.exists():
            logger.warning(f"Metadata not found at {self.metadata_path}")
            return {"feature_names": []}
        return joblib.load(self.metadata_path)
    
    # Compute SHAP values for input samples.
    def compute_shap_values(self, X: pd.DataFrame) -> np.ndarray:
        logger.info(f"Computing SHAP values for {len(X)} samples...")
        
        # Initialize explainer if not already done
        if self.explainer is None:
            # Use first 100 samples as background (for efficiency)
            background_size = min(100, len(X))
            self.background_data = X.iloc[:background_size]
            self.explainer = shap.TreeExplainer(self.model)
            logger.info(f"SHAP TreeExplainer initialized with {background_size} background samples")
        
        # Compute SHAP values
        shap_values = self.explainer.shap_values(X)
        
        # For binary classification, return SHAP values for positive class (index 1)
        if isinstance(shap_values, list):
            return shap_values[1]  # Positive class
        else:
            return shap_values
    
    # Get global feature importance based on mean absolute SHAP values.
    def get_feature_importance(self, X: pd.DataFrame, top_n: int = 15) -> pd.DataFrame: 
        logger.info("Computing global feature importance...")
        
        shap_values = self.compute_shap_values(X)
        
        # Mean absolute SHAP values
        feature_importance = pd.DataFrame({
            "feature": self.feature_names,
            "mean_abs_shap": np.abs(shap_values).mean(axis=0)
        }).sort_values("mean_abs_shap", ascending=False)
        
        logger.info(f"Top {top_n} important features:")
        for idx, row in feature_importance.head(top_n).iterrows():
            logger.info(f"  {row['feature']:40s}: {row['mean_abs_shap']:.6f}")
        
        return feature_importance
    
    def explain_single_prediction( # Generate explanation for a single shipment prediction.
        self,
        X_single: pd.DataFrame,
        y_pred_proba: float,
        risk_level: str,
        top_n: int = 5
    ) -> ShipmentExplanation:
        logger.info("Explaining individual shipment prediction...")
        
        # Compute SHAP values
        shap_values = self.compute_shap_values(X_single)
        
        # Get top contributing factors
        shap_row = shap_values[0]  # Single sample
        top_indices = np.argsort(np.abs(shap_row))[-top_n:][::-1]
        
        top_factors = [
            (self.feature_names[idx], float(shap_row[idx]))
            for idx in top_indices
        ]
        
        # Dominant driver (largest absolute SHAP)
        dominant_idx = np.argmax(np.abs(shap_row))
        dominant_driver = self.feature_names[dominant_idx]
        dominant_value = float(shap_row[dominant_idx])
        
        # Generate explanation text
        if abs(dominant_value) > 0.1:
            if dominant_value > 0:
                explanation_text = f"Main risk driver is {dominant_driver} (pushing toward higher delay risk). "
            else:
                explanation_text = f"Main protective factor is {dominant_driver} (reducing delay risk). "
        else:
            explanation_text = f"Risk is driven by combination of factors. "
        
        if risk_level == "HIGH":
            explanation_text += "This shipment requires attention and mitigation measures."
        elif risk_level == "MEDIUM":
            explanation_text += "This shipment should be monitored closely."
        else:
            explanation_text += "This shipment appears to be on track."
        
        return ShipmentExplanation(
            risk_probability=y_pred_proba,
            risk_level=risk_level,
            top_contributing_factors=top_factors,
            dominant_driver=dominant_driver,
            explanation_text=explanation_text
        )
    
    def analyze_regional_risk( # Analyze risk by region using SHAP values.
        self,
        X: pd.DataFrame,
        y_pred_proba: np.ndarray,
        region_column: str = "order_region",
        top_n: int = 5
    ) -> Dict[str, RegionalRiskAnalysis]:
        logger.info("Analyzing regional risk patterns...")
        
        # Compute SHAP values for all samples
        shap_values = self.compute_shap_values(X)
        
        # Reconstruct X with region info
        X_with_pred = X.copy()
        X_with_pred["_pred_proba"] = y_pred_proba
        X_with_pred["_shap_sum"] = np.abs(shap_values).sum(axis=1)
        
        regional_analysis = {}
        
        for region in X_with_pred[region_column].unique():
            region_mask = X_with_pred[region_column] == region
            region_avg_risk = X_with_pred.loc[region_mask, "_pred_proba"].mean()
            
            # Top risk factors for this region
            region_shap = shap_values[region_mask]
            mean_abs_shap = np.abs(region_shap).mean(axis=0)
            top_indices = np.argsort(mean_abs_shap)[-top_n:][::-1]
            
            top_factors = [
                (self.feature_names[idx], float(mean_abs_shap[idx]))
                for idx in top_indices
            ]
            
            # Summary
            if region_avg_risk > 0.6:
                risk_summary = f"High-risk region with {region_avg_risk*100:.1f}% average delay rate."
            elif region_avg_risk > 0.4:
                risk_summary = f"Moderate-risk region with {region_avg_risk*100:.1f}% average delay rate."
            else:
                risk_summary = f"Lower-risk region with {region_avg_risk*100:.1f}% average delay rate."
            
            regional_analysis[region] = RegionalRiskAnalysis(
                region=region,
                average_risk_score=region_avg_risk,
                top_risk_factors=top_factors,
                risk_summary=risk_summary
            )
        
        logger.info(f"Analyzed {len(regional_analysis)} regions")
        
        return regional_analysis
    
    def get_dominant_risk_drivers( # Identify globally dominant risk drivers across all predictions.
        self,
        X: pd.DataFrame,
        y_pred_proba: np.ndarray,
        top_n: int = 10
    ) -> List[Tuple[str, float]]:
        logger.info("Identifying dominant risk drivers...")
        
        shap_values = self.compute_shap_values(X)
        
        # Mean absolute SHAP values (weighted by prediction probability)
        # Higher predicted risk = more important to explain
        sample_weights = y_pred_proba / y_pred_proba.sum()  # Normalize
        weighted_shap = np.abs(shap_values) * sample_weights[:, np.newaxis]
        
        mean_impact = weighted_shap.sum(axis=0)
        
        top_indices = np.argsort(mean_impact)[-top_n:][::-1]
        
        drivers = [
            (self.feature_names[idx], float(mean_impact[idx]))
            for idx in top_indices
        ]
        
        logger.info(f"Top {top_n} risk drivers:")
        for feature, impact in drivers:
            logger.info(f"  {feature:40s}: {impact:.6f}")
        
        return drivers


# CONVENIENCE FUNCTIONS
def explain_prediction( # Generate SHAP-based explanation for a prediction.
    X_single: pd.DataFrame,
    y_pred_proba: float,
    risk_level: str,
    model_path: Optional[Path] = None
) -> Dict:
    explainer = ShapExplainer(model_path)
    explanation = explainer.explain_single_prediction(
        X_single, y_pred_proba, risk_level
    )
    return explanation.to_dict()

# get regional risk analysis
def get_regional_risk_analysis(
    X: pd.DataFrame,
    y_pred_proba: np.ndarray,
    model_path: Optional[Path] = None
) -> Dict:
    explainer = ShapExplainer(model_path)
    analysis = explainer.analyze_regional_risk(X, y_pred_proba)
    return {region: a.to_dict() for region, a in analysis.items()}


if __name__ == "__main__":
    logger.info("SHAP Explainer module loaded successfully")
