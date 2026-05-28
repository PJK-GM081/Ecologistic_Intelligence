# EcoLogistic Intelligence

EcoLogistic Intelligence adalah sistem AI-assisted logistics intelligence yang berfokus pada:

* shipment delay risk prediction,
* operational logistics analytics,
* explainable AI (SHAP),
* dan dashboard-ready logistics monitoring.

Project ini membangun pipeline machine learning end-to-end untuk membantu:

* monitoring risiko keterlambatan pengiriman,
* analisis distribusi logistik,
* interpretasi prediksi model,
* dan integrasi backend/frontend berbasis API.

---

# Project Goals

Sistem ini dirancang untuk:

1. Memprediksi risiko keterlambatan pengiriman
2. Menyediakan analytics operasional untuk dashboard
3. Menyediakan explainability menggunakan SHAP
4. Menyediakan service/API yang dapat dikonsumsi backend dan frontend

---

# System Architecture

```text
Raw Data
    ↓
Preprocessing Pipeline
    ↓
Training Pipeline
    ↓
Model Artifacts
    ↓
Service Layer
    ├── Prediction Service
    ├── Analytics Service
    └── Interpretation Service
    ↓
API Layer
    ↓
Frontend Dashboard
```

---

# Current Architecture Scope

| Layer         | Responsibility                       |
| ------------- | ------------------------------------ |
| preprocessing | data cleaning & feature engineering  |
| training      | model training & artifact generation |
| services      | ML logic & analytics                 |
| api           | expose backend services              |
---

# MVP

## Prediction Service

Purpose:

* shipment delay risk prediction
* shipment simulation

Responsibilities:

* load trained model
* inference preprocessing
* generate risk probability
* generate prediction outputs

---

## Analytics Service

Purpose:

* operational dashboard analytics

Responsibilities:

* region aggregation
* shipment distribution
* dashboard summaries
* operational monitoring

Important:
Analytics menggunakan:

* aggregated operational data
* precomputed summaries

Analytics TIDAK bergantung pada:

* expensive SHAP recomputation
* full realtime inference

---

## Interpretation Service

Purpose:

* explainability layer

Responsibilities:

* SHAP explanation
* feature contribution analysis
* local prediction explanation

Important:

* global SHAP menggunakan sampled/offline strategy
* runtime explanation hanya untuk lightweight/local explanation
* full dataset SHAP computation dihindari untuk menjaga runtime stability

---

# Project Structure

```text
src/
├── preprocessing/
├── training/
├── services/
│   ├── prediction_service.py
│   ├── analytics_service.py
│   └── interpretation_service.py
├── api/
│   ├── main.py
│   ├── prediction.py
│   ├── analytics.py
│   └── interpretation.py
└── utils/

artifacts/
├── models/
├── encoders/
├── transformers/
└── metadata/

data/
├── raw/
└── processed/
```

---

# Runtime Lifecycle

## 

## Offline Pipeline

Digunakan untuk:

* preprocessing dataset
* feature engineering
* training model
* artifact generation

Generated result:
`path folder = D:\Frans\Dicoding\Pijak\repo\Ecologistic_Intelligence\artifacts`
* trained model
* preprocessing artifacts
* metadata
* encoders/transformers

---

## Online API Runtime

Digunakan untuk:

* prediction API
* analytics API
* interpretation API

# Available API Endpoints

| Endpoint                      | Purpose                  |
| ----------------------------- | ------------------------ |
| POST `/predict`               | shipment risk prediction |
| GET `/analytics/home`         | dashboard summary        |
| GET `/analytics/region`       | regional aggregation     |
| GET `/analytics/distribution` | shipment distribution    |
| POST `/explain/shipment`      | SHAP explanation         |

---

# Frontend Integration Notes

Frontend fokus pada:

* dashboard rendering,
* charts,
* maps,
* tables,
* cards,
* dan interaction layer.

---

# Backend Integration Notes

Backend/API layer bertugas:

* menerima request frontend,
* memanggil backend services,
* validasi request,
* dan mengembalikan JSON response.

Business logic utama berada di:

* prediction_service.py
* analytics_service.py
* interpretation_service.py

---

# Explainability Strategy

Project menggunakan pendekatan SHAP dengan strategi:

| SHAP Type     | Strategy            |
| ------------- | ------------------- |
| Global SHAP   | sampled/offline     |
| Local SHAP    | lightweight runtime |
| Regional SHAP | sampled aggregation |

---

# Current Project Status

Current phase:
Prototype-Level Modular AI Analytics Platform

Current focus:

* service stabilization
* API integration
* analytics refinement
* frontend/backend collaboration
* runtime validation

Not yet focused on:

* enterprise deployment
* distributed infrastructure
* advanced MLOps
* large-scale production scaling
