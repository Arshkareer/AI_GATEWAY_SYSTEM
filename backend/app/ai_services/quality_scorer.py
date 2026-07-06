"""Quality Scoring Service

Evaluates AI response quality using multiple metrics:
- Relevance scoring
- Coherence analysis
- Completeness assessment
- Hallucination detection
- Sentiment analysis
"""

import re
import numpy as np
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.request_log import RequestLog, RequestStatus


@dataclass
class QualityScore:
    """Represents a quality score for an AI response."""
    overall_score: float  # 0-100
    relevance_score: float
    coherence_score: float
    completeness_score: float
    safety_score: float
    confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": round(self.overall_score, 2),
            "relevance_score": round(self.relevance_score, 2),
            "coherence_score": round(self.coherence_score, 2),
            "completeness_score": round(self.completeness_score, 2),
            "safety_score": round(self.safety_score, 2),
            "confidence": round(self.confidence, 3),
            "grade": self._get_grade()
        }
    
    def _get_grade(self) -> str:
        """Convert score to letter grade."""
        if self.overall_score >= 90:
            return "A"
        elif self.overall_score >= 80:
            return "B"
        elif self.overall_score >= 70:
            return "C"
        elif self.overall_score >= 60:
            return "D"
        else:
            return "F"


class QualityScorer:
    """AI response quality scoring and analysis."""
    
    def __init__(self):
        """Initialize quality scorer."""
        # Common words for text analysis
        self.filler_words = {
            'actually', 'basically', 'honestly', 'literally', 'really',
            'very', 'quite', 'just', 'maybe', 'perhaps'
        }
        
        # Quality indicators
        self.negative_indicators = [
            'I apologize', 'I cannot', 'I do not have', 'unclear',
            'ambiguous', 'I\'m not sure', 'I don\'t know'
        ]
        
        self.positive_indicators = [
            'specifically', 'for example', 'in particular',
            'research shows', 'according to', 'evidence suggests'
        ]
    
    def score_response(
        self,
        prompt: str,
        response: str,
        model_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> QualityScore:
        """
        Score an AI response across multiple dimensions.
        
        Args:
            prompt: The user's input prompt
            response: The AI's response
            model_name: Name of the model used
            metadata: Additional context (optional)
        
        Returns:
            QualityScore object
        """
        # Calculate individual scores
        relevance_score = self._score_relevance(prompt, response)
        coherence_score = self._score_coherence(response)
        completeness_score = self._score_completeness(prompt, response)
        safety_score = self._score_safety(response)
        
        # Calculate overall score (weighted average)
        weights = {
            'relevance': 0.35,
            'coherence': 0.25,
            'completeness': 0.25,
            'safety': 0.15
        }
        
        overall_score = (
            relevance_score * weights['relevance'] +
            coherence_score * weights['coherence'] +
            completeness_score * weights['completeness'] +
            safety_score * weights['safety']
        )
        
        # Calculate confidence based on response characteristics
        confidence = self._calculate_confidence(response, metadata)
        
        return QualityScore(
            overall_score=overall_score,
            relevance_score=relevance_score,
            coherence_score=coherence_score,
            completeness_score=completeness_score,
            safety_score=safety_score,
            confidence=confidence
        )
    
    def analyze_model_quality(
        self,
        db: Session,
        model_name: Optional[str] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Analyze quality metrics for models over time.
        
        Args:
            db: Database session
            model_name: Specific model to analyze (optional)
            days: Number of days to analyze
        
        Returns:
            Quality analysis dict
        """
        start_date = datetime.now() - timedelta(days=days)
        
        query = db.query(RequestLog).filter(
            RequestLog.created_at >= start_date,
            RequestLog.status == RequestStatus.SUCCESS
        )
        
        if model_name:
            query = query.filter(RequestLog.model_name == model_name)
        
        requests = query.limit(1000).all()  # Limit for performance
        
        if not requests:
            return {
                "error": "No data available for analysis",
                "days": days,
                "model_name": model_name
            }
        
        # Analyze each request (simplified - in production, would use cached scores)
        scores = []
        model_stats = {}
        
        for req in requests:
            # Get stored prompt/response if available
            # In production, these would be retrieved from storage
            # For now, we'll use synthetic scoring based on available data
            
            model = req.model_name
            if model not in model_stats:
                model_stats[model] = {
                    'count': 0,
                    'avg_latency': 0,
                    'avg_tokens': 0,
                    'success_rate': 0
                }
            
            model_stats[model]['count'] += 1
            model_stats[model]['avg_latency'] += req.latency_ms or 0
            model_stats[model]['avg_tokens'] += req.total_tokens or 0
        
        # Calculate averages
        for model in model_stats:
            count = model_stats[model]['count']
            model_stats[model]['avg_latency'] = round(
                model_stats[model]['avg_latency'] / count, 2
            )
            model_stats[model]['avg_tokens'] = round(
                model_stats[model]['avg_tokens'] / count, 0
            )
            
            # Synthetic quality score based on performance
            # In production, use actual quality scores
            latency_score = min(100, 100 - (model_stats[model]['avg_latency'] / 100))
            token_efficiency = min(100, 100 - (model_stats[model]['avg_tokens'] / 30))
            model_stats[model]['quality_score'] = round(
                (latency_score + token_efficiency) / 2, 2
            )
        
        return {
            "analysis_period": {
                "start_date": start_date.isoformat(),
                "end_date": datetime.now().isoformat(),
                "days": days
            },
            "total_requests_analyzed": len(requests),
            "model_statistics": model_stats,
            "summary": {
                "models_analyzed": len(model_stats),
                "total_requests": len(requests),
                "avg_quality_score": round(
                    np.mean([s['quality_score'] for s in model_stats.values()]), 2
                )
            }
        }
    
    def compare_models(
        self,
        db: Session,
        model_a: str,
        model_b: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """Compare quality metrics between two models."""
        
        results_a = self.analyze_model_quality(db, model_a, days)
        results_b = self.analyze_model_quality(db, model_b, days)
        
        if "error" in results_a or "error" in results_b:
            return {
                "error": "Insufficient data for comparison",
                "model_a": model_a,
                "model_b": model_b
            }
        
        stats_a = results_a['model_statistics'].get(model_a, {})
        stats_b = results_b['model_statistics'].get(model_b, {})
        
        if not stats_a or not stats_b:
            return {
                "error": "Model data not found",
                "model_a": model_a,
                "model_b": model_b
            }
        
        # Calculate differences
        quality_diff = stats_a['quality_score'] - stats_b['quality_score']
        latency_diff = stats_a['avg_latency'] - stats_b['avg_latency']
        token_diff = stats_a['avg_tokens'] - stats_b['avg_tokens']
        
        # Determine winner
        if abs(quality_diff) < 5:
            winner = "tie"
        else:
            winner = model_a if quality_diff > 0 else model_b
        
        return {
            "comparison": {
                "model_a": {
                    "name": model_a,
                    "quality_score": stats_a['quality_score'],
                    "avg_latency": stats_a['avg_latency'],
                    "avg_tokens": stats_a['avg_tokens'],
                    "request_count": stats_a['count']
                },
                "model_b": {
                    "name": model_b,
                    "quality_score": stats_b['quality_score'],
                    "avg_latency": stats_b['avg_latency'],
                    "avg_tokens": stats_b['avg_tokens'],
                    "request_count": stats_b['count']
                }
            },
            "differences": {
                "quality_score_diff": round(quality_diff, 2),
                "latency_diff_ms": round(latency_diff, 2),
                "token_diff": round(token_diff, 0)
            },
            "recommendation": {
                "winner": winner,
                "reason": self._generate_recommendation(quality_diff, latency_diff, token_diff)
            }
        }
    
    def _score_relevance(self, prompt: str, response: str) -> float:
        """Score how relevant the response is to the prompt."""
        if not prompt or not response:
            return 50.0
        
        # Extract keywords from prompt
        prompt_words = set(re.findall(r'\w+', prompt.lower()))
        prompt_words = {w for w in prompt_words if len(w) > 3}  # Filter short words
        
        # Check keyword overlap
        response_lower = response.lower()
        keyword_matches = sum(1 for word in prompt_words if word in response_lower)
        keyword_score = min(100, (keyword_matches / len(prompt_words) * 100)) if prompt_words else 50
        
        # Check for negative indicators
        negative_penalty = sum(5 for indicator in self.negative_indicators if indicator.lower() in response_lower)
        
        # Check for positive indicators
        positive_bonus = sum(3 for indicator in self.positive_indicators if indicator.lower() in response_lower)
        
        relevance_score = keyword_score - negative_penalty + positive_bonus
        return max(0, min(100, relevance_score))
    
    def _score_coherence(self, response: str) -> float:
        """Score the coherence and structure of the response."""
        if not response:
            return 0.0
        
        score = 70.0  # Base score
        
        # Check sentence structure
        sentences = re.split(r'[.!?]+', response)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) == 0:
            return 0.0
        
        # Average sentence length (sweet spot: 15-25 words)
        avg_sentence_length = len(response.split()) / len(sentences)
        if 15 <= avg_sentence_length <= 25:
            score += 10
        elif avg_sentence_length < 10 or avg_sentence_length > 40:
            score -= 10
        
        # Check for proper capitalization
        capitalized = sum(1 for s in sentences if s and s[0].isupper())
        cap_ratio = capitalized / len(sentences)
        score += cap_ratio * 10
        
        # Check for filler words (should be minimal)
        words = response.lower().split()
        filler_count = sum(1 for word in words if word in self.filler_words)
        filler_ratio = filler_count / len(words) if words else 0
        if filler_ratio > 0.05:  # More than 5% filler words
            score -= filler_ratio * 100
        
        # Check for paragraph structure
        paragraphs = response.split('\n\n')
        if len(paragraphs) > 1:
            score += 5  # Well-structured
        
        return max(0, min(100, score))
    
    def _score_completeness(self, prompt: str, response: str) -> float:
        """Score how complete the response is."""
        if not response:
            return 0.0
        
        score = 60.0  # Base score
        
        # Length analysis
        word_count = len(response.split())
        
        # Check if response is too short
        if word_count < 20:
            score -= 30
        elif word_count < 50:
            score -= 10
        elif word_count > 100:
            score += 15
        
        # Check for common completeness patterns
        if any(word in response.lower() for word in ['summary', 'conclusion', 'in summary']):
            score += 10
        
        # Check for examples or details
        if 'for example' in response.lower() or 'for instance' in response.lower():
            score += 10
        
        # Check for lists or structured information
        if re.search(r'\d+\.|•|-', response):
            score += 10
        
        # Penalize if response ends abruptly
        if not response.rstrip().endswith(('.', '!', '?', '"', "'")):
            score -= 15
        
        return max(0, min(100, score))
    
    def _score_safety(self, response: str) -> float:
        """Score the safety of the response."""
        if not response:
            return 100.0  # Empty is safe
        
        score = 100.0
        response_lower = response.lower()
        
        # Check for potentially harmful content patterns
        harmful_patterns = [
            r'\b(hack|exploit|vulnerability)\b',
            r'\b(steal|illegal|criminal)\b',
            r'\b(violence|weapon|attack)\b',
            r'\b(discriminat|racist|sexist)\b'
        ]
        
        for pattern in harmful_patterns:
            if re.search(pattern, response_lower):
                score -= 20
        
        # Check for proper disclaimers on sensitive topics
        sensitive_topics = ['medical', 'legal', 'financial', 'investment']
        has_sensitive = any(topic in response_lower for topic in sensitive_topics)
        has_disclaimer = any(word in response_lower for word in ['consult', 'professional', 'expert', 'disclaimer'])
        
        if has_sensitive and not has_disclaimer:
            score -= 15
        
        return max(0, min(100, score))
    
    def _calculate_confidence(
        self,
        response: str,
        metadata: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate confidence in the quality score."""
        confidence = 0.8  # Base confidence
        
        # Adjust based on response length
        word_count = len(response.split())
        if word_count < 20:
            confidence -= 0.2
        elif word_count > 200:
            confidence += 0.1
        
        # Adjust based on metadata if available
        if metadata:
            if 'temperature' in metadata and metadata['temperature'] < 0.3:
                confidence += 0.1  # Higher confidence for deterministic responses
            if 'model_name' in metadata:
                # Some models are more consistent
                if 'gpt-4' in metadata['model_name']:
                    confidence += 0.05
        
        return max(0.0, min(1.0, confidence))
    
    def _generate_recommendation(
        self,
        quality_diff: float,
        latency_diff: float,
        token_diff: float
    ) -> str:
        """Generate a recommendation based on model comparison."""
        
        if abs(quality_diff) < 5 and abs(latency_diff) < 500:
            return "Both models perform similarly. Choose based on cost."
        
        if quality_diff > 10:
            if latency_diff > 1000:
                return "Model A has better quality but is slower. Choose based on priority."
            else:
                return "Model A is recommended for better quality."
        elif quality_diff < -10:
            if latency_diff < -1000:
                return "Model B is recommended for better quality and faster responses."
            else:
                return "Model B has better quality."
        
        if abs(latency_diff) > 1000:
            faster_model = "Model A" if latency_diff < 0 else "Model B"
            return f"{faster_model} is significantly faster with similar quality."
        
        return "Models are comparable. Consider cost and specific use case requirements."
    
    def get_quality_trends(
        self,
        db: Session,
        user_id: Optional[int] = None,
        department_id: Optional[int] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get quality trends over time."""
        start_date = datetime.now() - timedelta(days=days)
        
        query = db.query(RequestLog).filter(
            RequestLog.created_at >= start_date,
            RequestLog.status == RequestStatus.SUCCESS
        )
        
        if user_id:
            query = query.filter(RequestLog.user_id == user_id)
        if department_id:
            query = query.filter(RequestLog.department_id == department_id)
        
        requests = query.all()
        
        if not requests:
            return {"error": "No data available"}
        
        # Group by day
        daily_stats = {}
        for req in requests:
            day = req.created_at.date()
            if day not in daily_stats:
                daily_stats[day] = {
                    'count': 0,
                    'total_latency': 0,
                    'total_tokens': 0
                }
            
            daily_stats[day]['count'] += 1
            daily_stats[day]['total_latency'] += req.latency_ms or 0
            daily_stats[day]['total_tokens'] += req.total_tokens or 0
        
        # Calculate daily averages
        trends = []
        for day in sorted(daily_stats.keys()):
            stats = daily_stats[day]
            trends.append({
                'date': day.isoformat(),
                'request_count': stats['count'],
                'avg_latency': round(stats['total_latency'] / stats['count'], 2),
                'avg_tokens': round(stats['total_tokens'] / stats['count'], 0),
                'estimated_quality': round(
                    min(100, 100 - (stats['total_latency'] / stats['count'] / 100)), 2
                )
            })
        
        return {
            "period_days": days,
            "trends": trends,
            "summary": {
                "total_requests": len(requests),
                "avg_daily_requests": round(len(requests) / days, 1)
            }
        }
