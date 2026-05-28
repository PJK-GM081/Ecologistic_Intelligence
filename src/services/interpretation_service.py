from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd

from src.utils.config import METADATA_DIR, MODEL_PATH
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ShipmentExplanation:
    """Explanation for a single shipment prediction."""

    risk_probability: float
    risk_level: str
    top_contributing_factors: List[Tuple[str, float]]
    dominant_driver: str
    explanation_text: str
    method: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "risk_probability": float(self.risk_probability),
            "risk_level": self.risk_level,
            "top_factors": [
                {"feature": feature, "contribution": float(contribution)}
                for feature, contribution in self.top_contributing_factors
            ],
            "dominant_driver": self.dominant_driver,
            "explanation": self.explanation_text,
            "method": self.method,
        }


class InterpretationService:
    """Explainability service with optional sampled SHAP workflows."""

    def __init__(
        self,
        model_path: Optional[Path] = None,
        metadata_path: Optional[Path] = None,
        background_sample_size: int = 100,
        global_sample_size: int = 500,
        random_state: int = 42,
    ) -> None:
        self.model_path = Path(model_path) if model_path else Path(MODEL_PATH)
        self.metadata_path = (
            Path(metadata_path) if metadata_path else Path(METADATA_DIR) / "preprocessing_metadata.pkl"
        )
        self.background_sample_size = background_sample_size
        self.global_sample_size = global_sample_size
        self.random_state = random_state

        self.model = self._load_optional_model()
        self.metadata = self._load_metadata()
        self.feature_names: List[str] = list(self.metadata.get("feature_names", []))
        self.explainer = None
        self._global_importance_cache: Optional[Dict[str, Any]] = None
        logger.info("InterpretationService initialized with method=%s", self.runtime_method)

    @property
    def runtime_method(self) -> str:
        if self.model is None:
            return "heuristic"
        if self._shap_available():
            return "sampled_shap"
        return "model_importance"

    def _load_optional_model(self) -> Any:
        if not self.model_path.exists():
            logger.warning("Model not found at %s; interpretation will use heuristics", self.model_path)
            return None
        return joblib.load(self.model_path)

    def _load_metadata(self) -> Dict[str, Any]:
        if not self.metadata_path.exists():
            return {"feature_names": [], "global_means": {}}
        return joblib.load(self.metadata_path)

    def _shap_available(self) -> bool:
        try:
            import shap  # noqa: F401

            return True
        except Exception:
            return False

    def _initialize_explainer(self) -> bool:
        if self.explainer is not None:
            return True
        if self.model is None or not self._shap_available():
            return False

        try:
            import shap

            self.explainer = shap.TreeExplainer(self.model)
            return True
        except Exception as exc:
            logger.warning("SHAP initialization failed; falling back to lightweight explanation: %s", exc)
            self.explainer = None
            return False

    def _positive_class_shap(self, shap_values: Any) -> np.ndarray:
        if isinstance(shap_values, list):
            return np.asarray(shap_values[1])
        values = np.asarray(shap_values)
        if values.ndim == 3 and values.shape[-1] > 1:
            return values[:, :, 1]
        return values

    def _compute_shap_values(self, X: pd.DataFrame) -> Optional[np.ndarray]:
        if not self._initialize_explainer():
            return None
        try:
            values = self.explainer.shap_values(X)
            return self._positive_class_shap(values)
        except Exception as exc:
            logger.warning("SHAP computation failed; falling back to lightweight explanation: %s", exc)
            return None

    def _feature_names_for(self, width: int, X: Optional[pd.DataFrame] = None) -> List[str]:
        if self.feature_names and len(self.feature_names) >= width:
            return self.feature_names[:width]
        if X is not None and len(X.columns) >= width:
            return list(X.columns[:width])
        return [f"feature_{index}" for index in range(width)]

    def _top_from_values(
        self,
        values: np.ndarray,
        feature_names: List[str],
        top_n: int,
    ) -> List[Tuple[str, float]]:
        row = np.asarray(values).reshape(-1)
        if row.size == 0:
            return []
        top_indices = np.argsort(np.abs(row))[-top_n:][::-1]
        return [(feature_names[index], float(row[index])) for index in top_indices if index < len(feature_names)]

    def _model_importance_factors(self, X_single: pd.DataFrame, top_n: int) -> List[Tuple[str, float]]:
        importances = getattr(self.model, "feature_importances_", None)
        if importances is None:
            return self._heuristic_factors(X_single, top_n)
        importances = np.asarray(importances, dtype=float)
        feature_names = self._feature_names_for(len(importances), X_single)
        top_indices = np.argsort(importances)[-top_n:][::-1]
        return [(feature_names[index], float(importances[index])) for index in top_indices]

    def _heuristic_factors(self, X_single: pd.DataFrame, top_n: int) -> List[Tuple[str, float]]:
        row = X_single.iloc[0].to_dict()
        factors = {
            "days_for_shipment_(scheduled)": -0.06 * float(row.get("days_for_shipment_(scheduled)", 1) or 0),
            "shipping_mode": 0.10 if str(row.get("shipping_mode", "")).lower() in {"standard class", "ship"} else 0.03,
            "order_region": 0.05,
            "category_name": 0.04,
            "order_item_quantity": min(float(row.get("order_item_quantity", 0) or 0) / 100.0, 0.15),
            "sales": min(float(row.get("sales", 0) or 0) / 10000.0, 0.10),
        }
        return sorted(factors.items(), key=lambda item: abs(item[1]), reverse=True)[:top_n]

    def _text_for(self, risk_level: str, top_factors: List[Tuple[str, float]], method: str) -> str:
        if not top_factors:
            return f"{risk_level.title()} risk explanation generated with {method}."
        driver, contribution = top_factors[0]
        direction = "increases" if contribution >= 0 else "reduces"
        return f"Main driver: {driver} ({direction} delay risk). Explanation method: {method}."

    def explain_prediction(
        self,
        X_single: pd.DataFrame,
        risk_probability: float,
        risk_level: str,
        top_n: int = 5,
        background_X: Optional[pd.DataFrame] = None,
    ) -> ShipmentExplanation:
        """Explain one prediction without dashboard-wide SHAP recomputation."""
        if len(X_single) != 1:
            raise ValueError("Runtime explanation accepts exactly one shipment row")

        method = "heuristic"
        top_factors: List[Tuple[str, float]]

        shap_input = X_single
        if background_X is not None and len(background_X) > self.background_sample_size:
            background_X = background_X.sample(n=self.background_sample_size, random_state=self.random_state)

        shap_values = self._compute_shap_values(shap_input)
        if shap_values is not None:
            method = "local_shap"
            names = self._feature_names_for(shap_values.shape[1], X_single)
            top_factors = self._top_from_values(shap_values[0], names, top_n)
        elif self.model is not None:
            method = "model_importance"
            top_factors = self._model_importance_factors(X_single, top_n)
        else:
            top_factors = self._heuristic_factors(X_single, top_n)

        dominant_driver = top_factors[0][0] if top_factors else "N/A"
        return ShipmentExplanation(
            risk_probability=risk_probability,
            risk_level=risk_level,
            top_contributing_factors=top_factors,
            dominant_driver=dominant_driver,
            explanation_text=self._text_for(risk_level, top_factors, method),
            method=method,
        )

    def explain_shipment(
        self,
        shipment_features: pd.DataFrame,
        risk_probability: float,
        risk_level: Optional[str] = None,
        top_n: int = 5,
    ) -> Dict[str, Any]:
        level = risk_level or ("HIGH" if risk_probability > 0.7 else "MEDIUM" if risk_probability > 0.4 else "LOW")
        return self.explain_prediction(
            X_single=shipment_features,
            risk_probability=risk_probability,
            risk_level=level,
            top_n=top_n,
        ).to_dict()

    def get_feature_importance(
        self,
        X_sample: pd.DataFrame,
        top_n: int = 15,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """Compute sampled global importance; caller should pass a bounded sample."""
        if use_cache and self._global_importance_cache is not None:
            return self._global_importance_cache

        sample = X_sample
        if len(sample) > self.global_sample_size:
            sample = sample.sample(n=self.global_sample_size, random_state=self.random_state)

        shap_values = self._compute_shap_values(sample)
        if shap_values is not None:
            scores = np.abs(shap_values).mean(axis=0)
            method = "sampled_global_shap"
        elif self.model is not None and hasattr(self.model, "feature_importances_"):
            scores = np.asarray(self.model.feature_importances_, dtype=float)
            method = "model_importance"
        else:
            scores = np.ones(len(sample.columns), dtype=float)
            method = "heuristic"

        names = self._feature_names_for(len(scores), sample)
        top_indices = np.argsort(scores)[-top_n:][::-1]
        features = [
            {"feature": names[index], "importance": float(scores[index])}
            for index in top_indices
            if index < len(names)
        ]
        result = {
            "features": features,
            "total_features": int(len(scores)),
            "sample_size": int(len(sample)),
            "method": method,
        }
        if use_cache:
            self._global_importance_cache = result
        return result

    def analyze_regional_patterns(
        self,
        X_test: pd.DataFrame,
        y_pred_proba: np.ndarray,
        region_column: str = "order_region",
        samples_per_region: int = 50,
        top_n: int = 5,
    ) -> Dict[str, Dict[str, Any]]:
        """Sample per region to avoid full-test SHAP computation."""
        if region_column not in X_test.columns:
            return {}

        proba = np.asarray(y_pred_proba, dtype=float).reshape(-1)
        if len(proba) != len(X_test):
            raise ValueError("X_test and y_pred_proba length mismatch")

        result: Dict[str, Dict[str, Any]] = {}
        for region, region_X in X_test.groupby(region_column, dropna=False):
            if len(region_X) > samples_per_region:
                sample_X = region_X.sample(n=samples_per_region, random_state=self.random_state)
            else:
                sample_X = region_X

            importance = self.get_feature_importance(sample_X, top_n=top_n, use_cache=False)
            region_mask = X_test[region_column] == region
            region_proba = proba[region_mask.to_numpy()]
            result[str(region)] = {
                "region": str(region),
                "average_risk": float(region_proba.mean()) if len(region_proba) else 0.0,
                "num_shipments": int(len(region_X)),
                "sample_size": int(len(sample_X)),
                "top_risk_drivers": importance["features"][:top_n],
                "method": importance["method"],
            }
        return result
