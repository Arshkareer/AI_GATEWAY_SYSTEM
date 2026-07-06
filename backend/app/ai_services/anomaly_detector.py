"""Anomaly Detection Service

Detects unusual patterns in AI gateway usage including:
- Abnormal usage spikes
- Suspicious cost patterns  
- Unusual request patterns
- Performance anomalies
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from sqlalchemy.orm import Session
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN

from app.models.user import User
from app.models.request_log import RequestLog, RequestStatus
from app.models.department import Department


class AnomalyType(Enum):
    USAGE_SPIKE = "usage_spike"
    COST_ANOMALY = "cost_anomaly"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    SUSPICIOUS_PATTERN = "suspicious_pattern"
    BULK_REQUESTS = "bulk_requests"
    UNUSUAL_TIMING = "unusual_timing"


class AnomalySeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Anomaly:
    """Represents a detected anomaly."""
    type: AnomalyType
    severity: AnomalySeverity
    score: float  # Anomaly confidence score (0-1)
    description: str
    detected_at: datetime
    user_id: Optional[int] = None
    department_id: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "severity": self.severity.value,
            "score": round(self.score, 4),
            "description": self.description,
            "detected_at": self.detected_at.isoformat(),
            "user_id": self.user_id,
            "department_id": self.department_id,
            "metadata": self.metadata or {}
        }


class AnomalyDetector:
    """Advanced anomaly detection for AI gateway usage."""
    
    def __init__(self, contamination: float = 0.1):
        """
        Initialize anomaly detector.
        
        Args:
            contamination: Expected proportion of outliers (0.1 = 10%)
        """
        self.contamination = contamination
        self.isolation_forest = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100
        )
        self.scaler = StandardScaler()
        self.dbscan = DBSCAN(eps=0.5, min_samples=5)
        
    def detect_all_anomalies(self, db: Session) -> List[Anomaly]:
        """Detect all types of anomalies."""
        anomalies = []
        
        # Usage anomalies
        anomalies.extend(self.detect_usage_anomalies(db))
        
        # Cost anomalies
        anomalies.extend(self.detect_cost_anomalies(db))
        
        # Performance anomalies
        anomalies.extend(self.detect_performance_anomalies(db))
        
        # Pattern anomalies
        anomalies.extend(self.detect_pattern_anomalies(db))
        
        return sorted(anomalies, key=lambda x: x.score, reverse=True)
    
    def detect_usage_anomalies(self, db: Session) -> List[Anomaly]:
        """Detect unusual usage patterns."""
        anomalies = []
        
        # Get recent usage data (last 30 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # Hourly usage analysis
        hourly_data = self._get_hourly_usage_data(db, start_date, end_date)
        if len(hourly_data) < 24:  # Need at least 24 hours of data
            return anomalies
        
        # Detect usage spikes
        usage_anomalies = self._detect_isolation_forest_anomalies(
            hourly_data[['request_count', 'unique_users', 'avg_cost']]
        )
        
        for idx in usage_anomalies:
            row = hourly_data.iloc[idx]
            
            # Determine severity based on deviation
            score = abs(row['request_count'] - hourly_data['request_count'].mean()) / hourly_data['request_count'].std()
            severity = self._calculate_severity(score)
            
            anomaly = Anomaly(
                type=AnomalyType.USAGE_SPIKE,
                severity=severity,
                score=min(score / 3.0, 1.0),  # Normalize to 0-1
                description=f"Unusual usage spike: {int(row['request_count'])} requests at {row['hour']}:00",
                detected_at=datetime.now(),
                metadata={
                    "timestamp": row['timestamp'].isoformat(),
                    "request_count": int(row['request_count']),
                    "unique_users": int(row['unique_users']),
                    "avg_cost": round(row['avg_cost'], 4)
                }
            )
            anomalies.append(anomaly)
        
        return anomalies
    
    def detect_cost_anomalies(self, db: Session) -> List[Anomaly]:
        """Detect unusual cost patterns."""
        anomalies = []
        
        # User-level cost analysis
        user_costs = self._get_user_cost_data(db)
        if len(user_costs) < 5:  # Need at least 5 users
            return anomalies
        
        # Detect cost outliers
        cost_features = user_costs[['daily_cost', 'cost_per_request', 'total_tokens']]
        cost_anomalies = self._detect_isolation_forest_anomalies(cost_features)
        
        for idx in cost_anomalies:
            user_data = user_costs.iloc[idx]
            
            # Calculate anomaly score
            mean_cost = user_costs['daily_cost'].mean()
            std_cost = user_costs['daily_cost'].std()
            score = abs(user_data['daily_cost'] - mean_cost) / std_cost if std_cost > 0 else 0
            severity = self._calculate_severity(score)
            
            anomaly = Anomaly(
                type=AnomalyType.COST_ANOMALY,
                severity=severity,
                score=min(score / 3.0, 1.0),
                description=f"Unusual cost pattern for user {user_data['username']}: ${user_data['daily_cost']:.2f}/day",
                detected_at=datetime.now(),
                user_id=int(user_data['user_id']),
                metadata={
                    "daily_cost": round(user_data['daily_cost'], 4),
                    "cost_per_request": round(user_data['cost_per_request'], 4),
                    "total_requests": int(user_data['total_requests'])
                }
            )
            anomalies.append(anomaly)
        
        return anomalies
    
    def detect_performance_anomalies(self, db: Session) -> List[Anomaly]:
        """Detect performance degradation patterns."""
        anomalies = []
        
        # Get performance data by provider/model
        perf_data = self._get_performance_data(db)
        if perf_data.empty:
            return anomalies
        
        # Group by provider and detect latency anomalies
        for provider, group in perf_data.groupby('provider'):
            if len(group) < 10:  # Need sufficient data
                continue
            
            # Calculate latency statistics
            mean_latency = group['latency_ms'].mean()
            std_latency = group['latency_ms'].std()
            
            if std_latency == 0:
                continue
            
            # Find requests with unusually high latency (> 3 std deviations)
            threshold = mean_latency + (3 * std_latency)
            slow_requests = group[group['latency_ms'] > threshold]
            
            if len(slow_requests) > 0:
                avg_slow_latency = slow_requests['latency_ms'].mean()
                score = (avg_slow_latency - mean_latency) / std_latency / 3.0
                severity = self._calculate_severity(score)
                
                anomaly = Anomaly(
                    type=AnomalyType.PERFORMANCE_DEGRADATION,
                    severity=severity,
                    score=min(score, 1.0),
                    description=f"Performance degradation in {provider}: {len(slow_requests)} slow requests (avg: {avg_slow_latency:.0f}ms)",
                    detected_at=datetime.now(),
                    metadata={
                        "provider": provider,
                        "slow_request_count": len(slow_requests),
                        "avg_slow_latency": round(avg_slow_latency, 2),
                        "normal_avg_latency": round(mean_latency, 2),
                        "threshold_latency": round(threshold, 2)
                    }
                )
                anomalies.append(anomaly)
        
        return anomalies
    
    def detect_pattern_anomalies(self, db: Session) -> List[Anomaly]:
        """Detect suspicious request patterns."""
        anomalies = []
        
        # Get recent request patterns
        patterns = self._get_request_patterns(db)
        if patterns.empty:
            return anomalies
        
        # Detect bulk request patterns
        bulk_anomalies = self._detect_bulk_requests(patterns)
        anomalies.extend(bulk_anomalies)
        
        # Detect unusual timing patterns
        timing_anomalies = self._detect_timing_anomalies(patterns)
        anomalies.extend(timing_anomalies)
        
        return anomalies
    
    def _get_hourly_usage_data(self, db: Session, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Get hourly usage statistics."""
        # Query hourly aggregated data
        query = """
        SELECT 
            DATE_TRUNC('hour', created_at) as timestamp,
            EXTRACT(hour FROM created_at) as hour,
            COUNT(*) as request_count,
            COUNT(DISTINCT user_id) as unique_users,
            AVG(total_cost) as avg_cost,
            AVG(latency_ms) as avg_latency
        FROM request_logs 
        WHERE created_at BETWEEN :start_date AND :end_date
            AND status = 'success'
        GROUP BY DATE_TRUNC('hour', created_at), EXTRACT(hour FROM created_at)
        ORDER BY timestamp
        """
        
        result = db.execute(query, {"start_date": start_date, "end_date": end_date})
        
        data = []
        for row in result:
            data.append({
                'timestamp': row.timestamp,
                'hour': int(row.hour),
                'request_count': float(row.request_count),
                'unique_users': float(row.unique_users),
                'avg_cost': float(row.avg_cost or 0),
                'avg_latency': float(row.avg_latency or 0)
            })
        
        return pd.DataFrame(data)
    
    def _get_user_cost_data(self, db: Session) -> pd.DataFrame:
        """Get user cost analysis data."""
        # Last 7 days for user cost analysis
        start_date = datetime.now() - timedelta(days=7)
        
        query = """
        SELECT 
            u.id as user_id,
            u.username,
            COUNT(rl.id) as total_requests,
            SUM(rl.total_cost) / 7.0 as daily_cost,
            AVG(rl.total_cost) as cost_per_request,
            SUM(rl.total_tokens) as total_tokens
        FROM users u
        JOIN request_logs rl ON u.id = rl.user_id
        WHERE rl.created_at >= :start_date
            AND rl.status = 'success'
        GROUP BY u.id, u.username
        HAVING COUNT(rl.id) >= 5
        """
        
        result = db.execute(query, {"start_date": start_date})
        
        data = []
        for row in result:
            data.append({
                'user_id': row.user_id,
                'username': row.username,
                'total_requests': int(row.total_requests),
                'daily_cost': float(row.daily_cost or 0),
                'cost_per_request': float(row.cost_per_request or 0),
                'total_tokens': int(row.total_tokens or 0)
            })
        
        return pd.DataFrame(data)
    
    def _get_performance_data(self, db: Session) -> pd.DataFrame:
        """Get performance data for analysis."""
        # Last 24 hours
        start_date = datetime.now() - timedelta(hours=24)
        
        requests = db.query(RequestLog).filter(
            RequestLog.created_at >= start_date,
            RequestLog.status == RequestStatus.SUCCESS,
            RequestLog.latency_ms.isnot(None)
        ).all()
        
        data = []
        for req in requests:
            data.append({
                'provider': req.provider.value,
                'model_name': req.model_name,
                'latency_ms': float(req.latency_ms),
                'total_tokens': int(req.total_tokens or 0),
                'created_at': req.created_at
            })
        
        return pd.DataFrame(data)
    
    def _get_request_patterns(self, db: Session) -> pd.DataFrame:
        """Get request patterns for analysis."""
        # Last 6 hours for pattern analysis
        start_date = datetime.now() - timedelta(hours=6)
        
        requests = db.query(RequestLog).filter(
            RequestLog.created_at >= start_date
        ).all()
        
        data = []
        for req in requests:
            data.append({
                'user_id': req.user_id,
                'created_at': req.created_at,
                'model_name': req.model_name,
                'total_tokens': int(req.total_tokens or 0),
                'status': req.status.value
            })
        
        return pd.DataFrame(data)
    
    def _detect_isolation_forest_anomalies(self, features: pd.DataFrame) -> List[int]:
        """Use Isolation Forest to detect anomalies."""
        if len(features) < 10:  # Need sufficient data
            return []
        
        # Fill NaN values and scale features
        features_clean = features.fillna(features.mean())
        features_scaled = self.scaler.fit_transform(features_clean)
        
        # Detect anomalies
        outliers = self.isolation_forest.fit_predict(features_scaled)
        
        # Return indices of anomalies (-1 indicates anomaly)
        return [i for i, outlier in enumerate(outliers) if outlier == -1]
    
    def _detect_bulk_requests(self, patterns: pd.DataFrame) -> List[Anomaly]:
        """Detect bulk request patterns that might be suspicious."""
        anomalies = []
        
        if patterns.empty:
            return anomalies
        
        # Group by user and 5-minute windows
        patterns['time_window'] = patterns['created_at'].dt.floor('5min')
        user_windows = patterns.groupby(['user_id', 'time_window']).size().reset_index(name='request_count')
        
        # Find windows with unusually high request counts
        mean_requests = user_windows['request_count'].mean()
        std_requests = user_windows['request_count'].std()
        
        if std_requests == 0:
            return anomalies
        
        threshold = mean_requests + (3 * std_requests)
        bulk_windows = user_windows[user_windows['request_count'] > threshold]
        
        for _, window in bulk_windows.iterrows():
            score = (window['request_count'] - mean_requests) / std_requests / 3.0
            severity = self._calculate_severity(score)
            
            anomaly = Anomaly(
                type=AnomalyType.BULK_REQUESTS,
                severity=severity,
                score=min(score, 1.0),
                description=f"Bulk request pattern: {window['request_count']} requests in 5 minutes",
                detected_at=datetime.now(),
                user_id=int(window['user_id']),
                metadata={
                    "request_count": int(window['request_count']),
                    "time_window": window['time_window'].isoformat(),
                    "threshold": round(threshold, 2)
                }
            )
            anomalies.append(anomaly)
        
        return anomalies
    
    def _detect_timing_anomalies(self, patterns: pd.DataFrame) -> List[Anomaly]:
        """Detect unusual timing patterns."""
        anomalies = []
        
        if patterns.empty:
            return anomalies
        
        # Check for requests outside normal business hours (assuming UTC)
        patterns['hour'] = patterns['created_at'].dt.hour
        night_requests = patterns[
            (patterns['hour'] < 6) | (patterns['hour'] > 22)
        ].groupby('user_id').size().reset_index(name='night_count')
        
        # Find users with unusual night activity
        total_requests = patterns.groupby('user_id').size().reset_index(name='total_count')
        night_analysis = night_requests.merge(total_requests, on='user_id')
        night_analysis['night_ratio'] = night_analysis['night_count'] / night_analysis['total_count']
        
        # Flag users with >50% night activity and >10 total requests
        suspicious_timing = night_analysis[
            (night_analysis['night_ratio'] > 0.5) & 
            (night_analysis['total_count'] > 10)
        ]
        
        for _, user_timing in suspicious_timing.iterrows():
            score = user_timing['night_ratio']
            severity = self._calculate_severity(score * 2)  # Amplify score for timing
            
            anomaly = Anomaly(
                type=AnomalyType.UNUSUAL_TIMING,
                severity=severity,
                score=score,
                description=f"Unusual timing pattern: {user_timing['night_ratio']:.1%} of requests outside business hours",
                detected_at=datetime.now(),
                user_id=int(user_timing['user_id']),
                metadata={
                    "night_requests": int(user_timing['night_count']),
                    "total_requests": int(user_timing['total_count']),
                    "night_ratio": round(user_timing['night_ratio'], 3)
                }
            )
            anomalies.append(anomaly)
        
        return anomalies
    
    def _calculate_severity(self, score: float) -> AnomalySeverity:
        """Calculate severity based on anomaly score."""
        if score >= 2.5:
            return AnomalySeverity.CRITICAL
        elif score >= 2.0:
            return AnomalySeverity.HIGH
        elif score >= 1.5:
            return AnomalySeverity.MEDIUM
        else:
            return AnomalySeverity.LOW
    
    def get_user_anomaly_score(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Get comprehensive anomaly score for a specific user."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found"}
        
        # Detect anomalies for this user
        all_anomalies = self.detect_all_anomalies(db)
        user_anomalies = [a for a in all_anomalies if a.user_id == user_id]
        
        if not user_anomalies:
            return {
                "user_id": user_id,
                "username": user.username,
                "anomaly_score": 0.0,
                "risk_level": "normal",
                "anomalies": []
            }
        
        # Calculate overall anomaly score
        total_score = sum(a.score for a in user_anomalies)
        avg_score = total_score / len(user_anomalies)
        
        # Determine risk level
        if avg_score >= 0.8:
            risk_level = "critical"
        elif avg_score >= 0.6:
            risk_level = "high"
        elif avg_score >= 0.4:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return {
            "user_id": user_id,
            "username": user.username,
            "anomaly_score": round(avg_score, 4),
            "risk_level": risk_level,
            "anomaly_count": len(user_anomalies),
            "anomalies": [a.to_dict() for a in user_anomalies]
        }