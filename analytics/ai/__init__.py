"""AI and LLM insights integration."""
from analytics.ai.groq_client import (
    GroqClient as GroqClient,
    DEFAULT_GROQ_MODEL as DEFAULT_GROQ_MODEL,
    DEFAULT_GROQ_TIMEOUT as DEFAULT_GROQ_TIMEOUT,
    DEFAULT_GROQ_MAX_RETRIES as DEFAULT_GROQ_MAX_RETRIES,
    GroqClientError as GroqClientError,
    GroqConfigurationError as GroqConfigurationError,
    GroqAuthenticationError as GroqAuthenticationError,
    GroqRateLimitError as GroqRateLimitError,
    GroqTimeoutError as GroqTimeoutError,
    GroqConnectionError as GroqConnectionError,
    GroqEmptyResponseError as GroqEmptyResponseError,
    GroqAPIError as GroqAPIError,
    load_groq_config as load_groq_config,
)
from analytics.ai.prompts import RECOMMENDATION_PROMPT_TEMPLATE as RECOMMENDATION_PROMPT_TEMPLATE
from analytics.insights.generator import generate_insights as generate_insights
from analytics.ai.schemas import (
    RecommendationCategory as RecommendationCategory,
    RecommendationSource as RecommendationSource,
    SupportingEvidence as SupportingEvidence,
    RecommendationItem as RecommendationItem,
    RecommendationBatch as RecommendationBatch,
    RecommendationResponse as RecommendationResponse,
    normalize_recommendation as normalize_recommendation,
)

__all__ = [
    "GroqClient",
    "DEFAULT_GROQ_MODEL",
    "DEFAULT_GROQ_TIMEOUT",
    "DEFAULT_GROQ_MAX_RETRIES",
    "GroqClientError",
    "GroqConfigurationError",
    "GroqAuthenticationError",
    "GroqRateLimitError",
    "GroqTimeoutError",
    "GroqConnectionError",
    "GroqEmptyResponseError",
    "GroqAPIError",
    "load_groq_config",
    "RECOMMENDATION_PROMPT_TEMPLATE",
    "generate_insights",
    "RecommendationCategory",
    "RecommendationSource",
    "SupportingEvidence",
    "RecommendationItem",
    "RecommendationBatch",
    "RecommendationResponse",
    "normalize_recommendation",
]
