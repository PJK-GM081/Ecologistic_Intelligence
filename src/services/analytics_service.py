"""Operational analytics service for dashboard-ready summaries.

This service intentionally uses raw operational data and simple aggregations.
It does not call SHAP and it does not run model inference across the dashboard
request path.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from src.utils.config import RAW_DATA_PATH, TARGET
from src.utils.logger import get_logger

logger = get_logger(__name__)


LOW_THRESHOLD = 0.4
HIGH_THRESHOLD = 0.7


def _json_value(value: Any) -> Any:
    """Convert pandas/numpy scalars into JSON-safe Python values."""
    if pd.isna(value):
        return None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    return value


def _percent(numerator: float, denominator: float) -> float:
    return float((numerator / denominator) * 100) if denominator else 0.0


@dataclass
class RegionalRiskSummary:
    """Regional risk statistics."""

    region: str
    average_risk_score: float
    num_shipments: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    delay_rate: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "region": self.region,
            "average_risk_score": float(self.average_risk_score),
            "num_shipments": int(self.num_shipments),
            "high_risk_count": int(self.high_risk_count),
            "medium_risk_count": int(self.medium_risk_count),
            "low_risk_count": int(self.low_risk_count),
            "high_risk_percentage": _percent(self.high_risk_count, self.num_shipments),
            "delay_rate": float(self.delay_rate),
        }


@dataclass
class ShippingModeRiskSummary:
    """Shipping mode reliability statistics."""

    shipping_mode: str
    average_risk_score: float
    num_shipments: int
    delayed_count: int

    def to_dict(self) -> Dict[str, Any]:
        reliability_rate = 1.0 - (self.delayed_count / self.num_shipments) if self.num_shipments else 0.0
        return {
            "shipping_mode": self.shipping_mode,
            "average_risk_score": float(self.average_risk_score),
            "num_shipments": int(self.num_shipments),
            "delayed_count": int(self.delayed_count),
            "delay_rate": _percent(self.delayed_count, self.num_shipments),
            "reliability_rate": float(reliability_rate),
            "risk_level": risk_level(self.average_risk_score),
        }


@dataclass
class CategoryRiskSummary:
    """Category-level delay statistics."""

    category: str
    average_risk_score: float
    num_shipments: int
    delayed_count: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "average_risk_score": float(self.average_risk_score),
            "num_shipments": int(self.num_shipments),
            "delayed_count": int(self.delayed_count),
            "delay_rate": _percent(self.delayed_count, self.num_shipments),
            "risk_level": risk_level(self.average_risk_score),
        }


@dataclass
class DashboardSummary:
    """Overall dashboard summary."""

    total_shipments: int
    high_risk_shipments: int
    medium_risk_shipments: int
    low_risk_shipments: int
    average_delay_risk: float
    delayed_shipments: int
    most_risky_region: str
    most_risky_shipping_mode: str
    most_risky_category: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_shipments": int(self.total_shipments),
            "high_risk_shipments": int(self.high_risk_shipments),
            "medium_risk_shipments": int(self.medium_risk_shipments),
            "low_risk_shipments": int(self.low_risk_shipments),
            "delayed_shipments": int(self.delayed_shipments),
            "average_delay_risk": float(self.average_delay_risk),
            "delay_rate": _percent(self.delayed_shipments, self.total_shipments),
            "risk_distribution": {
                "high": _percent(self.high_risk_shipments, self.total_shipments),
                "medium": _percent(self.medium_risk_shipments, self.total_shipments),
                "low": _percent(self.low_risk_shipments, self.total_shipments),
            },
            "most_risky_region": self.most_risky_region,
            "most_risky_shipping_mode": self.most_risky_shipping_mode,
            "most_risky_category": self.most_risky_category,
        }


def risk_level(probability: float) -> str:
    if probability > HIGH_THRESHOLD:
        return "HIGH"
    if probability > LOW_THRESHOLD:
        return "MEDIUM"
    return "LOW"


class AnalyticsService:
    """Fast operational analytics service for frontend dashboards."""

    def __init__(
        self,
        data_path: Optional[Path] = None,
        max_rows: Optional[int] = None,
    ) -> None:
        self.data_path = Path(data_path) if data_path else Path(RAW_DATA_PATH)
        self.max_rows = max_rows
        self._data_cache: Optional[pd.DataFrame] = None
        self._analytics_cache: Optional[Dict[str, Any]] = None
        logger.info("AnalyticsService initialized")

    def _load_operational_data(self) -> pd.DataFrame:
        if self._data_cache is not None:
            return self._data_cache.copy()

        if not self.data_path.exists():
            raise FileNotFoundError(f"Operational data not found at {self.data_path}")

        logger.info("Loading operational analytics data from %s", self.data_path)
        df = self._read_csv_with_fallback(self.data_path)
        df.columns = df.columns.str.lower().str.strip().str.replace(" ", "_", regex=False)
        self._data_cache = self._prepare_operational_frame(df)
        return self._data_cache.copy()

    def _read_csv_with_fallback(self, path: Path) -> pd.DataFrame:
        last_error: Optional[Exception] = None
        for encoding in ("utf-8", "latin1", "cp1252"):
            try:
                return pd.read_csv(path, nrows=self.max_rows, encoding=encoding)
            except UnicodeDecodeError as exc:
                last_error = exc
                logger.warning("Could not read %s with %s encoding", path, encoding)
        if last_error:
            raise last_error
        return pd.read_csv(path, nrows=self.max_rows)

    def _prepare_operational_frame(self, df: pd.DataFrame) -> pd.DataFrame:
        required = {"order_region", "shipping_mode", "category_name"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"Operational data missing required columns: {sorted(missing)}")

        prepared = df.copy()
        target_col = TARGET if TARGET in prepared.columns else "late_delivery_risk"

        if target_col in prepared.columns:
            prepared["delay_flag"] = pd.to_numeric(prepared[target_col], errors="coerce").fillna(0).clip(0, 1)
            prepared["risk_score"] = prepared["delay_flag"].astype(float)
            risk_source = "raw_target"
        else:
            prepared["delay_flag"] = 0.0
            prepared["risk_score"] = 0.0
            risk_source = "missing_target_default"

        for col in ("order_region", "shipping_mode", "category_name", "market", "customer_segment"):
            if col in prepared.columns:
                prepared[col] = prepared[col].fillna("Unknown").astype(str)

        if "sales" in prepared.columns:
            prepared["sales"] = pd.to_numeric(prepared["sales"], errors="coerce").fillna(0.0)
        if "order_item_quantity" in prepared.columns:
            prepared["order_item_quantity"] = pd.to_numeric(
                prepared["order_item_quantity"], errors="coerce"
            ).fillna(0.0)

        prepared.attrs["risk_source"] = risk_source
        return prepared

    def _with_prediction_scores(
        self,
        X_test: pd.DataFrame,
        y_pred_proba: np.ndarray,
    ) -> pd.DataFrame:
        df = X_test.copy()
        proba = np.asarray(y_pred_proba, dtype=float).reshape(-1)
        if len(df) != len(proba):
            raise ValueError("X_test and y_pred_proba length mismatch")
        df["risk_score"] = np.clip(proba, 0.0, 1.0)
        df["delay_flag"] = (df["risk_score"] > 0.5).astype(int)
        return df

    def _risk_counts(self, scores: pd.Series) -> Dict[str, int]:
        return {
            "high": int((scores > HIGH_THRESHOLD).sum()),
            "medium": int(((scores > LOW_THRESHOLD) & (scores <= HIGH_THRESHOLD)).sum()),
            "low": int((scores <= LOW_THRESHOLD).sum()),
        }

    def _top_name(self, df: pd.DataFrame, column: str) -> str:
        if column not in df.columns or df.empty:
            return "N/A"
        grouped = df.groupby(column, dropna=False)["risk_score"].mean().sort_values(ascending=False)
        return str(grouped.index[0]) if len(grouped) else "N/A"

    def compute_regional_summary(
        self,
        X_test: pd.DataFrame,
        y_pred_proba: np.ndarray,
        region_column: str = "order_region",
    ) -> Dict[str, RegionalRiskSummary]:
        return self._regional_summary_from_frame(self._with_prediction_scores(X_test, y_pred_proba), region_column)

    def compute_shipping_mode_summary(
        self,
        X_test: pd.DataFrame,
        y_pred_proba: np.ndarray,
        mode_column: str = "shipping_mode",
    ) -> Dict[str, ShippingModeRiskSummary]:
        return self._mode_summary_from_frame(self._with_prediction_scores(X_test, y_pred_proba), mode_column)

    def compute_category_summary(
        self,
        X_test: pd.DataFrame,
        y_pred_proba: np.ndarray,
        category_column: str = "category_name",
    ) -> Dict[str, CategoryRiskSummary]:
        return self._category_summary_from_frame(self._with_prediction_scores(X_test, y_pred_proba), category_column)

    def compute_dashboard_summary(
        self,
        X_test: pd.DataFrame,
        y_pred_proba: np.ndarray,
        regional_summaries: Dict[str, RegionalRiskSummary],
        mode_summaries: Dict[str, ShippingModeRiskSummary],
        category_summaries: Dict[str, CategoryRiskSummary],
    ) -> DashboardSummary:
        df = self._with_prediction_scores(X_test, y_pred_proba)
        return self._dashboard_summary_from_frame(
            df,
            regional_summaries,
            mode_summaries,
            category_summaries,
        )

    def _regional_summary_from_frame(
        self,
        df: pd.DataFrame,
        region_column: str = "order_region",
    ) -> Dict[str, RegionalRiskSummary]:
        if region_column not in df.columns:
            return {}

        summaries = {}
        for region, group in df.groupby(region_column, dropna=False):
            counts = self._risk_counts(group["risk_score"])
            summaries[str(region)] = RegionalRiskSummary(
                region=str(region),
                average_risk_score=float(group["risk_score"].mean()),
                num_shipments=int(len(group)),
                high_risk_count=counts["high"],
                medium_risk_count=counts["medium"],
                low_risk_count=counts["low"],
                delay_rate=float(group["delay_flag"].mean()) if len(group) else 0.0,
            )
        return summaries

    def _mode_summary_from_frame(
        self,
        df: pd.DataFrame,
        mode_column: str = "shipping_mode",
    ) -> Dict[str, ShippingModeRiskSummary]:
        if mode_column not in df.columns:
            return {}

        summaries = {}
        for mode, group in df.groupby(mode_column, dropna=False):
            summaries[str(mode)] = ShippingModeRiskSummary(
                shipping_mode=str(mode),
                average_risk_score=float(group["risk_score"].mean()),
                num_shipments=int(len(group)),
                delayed_count=int(group["delay_flag"].sum()),
            )
        return summaries

    def _category_summary_from_frame(
        self,
        df: pd.DataFrame,
        category_column: str = "category_name",
    ) -> Dict[str, CategoryRiskSummary]:
        if category_column not in df.columns:
            return {}

        summaries = {}
        for category, group in df.groupby(category_column, dropna=False):
            summaries[str(category)] = CategoryRiskSummary(
                category=str(category),
                average_risk_score=float(group["risk_score"].mean()),
                num_shipments=int(len(group)),
                delayed_count=int(group["delay_flag"].sum()),
            )
        return summaries

    def _dashboard_summary_from_frame(
        self,
        df: pd.DataFrame,
        regional_summaries: Dict[str, RegionalRiskSummary],
        mode_summaries: Dict[str, ShippingModeRiskSummary],
        category_summaries: Dict[str, CategoryRiskSummary],
    ) -> DashboardSummary:
        counts = self._risk_counts(df["risk_score"])
        return DashboardSummary(
            total_shipments=int(len(df)),
            high_risk_shipments=counts["high"],
            medium_risk_shipments=counts["medium"],
            low_risk_shipments=counts["low"],
            average_delay_risk=float(df["risk_score"].mean()) if len(df) else 0.0,
            delayed_shipments=int(df["delay_flag"].sum()) if "delay_flag" in df else 0,
            most_risky_region=max(
                regional_summaries.items(),
                key=lambda item: item[1].average_risk_score,
            )[0]
            if regional_summaries
            else "N/A",
            most_risky_shipping_mode=max(
                mode_summaries.items(),
                key=lambda item: item[1].average_risk_score,
            )[0]
            if mode_summaries
            else "N/A",
            most_risky_category=max(
                category_summaries.items(),
                key=lambda item: item[1].average_risk_score,
            )[0]
            if category_summaries
            else "N/A",
        )

    def generate_all_analytics(
        self,
        X_test: pd.DataFrame,
        y_pred_proba: np.ndarray,
    ) -> Dict[str, Any]:
        df = self._with_prediction_scores(X_test, y_pred_proba)
        return self._all_from_frame(df, source="prediction_scores")

    def _all_from_frame(self, df: pd.DataFrame, source: str) -> Dict[str, Any]:
        regional = self._regional_summary_from_frame(df)
        modes = self._mode_summary_from_frame(df)
        categories = self._category_summary_from_frame(df)
        dashboard = self._dashboard_summary_from_frame(df, regional, modes, categories)

        return {
            "dashboard_summary": dashboard.to_dict(),
            "regional_risk": {key: value.to_dict() for key, value in regional.items()},
            "shipping_mode_risk": {key: value.to_dict() for key, value in modes.items()},
            "category_risk": {key: value.to_dict() for key, value in categories.items()},
            "metadata": {
                "source": source,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "cached": False,
            },
        }

    def get_home_summary(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Return dashboard-ready aggregate summaries from operational data."""
        if self._analytics_cache is not None and not force_refresh:
            cached = dict(self._analytics_cache)
            cached["metadata"] = {**cached.get("metadata", {}), "cached": True}
            return cached

        df = self._load_operational_data()
        result = self._all_from_frame(df, source=df.attrs.get("risk_source", "operational_data"))
        self._analytics_cache = result
        return result

    def get_region_summary(self, region: Optional[str] = None) -> Dict[str, Any]:
        """Return all region summaries or one specific region summary."""
        data = self.get_home_summary()
        regions = data.get("regional_risk", {})

        if region is None:
            return {
                "regions": list(regions.values()),
                "count": len(regions),
                "metadata": data.get("metadata", {}),
            }

        match_key = next((key for key in regions if key.lower() == region.lower()), None)
        if match_key is None:
            return {
                "region": region,
                "found": False,
                "message": "Region not found",
                "available_regions": sorted(regions.keys()),
            }

        df = self._load_operational_data()
        region_df = df[df["order_region"].str.lower() == match_key.lower()]
        by_mode = self._mode_summary_from_frame(region_df)
        by_category = self._category_summary_from_frame(region_df)

        return {
            "found": True,
            "summary": regions[match_key],
            "shipping_mode_risk": {key: value.to_dict() for key, value in by_mode.items()},
            "category_risk": {key: value.to_dict() for key, value in by_category.items()},
            "metadata": data.get("metadata", {}),
        }

    def get_distribution_summary(self, dimension: str = "risk") -> Dict[str, Any]:
        """Return distribution data ready for charts."""
        df = self._load_operational_data()

        if dimension == "risk":
            counts = self._risk_counts(df["risk_score"])
            total = len(df)
            return {
                "dimension": "risk",
                "items": [
                    {"label": "HIGH", "count": counts["high"], "percentage": _percent(counts["high"], total)},
                    {"label": "MEDIUM", "count": counts["medium"], "percentage": _percent(counts["medium"], total)},
                    {"label": "LOW", "count": counts["low"], "percentage": _percent(counts["low"], total)},
                ],
            }

        dimension_map = {
            "region": "order_region",
            "shipping_mode": "shipping_mode",
            "mode": "shipping_mode",
            "category": "category_name",
            "market": "market",
            "customer_segment": "customer_segment",
        }
        column = dimension_map.get(dimension, dimension)
        if column not in df.columns:
            return {
                "dimension": dimension,
                "items": [],
                "message": f"Unsupported distribution dimension: {dimension}",
            }

        grouped = (
            df.groupby(column, dropna=False)
            .agg(
                count=("risk_score", "size"),
                average_risk_score=("risk_score", "mean"),
                delayed_count=("delay_flag", "sum"),
            )
            .sort_values(["average_risk_score", "count"], ascending=[False, False])
            .reset_index()
        )

        total = len(df)
        return {
            "dimension": dimension,
            "items": [
                {
                    "label": str(row[column]),
                    "count": int(row["count"]),
                    "percentage": _percent(row["count"], total),
                    "average_risk_score": float(row["average_risk_score"]),
                    "delayed_count": int(row["delayed_count"]),
                    "delay_rate": _percent(row["delayed_count"], row["count"]),
                }
                for _, row in grouped.iterrows()
            ],
        }
