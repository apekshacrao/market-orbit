"""
Live Groq Inference Pipeline for Market Orbit.

Phase 5.5: Orchestrates end-to-end evidence-grounded AI recommendations:
1. Assembles bounded analytics context from verified calculations.
2. Formulates prompt messages with injection defenses and strict schema contracts.
3. Submits chat completion requests to Groq SDK with bounded retries and sanitized errors.
4. Parses and validates raw LLM output against the canonical RecommendationBatch schema.
5. Enforces caller-controlled source attribution (source="groq_llm").
"""

import logging
from typing import Any, Dict, List, Optional

from analytics.ai.context import build_analytics_context
from analytics.ai.groq_client import (
    GroqClient,
    GroqClientError,
    GroqConfigurationError,
    GroqAuthenticationError,
    GroqRateLimitError,
    GroqTimeoutError,
    GroqConnectionError,
    GroqEmptyResponseError,
    GroqAPIError,
)
from analytics.ai.parser import (
    RecommendationParserError,
    ResponseParsingError,
    ResponseValidationError,
    parse_recommendations,
)
from analytics.ai.prompts import build_recommendation_prompt_messages
from analytics.ai.schemas import (
    RecommendationBatch,
    RecommendationSource,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pipeline Exceptions
# ---------------------------------------------------------------------------

class RecommendationPipelineError(Exception):
    """Base exception for all live recommendation pipeline failures."""


class PipelineConfigurationError(RecommendationPipelineError):
    """Raised when Groq API key or required client configuration is missing."""


class PipelineAuthenticationError(RecommendationPipelineError):
    """Raised when Groq credentials fail authentication (401/403)."""


class PipelineProviderError(RecommendationPipelineError):
    """Raised when Groq API encounters rate limits, timeouts, or provider errors."""


class PipelineParsingError(RecommendationPipelineError):
    """Raised when LLM output cannot be parsed as valid JSON after bounded retry."""


class PipelineValidationError(RecommendationPipelineError):
    """Raised when LLM output violates canonical recommendation schema contracts."""


# ---------------------------------------------------------------------------
# Pipeline Orchestrator Class
# ---------------------------------------------------------------------------

class RecommendationPipeline:
    """
    Orchestrates the live inference flow from analytics outputs to validated recommendations.
    """

    def __init__(
        self,
        client: Optional[GroqClient] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_parse_retries: int = 1,
    ) -> None:
        self.client = client or GroqClient()
        self.model = model
        self.temperature = temperature
        self.max_parse_retries = max(0, min(max_parse_retries, 2))

    def run(
        self,
        kpi_summary: Optional[Dict[str, Any]] = None,
        campaign_rankings: Optional[Dict[str, Any]] = None,
        time_series_trends: Optional[List[Dict[str, Any]]] = None,
        dimensional_breakdowns: Optional[Dict[str, Any]] = None,
        verified_insights: Optional[List[Dict[str, Any]]] = None,
        data_quality_warnings: Optional[List[str]] = None,
        dataset_id: Optional[str] = None,
    ) -> RecommendationBatch:
        """
        Executes the live recommendation inference pipeline.

        Args:
            kpi_summary: Summary KPI metrics dictionary.
            campaign_rankings: Top and bottom campaign rankings dictionary.
            time_series_trends: Chronological performance list.
            dimensional_breakdowns: Performance breakdowns by channel, region, etc.
            verified_insights: Deterministic insights from generate_insights().
            data_quality_warnings: List of data-quality caveats.
            dataset_id: Optional dataset UUID.

        Returns:
            Validated RecommendationBatch with source="groq_llm".

        Raises:
            PipelineConfigurationError: If GROQ_API_KEY is missing (no network request made).
            PipelineAuthenticationError: If credentials fail authentication (401/403).
            PipelineProviderError: If Groq rate limits, timeouts, or server errors occur.
            PipelineParsingError: If LLM output cannot be parsed into JSON after bounded retry.
            PipelineValidationError: If LLM output violates canonical recommendation contracts.
        """
        # 1. Verify client configuration before any operations
        if not self.client.is_configured:
            raise PipelineConfigurationError(
                "GROQ_API_KEY is not configured. Provide an API key in your environment or root .env file."
            )

        # 2. Build deterministic, bounded analytics context
        context = build_analytics_context(
            kpi_summary=kpi_summary,
            campaign_rankings=campaign_rankings,
            time_series_trends=time_series_trends,
            dimensional_breakdowns=dimensional_breakdowns,
            verified_insights=verified_insights,
            data_quality_warnings=data_quality_warnings,
        )

        # 3. Construct system and user messages
        messages = build_recommendation_prompt_messages(context)

        # 4. Perform live inference with bounded retry on parsing/validation failure
        attempts = 1 + self.max_parse_retries
        last_error: Optional[Exception] = None

        for attempt in range(1, attempts + 1):
            temp = self.temperature if attempt == 1 else max(0.0, self.temperature - 0.1)

            try:
                raw_response = self.client.chat_completion(
                    messages=messages,
                    model=self.model,
                    temperature=temp,
                )
            except GroqAuthenticationError as exc:
                # Do not retry authentication errors
                raise PipelineAuthenticationError(self.client._sanitize(str(exc))) from exc
            except GroqConfigurationError as exc:
                # Do not retry configuration errors
                raise PipelineConfigurationError(self.client._sanitize(str(exc))) from exc
            except (GroqRateLimitError, GroqTimeoutError, GroqConnectionError, GroqEmptyResponseError, GroqAPIError, GroqClientError) as exc:
                # Provider errors handled by SDK retry; fail immediately
                raise PipelineProviderError(self.client._sanitize(str(exc))) from exc
            except Exception as exc:
                raise PipelineProviderError(self.client._sanitize(f"Unexpected provider error: {exc}")) from exc

            # 5. Parse and strictly validate response against canonical contract
            try:
                batch = parse_recommendations(
                    raw_text=raw_response,
                    expected_source=RecommendationSource.GROQ_LLM,
                    enforce_source=True,
                    dataset_id=dataset_id,
                )
                return batch
            except ResponseParsingError as exc:
                last_error = exc
                logger.warning("Pipeline parse failure on attempt %d/%d: %s", attempt, attempts, exc)
                if attempt == attempts:
                    raise PipelineParsingError(
                        f"Failed to parse LLM response as JSON after {attempts} attempt(s): {exc}"
                    ) from exc
            except ResponseValidationError as exc:
                last_error = exc
                logger.warning("Pipeline schema validation failure on attempt %d/%d: %s", attempt, attempts, exc)
                if attempt == attempts:
                    raise PipelineValidationError(
                        f"LLM response violated recommendation schema after {attempts} attempt(s): {exc}"
                    ) from exc

        # Fallback if loop ends without return or explicit raise
        if isinstance(last_error, ResponseValidationError):
            raise PipelineValidationError(str(last_error)) from last_error
        raise PipelineParsingError(str(last_error or "Inference pipeline failed."))


# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------

def run_recommendation_pipeline(
    kpi_summary: Optional[Dict[str, Any]] = None,
    campaign_rankings: Optional[Dict[str, Any]] = None,
    time_series_trends: Optional[List[Dict[str, Any]]] = None,
    dimensional_breakdowns: Optional[Dict[str, Any]] = None,
    verified_insights: Optional[List[Dict[str, Any]]] = None,
    data_quality_warnings: Optional[List[str]] = None,
    dataset_id: Optional[str] = None,
    client: Optional[GroqClient] = None,
    model: Optional[str] = None,
    temperature: float = 0.2,
    max_parse_retries: int = 1,
) -> RecommendationBatch:
    """
    Executes the live recommendation pipeline and returns a validated RecommendationBatch.
    """
    pipeline = RecommendationPipeline(
        client=client,
        model=model,
        temperature=temperature,
        max_parse_retries=max_parse_retries,
    )
    return pipeline.run(
        kpi_summary=kpi_summary,
        campaign_rankings=campaign_rankings,
        time_series_trends=time_series_trends,
        dimensional_breakdowns=dimensional_breakdowns,
        verified_insights=verified_insights,
        data_quality_warnings=data_quality_warnings,
        dataset_id=dataset_id,
    )


def generate_live_recommendations(
    kpi_summary: Optional[Dict[str, Any]] = None,
    campaign_rankings: Optional[Dict[str, Any]] = None,
    time_series_trends: Optional[List[Dict[str, Any]]] = None,
    dimensional_breakdowns: Optional[Dict[str, Any]] = None,
    verified_insights: Optional[List[Dict[str, Any]]] = None,
    data_quality_warnings: Optional[List[str]] = None,
    dataset_id: Optional[str] = None,
    client: Optional[GroqClient] = None,
    model: Optional[str] = None,
    temperature: float = 0.2,
    max_parse_retries: int = 1,
) -> List[Dict[str, Any]]:
    """
    Executes the live recommendation pipeline and returns a list of dictionaries
    ready for database persistence (AnalysisResult.ai_recommendations) and API consumption.
    """
    batch = run_recommendation_pipeline(
        kpi_summary=kpi_summary,
        campaign_rankings=campaign_rankings,
        time_series_trends=time_series_trends,
        dimensional_breakdowns=dimensional_breakdowns,
        verified_insights=verified_insights,
        data_quality_warnings=data_quality_warnings,
        dataset_id=dataset_id,
        client=client,
        model=model,
        temperature=temperature,
        max_parse_retries=max_parse_retries,
    )
    return batch.to_list()
