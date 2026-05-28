"""Prediction service for runtime-safe shipment delay inference."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib
import numpy as np
import pandas as pd

from src.utils.config import ENCODERS_DIR, METADATA_DIR, MODEL_PATH, RISK_THRESHOLDS
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PredictionOutput:
    """Standard prediction output."""

    risk_probability: float
    risk_level: str
    risk_score: int
    explanation: str
    predicted_class: int
    input_features: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "risk_probability": float(self.risk_probability),
            "risk_level": self.risk_level,
            "risk_score": int(self.risk_score),
            "predicted_class": int(self.predicted_class),
            "explanation": self.explanation,
            "input_features": self.input_features,
        }


class PredictionService:
    """Production prediction service for single and batch inference."""

    def __init__(
        self,
        model_path: Optional[Path] = None,
        preprocessor_path: Optional[Path] = None,
        metadata_path: Optional[Path] = None,
    ) -> None:
        self.model_path = Path(model_path) if model_path else Path(MODEL_PATH)
        self.preprocessor_path = (
            Path(preprocessor_path) if preprocessor_path else Path(ENCODERS_DIR) / "preprocessor.pkl"
        )
        self.metadata_path = (
            Path(metadata_path) if metadata_path else Path(METADATA_DIR) / "preprocessing_metadata.pkl"
        )

        self.model = self._load_artifact(self.model_path, "model")
        self.preprocessor = self._load_artifact(self.preprocessor_path, "preprocessor")
        self.metadata = self._load_metadata()
        self.feature_names: List[str] = list(self.metadata.get("feature_names", []))
        self.global_means: Dict[str, Any] = dict(self.metadata.get("global_means", {}))
        self.expected_input_columns = self._resolve_expected_input_columns()
        logger.info("PredictionService initialized with %s output features", len(self.feature_names))

    def _load_artifact(self, path: Path, label: str) -> Any:
        if not path.exists():
            raise FileNotFoundError(f"{label.title()} artifact not found at {path}")
        logger.info("Loading %s from %s", label, path)
        return joblib.load(path)

    def _load_metadata(self) -> Dict[str, Any]:
        if not self.metadata_path.exists():
            logger.warning("Metadata not found at %s; continuing with defaults", self.metadata_path)
            return {"feature_names": [], "global_means": {}}
        return joblib.load(self.metadata_path)

    def _resolve_expected_input_columns(self) -> List[str]:
        if hasattr(self.preprocessor, "feature_names_in_"):
            return list(self.preprocessor.feature_names_in_)

        columns: List[str] = []
        transformers = getattr(self.preprocessor, "transformers", [])
        for _, _, transformer_columns in transformers:
            if isinstance(transformer_columns, (list, tuple)):
                columns.extend(list(transformer_columns))
        return list(dict.fromkeys(columns))

    def _global_mean(self, key: Optional[str] = None, default: float = 0.5) -> float:
        if key and isinstance(self.global_means.get(key), dict):
            return float(self.global_means.get("global_mean", default))
        return float(self.global_means.get(key or "global_mean", self.global_means.get("global_mean", default)))

    def build_feature_frame(
        self,
        *,
        region: str,
        shipping_mode: str,
        category: str,
        quantity: int,
        days_for_shipment: int = 1,
        sales: float = 100.0,
        benefit_per_order: float = 0.0,
        customer_segment: str = "Unknown",
        market: str = "Unknown",
        order_month: Optional[int] = None,
        order_dayofweek: Optional[int] = None,
        is_weekend: Optional[int] = None,
    ) -> pd.DataFrame:
        """Build a raw feature frame that matches the fitted preprocessor."""

        day = 0 if order_dayofweek is None else int(order_dayofweek)
        weekend = int(is_weekend) if is_weekend is not None else int(day in (5, 6))
        raw = {
            "order_region": region,
            "shipping_mode": shipping_mode,
            "category_name": category,
            "order_item_quantity": int(quantity),
            "days_for_shipment_(scheduled)": int(days_for_shipment),
            "sales": float(sales),
            "benefit_per_order": float(benefit_per_order),
            "customer_segment": customer_segment,
            "market": market,
            "order_month": int(order_month) if order_month is not None else datetime.now().month,
            "order_dayofweek": day,
            "is_weekend_order": weekend,
            "shipping_mode_risk": self._lookup_encoded_mean("shipping_mode_risk", shipping_mode),
            "avg_delay_by_region": self._lookup_encoded_mean("region_risk", region),
            "category_delay_risk": self._lookup_encoded_mean("category_risk", category),
            "customer_order_count": 1,
            "customer_late_rate": self._global_mean(),
        }

        if self.expected_input_columns:
            for column in self.expected_input_columns:
                raw.setdefault(column, self._default_value_for_column(column))
            raw = {column: raw[column] for column in self.expected_input_columns}

        return pd.DataFrame([raw])

    def _lookup_encoded_mean(self, mapping_key: str, value: str) -> float:
        mapping = self.global_means.get(mapping_key, {})
        if isinstance(mapping, dict) and value in mapping:
            return float(mapping[value])
        return self._global_mean()

    def _default_value_for_column(self, column: str) -> Any:
        if column in {
            "category_name",
            "customer_segment",
            "market",
            "order_region",
            "shipping_mode",
        }:
            return "Unknown"
        if column in {"order_month"}:
            return datetime.now().month
        if column in {"order_dayofweek", "is_weekend_order"}:
            return 0
        if "risk" in column or "rate" in column or "avg_delay" in column:
            return self._global_mean()
        return 0

    def _preprocess_input(self, X: pd.DataFrame) -> np.ndarray:
        if self.expected_input_columns:
            missing = [column for column in self.expected_input_columns if column not in X.columns]
            if missing:
                raise ValueError(f"Input missing columns required by preprocessor: {missing}")
            X = X[self.expected_input_columns]
        return self.preprocessor.transform(X)

    def predict_single(self, X: pd.DataFrame) -> tuple[int, float]:
        X_processed = self._preprocess_input(X)
        predicted_class = int(self.model.predict(X_processed)[0])
        if hasattr(self.model, "predict_proba"):
            probability = float(self.model.predict_proba(X_processed)[0, 1])
        else:
            probability = float(predicted_class)
        return predicted_class, max(0.0, min(1.0, probability))

    def predict_batch(self, X: pd.DataFrame) -> np.ndarray:
        X_processed = self._preprocess_input(X)
        if hasattr(self.model, "predict_proba"):
            probabilities = self.model.predict_proba(X_processed)[:, 1]
        else:
            probabilities = self.model.predict(X_processed)
        return np.clip(np.asarray(probabilities, dtype=float), 0.0, 1.0)

    def _get_risk_level(self, probability: float) -> str:
        low_high = RISK_THRESHOLDS.get("LOW", (0.0, 0.4))[1]
        medium_high = RISK_THRESHOLDS.get("MEDIUM", (0.4, 0.7))[1]
        if probability <= low_high:
            return "LOW"
        if probability <= medium_high:
            return "MEDIUM"
        return "HIGH"

    def _generate_explanation(self, probability: float, risk_level_name: str) -> str:
        pct = probability * 100
        if risk_level_name == "HIGH":
            return f"High risk of shipment delay ({pct:.1f}%). Requires operational attention."
        if risk_level_name == "MEDIUM":
            return f"Moderate risk of shipment delay ({pct:.1f}%). Monitor this shipment closely."
        return f"Low risk of shipment delay ({pct:.1f}%). Shipment appears on track."

    def predict(self, **shipment: Any) -> PredictionOutput:
        X = self.build_feature_frame(**shipment)
        predicted_class, probability = self.predict_single(X)
        level = self._get_risk_level(probability)
        return PredictionOutput(
            risk_probability=probability,
            risk_level=level,
            risk_score=int(round(probability * 100)),
            predicted_class=predicted_class,
            explanation=self._generate_explanation(probability, level),
            input_features={key: self._safe_json(value) for key, value in X.iloc[0].to_dict().items()},
        )

    def predict_from_frame(self, X: pd.DataFrame) -> List[Dict[str, Any]]:
        probabilities = self.predict_batch(X)
        results = []
        for probability in probabilities:
            level = self._get_risk_level(float(probability))
            results.append(
                {
                    "risk_probability": float(probability),
                    "risk_level": level,
                    "risk_score": int(round(float(probability) * 100)),
                    "explanation": self._generate_explanation(float(probability), level),
                }
            )
        return results

    def transform_for_model(self, X: pd.DataFrame) -> np.ndarray:
        """Expose inference-safe transformation for interpretation workflows."""
        return self._preprocess_input(X)

    def _safe_json(self, value: Any) -> Any:
        if pd.isna(value):
            return None
        if isinstance(value, (np.integer,)):
            return int(value)
        if isinstance(value, (np.floating,)):
            return float(value)
        return value
