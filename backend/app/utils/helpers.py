import uuid
import hashlib
from typing import Optional
from datetime import datetime, timezone


def generate_request_id() -> str:
    """Generate a unique request ID."""
    return f"req_{uuid.uuid4().hex[:12]}"


def generate_session_id() -> str:
    """Generate a unique session ID."""
    return f"sess_{uuid.uuid4().hex[:16]}"


def calculate_token_cost(
    prompt_tokens: int,
    completion_tokens: int,
    model_name: str,
    provider: str
) -> float:
    """Calculate cost based on token usage and model pricing."""
    from .constants import MODEL_PRICING
    
    # Get pricing for the model
    pricing = MODEL_PRICING.get(provider, {}).get(model_name)
    if not pricing:
        return 0.0
    
    input_cost = (prompt_tokens / 1000) * pricing["input_cost_per_1k"]
    output_cost = (completion_tokens / 1000) * pricing["output_cost_per_1k"]
    
    return round(input_cost + output_cost, 6)


def format_currency(amount: float, currency: str = "USD") -> str:
    """Format currency amount for display."""
    if currency == "USD":
        return f"${amount:.2f}"
    return f"{amount:.2f} {currency}"


def hash_content(content: str) -> str:
    """Generate a hash for content (for analytics without storing actual content)."""
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def estimate_tokens(text: str) -> int:
    """Estimate token count for text (rough approximation)."""
    # Very rough estimate: ~4 characters per token for English text
    return max(1, len(text) // 4)


def validate_email(email: str) -> bool:
    """Basic email validation."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations."""
    import re
    # Remove or replace unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Limit length
    return filename[:255]


def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """Calculate percentage change between two values."""
    if old_value == 0:
        return 100.0 if new_value > 0 else 0.0
    return ((new_value - old_value) / old_value) * 100


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human readable format."""
    if seconds < 1:
        return f"{int(seconds * 1000)}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = int(seconds % 60)
        return f"{minutes}m {remaining_seconds}s"
    else:
        hours = int(seconds // 3600)
        remaining_minutes = int((seconds % 3600) // 60)
        return f"{hours}h {remaining_minutes}m"


def get_current_utc_timestamp() -> datetime:
    """Get current UTC timestamp."""
    return datetime.now(timezone.utc)


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to specified length with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."


def parse_model_name(full_model_name: str) -> tuple[str, str]:
    """Parse full model name to extract provider and model."""
    # Handle cases like "openai/gpt-4" or just "gpt-4"
    if "/" in full_model_name:
        provider, model = full_model_name.split("/", 1)
        return provider.lower(), model
    
    # Try to infer provider from model name
    model_lower = full_model_name.lower()
    if model_lower.startswith("gpt"):
        return "openai", full_model_name
    elif model_lower.startswith("claude"):
        return "anthropic", full_model_name
    elif model_lower.startswith("gemini") or model_lower.startswith("palm"):
        return "google", full_model_name
    
    return "unknown", full_model_name


def validate_json_structure(data: dict, required_fields: list) -> tuple[bool, str]:
    """Validate that dictionary contains required fields."""
    missing_fields = []
    
    for field in required_fields:
        if field not in data:
            missing_fields.append(field)
    
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"
    
    return True, "Valid"


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning default if denominator is zero."""
    if denominator == 0:
        return default
    return numerator / denominator


def generate_api_key_preview(api_key: str) -> str:
    """Generate a preview of an API key for display purposes."""
    if len(api_key) < 8:
        return "***"
    return f"{api_key[:4]}...{api_key[-4:]}"