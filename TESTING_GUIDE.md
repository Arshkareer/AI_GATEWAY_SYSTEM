# Testing Guide

Comprehensive guide for testing the AI Gateway Monitoring Platform.

## Table of Contents

1. [Test Environment Setup](#test-environment-setup)
2. [Manual Testing](#manual-testing)
3. [API Testing](#api-testing)
4. [Integration Testing](#integration-testing)
5. [Load Testing](#load-testing)
6. [Security Testing](#security-testing)

---

## Test Environment Setup

### 1. Start Test Environment

```bash
# Use development docker-compose
docker-compose up -d

# Or start services individually
cd backend && uvicorn app.main:app --reload &
cd frontend && npm start &
```

### 2. Create Test Data

```bash
# Create test users
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "Test123!@#",
    "full_name": "Test User"
  }'

# Create test department
curl -X POST http://localhost:8000/api/v1/departments \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Department",
    "monthly_budget": 1000.00
  }'
```

---

## Manual Testing

### 1. Authentication Flow

**Test Cases**:
- [ ] User registration with valid data
- [ ] User registration with invalid email
- [ ] User registration with weak password
- [ ] Login with valid credentials
- [ ] Login with invalid credentials
- [ ] Token refresh
- [ ] Logout

**Steps**:
1. Open http://localhost:3000
2. Click "Sign Up"
3. Fill form with test data
4. Verify email validation
5. Submit and check for success
6. Login with credentials
7. Verify dashboard access

### 2. AI Gateway Testing

**Test Cases**:
- [ ] Send request to OpenAI
- [ ] Send request to Anthropic
- [ ] Send request to Google AI
- [ ] Test with invalid API key
- [ ] Test with rate limiting
- [ ] Test streaming responses
- [ ] Test cost calculation
- [ ] Test token counting

**Example Request**:
```bash
curl -X POST http://localhost:8000/api/v1/gateway/chat \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain quantum computing in simple terms",
    "provider": "openai",
    "model": "gpt-3.5-turbo",
    "max_tokens": 100
  }'
```

### 3. Analytics Testing

**Test Cases**:
- [ ] View dashboard metrics
- [ ] Check cost calculations
- [ ] Verify request counts
- [ ] Test date range filtering
- [ ] Export analytics data

**Steps**:
1. Navigate to Analytics page
2. Select date range
3. Verify metrics display
4. Check charts render correctly
5. Test export functionality

### 4. AI Insights Testing

**Anomaly Detection**:
```bash
# Get anomalies
curl http://localhost:8000/api/v1/ai-insights/anomalies \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Cost Prediction**:
```bash
# Get cost predictions
curl "http://localhost:8000/api/v1/ai-insights/cost-prediction?days_ahead=30" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Quality Scoring**:
```bash
# Compare models
curl "http://localhost:8000/api/v1/ai-insights/quality/compare-models?model_a=gpt-4&model_b=gpt-3.5-turbo" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Smart Routing**:
```bash
# Get routing recommendation
curl -X POST "http://localhost:8000/api/v1/ai-insights/routing/recommend?prompt=Write%20a%20poem&strategy=balanced" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Safety Monitoring**:
```bash
# Check content safety
curl -X POST "http://localhost:8000/api/v1/ai-insights/safety/check?prompt=My%20email%20is%20test@example.com" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 5. Notification Testing

**Email Test**:
```bash
# Trigger test email
curl -X POST http://localhost:8000/api/v1/test/send-email \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d "email=test@example.com"
```

**Webhook Test**:
```bash
# Trigger test webhook
curl -X POST http://localhost:8000/api/v1/test/send-webhook \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 6. Department Management Testing

**Test Cases**:
- [ ] Create department
- [ ] Update department budget
- [ ] Assign users to department
- [ ] Check budget status
- [ ] Trigger budget alerts
- [ ] View department analytics

---

## API Testing

### Using Postman

1. Import API collection (create from OpenAPI spec):
```bash
# Get OpenAPI spec
curl http://localhost:8000/api/v1/openapi.json > openapi.json
```

2. Import into Postman:
   - File → Import → openapi.json
   - Set environment variables (baseUrl, token)

### Using pytest (Recommended)

Create `backend/tests/test_api.py`:

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_register_user():
    response = client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "Test123!@#",
        "full_name": "Test User"
    })
    assert response.status_code == 201

def test_login():
    response = client.post("/api/v1/auth/login", data={
        "username": "testuser",
        "password": "Test123!@#"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_protected_endpoint():
    # Login first
    login_response = client.post("/api/v1/auth/login", data={
        "username": "testuser",
        "password": "Test123!@#"
    })
    token = login_response.json()["access_token"]
    
    # Access protected endpoint
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
```

Run tests:
```bash
cd backend
pytest tests/ -v
```

---

## Integration Testing

### Database Integration

```python
def test_user_creation_db():
    from app.config.database import SessionLocal
    from app.services.auth_service import auth_service
    
    db = SessionLocal()
    user = auth_service.create_user(
        db=db,
        username="testuser",
        email="test@example.com",
        password="password123",
        full_name="Test User"
    )
    assert user.id is not None
    assert user.username == "testuser"
```

### Redis Integration

```python
def test_redis_caching():
    from app.config.redis import redis_client
    
    # Set value
    redis_client.set("test_key", "test_value")
    
    # Get value
    value = redis_client.get("test_key")
    assert value == "test_value"
```

### LLM Provider Integration

```python
def test_openai_integration():
    from app.integrations.openai_client import OpenAIClient
    
    client = OpenAIClient()
    response = client.chat_completion(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Say hello"}]
    )
    assert response.content is not None
```

---

## Load Testing

### Using Apache Bench

```bash
# Test health endpoint
ab -n 1000 -c 10 http://localhost:8000/health

# Test API endpoint (with auth)
ab -n 100 -c 5 -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/users/me
```

### Using Locust

Create `locustfile.py`:

```python
from locust import HttpUser, task, between

class AIGatewayUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # Login
        response = self.client.post("/api/v1/auth/login", data={
            "username": "testuser",
            "password": "Test123!@#"
        })
        self.token = response.json()["access_token"]
    
    @task(3)
    def get_dashboard(self):
        self.client.get(
            "/api/v1/analytics/dashboard",
            headers={"Authorization": f"Bearer {self.token}"}
        )
    
    @task(1)
    def send_ai_request(self):
        self.client.post(
            "/api/v1/gateway/chat",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "prompt": "Hello",
                "provider": "openai",
                "model": "gpt-3.5-turbo"
            }
        )
```

Run load test:
```bash
locust -f locustfile.py --host=http://localhost:8000
```

Access UI: http://localhost:8089

---

## Security Testing

### 1. Authentication Security

**Test Cases**:
- [ ] SQL injection in login
- [ ] XSS in user inputs
- [ ] CSRF protection
- [ ] JWT token expiration
- [ ] Password strength enforcement
- [ ] Rate limiting on login

**SQL Injection Test**:
```bash
# Try SQL injection in login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=admin' OR '1'='1&password=anything"
```

**Expected**: Should fail, not bypass authentication

### 2. Authorization Testing

**Test Cases**:
- [ ] Access admin endpoints as regular user
- [ ] Access other users' data
- [ ] Modify without permission
- [ ] Privilege escalation attempts

**Example**:
```bash
# Try to access admin endpoint as regular user
curl http://localhost:8000/api/v1/admin/users \
  -H "Authorization: Bearer REGULAR_USER_TOKEN"
```

**Expected**: 403 Forbidden

### 3. Input Validation

**Test Cases**:
- [ ] Invalid email formats
- [ ] Extremely long inputs
- [ ] Special characters
- [ ] Unicode characters
- [ ] Null bytes

### 4. Rate Limiting

```bash
# Send 100 requests quickly
for i in {1..100}; do
  curl http://localhost:8000/api/v1/auth/login \
    -d "username=test&password=test" &
done
```

**Expected**: Should get rate limit errors after threshold

### 5. PII Detection

```bash
# Test PII detection
curl -X POST "http://localhost:8000/api/v1/ai-insights/safety/detect-pii" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d "text=My email is john@example.com and my SSN is 123-45-6789"
```

**Expected**: Should detect email and SSN

---

## Test Checklist

### Pre-Deployment Testing

#### Functionality
- [ ] All API endpoints respond correctly
- [ ] Authentication and authorization work
- [ ] AI gateway processes requests
- [ ] Analytics display correctly
- [ ] AI insights generate results
- [ ] Notifications send successfully

#### Performance
- [ ] Response times <200ms for simple endpoints
- [ ] Database queries optimized
- [ ] No memory leaks
- [ ] Handles concurrent requests

#### Security
- [ ] No SQL injection vulnerabilities
- [ ] No XSS vulnerabilities
- [ ] No CSRF vulnerabilities
- [ ] PII properly redacted
- [ ] Passwords hashed
- [ ] Tokens expire correctly

#### Integration
- [ ] Database operations work
- [ ] Redis caching works
- [ ] LLM providers respond
- [ ] Email delivery works
- [ ] Webhooks deliver

#### UI/UX
- [ ] All pages load
- [ ] Forms validate
- [ ] Charts render
- [ ] Mobile responsive
- [ ] No console errors

---

## Automated Testing Script

Create `run_tests.sh`:

```bash
#!/bin/bash

echo "=== Running AI Gateway Tests ==="

# Start services
echo "Starting services..."
docker-compose up -d
sleep 10

# Health checks
echo "Checking health endpoints..."
curl -f http://localhost:8000/health || exit 1

# Run backend tests
echo "Running backend tests..."
cd backend
pytest tests/ -v || exit 1
cd ..

# Run frontend tests
echo "Running frontend tests..."
cd frontend
npm test -- --watchAll=false || exit 1
cd ..

# API integration tests
echo "Running API integration tests..."
pytest integration_tests/ -v || exit 1

# Load tests
echo "Running load tests..."
ab -n 100 -c 10 http://localhost:8000/health || exit 1

echo "=== All Tests Passed ==="
```

Run:
```bash
chmod +x run_tests.sh
./run_tests.sh
```

---

## Continuous Testing

### GitHub Actions

Create `.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest
      
      - name: Run tests
        run: |
          cd backend
          pytest tests/ -v
```

---

## Troubleshooting Tests

### Tests Fail Randomly

- Check for race conditions
- Add proper waits for async operations
- Use database transactions
- Clean up test data

### Tests Are Slow

- Use fixtures for setup/teardown
- Mock external services
- Use in-memory database for unit tests
- Parallelize tests

### Integration Tests Fail

- Ensure services are running
- Check network connectivity
- Verify credentials
- Check logs for errors

---

## Support

For testing issues:
- GitHub Issues: https://github.com/Arshkareer/AI_GATEWAY_SYSTEM/issues
- Documentation: README.md

---

**Last Updated**: Phase 5 completion
**Version**: 1.0.0
