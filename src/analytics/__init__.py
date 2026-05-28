"""Analytics module for dashboard backend aggregations.

This module provides:
- Regional risk aggregations
- Shipping mode risk summary
- Category risk analysis
- Operational monitoring metrics
- Summary statistics for dashboard
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from dataclasses import dataclass

from src.utils.logger import get_logger

logger = get_logger(__name__)


# ============================================================
# DATA CLASSES
# ============================================================

@dataclass
class RegionalRiskSummary:
    """Summary of risk metrics for a region."""
    region: str
    average_risk_score: float
    num_shipments: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "region": self.region,
            "average_risk_score": float(self.average_risk_score),
            "num_shipments": int(self.num_shipments),
            "high_risk_count": int(self.high_risk_count),
            "medium_risk_count": int(self.medium_risk_count),
            "low_risk_count": int(self.low_risk_count),
            "high_risk_percentage": float(self.high_risk_count / self.num_shipments * 100) if self.num_shipments > 0 else 0,
        }


@dataclass
class ShippingModeRiskSummary:
    """Summary of risk metrics for a shipping mode."""
    shipping_mode: str
    average_risk_score: float
    num_shipments: int
    reliability_rate: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "shipping_mode": self.shipping_mode,
            "average_risk_score": float(self.average_risk_score),
            "num_shipments": int(self.num_shipments),
            "reliability_rate": float(self.reliability_rate),
            "risk_level": self._get_risk_level(),
        }
    
    def _get_risk_level(self) -> str:
        """Categorize risk level."""
        if self.average_risk_score > 0.6:
            return "HIGH"
        elif self.average_risk_score > 0.4:
            return "MEDIUM"
        else:
            return "LOW"


@dataclass
class CategoryRiskSummary:
    """Summary of risk metrics for a product category."""
    category: str
    average_risk_score: float
    num_shipments: int
    delayed_count: int
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "category": self.category,
            "average_risk_score": float(self.average_risk_score),
            "num_shipments": int(self.num_shipments),
            "delayed_count": int(self.delayed_count),
            "delay_rate": float(self.delayed_count / self.num_shipments * 100) if self.num_shipments > 0 else 0,
        }


@dataclass
class DashboardSummary:
    """Overall dashboard summary."""
    total_shipments: int
    high_risk_shipments: int
    medium_risk_shipments: int
    low_risk_shipments: int
    average_delay_risk: float
    most_risky_region: str
    most_risky_shipping_mode: str
    most_risky_category: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "total_shipments": int(self.total_shipments),
            "high_risk_shipments": int(self.high_risk_shipments),
            "medium_risk_shipments": int(self.medium_risk_shipments),
            "low_risk_shipments": int(self.low_risk_shipments),
            "average_delay_risk": float(self.average_delay_risk),
            "risk_distribution": {
                "high": float(self.high_risk_shipments / self.total_shipments * 100) if self.total_shipments > 0 else 0,
                "medium": float(self.medium_risk_shipments / self.total_shipments * 100) if self.total_shipments > 0 else 0,
                "low": float(self.low_risk_shipments / self.total_shipments * 100) if self.total_shipments > 0 else 0,
            },
            "most_risky_region": self.most_risky_region,
            "most_risky_shipping_mode": self.most_risky_shipping_mode,
            "most_risky_category": self.most_risky_category,
        }


# ============================================================
# REGIONAL ANALYTICS
# ============================================================

def compute_regional_risk_summary(
    X_test: pd.DataFrame,
    y_pred_proba: np.ndarray,
    region_column: str = "order_region"
) -> Dict[str, RegionalRiskSummary]:
    """
    Compute risk summary by region.
    
    Args:
        X_test: Test features with region column
        y_pred_proba: Predicted probabilities
        region_column: Name of region column
        
    Returns:
        Dictionary of RegionalRiskSummary by region
    """
    logger.info("Computing regional risk summary...")
    
    # Create analysis dataframe
    df = X_test.copy()
    df["risk_score"] = y_pred_proba
    
    # Categorize risk
    df["risk_level"] = pd.cut(
        df["risk_score"],
        bins=[0, 0.4, 0.7, 1.0],
        labels=["LOW", "MEDIUM", "HIGH"]
    )
    
    # Group by region
    regional_summaries = {}
    
    for region in df[region_column].unique():
        region_data = df[df[region_column] == region]
        
        summary = RegionalRiskSummary(
            region=region,
            average_risk_score=region_data["risk_score"].mean(),
            num_shipments=len(region_data),
            high_risk_count=(region_data["risk_level"] == "HIGH").sum(),
            medium_risk_count=(region_data["risk_level"] == "MEDIUM").sum(),
            low_risk_count=(region_data["risk_level"] == "LOW").sum(),
        )
        
        regional_summaries[region] = summary
        
        logger.debug(f"{region}: {summary.average_risk_score:.3f} risk, {len(region_data)} shipments")
    
    logger.info(f"Computed summaries for {len(regional_summaries)} regions")
    
    return regional_summaries


# ============================================================
# SHIPPING MODE ANALYTICS
# ============================================================

def compute_shipping_mode_risk_summary(
    X_test: pd.DataFrame,
    y_pred_proba: np.ndarray,
    mode_column: str = "shipping_mode"
) -> Dict[str, ShippingModeRiskSummary]:
    """
    Compute risk summary by shipping mode.
    
    Args:
        X_test: Test features with shipping mode column
        y_pred_proba: Predicted probabilities
        mode_column: Name of shipping mode column
        
    Returns:
        Dictionary of ShippingModeRiskSummary by mode
    """
    logger.info("Computing shipping mode risk summary...")
    
    df = X_test.copy()
    df["risk_score"] = y_pred_proba
    df["is_delayed"] = (y_pred_proba > 0.5).astype(int)
    
    mode_summaries = {}
    
    for mode in df[mode_column].unique():
        mode_data = df[df[mode_column] == mode]
        
        summary = ShippingModeRiskSummary(
            shipping_mode=mode,
            average_risk_score=mode_data["risk_score"].mean(),
            num_shipments=len(mode_data),
            reliability_rate=1.0 - mode_data["is_delayed"].mean(),
        )
        
        mode_summaries[mode] = summary
        
        logger.debug(f"{mode}: {summary.average_risk_score:.3f} risk, {summary.reliability_rate*100:.1f}% reliability")
    
    logger.info(f"Computed summaries for {len(mode_summaries)} shipping modes")
    
    return mode_summaries


# ============================================================
# CATEGORY ANALYTICS
# ============================================================

def compute_category_risk_summary(
    X_test: pd.DataFrame,
    y_pred_proba: np.ndarray,
    category_column: str = "category_name"
) -> Dict[str, CategoryRiskSummary]:
    """
    Compute risk summary by product category.
    
    Args:
        X_test: Test features with category column
        y_pred_proba: Predicted probabilities
        category_column: Name of category column
        
    Returns:
        Dictionary of CategoryRiskSummary by category
    """
    logger.info("Computing category risk summary...")
    
    df = X_test.copy()
    df["risk_score"] = y_pred_proba
    df["is_delayed"] = (y_pred_proba > 0.5).astype(int)
    
    category_summaries = {}
    
    for category in df[category_column].unique():
        category_data = df[df[category_column] == category]
        
        summary = CategoryRiskSummary(
            category=category,
            average_risk_score=category_data["risk_score"].mean(),
            num_shipments=len(category_data),
            delayed_count=category_data["is_delayed"].sum(),
        )
        
        category_summaries[category] = summary
        
        logger.debug(f"{category}: {summary.average_risk_score:.3f} risk, {summary.delayed_count} delayed")
    
    logger.info(f"Computed summaries for {len(category_summaries)} categories")
    
    return category_summaries


# ============================================================
# DASHBOARD SUMMARY
# ============================================================

def compute_dashboard_summary(
    X_test: pd.DataFrame,
    y_pred_proba: np.ndarray,
    regional_summaries: Dict[str, RegionalRiskSummary],
    mode_summaries: Dict[str, ShippingModeRiskSummary],
    category_summaries: Dict[str, CategoryRiskSummary],
) -> DashboardSummary:
    """
    Compute overall dashboard summary.
    
    Args:
        X_test: Test features
        y_pred_proba: Predicted probabilities
        regional_summaries: Regional risk summaries
        mode_summaries: Shipping mode summaries
        category_summaries: Category summaries
        
    Returns:
        DashboardSummary object
    """
    logger.info("Computing overall dashboard summary...")
    
    # Risk categorization
    high_risk = (y_pred_proba > 0.7).sum()
    medium_risk = ((y_pred_proba > 0.4) & (y_pred_proba <= 0.7)).sum()
    low_risk = (y_pred_proba <= 0.4).sum()
    
    # Most risky
    most_risky_region = max(regional_summaries.items(), key=lambda x: x[1].average_risk_score)[0]
    most_risky_mode = max(mode_summaries.items(), key=lambda x: x[1].average_risk_score)[0]
    most_risky_category = max(category_summaries.items(), key=lambda x: x[1].average_risk_score)[0]
    
    summary = DashboardSummary(
        total_shipments=len(X_test),
        high_risk_shipments=high_risk,
        medium_risk_shipments=medium_risk,
        low_risk_shipments=low_risk,
        average_delay_risk=float(y_pred_proba.mean()),
        most_risky_region=most_risky_region,
        most_risky_shipping_mode=most_risky_mode,
        most_risky_category=most_risky_category,
    )
    
    logger.info(f"Dashboard Summary: {high_risk} high-risk, {medium_risk} medium-risk, {low_risk} low-risk")
    logger.info(f"Riskiest: Region={most_risky_region}, Mode={most_risky_mode}, Category={most_risky_category}")
    
    return summary


# ============================================================
# CONVENIENCE FUNCTION
# ============================================================

def generate_all_analytics(
    X_test: pd.DataFrame,
    y_pred_proba: np.ndarray,
) -> Dict:
    """
    Generate all analytics for dashboard.
    
    Args:
        X_test: Test features
        y_pred_proba: Predicted probabilities
        
    Returns:
        Dictionary containing all analytics
    """
    logger.info("Generating comprehensive analytics...")
    
    # Compute all summaries
    regional = compute_regional_risk_summary(X_test, y_pred_proba)
    modes = compute_shipping_mode_risk_summary(X_test, y_pred_proba)
    categories = compute_category_risk_summary(X_test, y_pred_proba)
    dashboard = compute_dashboard_summary(X_test, y_pred_proba, regional, modes, categories)
    
    return {
        "dashboard_summary": dashboard.to_dict(),
        "regional_risk": {region: summary.to_dict() for region, summary in regional.items()},
        "shipping_mode_risk": {mode: summary.to_dict() for mode, summary in modes.items()},
        "category_risk": {category: summary.to_dict() for category, summary in categories.items()},
    }


if __name__ == "__main__":
    logger.info("Analytics module loaded successfully")
