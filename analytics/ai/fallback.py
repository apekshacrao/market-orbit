"""
Deterministic fallback recommendation engine for Market Orbit AI subsystem.

Phase 5.6: Converts rule-based, evidence-grounded insights from generate_insights()
into canonical RecommendationItem contracts with source="deterministic_fallback".
Never fabricates metrics, benchmarks, or causal claims absent from analytics outputs.
"""

from typing import Any, Dict, List, Optional
import pandas as pd
from pydantic import ValidationError

from analytics.insights.generator import generate_insights
from analytics.ai.schemas import (
    RecommendationCategory,
    RecommendationItem,
    RecommendationBatch,
    RecommendationSource,
    SupportingEvidence,
)


def _determine_category_and_action(insight: Dict[str, Any]) -> tuple[RecommendationCategory, str]:
    """
    Deterministically maps an insight type and title to a canonical RecommendationCategory
    and an actionable imperative directive.
    """
    itype = str(insight.get("type", "")).strip().lower()
    title = str(insight.get("title", "")).strip()
    title_lower = title.lower()
    evidence = insight.get("evidence", {}) or {}
    campaign_name = evidence.get("campaign_name", "")

    # 1. Data Quality Insights -> DATA_TRACKING
    if itype == "data_quality":
        if "revenue" in title_lower:
            return (
                RecommendationCategory.DATA_TRACKING,
                "Implement revenue tracking pixels and server-side conversion APIs across all active campaigns.",
            )
        if "date" in title_lower or "coverage" in title_lower:
            return (
                RecommendationCategory.DATA_TRACKING,
                "Collect campaign performance data across multiple calendar dates to enable time-series forecasting.",
            )
        return (
            RecommendationCategory.DATA_TRACKING,
            "Audit and verify marketing analytics tracking configuration across all channels.",
        )

    # 2. Campaign Performance Insights
    if itype == "campaign_performance":
        if "zero-conversion" in title_lower or evidence.get("conversions", -1) == 0:
            act = (
                f"Pause or restructure zero-conversion campaign '{campaign_name}' to eliminate acquisition waste."
                if campaign_name
                else "Pause or restructure zero-conversion campaigns to eliminate acquisition waste."
            )
            return (RecommendationCategory.WASTE_REDUCTION, act)
        act = (
            f"Maintain and scale daily budget for top conversion driver '{campaign_name}'."
            if campaign_name
            else "Maintain and scale daily budget for top conversion driver campaigns."
        )
        return (RecommendationCategory.CHANNEL_SCALING, act)

    # 3. Cost Efficiency Insights
    if itype == "cost_efficiency":
        if "lowest" in title_lower or "best" in title_lower:
            act = (
                f"Prioritize budget allocation toward '{campaign_name}' achieving the lowest cost per acquisition."
                if campaign_name
                else "Prioritize budget allocation toward campaigns achieving the lowest cost per acquisition."
            )
            return (RecommendationCategory.BUDGET_ALLOCATION, act)
        act = (
            f"Review targeting parameters and creative fatigue for '{campaign_name}' to reduce elevated CPA."
            if campaign_name
            else "Review targeting parameters and creative fatigue for campaigns with elevated CPA."
        )
        return (RecommendationCategory.WASTE_REDUCTION, act)

    # 4. Revenue Efficiency Insights
    if itype == "revenue_efficiency":
        if "top" in title_lower or "highest" in title_lower:
            act = (
                f"Increase budget allocation to top ROAS performer '{campaign_name}'."
                if campaign_name
                else "Increase budget allocation to top ROAS performing campaigns."
            )
            return (RecommendationCategory.BUDGET_ALLOCATION, act)
        act = (
            f"Reallocate spend away from underperforming campaign '{campaign_name}' demonstrating low return on ad spend."
            if campaign_name
            else "Reallocate spend away from underperforming campaigns demonstrating low return on ad spend."
        )
        return (RecommendationCategory.WASTE_REDUCTION, act)

    # 5. Dimensional Performance Insights
    if itype == "dimensional":
        dim = evidence.get("dimension", "segment")
        cat = evidence.get("category", "")
        if "leading" in title_lower or insight.get("metric") == "conversions":
            act = (
                f"Scale campaigns targeting '{cat}' within {dim} segment."
                if cat
                else f"Scale high-converting segments within {dim}."
            )
            return (RecommendationCategory.CHANNEL_SCALING, act)
        act = (
            f"Prioritize spend toward '{cat}' within {dim} for optimal cost efficiency."
            if cat
            else f"Prioritize spend toward cost-effective segments within {dim}."
        )
        return (RecommendationCategory.BUDGET_ALLOCATION, act)

    # 6. Time-Series Insights
    if itype == "time_series":
        if "peak" in title_lower:
            date = evidence.get("date", "")
            act = (
                f"Schedule high-impact promotions and bid boosts around peak volume periods like {date}."
                if date
                else "Schedule high-impact promotions and bid boosts around peak volume dates."
            )
            return (RecommendationCategory.CREATIVE_OPTIMIZATION, act)
        return (
            RecommendationCategory.BUDGET_ALLOCATION,
            "Align weekly spend pacing and bidding schedules with observed historical volume momentum.",
        )

    raise ValueError(f"Unrecognized deterministic insight type '{itype}'. Cannot map safely.")


def _extract_supporting_evidence(insight: Dict[str, Any]) -> Optional[SupportingEvidence]:
    """
    Extracts verifiable SupportingEvidence from insight evidence dict.
    Preserves None for untracked values and strictly avoids fabricated numbers.
    """
    raw_evidence = insight.get("evidence")
    if not isinstance(raw_evidence, dict) or not raw_evidence:
        return None

    metric = str(insight.get("metric", "performance")).strip().lower()

    # Determine primary observed value
    observed_value: Optional[float] = None
    if "roas" in raw_evidence and raw_evidence["roas"] is not None:
        try:
            observed_value = float(raw_evidence["roas"])
        except (ValueError, TypeError):
            pass
    elif "cpa" in raw_evidence and raw_evidence["cpa"] is not None:
        try:
            observed_value = float(raw_evidence["cpa"])
        except (ValueError, TypeError):
            pass
    elif "conversions" in raw_evidence and raw_evidence["conversions"] is not None:
        try:
            observed_value = float(raw_evidence["conversions"])
        except (ValueError, TypeError):
            pass
    elif "spend" in raw_evidence and raw_evidence["spend"] is not None:
        try:
            observed_value = float(raw_evidence["spend"])
        except (ValueError, TypeError):
            pass
    elif "observed_revenue" in raw_evidence and raw_evidence["observed_revenue"] is not None:
        try:
            observed_value = float(raw_evidence["observed_revenue"])
        except (ValueError, TypeError):
            pass
    elif "distinct_dates_count" in raw_evidence and raw_evidence["distinct_dates_count"] is not None:
        try:
            observed_value = float(raw_evidence["distinct_dates_count"])
        except (ValueError, TypeError):
            pass

    campaign_name = raw_evidence.get("campaign_name")
    dimension = raw_evidence.get("dimension")
    dimension_value = raw_evidence.get("category")

    # Build context dictionary containing remaining facts
    context: Dict[str, Any] = {}
    for k, v in raw_evidence.items():
        if k in ("campaign_name", "dimension", "category"):
            continue
        if v is not None:
            if isinstance(v, (int, float, str, bool)):
                context[k] = v

    return SupportingEvidence(
        metric=metric,
        observed_value=observed_value,
        campaign_name=str(campaign_name).strip() if campaign_name else None,
        dimension=str(dimension).strip() if dimension else None,
        dimension_value=str(dimension_value).strip() if dimension_value else None,
        benchmark_value=None,
        context=context or None,
    )


def map_insight_to_recommendation(
    insight: Dict[str, Any],
    default_id: Optional[str] = None,
) -> RecommendationItem:
    """
    Converts a single deterministic insight dictionary into a canonical RecommendationItem.

    Args:
        insight: Structured insight dictionary from generate_insights().
        default_id: Fallback identifier if insight lacks 'id'.

    Returns:
        Validated RecommendationItem with source=RecommendationSource.DETERMINISTIC_FALLBACK.

    Raises:
        ValueError: If insight is malformed, lacks required fields, or has an unknown type.
    """
    if not isinstance(insight, dict):
        raise ValueError(f"Insight must be a dictionary, got {type(insight).__name__}.")

    title = insight.get("title")
    if not title or not isinstance(title, str) or not title.strip():
        raise ValueError("Insight is missing a valid non-empty 'title'.")

    description = insight.get("description")
    if not description or not isinstance(description, str) or not description.strip():
        raise ValueError("Insight is missing a valid non-empty 'description'.")

    rec_id = str(insight.get("id") or default_id or f"rec-fb-{abs(hash(title)) % 10000:04d}").strip()
    category, action = _determine_category_and_action(insight)
    evidence = _extract_supporting_evidence(insight)

    # Extract limitations
    limitations: List[str] = []
    title_lower = title.lower()
    if "revenue tracking incomplete" in title_lower:
        limitations.append("Revenue is untracked across campaigns; ROAS metrics cannot be evaluated.")
    elif "partial revenue tracking" in title_lower:
        limitations.append("Revenue is tracked for only a subset of campaigns; portfolio ROAS may be incomplete.")
    elif "insufficient date coverage" in title_lower:
        limitations.append("Time-series forecasting requires at least 2 distinct calendar dates.")

    payload = {
        "id": rec_id,
        "category": category,
        "title": title.strip(),
        "action": action.strip(),
        "rationale": description.strip(),
        "description": description.strip(),
        "supporting_evidence": evidence,
        "limitations": limitations,
        "source": RecommendationSource.DETERMINISTIC_FALLBACK,
    }

    try:
        return RecommendationItem.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"Failed to validate RecommendationItem from insight: {exc}") from exc


def convert_insights_to_recommendations(
    insights: List[Dict[str, Any]],
    dataset_id: Optional[str] = None,
) -> RecommendationBatch:
    """
    Converts a list of deterministic insights into a validated RecommendationBatch.

    Args:
        insights: List of insight dictionaries from generate_insights().
        dataset_id: Optional dataset UUID.

    Returns:
        Validated RecommendationBatch with source="deterministic_fallback".
    """
    if not isinstance(insights, list):
        raise ValueError(f"Expected list of insights, got {type(insights).__name__}.")

    recommendations: List[RecommendationItem] = []
    for idx, insight in enumerate(insights, 1):
        rec_item = map_insight_to_recommendation(
            insight=insight,
            default_id=f"rec-fallback-{idx:03d}",
        )
        recommendations.append(rec_item)

    return RecommendationBatch(
        recommendations=recommendations,
        dataset_id=dataset_id,
    )


def generate_fallback_recommendations(
    kpis: Optional[Dict[str, Any]] = None,
    rankings: Optional[Dict[str, Any]] = None,
    trends: Optional[Dict[str, Any]] = None,
    insights: Optional[List[Dict[str, Any]]] = None,
    df: Optional[pd.DataFrame] = None,
    dataset_id: Optional[str] = None,
    **kwargs: Any,
) -> RecommendationBatch:
    """
    Executes the deterministic fallback engine to generate evidence-grounded recommendations.

    Reuses existing insights if provided; otherwise derives them from kpis, rankings,
    trends, or DataFrame without LLM dependency.
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

    # Derive deterministic insights if not supplied
    if insights is None:
        insights = generate_insights(kpis=kpis, rankings=rankings, trends=trends, df=df)

    return convert_insights_to_recommendations(insights=insights, dataset_id=dataset_id)
