"""Constants for the AI Gateway system."""

# Model pricing (per 1K tokens) - Updated as of December 2023
MODEL_PRICING = {
    "openai": {
        "gpt-4": {
            "input_cost_per_1k": 0.03,
            "output_cost_per_1k": 0.06
        },
        "gpt-4-32k": {
            "input_cost_per_1k": 0.06,
            "output_cost_per_1k": 0.12
        },
        "gpt-3.5-turbo": {
            "input_cost_per_1k": 0.0015,
            "output_cost_per_1k": 0.002
        },
        "gpt-3.5-turbo-16k": {
            "input_cost_per_1k": 0.003,
            "output_cost_per_1k": 0.004
        },
        "text-davinci-003": {
            "input_cost_per_1k": 0.02,
            "output_cost_per_1k": 0.02
        }
    },
    "anthropic": {
        "claude-3-opus": {
            "input_cost_per_1k": 0.015,
            "output_cost_per_1k": 0.075
        },
        "claude-3-sonnet": {
            "input_cost_per_1k": 0.003,
            "output_cost_per_1k": 0.015
        },
        "claude-3-haiku": {
            "input_cost_per_1k": 0.00025,
            "output_cost_per_1k": 0.00125
        },
        "claude-2": {
            "input_cost_per_1k": 0.008,
            "output_cost_per_1k": 0.024
        },
        "claude-instant": {
            "input_cost_per_1k": 0.0008,
            "output_cost_per_1k": 0.0024
        }
    },
    "google": {
        "gemini-pro": {
            "input_cost_per_1k": 0.00025,
            "output_cost_per_1k": 0.0005
        },
        "gemini-pro-vision": {
            "input_cost_per_1k": 0.00025,
            "output_cost_per_1k": 0.0005
        },
        "palm-2": {
            "input_cost_per_1k": 0.0005,
            "output_cost_per_1k": 0.0005
        }
    }
}

# Provider API endpoints
PROVIDER_ENDPOINTS = {
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "chat_completions": "/chat/completions",
        "models": "/models"
    },
    "anthropic": {
        "base_url": "https://api.anthropic.com",
        "messages": "/v1/messages",
        "models": "/v1/models"
    },
    "google": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "generateContent": "/models/{model}:generateContent",
        "models": "/models"
    }
}

# Default model configurations
DEFAULT_MODEL_CONFIGS = {
    "openai": {
        "gpt-3.5-turbo": {
            "max_tokens": 4096,
            "temperature": 0.7,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0
        },
        "gpt-4": {
            "max_tokens": 8192,
            "temperature": 0.7,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0
        }
    },
    "anthropic": {
        "claude-3-haiku": {
            "max_tokens": 4096,
            "temperature": 0.7
        },
        "claude-3-sonnet": {
            "max_tokens": 4096,
            "temperature": 0.7
        }
    }
}

# Rate limits (requests per minute)
RATE_LIMITS = {
    "openai": {
        "gpt-3.5-turbo": 3500,
        "gpt-4": 200,
        "gpt-4-32k": 200
    },
    "anthropic": {
        "claude-3-haiku": 1000,
        "claude-3-sonnet": 500,
        "claude-3-opus": 100
    },
    "google": {
        "gemini-pro": 60
    }
}

# Error codes
ERROR_CODES = {
    "INVALID_API_KEY": "API key is invalid or missing",
    "RATE_LIMIT_EXCEEDED": "Rate limit exceeded",
    "MODEL_NOT_AVAILABLE": "Requested model is not available",
    "INSUFFICIENT_QUOTA": "Insufficient quota or credits",
    "REQUEST_TOO_LARGE": "Request payload is too large",
    "CONTENT_FILTERED": "Content was filtered by safety systems",
    "NETWORK_ERROR": "Network connection error",
    "TIMEOUT_ERROR": "Request timed out",
    "UNKNOWN_ERROR": "Unknown error occurred"
}

# HTTP status codes for different error types
HTTP_ERROR_MAPPING = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED", 
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMITED",
    500: "INTERNAL_ERROR",
    502: "BAD_GATEWAY",
    503: "SERVICE_UNAVAILABLE",
    504: "GATEWAY_TIMEOUT"
}

# Supported file types for document processing
SUPPORTED_FILE_TYPES = {
    "text": [".txt", ".md", ".csv"],
    "documents": [".pdf", ".docx", ".doc"],
    "code": [".py", ".js", ".html", ".css", ".json", ".xml"],
    "images": [".jpg", ".jpeg", ".png", ".gif", ".webp"]
}

# Maximum file sizes (in bytes)
MAX_FILE_SIZES = {
    "text": 10 * 1024 * 1024,      # 10 MB
    "documents": 50 * 1024 * 1024,  # 50 MB
    "code": 5 * 1024 * 1024,     # 5 MB
    "images": 20 * 1024 * 1024    # 20 MB
}

# Analytics time ranges
TIME_RANGES = {
    "1h": {"hours": 1},
    "6h": {"hours": 6}, 
    "24h": {"days": 1},
    "7d": {"days": 7},
    "30d": {"days": 30},
    "90d": {"days": 90},
    "1y": {"days": 365}
}

# Default pagination limits
PAGINATION_DEFAULTS = {
    "default_limit": 50,
    "max_limit": 1000,
    "min_limit": 1
}

# Cache TTL values (in seconds)
CACHE_TTL = {
    "user_session": 3600,        # 1 hour
    "analytics_data": 300,       # 5 minutes
    "model_info": 1800,          # 30 minutes
    "rate_limit": 60,            # 1 minute
    "dashboard_stats": 60        # 1 minute
}

# Monitoring thresholds
MONITORING_THRESHOLDS = {
    "error_rate": {
        "warning": 5.0,    # 5%
        "critical": 10.0   # 10%
    },
    "latency_ms": {
        "warning": 5000,   # 5 seconds
        "critical": 10000  # 10 seconds
    },
    "cost_spike": {
        "warning": 1.5,    # 50% increase
        "critical": 2.0    # 100% increase
    }
}

# User roles and their permissions
ROLE_PERMISSIONS = {
    "admin": [
        "read:users", "write:users", "delete:users",
        "read:departments", "write:departments", "delete:departments", 
        "read:analytics", "write:analytics",
        "read:gateway", "write:gateway",
        "admin:all"
    ],
    "employee": [
        "read:analytics", "read:gateway", "write:gateway"
    ],
    "viewer": [
        "read:analytics", "read:gateway"
    ]
}

# Default budget alerts
DEFAULT_BUDGET_ALERTS = [
    {"threshold": 0.5, "message": "50% of monthly budget used"},
    {"threshold": 0.8, "message": "80% of monthly budget used - consider reviewing usage"},
    {"threshold": 0.95, "message": "95% of monthly budget used - approaching limit"},
    {"threshold": 1.0, "message": "Monthly budget exceeded"}
]