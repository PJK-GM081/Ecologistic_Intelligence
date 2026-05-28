"""Interpretation module for SHAP-based explainability."""

from src.interpretation.explainer import (
    ShipmentExplanation,
    RegionalRiskAnalysis,
    ShapExplainer,
    explain_prediction,
    get_regional_risk_analysis,
)

__all__ = [
    "ShipmentExplanation",
    "RegionalRiskAnalysis",
    "ShapExplainer",
    "explain_prediction",
    "get_regional_risk_analysis",
]
