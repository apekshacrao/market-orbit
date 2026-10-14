"""AI and LLM insights integration."""
from analytics.ai.groq_client import GroqClient as GroqClient
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
