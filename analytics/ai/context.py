"""
Analytics Context Builder for Market Orbit AI Subsystem.

Phase 5.3: Constructs deterministic, evidence-grounded, JSON-serializable payloads
from KPI summaries, campaign rankings, trends, dimensional breakdowns, and
deterministic insights. Treats dataset strings as untrusted data with strict
sanitization and size bounds.
"""

import json
import math
import re
from typing import Any, Dict, List, Optional
import pandas as pd

from analytics.kpi.metrics import calculate_kpis
from analytics.performance.ranking import rank_campaigns
from analytics.trends.customer_trends import analyze_trends
from analytics.insights.generator import generate_insights


DEFAULT_MAX_CAMPAIGNS_PER_RANKING = 5
DEFAULT_MAX_INSIGHTS = 10
DEFAULT_MAX_DIMENSION_CATEGORIES = 5
DEFAULT_MAX_TIMELINE_POINTS = 14
MAX_STRING_LENGTH = 120
MAX_CONTEXT_SERIALIZED_CHARS = 32000


def sanitize_untrusted_string(val: Any, max_length: int = MAX_STRING_LENGTH) -> str:
    """
    Sanitizes untrusted dataset strings (e.g., campaign names, dimensions) to defend
    against prompt injection, control character abuse, and delimiter breakout.
    """
    if val is None:
        return ""
    s = str(val).strip()
    # Strip null bytes and non-printable control characters
    s = "".join(ch for ch in s if ch.isprintable() or ch in ("\n", "\t"))
    # Neutralize XML tag delimiters to prevent delimiter escaping
    s = s.replace("</verified_analytics_context>", "[TAG_FILTERED]")
    s = s.replace("<verified_analytics_context>", "[TAG_FILTERED]")
    s = re.sub(r"<\s*/?\s*system\s*>", "[TAG_FILTERED]", s, flags=re.IGNORECASE)
    # Truncate length to prevent context flooding
    if len(s) > max_length:
        s = s[:max_length].rstrip() + "..."
    return s


def format_finite_float(val: Any) -> Optional[float]:
    """Ensures numeric values are finite Python floats or None (strictly rejects NaN/Inf)."""
    if val is None:
        return None
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return None
        return round(f, 2)
    except (TypeError, ValueError):
        return None


def _format_campaign_entry(item: Dict[str, Any]) -> Dict[str, Any]:
    """Extracts verified campaign metrics preserving missing vs zero semantics."""
    return {
        "campaign_name": sanitize_untrusted_string(item.get("campaign_name", "")),
        "spend": format_finite_float(item.get("spend")) or 0.0,
        "conversions": int(item.get("conversions") or 0),
        "clicks": int(item.get("clicks") or 0),
        "impressions": int(item.get("impressions") or 0),
        "revenue": format_finite_float(item.get("revenue")),  # None when untracked
        "roas": format_finite_float(item.get("roas")),        # None when untracked or spend == 0
        "cpa": format_finite_float(item.get("cpa")),          # None when conversions == 0
    }


def build_analytics_context(
    kpis: Optional[Dict[str, Any]] = None,
    rankings: Optional[Dict[str, Any]] = None,
    trends: Optional[Dict[str, Any]] = None,
    insights: Optional[List[Dict[str, Any]]] = None,
    df: Optional[pd.DataFrame] = None,
    max_campaigns: int = DEFAULT_MAX_CAMPAIGNS_PER_RANKING,
    max_insights: int = DEFAULT_MAX_INSIGHTS,
    max_dimension_categories: int = DEFAULT_MAX_DIMENSION_CATEGORIES,
    max_timeline_points: int = DEFAULT_MAX_TIMELINE_POINTS,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Builds a deterministic, evidence-grounded analytics context payload.

    Accepts pre-computed analytics components or automatically derives them
    if a DataFrame `df` is provided. Reuses existing results without redundant
    recalculation.

    Returns:
        A strictly JSON-serializable dictionary with structured, verified facts.
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
    # Derive missing components if DataFrame is provided
    if df is not None and not df.empty:
        if kpis is None:
            kpis = calculate_kpis(df)
        if rankings is None:
            rankings = rank_campaigns(df)
        if trends is None:
            trends = analyze_trends(df)

    kpis = kpis or {}
    rankings = rankings or {}
    trends = trends or {}

    # Automatically derive deterministic insights if not supplied
    if insights is None:
        try:
            insights = generate_insights(kpis=kpis, rankings=rankings, trends=trends, df=df)
        except Exception:
            insights = []
    insights = insights or []

    # -------------------------------------------------------------------------
    # 1. KPI Summary
    # -------------------------------------------------------------------------
    total_spend = format_finite_float(kpis.get("total_spend")) or 0.0
    total_revenue = format_finite_float(kpis.get("total_revenue"))
    overall_roas = format_finite_float(kpis.get("overall_roas", kpis.get("roas")))
    cpa = format_finite_float(kpis.get("avg_cpa", kpis.get("cpa")))
    cpc = format_finite_float(kpis.get("avg_cpc", kpis.get("cpc")))
    conversion_rate = format_finite_float(kpis.get("avg_conversion_rate", kpis.get("conversion_rate")))
    ctr = format_finite_float(kpis.get("ctr"))

    kpi_summary = {
        "total_spend": total_spend,
        "total_revenue": total_revenue,
        "overall_roas": overall_roas,
        "total_conversions": int(kpis.get("total_conversions") or 0),
        "total_clicks": int(kpis.get("total_clicks") or 0),
        "total_impressions": int(kpis.get("total_impressions") or 0),
        "cpa": cpa,
        "cpc": cpc,
        "conversion_rate_pct": conversion_rate,
        "ctr_pct": ctr,
        "revenue_tracked": total_revenue is not None,
    }

    # -------------------------------------------------------------------------
    # 2. Data Quality & Limitations Information
    # -------------------------------------------------------------------------
    summary = rankings.get("summary", {})
    total_campaigns = int(summary.get("total_campaigns_evaluated", summary.get("total_campaigns", 0)))
    campaigns_with_roas = int(summary.get("campaigns_with_roas", 0))
    campaigns_with_cpa = int(summary.get("campaigns_with_cpa", 0))

    warnings: List[str] = []
    if total_campaigns == 0:
        rev_status = "no_campaigns"
        warnings.append("No campaign records evaluated in this dataset.")
    elif total_revenue is None or campaigns_with_roas == 0:
        rev_status = "untracked"
        warnings.append("Revenue is completely untracked; ROAS and ROI cannot be computed.")
    elif campaigns_with_roas < total_campaigns:
        rev_status = "partial"
        warnings.append(
            f"Revenue is tracked for only {campaigns_with_roas} of {total_campaigns} campaigns; "
            "portfolio ROAS may be incomplete."
        )
    else:
        rev_status = "complete"

    ts_data = trends.get("time_series", {})
    ts_status = ts_data.get("status", "not_provided")
    if ts_status == "insufficient_data":
        distinct_days = ts_data.get("distinct_dates_count", 0)
        warnings.append(
            f"Time-series has only {distinct_days} distinct calendar date(s); at least 2 dates required for trend analysis."
        )

    data_quality = {
        "total_campaigns_evaluated": total_campaigns,
        "campaigns_with_roas": campaigns_with_roas,
        "campaigns_with_cpa": campaigns_with_cpa,
        "revenue_tracking_status": rev_status,
        "time_series_status": ts_status,
        "warnings": warnings,
    }

    # -------------------------------------------------------------------------
    # 3. Campaign Performance Rankings (Top and Bottom)
    # -------------------------------------------------------------------------
    def _slice_campaigns(items: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
        clean_list = [_format_campaign_entry(c) for c in items if isinstance(c, dict)]
        return clean_list[:limit]

    # ROAS Rankings
    by_roas_data = rankings.get("by_roas", {})
    top_roas = _slice_campaigns(by_roas_data.get("top", []), max_campaigns)
    bottom_roas = _slice_campaigns(by_roas_data.get("bottom", []), max_campaigns)

    # Conversions Rankings
    by_conv_data = rankings.get("by_conversions", {})
    top_conv = _slice_campaigns(by_conv_data.get("top", []), max_campaigns)
    bottom_conv = _slice_campaigns(by_conv_data.get("bottom", []), max_campaigns)

    # CPA Rankings
    by_cpa_data = rankings.get("by_cpa", {})
    top_cpa = _slice_campaigns(by_cpa_data.get("top", []), max_campaigns)
    bottom_cpa = _slice_campaigns(by_cpa_data.get("bottom", []), max_campaigns)

    campaign_rankings = {
        "top_by_conversions": top_conv,
        "bottom_by_conversions": bottom_conv,
        "top_by_roas": top_roas,
        "bottom_by_roas": bottom_roas,
        "top_by_cpa": top_cpa,
        "bottom_by_cpa": bottom_cpa,
    }

    # -------------------------------------------------------------------------
    # 4. Historical Time-Series Summary
    # -------------------------------------------------------------------------
    raw_timeline = ts_data.get("timeline", [])
    clean_timeline = []
    if raw_timeline:
        # If timeline exceeds limit, sample start, peak, and end dates
        if len(raw_timeline) > max_timeline_points:
            step = max(1, len(raw_timeline) // max_timeline_points)
            sampled = raw_timeline[::step]
            if raw_timeline[-1] not in sampled:
                sampled.append(raw_timeline[-1])
            selected_points = sampled[:max_timeline_points]
        else:
            selected_points = raw_timeline

        for pt in selected_points:
            clean_timeline.append({
                "date": str(pt.get("date", "")),
                "spend": format_finite_float(pt.get("spend")) or 0.0,
                "conversions": int(pt.get("conversions") or 0),
                "revenue": format_finite_float(pt.get("revenue")),
            })

    time_series_summary = {
        "has_time_series": bool(ts_data.get("has_time_series", False)),
        "status": ts_status,
        "start_date": ts_data.get("start_date"),
        "end_date": ts_data.get("end_date"),
        "distinct_dates_count": int(ts_data.get("distinct_dates_count", 0)),
        "timeline_sample": clean_timeline,
    }

    # -------------------------------------------------------------------------
    # 5. Dimensional Breakdowns
    # -------------------------------------------------------------------------
    raw_dim_breakdowns = trends.get("dimension_breakdowns", {})
    dimensional_performance: Dict[str, List[Dict[str, Any]]] = {}

    for dim_name in sorted(raw_dim_breakdowns.keys()):
        dim_data = raw_dim_breakdowns[dim_name]
        if not isinstance(dim_data, dict):
            continue

        cat_entries = []
        for cat_name, cat_metrics in dim_data.items():
            if not isinstance(cat_metrics, dict):
                continue
            cat_entries.append({
                "category": sanitize_untrusted_string(cat_name),
                "spend": format_finite_float(cat_metrics.get("spend")) or 0.0,
                "conversions": int(cat_metrics.get("conversions") or 0),
                "cpa": format_finite_float(cat_metrics.get("cpa")),
                "revenue": format_finite_float(cat_metrics.get("revenue")),
                "roas": format_finite_float(cat_metrics.get("roas")),
            })

        # Sort categories deterministically: conversions desc, then spend desc, then category name
        sorted_cats = sorted(
            cat_entries,
            key=lambda c: (-c["conversions"], -c["spend"], str(c["category"])),
        )
        dimensional_performance[dim_name] = sorted_cats[:max_dimension_categories]

    # -------------------------------------------------------------------------
    # 6. Verified Deterministic Insights
    # -------------------------------------------------------------------------
    verified_insights: List[Dict[str, Any]] = []
    for item in insights[:max_insights]:
        if not isinstance(item, dict):
            continue

        raw_ev = item.get("evidence", {})
        clean_ev: Dict[str, Any] = {}
        if isinstance(raw_ev, dict):
            for k, v in raw_ev.items():
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    clean_ev[k] = format_finite_float(v)
                elif isinstance(v, str):
                    clean_ev[k] = sanitize_untrusted_string(v)
                else:
                    clean_ev[k] = v

        verified_insights.append({
            "id": str(item.get("id", "")),
            "type": str(item.get("type", "")),
            "title": str(item.get("title", "")),
            "description": str(item.get("description", "")),
            "metric": str(item.get("metric", "")),
            "evidence": clean_ev,
        })

    # Assemble complete context
    context_payload = {
        "kpi_summary": kpi_summary,
        "data_quality": data_quality,
        "campaign_rankings": campaign_rankings,
        "time_series_summary": time_series_summary,
        "dimensional_performance": dimensional_performance,
        "verified_insights": verified_insights,
    }

    return context_payload


def serialize_analytics_context(context: Dict[str, Any], indent: Optional[int] = 2) -> str:
    """
    Serializes analytics context payload to a deterministic JSON string with size validation.
    """
    serialized = json.dumps(context, indent=indent, sort_keys=True)
    if len(serialized) > MAX_CONTEXT_SERIALIZED_CHARS:
        # Compact JSON if exceeds limit
        serialized = json.dumps(context, separators=(",", ":"), sort_keys=True)
    return serialized
