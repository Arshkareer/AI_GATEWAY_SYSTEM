"""Smart Routing Engine

ML-powered routing decisions for optimal model selection:
- Context-aware model selection
- Cost-performance optimization
- Load balancing
- Fallback strategies
- A/B testing support
"""

import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from sqlalchemy.orm import Session

from app.models.request_log import RequestLog, RequestStatus, LLMProvider
from app.utils.constants import MODEL_PRICING


class RoutingStrategy(Enum):
    """Routing strategies."""
    COST_OPTIMIZED = "cost_optimized"
    SPEED_OPTIMIZED = "speed_optimized"
    QUALITY_OPTIMIZED = "quality_optimized"
    BALANCED = "balanced"
    CUSTOM = "custom"


class TaskComplexity(Enum):
    """Task complexity levels."""
    SIMPLE = "simple"          # Basic queries, simple tasks
    MODERATE = "moderate"      # Standard requests
    COMPLEX = "complex"        # Complex reasoning, long context
    CRITICAL = "critical"      # Mission-critical, highest quality needed


@dataclass
class RoutingDecision:
    """Represents a routing decision."""
    recommended_model: str
    recommended_provider: str
    confidence: float  # 0-1
    estimated_cost: float
    estimated_latency_ms: float
    estimated_quality_score: float
    reasoning: str
    alternatives: List[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "recommended_model": self.recommended_model,
            "recommended_provider": self.recommended_provider,
            "confidence": round(self.confidence, 3),
            "estimated_cost": round(self.estimated_cost, 6),
            "estimated_latency_ms": round(self.estimated_latency_ms, 0),
            "estimated_quality_score": round(self.estimated_quality_score, 2),
            "reasoning": self.reasoning,
            "alternatives": self.alternatives
        }


class SmartRoutingEngine:
    """ML-powered smart routing for model selection."""
    
    def __init__(self):
        """Initialize routing engine."""
        # Model capabilities and characteristics
        self.model_profiles = {
            "gpt-4": {
                "provider": "openai",
                "max_tokens": 8192,
                "complexity_score": 95,
                "speed_score": 60,
                "cost_score": 30,
                "quality_score": 95,
                "best_for": ["complex reasoning", "code generation", "analysis"]
            },
            "gpt-3.5-turbo": {
                "provider": "openai",
                "max_tokens": 4096,
                "complexity_score": 70,
                "speed_score": 90,
                "cost_score": 95,
                "quality_score": 75,
                "best_for": ["simple queries", "chat", "quick tasks"]
            },
            "claude-3-opus": {
                "provider": "anthropic",
                "max_tokens": 200000,
                "complexity_score": 98,
                "speed_score": 55,
                "cost_score": 25,
                "quality_score": 98,
                "best_for": ["long context", "complex analysis", "creative writing"]
            },
            "claude-3-sonnet": {
                "provider": "anthropic",
                "max_tokens": 200000,
                "complexity_score": 85,
                "speed_score": 75,
                "cost_score": 70,
                "quality_score": 85,
                "best_for": ["balanced tasks", "general purpose", "moderate complexity"]
            },
            "claude-3-haiku": {
                "provider": "anthropic",
                "max_tokens": 200000,
                "complexity_score": 65,
                "speed_score": 95,
                "cost_score": 98,
                "quality_score": 70,
                "best_for": ["simple tasks", "high-volume", "cost-sensitive"]
            },
            "gemini-pro": {
                "provider": "google",
                "max_tokens": 30720,
                "complexity_score": 75,
                "speed_score": 85,
                "cost_score": 99,
                "quality_score": 75,
                "best_for": ["cost-effective", "multimodal", "simple-moderate tasks"]
            }
        }
        
        # Historical performance cache
        self.performance_cache = {}
    
    def route_request(
        self,
        db: Session,
        prompt: str,
        strategy: RoutingStrategy = RoutingStrategy.BALANCED,
        user_preferences: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> RoutingDecision:
        """
        Make intelligent routing decision for a request.
        
        Args:
            db: Database session
            prompt: User's input prompt
            strategy: Routing strategy to use
            user_preferences: User-specific preferences
            context: Additional context (task type, urgency, etc.)
        
        Returns:
            RoutingDecision with recommended model and reasoning
        """
        # Analyze the request
        analysis = self._analyze_request(prompt, context)
        
        # Get available models
        available_models = self._get_available_models(db)
        
        # Score each model based on strategy
        model_scores = self._score_models(
            analysis,
            available_models,
            strategy,
            user_preferences
        )
        
        # Select best model
        best_model = max(model_scores, key=lambda x: x['total_score'])
        
        # Get alternatives
        alternatives = sorted(
            [m for m in model_scores if m['model'] != best_model['model']],
            key=lambda x: x['total_score'],
            reverse=True
        )[:3]
        
        # Build decision
        decision = RoutingDecision(
            recommended_model=best_model['model'],
            recommended_provider=best_model['provider'],
            confidence=best_model['confidence'],
            estimated_cost=best_model['estimated_cost'],
            estimated_latency_ms=best_model['estimated_latency'],
            estimated_quality_score=best_model['quality_score'],
            reasoning=best_model['reasoning'],
            alternatives=[
                {
                    "model": alt['model'],
                    "provider": alt['provider'],
                    "estimated_cost": round(alt['estimated_cost'], 6),
                    "estimated_latency_ms": round(alt['estimated_latency'], 0),
                    "quality_score": round(alt['quality_score'], 2),
                    "reason": alt['reasoning']
                }
                for alt in alternatives
            ]
        )
        
        return decision
    
    def optimize_for_budget(
        self,
        db: Session,
        monthly_budget: float,
        expected_requests: int
    ) -> Dict[str, Any]:
        """
        Optimize routing to stay within budget.
        
        Args:
            db: Database session
            monthly_budget: Monthly budget in USD
            expected_requests: Expected number of requests per month
        
        Returns:
            Optimization recommendations
        """
        cost_per_request = monthly_budget / expected_requests
        
        # Analyze which models fit the budget
        recommendations = []
        
        for model_name, profile in self.model_profiles.items():
            # Estimate average cost per request
            # Assume average 500 tokens input, 500 tokens output
            pricing = self._get_model_pricing(model_name)
            if not pricing:
                continue
            
            estimated_cost = (
                (500 / 1000) * pricing['input_cost_per_1k'] +
                (500 / 1000) * pricing['output_cost_per_1k']
            )
            
            if estimated_cost <= cost_per_request:
                requests_possible = int(monthly_budget / estimated_cost)
                recommendations.append({
                    "model": model_name,
                    "provider": profile['provider'],
                    "estimated_cost_per_request": round(estimated_cost, 6),
                    "requests_possible": requests_possible,
                    "quality_score": profile['quality_score'],
                    "speed_score": profile['speed_score'],
                    "fits_budget": True
                })
        
        # Sort by quality score
        recommendations.sort(key=lambda x: x['quality_score'], reverse=True)
        
        # Calculate mixed strategy
        mixed_strategy = self._calculate_mixed_strategy(
            monthly_budget,
            expected_requests,
            recommendations
        )
        
        return {
            "budget_info": {
                "monthly_budget": monthly_budget,
                "expected_requests": expected_requests,
                "target_cost_per_request": round(cost_per_request, 6)
            },
            "single_model_options": recommendations,
            "mixed_strategy": mixed_strategy,
            "recommendation": self._generate_budget_recommendation(
                recommendations,
                mixed_strategy
            )
        }
    
    def a_b_test_models(
        self,
        db: Session,
        model_a: str,
        model_b: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Compare performance of two models for A/B testing.
        
        Args:
            db: Database session
            model_a: First model to compare
            model_b: Second model to compare
            days: Number of days to analyze
        
        Returns:
            A/B test results and winner
        """
        start_date = datetime.now() - timedelta(days=days)
        
        # Get data for both models
        results_a = self._get_model_performance(db, model_a, start_date)
        results_b = self._get_model_performance(db, model_b, start_date)
        
        if not results_a or not results_b:
            return {
                "error": "Insufficient data for A/B testing",
                "model_a": model_a,
                "model_b": model_b
            }
        
        # Calculate scores
        score_a = self._calculate_ab_score(results_a)
        score_b = self._calculate_ab_score(results_b)
        
        # Determine statistical significance
        significance = self._calculate_significance(results_a, results_b)
        
        # Determine winner
        if abs(score_a - score_b) < 5:
            winner = "tie"
            recommendation = "No clear winner. Both models perform similarly."
        elif score_a > score_b:
            winner = model_a
            recommendation = f"{model_a} is recommended based on {significance['confidence']:.1%} confidence."
        else:
            winner = model_b
            recommendation = f"{model_b} is recommended based on {significance['confidence']:.1%} confidence."
        
        return {
            "test_period": {
                "start_date": start_date.isoformat(),
                "end_date": datetime.now().isoformat(),
                "days": days
            },
            "model_a": {
                "name": model_a,
                "score": round(score_a, 2),
                "metrics": results_a
            },
            "model_b": {
                "name": model_b,
                "score": round(score_b, 2),
                "metrics": results_b
            },
            "statistical_significance": significance,
            "winner": winner,
            "recommendation": recommendation
        }
    
    def _analyze_request(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze request characteristics."""
        analysis = {
            "token_estimate": len(prompt.split()) * 1.3,  # Rough estimate
            "complexity": self._estimate_complexity(prompt),
            "task_type": self._identify_task_type(prompt),
            "urgency": context.get("urgency", "normal") if context else "normal"
        }
        
        return analysis
    
    def _estimate_complexity(self, prompt: str) -> TaskComplexity:
        """Estimate task complexity from prompt."""
        word_count = len(prompt.split())
        
        # Complexity indicators
        complex_keywords = [
            'analyze', 'explain', 'compare', 'evaluate', 'design',
            'create', 'develop', 'implement', 'complex', 'detailed'
        ]
        
        simple_keywords = [
            'what', 'simple', 'quick', 'brief', 'summarize', 'list'
        ]
        
        prompt_lower = prompt.lower()
        
        complex_count = sum(1 for kw in complex_keywords if kw in prompt_lower)
        simple_count = sum(1 for kw in simple_keywords if kw in prompt_lower)
        
        # Decision logic
        if complex_count >= 2 or word_count > 200:
            return TaskComplexity.COMPLEX
        elif simple_count >= 2 and word_count < 50:
            return TaskComplexity.SIMPLE
        else:
            return TaskComplexity.MODERATE
    
    def _identify_task_type(self, prompt: str) -> str:
        """Identify the type of task."""
        prompt_lower = prompt.lower()
        
        if any(kw in prompt_lower for kw in ['code', 'function', 'program', 'debug']):
            return "coding"
        elif any(kw in prompt_lower for kw in ['write', 'essay', 'story', 'creative']):
            return "writing"
        elif any(kw in prompt_lower for kw in ['analyze', 'data', 'statistics']):
            return "analysis"
        elif any(kw in prompt_lower for kw in ['translate', 'language']):
            return "translation"
        else:
            return "general"
    
    def _get_available_models(self, db: Session) -> List[str]:
        """Get list of available models based on recent usage."""
        # Get models used in last 24 hours
        yesterday = datetime.now() - timedelta(hours=24)
        
        models = db.query(RequestLog.model_name).filter(
            RequestLog.created_at >= yesterday
        ).distinct().all()
        
        available = [m[0] for m in models if m[0] in self.model_profiles]
        
        # If no recent usage, return all models
        if not available:
            available = list(self.model_profiles.keys())
        
        return available
    
    def _score_models(
        self,
        analysis: Dict[str, Any],
        available_models: List[str],
        strategy: RoutingStrategy,
        user_preferences: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Score each model based on analysis and strategy."""
        scores = []
        
        for model_name in available_models:
            profile = self.model_profiles[model_name]
            
            # Base scores from profile
            complexity_match = self._match_complexity(
                analysis['complexity'],
                profile['complexity_score']
            )
            
            # Strategy-specific weights
            weights = self._get_strategy_weights(strategy)
            
            # Calculate weighted score
            total_score = (
                complexity_match * weights['complexity'] +
                profile['speed_score'] * weights['speed'] +
                profile['cost_score'] * weights['cost'] +
                profile['quality_score'] * weights['quality']
            )
            
            # Apply user preferences
            if user_preferences:
                total_score = self._apply_user_preferences(
                    total_score,
                    model_name,
                    user_preferences
                )
            
            # Estimate cost
            pricing = self._get_model_pricing(model_name)
            estimated_cost = 0
            if pricing:
                token_est = analysis['token_estimate']
                estimated_cost = (
                    (token_est / 1000) * pricing['input_cost_per_1k'] +
                    (token_est / 1000) * pricing['output_cost_per_1k']
                )
            
            # Build reasoning
            reasoning = self._build_reasoning(
                model_name,
                profile,
                analysis,
                strategy
            )
            
            scores.append({
                "model": model_name,
                "provider": profile['provider'],
                "total_score": total_score,
                "complexity_match": complexity_match,
                "quality_score": profile['quality_score'],
                "speed_score": profile['speed_score'],
                "cost_score": profile['cost_score'],
                "estimated_cost": estimated_cost,
                "estimated_latency": 10000 / profile['speed_score'] * 50,  # Rough estimate
                "confidence": 0.85,  # Base confidence
                "reasoning": reasoning
            })
        
        return scores
    
    def _match_complexity(
        self,
        task_complexity: TaskComplexity,
        model_complexity_score: float
    ) -> float:
        """Match task complexity to model capability."""
        complexity_requirements = {
            TaskComplexity.SIMPLE: 60,
            TaskComplexity.MODERATE: 75,
            TaskComplexity.COMPLEX: 85,
            TaskComplexity.CRITICAL: 95
        }
        
        required = complexity_requirements[task_complexity]
        
        if model_complexity_score >= required:
            return 100  # Perfect match
        else:
            return (model_complexity_score / required) * 100
    
    def _get_strategy_weights(self, strategy: RoutingStrategy) -> Dict[str, float]:
        """Get weights for different routing strategies."""
        strategies = {
            RoutingStrategy.COST_OPTIMIZED: {
                'complexity': 0.2,
                'speed': 0.1,
                'cost': 0.6,
                'quality': 0.1
            },
            RoutingStrategy.SPEED_OPTIMIZED: {
                'complexity': 0.2,
                'speed': 0.6,
                'cost': 0.1,
                'quality': 0.1
            },
            RoutingStrategy.QUALITY_OPTIMIZED: {
                'complexity': 0.3,
                'speed': 0.1,
                'cost': 0.1,
                'quality': 0.5
            },
            RoutingStrategy.BALANCED: {
                'complexity': 0.25,
                'speed': 0.25,
                'cost': 0.25,
                'quality': 0.25
            }
        }
        
        return strategies.get(strategy, strategies[RoutingStrategy.BALANCED])
    
    def _apply_user_preferences(
        self,
        score: float,
        model_name: str,
        preferences: Dict[str, Any]
    ) -> float:
        """Apply user-specific preferences to score."""
        # Preferred providers
        if 'preferred_providers' in preferences:
            profile = self.model_profiles[model_name]
            if profile['provider'] in preferences['preferred_providers']:
                score *= 1.1  # 10% bonus
        
        # Avoid certain models
        if 'avoid_models' in preferences:
            if model_name in preferences['avoid_models']:
                score *= 0.5  # 50% penalty
        
        return score
    
    def _build_reasoning(
        self,
        model_name: str,
        profile: Dict[str, Any],
        analysis: Dict[str, Any],
        strategy: RoutingStrategy
    ) -> str:
        """Build human-readable reasoning for model selection."""
        reasons = []
        
        # Complexity match
        if analysis['complexity'] == TaskComplexity.COMPLEX and profile['complexity_score'] >= 85:
            reasons.append("handles complex tasks well")
        elif analysis['complexity'] == TaskComplexity.SIMPLE and profile['cost_score'] >= 90:
            reasons.append("cost-effective for simple tasks")
        
        # Strategy alignment
        if strategy == RoutingStrategy.COST_OPTIMIZED and profile['cost_score'] >= 90:
            reasons.append("optimized for cost")
        elif strategy == RoutingStrategy.SPEED_OPTIMIZED and profile['speed_score'] >= 85:
            reasons.append("optimized for speed")
        elif strategy == RoutingStrategy.QUALITY_OPTIMIZED and profile['quality_score'] >= 90:
            reasons.append("optimized for quality")
        
        # Best for
        if analysis['task_type'] in [bf.split()[0] for bf in profile['best_for']]:
            reasons.append(f"excels at {analysis['task_type']} tasks")
        
        if not reasons:
            reasons.append("balanced performance")
        
        return f"{model_name}: {', '.join(reasons)}"
    
    def _get_model_pricing(self, model_name: str) -> Optional[Dict[str, float]]:
        """Get pricing for a model."""
        for provider, models in MODEL_PRICING.items():
            if model_name in models:
                return models[model_name]
        return None
    
    def _get_model_performance(
        self,
        db: Session,
        model_name: str,
        start_date: datetime
    ) -> Optional[Dict[str, Any]]:
        """Get performance metrics for a model."""
        requests = db.query(RequestLog).filter(
            RequestLog.model_name == model_name,
            RequestLog.created_at >= start_date,
            RequestLog.status == RequestStatus.SUCCESS
        ).all()
        
        if not requests:
            return None
        
        return {
            "count": len(requests),
            "avg_latency": np.mean([r.latency_ms for r in requests if r.latency_ms]),
            "avg_cost": np.mean([r.total_cost for r in requests]),
            "avg_tokens": np.mean([r.total_tokens for r in requests if r.total_tokens]),
            "success_rate": 100.0  # Already filtered for success
        }
    
    def _calculate_ab_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate overall score for A/B testing."""
        # Normalize metrics
        latency_score = max(0, 100 - (metrics['avg_latency'] / 100))
        cost_score = max(0, 100 - (metrics['avg_cost'] * 10000))
        
        # Weighted score
        score = (
            latency_score * 0.4 +
            cost_score * 0.3 +
            metrics['success_rate'] * 0.3
        )
        
        return score
    
    def _calculate_significance(
        self,
        results_a: Dict[str, Any],
        results_b: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate statistical significance of A/B test."""
        # Simplified significance calculation
        sample_size_a = results_a['count']
        sample_size_b = results_b['count']
        
        total_samples = sample_size_a + sample_size_b
        min_samples = min(sample_size_a, sample_size_b)
        
        # Confidence based on sample size
        if min_samples < 10:
            confidence = 0.5
            is_significant = False
        elif min_samples < 50:
            confidence = 0.75
            is_significant = False
        elif min_samples < 100:
            confidence = 0.85
            is_significant = True
        else:
            confidence = 0.95
            is_significant = True
        
        return {
            "is_significant": is_significant,
            "confidence": confidence,
            "sample_size_a": sample_size_a,
            "sample_size_b": sample_size_b,
            "total_samples": total_samples
        }
    
    def _calculate_mixed_strategy(
        self,
        monthly_budget: float,
        expected_requests: int,
        recommendations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate optimal mixed model strategy."""
        if not recommendations:
            return {}
        
        # Use 70% budget for best quality model, 30% for cost-effective
        best_quality = recommendations[0]  # Already sorted by quality
        most_efficient = sorted(recommendations, key=lambda x: x['estimated_cost_per_request'])[0]
        
        budget_high_quality = monthly_budget * 0.7
        budget_efficient = monthly_budget * 0.3
        
        requests_high_quality = int(budget_high_quality / best_quality['estimated_cost_per_request'])
        requests_efficient = int(budget_efficient / most_efficient['estimated_cost_per_request'])
        
        return {
            "strategy": "70% high-quality, 30% cost-effective",
            "primary_model": {
                "model": best_quality['model'],
                "allocation_percent": 70,
                "estimated_requests": requests_high_quality,
                "estimated_cost": round(budget_high_quality, 2)
            },
            "secondary_model": {
                "model": most_efficient['model'],
                "allocation_percent": 30,
                "estimated_requests": requests_efficient,
                "estimated_cost": round(budget_efficient, 2)
            },
            "total_requests_possible": requests_high_quality + requests_efficient
        }
    
    def _generate_budget_recommendation(
        self,
        single_options: List[Dict[str, Any]],
        mixed_strategy: Dict[str, Any]
    ) -> str:
        """Generate budget recommendation text."""
        if not single_options:
            return "No models fit within the specified budget."
        
        best_single = single_options[0]
        
        if mixed_strategy:
            return (f"Recommended: Use mixed strategy with {mixed_strategy['primary_model']['model']} "
                   f"for important requests and {mixed_strategy['secondary_model']['model']} "
                   f"for routine tasks to maximize value.")
        else:
            return f"Recommended: Use {best_single['model']} exclusively for best quality within budget."
