"""Safety Monitoring Service

Monitors AI interactions for safety and compliance:
- PII detection and redaction
- Content safety filtering
- Compliance checking
- Sensitive topic detection
- Inappropriate content flagging
"""

import re
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class SafetyLevel(Enum):
    """Safety levels for content."""
    SAFE = "safe"
    WARNING = "warning"
    UNSAFE = "unsafe"
    CRITICAL = "critical"


class PIIType(Enum):
    """Types of PII that can be detected."""
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    IP_ADDRESS = "ip_address"
    NAME = "name"
    ADDRESS = "address"
    DATE_OF_BIRTH = "date_of_birth"


@dataclass
class SafetyIssue:
    """Represents a detected safety issue."""
    type: str
    severity: SafetyLevel
    description: str
    location: str  # 'prompt' or 'response'
    position: Optional[int] = None  # Character position
    suggestion: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "severity": self.severity.value,
            "description": self.description,
            "location": self.location,
            "position": self.position,
            "suggestion": self.suggestion
        }


@dataclass
class SafetyReport:
    """Comprehensive safety report."""
    is_safe: bool
    overall_level: SafetyLevel
    pii_detected: List[Dict[str, Any]]
    safety_issues: List[SafetyIssue]
    content_warnings: List[str]
    redacted_prompt: Optional[str] = None
    redacted_response: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_safe": self.is_safe,
            "overall_level": self.overall_level.value,
            "pii_detected": self.pii_detected,
            "safety_issues": [issue.to_dict() for issue in self.safety_issues],
            "content_warnings": self.content_warnings,
            "has_redactions": self.redacted_prompt is not None or self.redacted_response is not None
        }


class SafetyMonitor:
    """Monitors content safety and PII in AI interactions."""
    
    def __init__(self):
        """Initialize safety monitor with patterns."""
        # PII detection patterns
        self.pii_patterns = {
            PIIType.EMAIL: r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            PIIType.PHONE: r'\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b',
            PIIType.SSN: r'\b\d{3}-\d{2}-\d{4}\b',
            PIIType.CREDIT_CARD: r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
            PIIType.IP_ADDRESS: r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
        }
        
        # Unsafe content patterns
        self.unsafe_patterns = {
            'violence': [
                r'\b(kill|murder|assault|attack|harm|hurt|destroy)\b',
                r'\b(weapon|gun|knife|bomb|explosive)\b'
            ],
            'hate_speech': [
                r'\b(hate|racist|sexist|discriminat)\w*\b',
            ],
            'illegal_activity': [
                r'\b(illegal|criminal|steal|hack|fraud|scam)\b',
            ],
            'self_harm': [
                r'\b(suicide|self[\s-]?harm|kill\s+myself)\b',
            ]
        }
        
        # Sensitive topics that require warnings
        self.sensitive_topics = {
            'medical': ['diagnosis', 'treatment', 'medication', 'symptoms', 'disease'],
            'legal': ['lawsuit', 'legal advice', 'attorney', 'court', 'litigation'],
            'financial': ['investment', 'stock', 'financial advice', 'trading', 'crypto'],
            'political': ['election', 'political', 'government', 'policy', 'vote']
        }
        
        # Required disclaimers for sensitive topics
        self.disclaimer_keywords = [
            'consult', 'professional', 'expert', 'qualified',
            'not a substitute', 'seek help', 'advice', 'disclaimer'
        ]
    
    def check_safety(
        self,
        prompt: str,
        response: Optional[str] = None,
        redact_pii: bool = True
    ) -> SafetyReport:
        """
        Perform comprehensive safety check.
        
        Args:
            prompt: User's input prompt
            response: AI's response (optional)
            redact_pii: Whether to redact detected PII
        
        Returns:
            SafetyReport with all findings
        """
        pii_detected = []
        safety_issues = []
        content_warnings = []
        
        redacted_prompt = None
        redacted_response = None
        
        # Check prompt
        prompt_pii = self._detect_pii(prompt)
        if prompt_pii:
            pii_detected.extend([{**pii, 'location': 'prompt'} for pii in prompt_pii])
            if redact_pii:
                redacted_prompt = self._redact_pii(prompt, prompt_pii)
        
        prompt_issues = self._check_unsafe_content(prompt, 'prompt')
        safety_issues.extend(prompt_issues)
        
        prompt_warnings = self._check_sensitive_topics(prompt)
        content_warnings.extend(prompt_warnings)
        
        # Check response if provided
        if response:
            response_pii = self._detect_pii(response)
            if response_pii:
                pii_detected.extend([{**pii, 'location': 'response'} for pii in response_pii])
                if redact_pii:
                    redacted_response = self._redact_pii(response, response_pii)
            
            response_issues = self._check_unsafe_content(response, 'response')
            safety_issues.extend(response_issues)
            
            response_warnings = self._check_sensitive_topics(response)
            content_warnings.extend(response_warnings)
            
            # Check for missing disclaimers
            disclaimer_issues = self._check_disclaimers(response, response_warnings)
            safety_issues.extend(disclaimer_issues)
        
        # Determine overall safety level
        overall_level = self._calculate_overall_level(safety_issues)
        is_safe = overall_level in [SafetyLevel.SAFE, SafetyLevel.WARNING]
        
        return SafetyReport(
            is_safe=is_safe,
            overall_level=overall_level,
            pii_detected=pii_detected,
            safety_issues=safety_issues,
            content_warnings=list(set(content_warnings)),  # Remove duplicates
            redacted_prompt=redacted_prompt,
            redacted_response=redacted_response
        )
    
    def detect_pii(self, text: str) -> List[Dict[str, Any]]:
        """Detect PII in text."""
        return self._detect_pii(text)
    
    def redact_pii(self, text: str, pii_items: Optional[List[Dict[str, Any]]] = None) -> str:
        """Redact PII from text."""
        if pii_items is None:
            pii_items = self._detect_pii(text)
        return self._redact_pii(text, pii_items)
    
    def hash_sensitive_data(self, data: str) -> str:
        """Create one-way hash of sensitive data for storage."""
        return hashlib.sha256(data.encode()).hexdigest()
    
    def check_compliance(
        self,
        prompt: str,
        response: str,
        compliance_rules: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Check compliance with organizational rules.
        
        Args:
            prompt: User's prompt
            response: AI's response
            compliance_rules: List of compliance rules to check
        
        Returns:
            Compliance report
        """
        violations = []
        
        # Default compliance rules
        default_rules = [
            'no_pii',
            'no_unsafe_content',
            'sensitive_disclaimers',
            'data_retention'
        ]
        
        rules_to_check = compliance_rules or default_rules
        
        # Check each rule
        if 'no_pii' in rules_to_check:
            pii_in_response = self._detect_pii(response)
            if pii_in_response:
                violations.append({
                    'rule': 'no_pii',
                    'description': 'PII detected in response',
                    'severity': 'high',
                    'count': len(pii_in_response)
                })
        
        if 'no_unsafe_content' in rules_to_check:
            unsafe_issues = self._check_unsafe_content(response, 'response')
            if unsafe_issues:
                violations.append({
                    'rule': 'no_unsafe_content',
                    'description': 'Unsafe content detected',
                    'severity': 'critical',
                    'issues': [issue.type for issue in unsafe_issues]
                })
        
        if 'sensitive_disclaimers' in rules_to_check:
            warnings = self._check_sensitive_topics(response)
            if warnings:
                has_disclaimer = any(
                    kw in response.lower() 
                    for kw in self.disclaimer_keywords
                )
                if not has_disclaimer:
                    violations.append({
                        'rule': 'sensitive_disclaimers',
                        'description': 'Sensitive topic without disclaimer',
                        'severity': 'medium',
                        'topics': warnings
                    })
        
        is_compliant = len(violations) == 0
        
        return {
            'is_compliant': is_compliant,
            'rules_checked': rules_to_check,
            'violations': violations,
            'violation_count': len(violations),
            'checked_at': datetime.utcnow().isoformat()
        }
    
    def anonymize_for_logging(
        self,
        prompt: str,
        response: str
    ) -> Tuple[str, str]:
        """
        Anonymize content for safe logging.
        
        Returns:
            Tuple of (anonymized_prompt, anonymized_response)
        """
        # Detect and redact PII
        prompt_pii = self._detect_pii(prompt)
        response_pii = self._detect_pii(response)
        
        anonymized_prompt = self._redact_pii(prompt, prompt_pii)
        anonymized_response = self._redact_pii(response, response_pii)
        
        return anonymized_prompt, anonymized_response
    
    def _detect_pii(self, text: str) -> List[Dict[str, Any]]:
        """Detect PII in text using regex patterns."""
        detected = []
        
        for pii_type, pattern in self.pii_patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                detected.append({
                    'type': pii_type.value,
                    'value': match.group(),
                    'start': match.start(),
                    'end': match.end(),
                    'confidence': 0.9  # High confidence for regex matches
                })
        
        # Additional heuristic checks for names (simplified)
        # In production, use NER models for better accuracy
        name_pattern = r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'
        name_matches = re.finditer(name_pattern, text)
        for match in name_matches:
            # Filter out common false positives
            if match.group() not in ['United States', 'New York', 'San Francisco']:
                detected.append({
                    'type': PIIType.NAME.value,
                    'value': match.group(),
                    'start': match.start(),
                    'end': match.end(),
                    'confidence': 0.6  # Lower confidence for name detection
                })
        
        return detected
    
    def _redact_pii(self, text: str, pii_items: List[Dict[str, Any]]) -> str:
        """Redact PII from text."""
        if not pii_items:
            return text
        
        # Sort by position (reverse) to avoid index shifting
        pii_items_sorted = sorted(pii_items, key=lambda x: x['start'], reverse=True)
        
        redacted = text
        for pii in pii_items_sorted:
            pii_type = pii['type']
            start = pii['start']
            end = pii['end']
            
            # Create redaction placeholder
            placeholder = f"[REDACTED_{pii_type.upper()}]"
            
            redacted = redacted[:start] + placeholder + redacted[end:]
        
        return redacted
    
    def _check_unsafe_content(self, text: str, location: str) -> List[SafetyIssue]:
        """Check for unsafe content patterns."""
        issues = []
        text_lower = text.lower()
        
        for category, patterns in self.unsafe_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text_lower)
                for match in matches:
                    severity = SafetyLevel.CRITICAL if category in ['violence', 'self_harm'] else SafetyLevel.UNSAFE
                    
                    issues.append(SafetyIssue(
                        type=category,
                        severity=severity,
                        description=f"Detected {category} content",
                        location=location,
                        position=match.start(),
                        suggestion=f"Review and potentially rephrase to avoid {category} content"
                    ))
        
        return issues
    
    def _check_sensitive_topics(self, text: str) -> List[str]:
        """Check for sensitive topics."""
        warnings = []
        text_lower = text.lower()
        
        for topic, keywords in self.sensitive_topics.items():
            if any(kw.lower() in text_lower for kw in keywords):
                warnings.append(topic)
        
        return warnings
    
    def _check_disclaimers(
        self,
        response: str,
        sensitive_warnings: List[str]
    ) -> List[SafetyIssue]:
        """Check if sensitive topics have appropriate disclaimers."""
        issues = []
        
        if not sensitive_warnings:
            return issues
        
        response_lower = response.lower()
        has_disclaimer = any(
            kw in response_lower 
            for kw in self.disclaimer_keywords
        )
        
        if not has_disclaimer:
            for topic in sensitive_warnings:
                issues.append(SafetyIssue(
                    type='missing_disclaimer',
                    severity=SafetyLevel.WARNING,
                    description=f"Sensitive {topic} topic without disclaimer",
                    location='response',
                    suggestion=f"Add disclaimer advising to consult a qualified {topic} professional"
                ))
        
        return issues
    
    def _calculate_overall_level(self, safety_issues: List[SafetyIssue]) -> SafetyLevel:
        """Calculate overall safety level from issues."""
        if not safety_issues:
            return SafetyLevel.SAFE
        
        # Get highest severity
        severities = [issue.severity for issue in safety_issues]
        
        if SafetyLevel.CRITICAL in severities:
            return SafetyLevel.CRITICAL
        elif SafetyLevel.UNSAFE in severities:
            return SafetyLevel.UNSAFE
        elif SafetyLevel.WARNING in severities:
            return SafetyLevel.WARNING
        else:
            return SafetyLevel.SAFE
    
    def get_safety_statistics(
        self,
        reports: List[SafetyReport]
    ) -> Dict[str, Any]:
        """Generate statistics from multiple safety reports."""
        if not reports:
            return {
                'error': 'No reports to analyze'
            }
        
        total_reports = len(reports)
        safe_count = sum(1 for r in reports if r.is_safe)
        
        # Count PII occurrences
        pii_by_type = {}
        for report in reports:
            for pii in report.pii_detected:
                pii_type = pii['type']
                pii_by_type[pii_type] = pii_by_type.get(pii_type, 0) + 1
        
        # Count issue types
        issues_by_type = {}
        for report in reports:
            for issue in report.safety_issues:
                issue_type = issue.type
                issues_by_type[issue_type] = issues_by_type.get(issue_type, 0) + 1
        
        # Count warnings
        warnings_by_topic = {}
        for report in reports:
            for warning in report.content_warnings:
                warnings_by_topic[warning] = warnings_by_topic.get(warning, 0) + 1
        
        return {
            'total_reports': total_reports,
            'safe_count': safe_count,
            'unsafe_count': total_reports - safe_count,
            'safety_rate': round((safe_count / total_reports * 100), 2),
            'pii_detections': {
                'total': sum(pii_by_type.values()),
                'by_type': pii_by_type
            },
            'safety_issues': {
                'total': sum(issues_by_type.values()),
                'by_type': issues_by_type
            },
            'content_warnings': {
                'total': sum(warnings_by_topic.values()),
                'by_topic': warnings_by_topic
            }
        }
