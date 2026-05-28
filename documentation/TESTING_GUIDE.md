# Depedencies - Ecologistic Intelligence

## 🎯 Quick Test (2 Minutes)

Dependencies Check?

```bash
# 1. Verify setup
python verify_setup.py

# 2. Train models (if needed)
python main.py --mode full

# 3. Start API
python run_api.py

# 4. Test health endpoint (in another terminal)
curl http://localhost:8000/health

# Expected: {"status": "healthy", ...}

```
## 📋 Complete Testing Checklist

### Phase 1: Setup Verification
```bash
# Check Python version
python --version
# Expected: Python 3.8 or higher

# Check packages installed
python verify_setup.py
# Expected: All ✅ checks pass

# Check .env file
cat .env
# Expected: API_HOST=127.0.0.1, API_PORT=8000
```

### Phase 2: Model Training
```bash
# Train models (5-10 minutes)
python main.py --mode full

# Expected output:
# ✓ Loading data...
# ✓ Preprocessing...
# ✓ Training model...
# ✓ Model saved to models/
# ✓ Preprocessor saved to artifacts/

# Verify files created
ls models/
ls artifacts/

# Should have: model.pkl, preprocessor.pkl, metadata.json
```

### Phase 3: API Server
```bash
# Start API
python run_api.py

# Expected:
# INFO:     Started server process
# INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Phase 4: Endpoint Testing
Keep terminal running and test in another terminal:

```bash
# Test 1: Health Check
curl http://localhost:8000/health

# Expected: {"status": "healthy", "service": "...", "version": "1.1.0"}

# Test 2: Analytics
curl http://localhost:8000/api/analytics

# Expected: {"success": true, "data": {...}, "latency_ms": ...}

# Test 3: Prediction
curl -X POST http://localhost:8000/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "shipment_id": "TEST001",
    "origin": "Jakarta",
    "destination": "Surabaya",
    "departure_date": "2026-05-28",
    "estimated_delivery": "2026-05-30",
    "shipping_mode": "ground",
    "product_category": "electronics",
    "product_weight": 2.5,
    "product_importance": "high",
    "customer_id": "CUST001"
  }'

# Expected: {"success": true, "data": {"risk_level": "LOW", ...}, "latency_ms": ...}
```

---

## 🧪 Detailed API Testing

### Using cURL (Command Line)

#### Test 1: Health Status
```bash
curl -v http://localhost:8000/health
```

**Verify**:
- Status Code: `200`
- Response has: `status`, `service`, `version`

---

#### Test 2: Predict Single Shipment
```bash
curl -X POST http://localhost:8000/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "shipment_id": "SHIP_TEST_001",
    "origin": "Jakarta",
    "destination": "Bandung",
    "departure_date": "2026-05-28",
    "estimated_delivery": "2026-05-29",
    "shipping_mode": "ground",
    "product_category": "electronics",
    "product_weight": 1.5,
    "product_importance": "high",
    "customer_id": "CUST_ABC"
  }'
```

**Verify**:
- Status Code: `200`
- Response has: `success: true`, `data.risk_level` (LOW/MEDIUM/HIGH), `data.late_delivery_risk_probability` (0-1)
- `latency_ms` shows response time

---

#### Test 3: Dashboard Analytics
```bash
curl http://localhost:8000/api/analytics
```

**Verify**:
- Returns: `total_shipments`, `high_risk_count`, `average_risk_probability`
- Latency < 50ms (should be fast)

---

#### Test 4: Regional Analytics
```bash
# List all regions
curl "http://localhost:8000/api/analytics/region"

# Specific region
curl "http://localhost:8000/api/analytics/region?region=Jakarta"
```

**Verify**:
- Returns regional breakdown
- Filtering works correctly

---

#### Test 5: Risk Distribution
```bash
curl "http://localhost:8000/api/analytics/distribution?dimension=risk"
```

**Verify**:
- Returns: `LOW`, `MEDIUM`, `HIGH` counts
- Percentages add up to 100%

---

#### Test 6: Feature Importance
```bash
curl http://localhost:8000/api/features/importance
```

**Verify**:
- Returns list of features with importance scores
- Scores sum to ~1.0

---

#### Test 7: SHAP Explanation
```bash
curl -X POST http://localhost:8000/api/explain \
  -H "Content-Type: application/json" \
  -d '{
    "shipment_id": "SHIP_EXPLAIN_001",
    "origin": "Jakarta",
    "destination": "Yogyakarta",
    "departure_date": "2026-05-28",
    "estimated_delivery": "2026-05-31",
    "shipping_mode": "ground",
    "product_category": "fragile_goods",
    "product_weight": 3.0,
    "product_importance": "high",
    "customer_id": "CUST_XYZ"
  }'
```

**Verify**:
- Returns: `base_value`, `predicted_probability`, `feature_contributions`
- Explains why model made prediction
- Takes longer (~200-300ms due to SHAP)

---

### Using Python
```python
import requests
import json

BASE_URL = "http://localhost:8000"

# Test health
print("=== Testing Health ===")
response = requests.get(f"{BASE_URL}/health")
print(f"Status: {response.status_code}")
print(json.dumps(response.json(), indent=2))

# Test prediction
print("\n=== Testing Prediction ===")
payload = {
    "shipment_id": "SHIP_001",
    "origin": "Jakarta",
    "destination": "Surabaya",
    "departure_date": "2026-05-28",
    "estimated_delivery": "2026-05-30",
    "shipping_mode": "ground",
    "product_category": "electronics",
    "product_weight": 2.5,
    "product_importance": "high",
    "customer_id": "CUST_001"
}

response = requests.post(
    f"{BASE_URL}/api/predict",
    json=payload
)
print(f"Status: {response.status_code}")
print(json.dumps(response.json(), indent=2))

# Test analytics
print("\n=== Testing Analytics ===")
response = requests.get(f"{BASE_URL}/api/analytics")
print(f"Status: {response.status_code}")
data = response.json()
if data['success']:
    print(f"Total shipments: {data['data'].get('total_shipments')}")
    print(f"High risk: {data['data'].get('high_risk_percentage')}%")
    print(f"On-time rate: {data['data'].get('on_time_delivery_rate')}%")

# Test regional
print("\n=== Testing Regional Analytics ===")
response = requests.get(f"{BASE_URL}/api/analytics/region?region=Jakarta")
print(f"Status: {response.status_code}")
print(json.dumps(response.json(), indent=2))

# Test feature importance
print("\n=== Testing Feature Importance ===")
response = requests.get(f"{BASE_URL}/api/features/importance")
print(f"Status: {response.status_code}")
data = response.json()
if data['success']:
    for feature in data['data']['features'][:5]:
        print(f"  {feature['name']}: {feature['importance']:.3f}")

# Test explanation
print("\n=== Testing SHAP Explanation ===")
response = requests.post(
    f"{BASE_URL}/api/explain",
    json=payload
)
print(f"Status: {response.status_code}")
data = response.json()
if data['success']:
    print(f"Base value: {data['data']['base_value']:.3f}")
    print(f"Prediction: {data['data']['predicted_probability']:.3f}")
    print(f"Explanation: {data['data']['prediction_explanation']}")
```

**Run it**:
```bash
python test_api.py
```

---

## 🔍 Error Testing (What Happens When Something Breaks?)

### Test 1: Invalid Shipment Data
```bash
curl -X POST http://localhost:8000/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "shipment_id": "SHIP_BAD",
    "origin": "Jakarta"
    # Missing other required fields
  }'
```

**Expected**: Status `422` with validation error

---

### Test 2: Wrong Data Types
```bash
curl -X POST http://localhost:8000/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "shipment_id": "SHIP_WRONG",
    "origin": "Jakarta",
    "destination": "Surabaya",
    "departure_date": "2026-05-28",
    "estimated_delivery": "2026-05-30",
    "shipping_mode": "ground",
    "product_category": "electronics",
    "product_weight": "2.5",  # Should be number, not string
    "product_importance": "high",
    "customer_id": "CUST_001"
  }'
```

**Expected**: Status `422` with type error

---

### Test 3: Invalid Date Format
```bash
curl -X POST http://localhost:8000/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "shipment_id": "SHIP_DATE",
    "origin": "Jakarta",
    "destination": "Surabaya",
    "departure_date": "28-05-2026",  # Wrong format
    "estimated_delivery": "2026-05-30",
    "shipping_mode": "ground",
    "product_category": "electronics",
    "product_weight": 2.5,
    "product_importance": "high",
    "customer_id": "CUST_001"
  }'
```

**Expected**: Status `422` with date format error

---

### Test 4: Models Not Loaded
```bash
# Stop API, delete models
rm models/model.pkl

# Restart API - it will fail to load models
python run_api.py

# Test prediction
curl -X POST http://localhost:8000/api/predict ...
```

**Expected**: Status `503` - Service Unavailable

**Fix**: 
```bash
python main.py --mode full  # Retrain models
```

---

## 📊 Performance Testing

### Test Response Times

```python
import requests
import time

BASE_URL = "http://localhost:8000"

# Test endpoints and measure time
endpoints = [
    ("GET", "/health", None),
    ("GET", "/api/analytics", None),
    ("GET", "/api/features/importance", None),
    ("POST", "/api/predict", {
        "shipment_id": "PERF_TEST_001",
        "origin": "Jakarta",
        "destination": "Surabaya",
        "departure_date": "2026-05-28",
        "estimated_delivery": "2026-05-30",
        "shipping_mode": "ground",
        "product_category": "electronics",
        "product_weight": 2.5,
        "product_importance": "high",
        "customer_id": "CUST_001"
    }),
]

print("Performance Test Results:")
print("-" * 60)
print(f"{'Endpoint':<40} {'Time (ms)':<15}")
print("-" * 60)

for method, endpoint, data in endpoints:
    times = []
    for _ in range(5):  # Run 5 times
        start = time.time()        if method == "GET":
            requests.get(f"{BASE_URL}{endpoint}")
        else:
            requests.post(f"{BASE_URL}{endpoint}", json=data)
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
    
    avg_time = sum(times) / len(times)
    print(f"{endpoint:<40} {avg_time:>10.2f} ms")

print("-" * 60)
```

**Expected Response Times**:
- `/health`: < 10ms
- `/api/analytics`: < 50ms
- `/api/features/importance`: < 200ms
- `/api/predict`: 50-100ms
- `/api/explain`: 200-500ms

---

## 🔄 Testing Model Training Pipeline

### Test 1: Preprocess Only
```bash
python main.py --mode preprocess

# Check output
ls data/processed/
# Should have: X_train.csv, X_test.csv, y_train.csv, y_test.csv
```

---

### Test 2: Train Only (Uses Existing Preprocessed Data)
```bash
python main.py --mode train

# Check output
ls models/
# Should have: model.pkl

# Check logs
cat logs/training.log
```

---

### Test 3: Full Pipeline
```bash
python main.py --mode full

# Takes 5-10 minutes
# Generates: data/processed/, models/, artifacts/
```

---

## 🧬 Integration Testing

### Test Complete Workflow
```python
import requests
import json

BASE_URL = "http://localhost:8000"

print("🧪 Integration Test: Complete Workflow")
print("=" * 60)

# Step 1: Health check
print("\n1️⃣ Health Check")
response = requests.get(f"{BASE_URL}/health")
assert response.status_code == 200
assert response.json()['status'] == 'healthy'
print("✅ API is healthy")

# Step 2: Get dashboard
print("\n2️⃣ Get Dashboard")
response = requests.get(f"{BASE_URL}/api/analytics")
assert response.status_code == 200
assert response.json()['success'] == True
dashboard = response.json()['data']
print(f"✅ Dashboard loaded: {dashboard['total_shipments']} shipments")

# Step 3: Get regional analytics
print("\n3️⃣ Get Regional Analytics")
response = requests.get(f"{BASE_URL}/api/analytics/region?region=Jakarta")
assert response.status_code == 200
print("✅ Regional analytics loaded")

# Step 4: Get feature importance
print("\n4️⃣ Get Feature Importance")
response = requests.get(f"{BASE_URL}/api/features/importance")
assert response.status_code == 200
features = response.json()['data']['features']
print(f"✅ Feature importance loaded: {len(features)} features")

# Step 5: Make prediction
print("\n5️⃣ Make Prediction")
payload = {
    "shipment_id": "INT_TEST_001",
    "origin": "Jakarta",
    "destination": "Bandung",
    "departure_date": "2026-05-28",
    "estimated_delivery": "2026-05-29",
    "shipping_mode": "ground",
    "product_category": "electronics",
    "product_weight": 2.5,
    "product_importance": "high",
    "customer_id": "CUST_INT_TEST"
}
response = requests.post(f"{BASE_URL}/api/predict", json=payload)
assert response.status_code == 200
assert response.json()['success'] == True
prediction = response.json()['data']
print(f"✅ Prediction made: {prediction['risk_level']} (prob: {prediction['late_delivery_risk_probability']:.2%})")

# Step 6: Get explanation
print("\n6️⃣ Get SHAP Explanation")
response = requests.post(f"{BASE_URL}/api/explain", json=payload)
assert response.status_code == 200
assert response.json()['success'] == True
explanation = response.json()['data']
print(f"✅ Explanation generated: {explanation['prediction_explanation']}")

print("\n" + "=" * 60)
print("🎉 All integration tests passed!")
```

**Run it**:
```bash
python integration_test.py
```

---

## 📋 Test Results Checklist

### Setup Tests
- [ ] Python 3.8+ installed
- [ ] verify_setup.py passes all checks
- [ ] .env file configured correctly

### Training Tests
- [ ] main.py --mode full completes successfully
- [ ] models/ directory has model.pkl
- [ ] artifacts/ directory has encoder files
- [ ] data/processed/ has train/test splits

### API Server Tests
- [ ] python run_api.py starts without errors
- [ ] Server listens on http://localhost:8000
- [ ] No error messages in startup logs

### Endpoint Tests
- [ ] GET /health returns 200 with healthy status
- [ ] POST /api/predict returns 200 with risk prediction
- [ ] GET /api/analytics returns 200 with dashboard data
- [ ] GET /api/analytics/region returns regional breakdown
- [ ] GET /api/analytics/distribution returns risk distribution
- [ ] GET /api/features/importance returns feature rankings
- [ ] POST /api/explain returns SHAP explanation
- [ ] All responses have "success": true

### Error Handling Tests
- [ ] Invalid input returns 422
- [ ] Missing models returns 503
- [ ] Malformed JSON returns 422
- [ ] Wrong field types return 422

### Performance Tests
- [ ] /health responds in < 10ms
- [ ] /api/analytics responds in < 50ms
- [ ] /api/predict responds in 50-100ms
- [ ] /api/explain responds in 200-500ms

---

## 🚀 Quick Test Scripts

### Create `test_all.py`
```bash
# Run all tests at once
python test_all.py
```

Content:
```python
#!/usr/bin/env python
"""Run all tests"""
import subprocess
import sys

tests = [
    ("Setup", "python verify_setup.py"),
    ("API Health", "curl http://localhost:8000/health"),
    ("Analytics", "curl http://localhost:8000/api/analytics"),
    ("Prediction", "curl -X POST http://localhost:8000/api/predict ..."),
]

passed = 0
failed = 0

for name, cmd in tests:
    print(f"\n🧪 Testing: {name}")
    result = subprocess.run(cmd, shell=True, capture_output=True)
    if result.returncode == 0:
        print(f"✅ {name} passed")
        passed += 1
    else:
        print(f"❌ {name} failed")
        failed += 1

print(f"\n{'=' * 40}")
print(f"Results: {passed} passed, {failed} failed")
sys.exit(0 if failed == 0 else 1)
```

---

## 🔧 Troubleshooting During Tests

### Problem: Port Already in Use
```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

### Problem: Models Missing
```bash
# Retrain
python main.py --mode full

# Verify
ls models/model.pkl
```

### Problem: API Won't Start
```bash
# Check logs
cat logs/api.log

# Check Python version
python --version

# Check packages
python verify_setup.py
```

### Problem: Predictions Taking Too Long
```bash
# Check logs for errors
tail -f logs/api.log

# Monitor resources
# Windows: Task Manager
# Linux/Mac: top, htop
```

---

## ✅ Final Verification

After testing everything:

```bash
# 1. All checks pass
python verify_setup.py          # ✅

# 2. Models trained
ls models/model.pkl             # ✅

# 3. API starts
python run_api.py &             # ✅

# 4. All endpoints work
curl http://localhost:8000/health  # ✅
curl -X POST http://localhost:8000/api/predict ... # ✅
curl http://localhost:8000/api/analytics # ✅

# 5. Performance acceptable
# Response times within expected ranges # ✅
```

If all ✅, you're **ready for production!**

---

**Last Updated**: May 28, 2026  
**Status**: ✅ All Tests Documented  
**Version**: 1.1.0
