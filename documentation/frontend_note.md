# Frontend Developer Guide

This guide lists the data available from the backend, endpoint contracts, response shapes, and dashboard visualizations that can be built.

## API Base URL

Local backend:

```text
http://127.0.0.1:8000
```

All product endpoints use `/api/*`.

## Available Endpoints

| Method | Endpoint | Use In UI |
|---|---|---|
| GET | `/health` | API availability check |
| POST | `/api/predict` | Shipment simulator / risk prediction |
| GET | `/api/analytics/home` | Dashboard landing page |
| GET | `/api/analytics/region` | Region dropdown and regional detail |
| GET | `/api/analytics/distribution` | Charts and ranked distributions |
| POST | `/api/explain/shipment` | Explanation modal/detail panel |
| GET | `/api/features/importance` | Feature importance chart |

Do not use old/non-API aliases such as `/predict`, `/analytics/home`, or `/explain/shipment`.

## Standard Response Envelope

Successful service responses:

```json
{
  "status": "success",
  "data": {},
  "metadata": {
    "timestamp": "2026-05-28T00:00:00+00:00",
    "latency_ms": 12.3
  }
}
```

FastAPI validation errors use HTTP `422`.

## Prediction

Endpoint:

```text
POST /api/predict
```

Request:

```json
{
  "region": "Western Europe",
  "shipping_mode": "Standard Class",
  "category": "Fishing",
  "quantity": 3,
  "days_for_shipment": 4,
  "sales": 250.0,
  "benefit_per_order": 0.0,
  "customer_segment": "Consumer",
  "market": "Europe",
  "order_month": 5,
  "order_dayofweek": 1,
  "is_weekend": 0
}
```

Required fields:

- `region`
- `shipping_mode`
- `category`
- `quantity`

Response data:

```json
{
  "risk_probability": 0.3564,
  "risk_level": "LOW",
  "risk_score": 36,
  "predicted_class": 0,
  "explanation": "Low risk of shipment delay (35.6%). Shipment appears on track.",
  "input_features": {}
}
```

Visualize as:

- Risk score gauge.
- LOW/MEDIUM/HIGH badge.
- Prediction result card.
- Human-readable explanation text.

## Home Analytics

Endpoint:

```text
GET /api/analytics/home
```

Response data sections:

- `dashboard_summary`
- `regional_risk`
- `shipping_mode_risk`
- `category_risk`

Useful dashboard fields:

- `total_shipments`
- `high_risk_shipments`
- `medium_risk_shipments`
- `low_risk_shipments`
- `delayed_shipments`
- `average_delay_risk`
- `delay_rate`
- `risk_distribution`
- `most_risky_region`
- `most_risky_shipping_mode`
- `most_risky_category`

Visualize as:

- KPI cards.
- Risk distribution pie/donut chart.
- Region ranking table/map.
- Shipping mode reliability bar chart.
- Category risk ranking.

## Regional Analytics

Endpoint:

```text
GET /api/analytics/region
GET /api/analytics/region?region=Western Europe
```

Without query param, returns available regions.

With `region`, response data includes:

- `summary`
- `shipping_mode_risk`
- `category_risk`

Visualize as:

- Region detail drawer/page.
- Region-specific mode breakdown.
- Region-specific category breakdown.

## Distribution Analytics

Endpoint:

```text
GET /api/analytics/distribution?dimension=risk
```

Supported dimensions:

- `risk`
- `region`
- `shipping_mode`
- `mode`
- `category`
- `market`
- `customer_segment`

Response data:

```json
{
  "dimension": "risk",
  "items": [
    {"label": "HIGH", "count": 100, "percentage": 10.0},
    {"label": "MEDIUM", "count": 300, "percentage": 30.0},
    {"label": "LOW", "count": 600, "percentage": 60.0}
  ]
}
```

Visualize as:

- Bar chart.
- Pie/donut chart.
- Ranked table.

## Shipment Explanation

Endpoint:

```text
POST /api/explain/shipment
```

Request:

```json
{
  "region": "Western Europe",
  "shipping_mode": "Standard Class",
  "category": "Fishing",
  "quantity": 3,
  "days_for_shipment": 4,
  "sales": 250.0,
  "risk_probability": 0.65,
  "top_n": 5
}
```

Response data:

```json
{
  "risk_probability": 0.65,
  "risk_level": "MEDIUM",
  "top_factors": [
    {"feature": "shipping_mode_risk", "contribution": -0.058}
  ],
  "dominant_driver": "shipping_mode_risk",
  "explanation": "Main driver: shipping_mode_risk (reduces delay risk). Explanation method: local_shap.",
  "method": "local_shap"
}
```

Visualize as:

- Factor contribution bars.
- Dominant driver text.
- Explanation modal.

Note: explanation is slower than analytics because it may use SHAP. Trigger it on user action, not on every dashboard load.

## Feature Importance

Endpoint:

```text
GET /api/features/importance
```

Visualize as:

- Horizontal feature importance bar chart.

## Frontend Integration Example

```javascript
const API_BASE_URL = "http://127.0.0.1:8000";

export async function predictShipment(payload) {
  const response = await fetch(`${API_BASE_URL}/api/predict`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(payload),
  });
  return response.json();
}

export async function getHomeAnalytics() {
  const response = await fetch(`${API_BASE_URL}/api/analytics/home`);
  return response.json();
}

export async function explainShipment(payload) {
  const response = await fetch(`${API_BASE_URL}/api/explain/shipment`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(payload),
  });
  return response.json();
}
```

