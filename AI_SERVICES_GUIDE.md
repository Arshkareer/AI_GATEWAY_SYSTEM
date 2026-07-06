# AI Services Guide

This document describes the AI-powered features available in the AI Gateway Platform.

## Overview

The AI Gateway includes five intelligent services that provide insights, predictions, and recommendations:

1. **Anomaly Detector** - Detects unusual patterns in usage
2. **Cost Predictor** - Forecasts future costs and provides budget recommendations
3. **Quality Scorer** - Evaluates AI response quality
4. **Smart Routing Engine** - Optimizes model selection
5. **Safety Monitor** - Ensures content safety and compliance

## 1. Anomaly Detector

### Purpose
Automatically detects unusual patterns in AI gateway usage including spikes, suspicious patterns, and performance issues.

### Features
- **Usage Spike Detection**: Identifies abnormal request volumes
- **Cost Anomalies**: Detects unusual spending patterns
- **Performance Issues**: Identifies latency degradation
- **Suspicious Patterns**: Flags bulk requests and unusual timing

### API Endpoints
```http
GET /api/v1/ai-insights/anomalies
GET /api/v1/ai-insights/anomalies/user/{user_id}
```

### Example Response
```json
{
  "anomalies": [
    {
      "type": "usage_spike",
      "severity": "high",
      "score": 0.85,
      "description": "Unusual usage spike: 1250 requests at 14:00",
      "detected_at": "2024-01-15T14:05:00Z",
      "metadata": {
        "request_count": 1250,
        "unique_users": 45,
        "avg_cost": 0.0023
      }
    }
  ],
  "total_count": 5,
  "critical_count": 1,
  "high_count": 2
}
```

## 2. Cost Predictor

### Purpose
Predicts future costs based on historical patterns and provides optimization recommendations.

### Features
- **Daily/Monthly Predictions**: Forecast costs for up to 90 days
- **Budget Planning**: Calculate optimal budget allocation
- **Cost Optimization**: Identify savings opportunities
- **Trend Analysis**: Understand cost patterns over time

### API Endpoints
```http
GET /api/v1/ai-insights/cost-prediction?days_ahead=30
GET /api/v1/ai-insights/cost-prediction/monthly
GET /api/v1/ai-insights/cost-optimization
```

### Example Use Cases

#### 1. Monthly Cost Prediction
```http
GET /api/v1/ai-insights/cost-prediction/monthly?department_id=5
```

Response:
```json
{
  "month": "2024-01",
  "days_elapsed": 15,
  "days_remaining": 16,
  "month_to_date_cost": 245.67,
  "predicted_remaining_cost": 238.45,
  "projected_month_end_cost": 484.12,
  "budget_info": {
    "monthly_budget": 500.00,
    "projected_utilization": 96.82,
    "within_budget": true,
    "projected_overage": 0
  }
}
```

#### 2. Cost Optimization
```http
GET /api/v1/ai-insights/cost-optimization
```

Response:
```json
{
  "current_monthly_cost": 450.00,
  "potential_monthly_savings": 135.00,
  "optimization_percentage": 30.0,
  "recommendations": [
    {
      "type": "optimization",
      "title": "Switch to Cost-Effective Models",
      "description": "You're using expensive models 65% of the time. Consider using GPT-3.5 or Claude Haiku for simpler tasks.",
      "potential_savings": 90.00,
      "priority": "high"
    },
    {
      "type": "optimization",
      "title": "Implement Response Caching",
      "description": "15% of requests are similar. Implement caching to avoid redundant API calls.",
      "potential_savings": 45.00,
      "priority": "high"
    }
  ]
}
```

## 3. Quality Scorer

### Purpose
Evaluates the quality of AI responses using multiple metrics.

### Features
- **Relevance Scoring**: How well response matches the prompt
- **Coherence Analysis**: Structural quality and readability
- **Completeness Assessment**: Whether response is thorough
- **Safety Scoring**: Content safety evaluation
- **Model Comparison**: A/B testing capabilities

### Scoring Dimensions
- **Relevance** (0-100): Keyword matching, context alignment
- **Coherence** (0-100): Sentence structure, flow, readability
- **Completeness** (0-100): Length, detail level, examples
- **Safety** (0-100): Harmful content, disclaimers
- **Overall** (0-100): Weighted average

### API Endpoints
```http
GET /api/v1/ai-insights/quality/model-analysis?model_name=gpt-4&days=7
GET /api/v1/ai-insights/quality/compare-models?model_a=gpt-4&model_b=claude-3-sonnet
GET /api/v1/ai-insights/quality/trends?days=30
```

### Example: Model Comparison
```http
GET /api/v1/ai-insights/quality/compare-models?model_a=gpt-4&model_b=gpt-3.5-turbo&days=7
```

Response:
```json
{
  "comparison": {
    "model_a": {
      "name": "gpt-4",
      "quality_score": 92.5,
      "avg_latency": 3200,
      "avg_tokens": 450
    },
    "model_b": {
      "name": "gpt-3.5-turbo",
      "quality_score": 78.3,
      "avg_latency": 1100,
      "avg_tokens": 380
    }
  },
  "recommendation": {
    "winner": "gpt-4",
    "reason": "Model A has better quality but is slower. Choose based on priority."
  }
}
```

## 4. Smart Routing Engine

### Purpose
Intelligently routes requests to the optimal model based on various strategies.

### Features
- **Context-Aware Routing**: Analyzes prompt complexity
- **Multiple Strategies**: Cost, speed, quality, or balanced
- **Budget Optimization**: Maximize value within budget constraints
- **A/B Testing**: Compare model performance
- **Load Balancing**: Distribute requests efficiently

### Routing Strategies
1. **Cost Optimized**: Minimize costs while maintaining acceptable quality
2. **Speed Optimized**: Fastest response times
3. **Quality Optimized**: Best possible response quality
4. **Balanced**: Equal weight to all factors

### API Endpoints
```http
POST /api/v1/ai-insights/routing/recommend
POST /api/v1/ai-insights/routing/optimize-budget
GET /api/v1/ai-insights/routing/ab-test
```

### Example: Get Routing Recommendation
```http
POST /api/v1/ai-insights/routing/recommend
  ?prompt="Explain quantum computing in simple terms"
  &strategy=balanced
```

Response:
```json
{
  "recommended_model": "claude-3-sonnet",
  "recommended_provider": "anthropic",
  "confidence": 0.87,
  "estimated_cost": 0.0012,
  "estimated_latency_ms": 1850,
  "estimated_quality_score": 85.0,
  "reasoning": "claude-3-sonnet: handles complex tasks well, balanced performance",
  "alternatives": [
    {
      "model": "gpt-3.5-turbo",
      "provider": "openai",
      "estimated_cost": 0.0008,
      "estimated_latency_ms": 950,
      "quality_score": 75.0,
      "reason": "gpt-3.5-turbo: cost-effective for simple tasks, optimized for speed"
    }
  ]
}
```

### Example: Budget Optimization
```http
POST /api/v1/ai-insights/routing/optimize-budget
  ?monthly_budget=1000
  &expected_requests=50000
```

Response:
```json
{
  "budget_info": {
    "monthly_budget": 1000.00,
    "expected_requests": 50000,
    "target_cost_per_request": 0.02
  },
  "mixed_strategy": {
    "strategy": "70% high-quality, 30% cost-effective",
    "primary_model": {
      "model": "claude-3-sonnet",
      "allocation_percent": 70,
      "estimated_requests": 35000,
      "estimated_cost": 700.00
    },
    "secondary_model": {
      "model": "claude-3-haiku",
      "allocation_percent": 30,
      "estimated_requests": 15000,
      "estimated_cost": 300.00
    }
  }
}
```

## 5. Safety Monitor

### Purpose
Monitors AI interactions for safety, compliance, and PII protection.

### Features
- **PII Detection**: Identifies emails, phones, SSN, credit cards, etc.
- **Content Safety**: Flags violence, hate speech, illegal content
- **Compliance Checking**: Validates against organizational rules
- **Automatic Redaction**: Removes sensitive information
- **Disclaimer Checking**: Ensures sensitive topics have warnings

### PII Types Detected
- Email addresses
- Phone numbers
- Social Security Numbers
- Credit card numbers
- IP addresses
- Names (heuristic)
- Addresses

### API Endpoints
```http
POST /api/v1/ai-insights/safety/check
POST /api/v1/ai-insights/safety/detect-pii
POST /api/v1/ai-insights/safety/check-compliance
```

### Example: Safety Check
```http
POST /api/v1/ai-insights/safety/check
  ?prompt="My email is john@example.com"
  &response="I can help with that. Contact me at..."
  &redact_pii=true
```

Response:
```json
{
  "is_safe": true,
  "overall_level": "warning",
  "pii_detected": [
    {
      "type": "email",
      "location": "prompt",
      "confidence": 0.9
    }
  ],
  "safety_issues": [],
  "content_warnings": [],
  "has_redactions": true
}
```

### Example: Compliance Check
```http
POST /api/v1/ai-insights/safety/check-compliance
  ?prompt="What's my medical diagnosis?"
  &response="Based on your symptoms, you might have..."
```

Response:
```json
{
  "is_compliant": false,
  "violations": [
    {
      "rule": "sensitive_disclaimers",
      "description": "Sensitive medical topic without disclaimer",
      "severity": "medium",
      "topics": ["medical"]
    }
  ],
  "violation_count": 1
}
```

## Integration Examples

### 1. Complete Request Flow with All Services

```python
# 1. Check safety before processing
safety_report = await check_safety(prompt=user_prompt)
if not safety_report.is_safe:
    return {"error": "Content safety violation"}

# 2. Get smart routing recommendation
routing = await get_routing_recommendation(
    prompt=user_prompt,
    strategy="balanced"
)

# 3. Process request with recommended model
response = await process_ai_request(
    model=routing.recommended_model,
    prompt=user_prompt
)

# 4. Score response quality
quality = quality_scorer.score_response(
    prompt=user_prompt,
    response=response,
    model_name=routing.recommended_model
)

# 5. Check for anomalies (background)
await detect_anomalies_async()

# 6. Update cost predictions (periodic)
await update_cost_predictions()
```

### 2. Dashboard Integration

```typescript
// Fetch AI insights summary
const insights = await fetch('/api/v1/ai-insights/insights-summary');

// Display anomaly alerts
if (insights.anomalies.critical > 0) {
  showAlert('Critical anomalies detected!');
}

// Show cost predictions
displayCostProjection(insights.cost_prediction);

// Show optimization recommendations
displayRecommendations(insights.cost_optimization.top_recommendations);
```

## Best Practices

### 1. Anomaly Detection
- Run detection hourly or daily
- Set up alerts for critical anomalies
- Review medium/low anomalies weekly
- Track false positive rate

### 2. Cost Prediction
- Update predictions weekly
- Review budget status daily
- Act on optimization recommendations
- A/B test model changes

### 3. Quality Monitoring
- Sample and score 10% of responses
- Compare models monthly
- Track quality trends
- Set minimum quality thresholds

### 4. Smart Routing
- Start with "balanced" strategy
- Adjust based on priorities
- Use budget optimization for planning
- Run A/B tests before switching models

### 5. Safety Monitoring
- Check all prompts and responses
- Automatically redact PII
- Log compliance violations
- Regular compliance audits

## Performance Considerations

### Caching
- Cache routing decisions for similar prompts
- Cache model performance statistics
- Cache PII detection patterns

### Asynchronous Processing
- Run anomaly detection in background
- Update predictions periodically
- Batch quality scoring

### Rate Limiting
- Limit intensive operations (predictions, analysis)
- Implement request queuing for heavy loads
- Use Redis for distributed rate limiting

## Troubleshooting

### Anomaly Detection Issues
**Problem**: Too many false positives
**Solution**: Adjust contamination parameter, increase historical data window

**Problem**: Missing real anomalies
**Solution**: Lower detection thresholds, check data quality

### Cost Prediction Issues
**Problem**: Inaccurate predictions
**Solution**: Ensure at least 7 days of historical data, check for data gaps

**Problem**: Predictions too volatile
**Solution**: Increase smoothing window, filter outliers

### Quality Scoring Issues
**Problem**: Low confidence scores
**Solution**: Increase sample size, improve response length

**Problem**: Inconsistent scores
**Solution**: Standardize prompt formats, use consistent models

### Routing Issues
**Problem**: Suboptimal model selection
**Solution**: Review strategy weights, update model profiles

**Problem**: Budget exceeded
**Solution**: Use cost-optimized routing, implement hard limits

### Safety Monitoring Issues
**Problem**: Missing PII detections
**Solution**: Update regex patterns, use NER models

**Problem**: Too many false positives
**Solution**: Adjust confidence thresholds, whitelist common terms

## API Rate Limits

All AI Insights endpoints are rate limited:
- **Standard Users**: 60 requests/minute
- **Premium Users**: 300 requests/minute
- **Enterprise**: Custom limits

## Data Retention

- **Anomaly Records**: 90 days
- **Prediction History**: 1 year
- **Quality Scores**: 6 months
- **Safety Reports**: 1 year (compliance)

## Support

For issues or questions:
- GitHub Issues: https://github.com/Arshkareer/AI_GATEWAY_SYSTEM/issues
- Documentation: See README.md
- API Docs: http://localhost:8000/api/v1/docs
