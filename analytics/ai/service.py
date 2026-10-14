"""
Unified recommendation service for Market Orbit.

Phase 5.6: Coordinates live Groq LLM inference with deterministic, evidence-grounded
fallback. When Groq is configured and operational, returns validated AI recommendations
with source="groq_llm". If Groq is unconfigured or fails (authentication, rate-limit,
timeout, parsing, or validation error), seamlessly generates fallback recommendations
from deterministic analytics with source="deterministic_fallback".
"""

import logging
from typing import Any, Dict, List, Optional
import pandas as pd

from analytics.ai.fallback import generate_fallback_recommendations
from analytics.ai.groq_client import (
    GroqClient,
    GroqClientError,
)
from analytics.ai.pipeline import (
    RecommendationPipeline,
    RecommendationPipelineError,
    PipelineConfigurationError,
    PipelineAuthenticationError,
    PipelineProviderError,
    PipelineParsingError,
    PipelineValidationError,
)
from analytics.ai.schemas import (
    RecommendationBatch,
)

logger = logging.getLogger(__name__)


class RecommendationService:
    """
    Unified recommendation service managing live Groq inference and deterministic fallback.
    """

    def __init__(
        self,
        client: Optional[GroqClient] = None,
        pipeline: Optional[RecommendationPipeline] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> None:
        self.client = client or GroqClient(model=model, timeout=timeout)
        self.pipeline = pipeline or RecommendationPipeline(client=self.client, model=model)

    def get_recommendations(
        self,
        kpis: Optional[Dict[str, Any]] = None,
        rankings: Optional[Dict[str, Any]] = None,
        trends: Optional[Dict[str, Any]] = None,
        insights: Optional[List[Dict[str, Any]]] = None,
        df: Optional[pd.DataFrame] = None,
        dataset_id: Optional[str] = None,
        force_fallback: bool = False,
        **kwargs: Any,
    ) -> RecommendationBatch:
        """
        Retrieves recommendations for a dataset, attempting live Groq inference first
        and gracefully falling back to deterministic recommendations upon failure.

        Args:
            kpis: KPI summary dictionary.
            rankings: Campaign rankings dictionary.
            trends: Trend and dimensional breakdowns dictionary.
            insights: Optional pre-computed deterministic insights.
            df: Optional campaign DataFrame.
            dataset_id: Optional dataset UUID.
            force_fallback: If True, bypasses Groq inference and uses deterministic engine.
            **kwargs: Keyword aliases for analytics inputs.

        Returns:
            RecommendationBatch containing either live or fallback recommendations.
        """
        # Resolve aliases
        if kpis is None and "kpi_summary" in kwargs:
            kpis = kwargs["kpi_summary"]
        if rankings is None and "campaign_rankings" in kwargs:
            rankings = kwargs["campaign_rankings"]
        if trends is None and "time_series_trends" in kwargs:
            trends = kwargs["time_series_trends"]
        if trends is None and "dimensional_breakdowns" in kwargs:
            trends = kwargs["dimensional_breakdowns"]
        if insights is None and "verified_insights" in kwargs:
            insights = kwargs["verified_insights"]

        # 1. Direct fallback override
        if force_fallback:
            logger.info("force_fallback=True requested; executing deterministic recommendation engine.")
            return generate_fallback_recommendations(
                kpis=kpis,
                rankings=rankings,
                trends=trends,
                insights=insights,
                df=df,
                dataset_id=dataset_id,
            )

        # 2. Check if Groq client is configured
        if not self.client.is_configured:
            logger.info("Groq API key is not configured; using deterministic fallback recommendation engine.")
            return generate_fallback_recommendations(
                kpis=kpis,
                rankings=rankings,
                trends=trends,
                insights=insights,
                df=df,
                dataset_id=dataset_id,
            )

        # 3. Attempt live inference with safe fallback upon expected errors
        try:
            return self.pipeline.run(
                kpi_summary=kpis,
                campaign_rankings=rankings,
                time_series_trends=trends if isinstance(trends, list) else None,
                dimensional_breakdowns=trends if isinstance(trends, dict) else None,
                verified_insights=insights,
                dataset_id=dataset_id,
            )
        except (
            PipelineConfigurationError,
            PipelineAuthenticationError,
            PipelineProviderError,
            PipelineParsingError,
            PipelineValidationError,
            RecommendationPipelineError,
            GroqClientError,
        ) as exc:
            logger.warning(
                "Live Groq recommendation pipeline failed (%s: %s). Falling back to deterministic recommendation engine.",
                type(exc).__name__,
                exc,
            )
            return generate_fallback_recommendations(
                kpis=kpis,
                rankings=rankings,
                trends=trends,
                insights=insights,
                df=df,
                dataset_id=dataset_id,
            )

    def get_recommendation_list(
        self,
        kpis: Optional[Dict[str, Any]] = None,
        rankings: Optional[Dict[str, Any]] = None,
        trends: Optional[Dict[str, Any]] = None,
        insights: Optional[List[Dict[str, Any]]] = None,
        df: Optional[pd.DataFrame] = None,
        dataset_id: Optional[str] = None,
        force_fallback: bool = False,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """
        Executes recommendation resolution and returns a list of dictionaries
        suitable for persistence in AnalysisResult.ai_recommendations and backend callers.
        """
        batch = self.get_recommendations(
            kpis=kpis,
            rankings=rankings,
            trends=trends,
            insights=insights,
            df=df,
            dataset_id=dataset_id,
            force_fallback=force_fallback,
            **kwargs,
        )
        return batch.to_list()


# ---------------------------------------------------------------------------
# Module-level Convenience Functions
# ---------------------------------------------------------------------------

_default_service: Optional[RecommendationService] = None


def get_recommendation_service() -> RecommendationService:
    """Returns a shared default RecommendationService instance."""
    global _default_service
    if _default_service is None:
        _default_service = RecommendationService()
    return _default_service


def get_recommendations(
    kpis: Optional[Dict[str, Any]] = None,
    rankings: Optional[Dict[str, Any]] = None,
    trends: Optional[Dict[str, Any]] = None,
    insights: Optional[List[Dict[str, Any]]] = None,
    df: Optional[pd.DataFrame] = None,
    dataset_id: Optional[str] = None,
    force_fallback: bool = False,
    client: Optional[GroqClient] = None,
    **kwargs: Any,
) -> RecommendationBatch:
    """
    Module-level function to retrieve recommendations via unified service.
    """
    service = RecommendationService(client=client) if client else get_recommendation_service()
    return service.get_recommendations(
        kpis=kpis,
        rankings=rankings,
        trends=trends,
        insights=insights,
        df=df,
        dataset_id=dataset_id,
        force_fallback=force_fallback,
        **kwargs,
    )


def get_recommendation_list(
    kpis: Optional[Dict[str, Any]] = None,
    rankings: Optional[Dict[str, Any]] = None,
    trends: Optional[Dict[str, Any]] = None,
    insights: Optional[List[Dict[str, Any]]] = None,
    df: Optional[pd.DataFrame] = None,
    dataset_id: Optional[str] = None,
    force_fallback: bool = False,
    client: Optional[GroqClient] = None,
    **kwargs: Any,
) -> List[Dict[str, Any]]:
    """
    Module-level function returning a list of recommendation dictionaries.
    """
    batch = get_recommendations(
        kpis=kpis,
        rankings=rankings,
        trends=trends,
        insights=insights,
        df=df,
        dataset_id=dataset_id,
        force_fallback=force_fallback,
        client=client,
        **kwargs,
    )
    return batch.to_list()
