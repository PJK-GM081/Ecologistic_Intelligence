"""FastAPI application for Ecologistic Intelligence backend."""

from __future__ import annotations

from datetime import datetime, timezone
from time import perf_counter
from typing import Any, Dict, Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.services.analytics_service import AnalyticsService
from src.services.interpretation_service import InterpretationService
from src.services.prediction_service import PredictionService
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PredictRequest(BaseModel):
    """Shipment prediction request."""

    region: str
    shipping_mode: str
    category: str
    quantity: int = Field(..., ge=0)
    days_for_shipment: int = Field(1, ge=0)
    sales: float = 100.0
    benefit_per_order: float = 0.0
    customer_segment: str = "Unknown"
    market: str = "Unknown"
    order_month: Optional[int] = Field(None, ge=1, le=12)
    order_dayofweek: Optional[int] = Field(None, ge=0, le=6)
    is_weekend: Optional[int] = Field(None, ge=0, le=1)


class ExplainRequest(PredictRequest):
    """Explanation request for a shipment."""

    risk_probability: Optional[float] = Field(None, ge=0.0, le=1.0)
    risk_level: Optional[str] = None
    top_n: int = Field(5, ge=1, le=20)


app = FastAPI(
    title="Ecologistic Intelligence API",
    description="AI-assisted logistics delay risk intelligence backend",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


_prediction_service: Optional[PredictionService] = None
_analytics_service: Optional[AnalyticsService] = None
_interpretation_service: Optional[InterpretationService] = None


def _metadata(start: float, **extra: Any) -> Dict[str, Any]:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "latency_ms": round((perf_counter() - start) * 1000, 2),
        **extra,
    }


def _success(data: Any, start: float, **metadata: Any) -> Dict[str, Any]:
    return {"status": "success", "data": data, "metadata": _metadata(start, **metadata)}


def get_prediction_service() -> PredictionService:
    global _prediction_service
    if _prediction_service is None:
        _prediction_service = PredictionService()
    return _prediction_service


def get_analytics_service() -> AnalyticsService:
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = AnalyticsService()
    return _analytics_service


def get_interpretation_service() -> InterpretationService:
    global _interpretation_service
    if _interpretation_service is None:
        _interpretation_service = InterpretationService()
    return _interpretation_service


def _shipment_kwargs(request: PredictRequest) -> Dict[str, Any]:
    return {
        "region": request.region,
        "shipping_mode": request.shipping_mode,
        "category": request.category,
        "quantity": request.quantity,
        "days_for_shipment": request.days_for_shipment,
        "sales": request.sales,
        "benefit_per_order": request.benefit_per_order,
        "customer_segment": request.customer_segment,
        "market": request.market,
        "order_month": request.order_month,
        "order_dayofweek": request.order_dayofweek,
        "is_weekend": request.is_weekend,
    }


def _to_model_feature_frame(raw_frame: pd.DataFrame) -> pd.DataFrame:
    """Transform raw shipment features when preprocessing artifacts are available."""
    try:
        prediction_service = get_prediction_service()
        transformed = prediction_service.transform_for_model(raw_frame)
        columns = prediction_service.feature_names
        if len(columns) != transformed.shape[1]:
            columns = [f"feature_{index}" for index in range(transformed.shape[1])]
        return pd.DataFrame(transformed, columns=columns)
    except Exception as exc:
        logger.warning("Could not transform explanation features; using raw frame: %s", exc)
        return raw_frame


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    return {
        "status": "ok",
        "service": "Ecologistic Intelligence API",
        "version": "1.1.0",
    }


@app.post("/api/predict")
async def predict_shipment(request: PredictRequest) -> Dict[str, Any]:
    start = perf_counter()
    try:
        prediction = get_prediction_service().predict(**_shipment_kwargs(request))
        return _success(prediction.to_dict(), start, model_loaded=True)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Prediction failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Prediction failed: {exc}") from exc


@app.get("/api/analytics/home")
async def get_home_dashboard(force_refresh: bool = False) -> Dict[str, Any]:
    start = perf_counter()
    try:
        data = get_analytics_service().get_home_summary(force_refresh=force_refresh)
        metadata = data.pop("metadata", {})
        return _success(data, start, **metadata)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Analytics home failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analytics failed: {exc}") from exc


@app.get("/api/analytics/region")
async def get_region_summary(region: Optional[str] = Query(default=None)) -> Dict[str, Any]:
    start = perf_counter()
    try:
        data = get_analytics_service().get_region_summary(region=region)
        return _success(data, start)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Region analytics failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Region analytics failed: {exc}") from exc


@app.get("/api/analytics/distribution")
async def get_distribution_summary(dimension: str = "risk") -> Dict[str, Any]:
    start = perf_counter()
    try:
        data = get_analytics_service().get_distribution_summary(dimension=dimension)
        return _success(data, start)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Distribution analytics failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Distribution analytics failed: {exc}") from exc


@app.post("/api/explain/shipment")
async def explain_shipment(request: ExplainRequest) -> Dict[str, Any]:
    start = perf_counter()
    try:
        shipment_kwargs = _shipment_kwargs(request)
        risk_probability = request.risk_probability

        feature_frame: pd.DataFrame
        if risk_probability is None:
            prediction_service = get_prediction_service()
            prediction = prediction_service.predict(**shipment_kwargs)
            risk_probability = prediction.risk_probability
            risk_level_value = prediction.risk_level
            feature_frame = prediction_service.build_feature_frame(**shipment_kwargs)
        else:
            risk_level_value = request.risk_level or (
                "HIGH" if risk_probability > 0.7 else "MEDIUM" if risk_probability > 0.4 else "LOW"
            )
            try:
                feature_frame = get_prediction_service().build_feature_frame(**shipment_kwargs)
            except FileNotFoundError:
                feature_frame = pd.DataFrame(
                    [
                        {
                            "order_region": request.region,
                            "shipping_mode": request.shipping_mode,
                            "category_name": request.category,
                            "order_item_quantity": request.quantity,
                            "days_for_shipment_(scheduled)": request.days_for_shipment,
                            "sales": request.sales,
                            "benefit_per_order": request.benefit_per_order,
                            "customer_segment": request.customer_segment,
                            "market": request.market,
                        }
                    ]
                )

        feature_frame = _to_model_feature_frame(feature_frame)
        explanation = get_interpretation_service().explain_prediction(
            X_single=feature_frame,
            risk_probability=float(risk_probability),
            risk_level=risk_level_value,
            top_n=request.top_n,
        )
        return _success(
            explanation.to_dict(),
            start,
            warning="SHAP is sampled and optional; service falls back to lightweight explanation if unavailable.",
        )
    except Exception as exc:
        logger.error("Explanation failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Explanation failed: {exc}") from exc


@app.get("/api/features/importance")
async def get_feature_importance() -> Dict[str, Any]:
    start = perf_counter()
    try:
        analytics = get_analytics_service()
        raw = analytics._load_operational_data()  # Shared bounded operational source, no SHAP by analytics.
        sample = raw.drop(columns=[column for column in ("delay_flag", "risk_score") if column in raw.columns])
        data = get_interpretation_service().get_feature_importance(sample, top_n=15)
        return _success(data, start)
    except Exception as exc:
        logger.error("Feature importance failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Feature importance failed: {exc}") from exc


@app.on_event("startup")
async def startup_event() -> None:
    logger.info("API startup")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    logger.info("API shutdown")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.api.main:app", host="127.0.0.1", port=8000, reload=True)
