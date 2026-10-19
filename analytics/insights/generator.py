"""
Deterministic evidence-based insight generator for Market Orbit analytics.

Produces structured, verifiable observations from KPI calculations, campaign rankings,
time-series trends, and dimensional breakdowns without external LLM dependencies.
"""

from typing import Dict, Any, List, Optional
import pandas as pd

from analytics.kpi.metrics import calculate_kpis
from analytics.performance.ranking import rank_campaigns
from analytics.trends.customer_trends import analyze_trends, SUPPORTED_DIMENSIONS


DIMENSION_LABELS = {
    "location": "Location",
    "age_group": "Age Group",
    "customer_segment": "Customer Segment",
    "device": "Device",
}


def generate_insights(
    kpis: Optional[Dict[str, Any]] = None,
    rankings: Optional[Dict[str, Any]] = None,
    trends: Optional[Dict[str, Any]] = None,
    df: Optional[pd.DataFrame] = None,
) -> List[Dict[str, Any]]:
    """
    Generates deterministic, evidence-based marketing insights from analytics results.

    Accepts pre-computed kpis, rankings, and trends, or automatically derives them
    if a DataFrame `df` is provided.

    Returns:
        List of structured insight dictionaries, each with:
        - 'id': Deterministic identifier (e.g., 'insight-001')
        - 'type': Insight category ('data_quality', 'campaign_performance',
                  'cost_efficiency', 'revenue_efficiency', 'dimensional', 'time_series')
        - 'title': Plain-language summary title
        - 'description': Verifiable observation grounded in source metrics
        - 'metric': Primary metric under observation
        - 'evidence': Structured dictionary containing source metric values
    """
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

    # If completely empty or no campaigns evaluated, return empty list
    summary = rankings.get("summary", {})
    total_campaigns = summary.get("total_campaigns_evaluated", 0)
    if total_campaigns == 0 and not kpis and not trends:
        return []

    raw_insights: List[Dict[str, Any]] = []

    # -------------------------------------------------------------------------
    # 1. Data Quality & Limitation Insights
    # -------------------------------------------------------------------------
    # Check for untracked or partially missing revenue
    total_revenue = kpis.get("total_revenue")
    campaigns_with_roas = summary.get("campaigns_with_roas", 0)

    if total_campaigns > 0:
        if total_revenue is None:
            spend_val = kpis.get("total_spend", 0.0)
            raw_insights.append({
                "type": "data_quality",
                "title": "Revenue Tracking Incomplete",
                "description": (
                    "Revenue data is untracked across campaigns, "
                    "preventing portfolio-level ROAS and ROI calculations."
                ),
                "metric": "revenue",
                "evidence": {
                    "total_revenue": None,
                    "total_spend": spend_val,
                    "campaigns_evaluated": total_campaigns,
                },
            })
        elif campaigns_with_roas < total_campaigns:
            raw_insights.append({
                "type": "data_quality",
                "title": "Partial Revenue Tracking",
                "description": (
                    f"Revenue is tracked for only {campaigns_with_roas} of {total_campaigns} campaigns; "
                    "portfolio-level ROAS may not reflect complete returns."
                ),
                "metric": "revenue",
                "evidence": {
                    "tracked_campaigns_count": campaigns_with_roas,
                    "total_campaigns": total_campaigns,
                    "observed_revenue": total_revenue,
                },
            })

    # Check for insufficient time-series date coverage
    ts_data = trends.get("time_series", {})
    if total_campaigns > 0 and ts_data.get("status") == "insufficient_data":
        distinct_count = ts_data.get("distinct_dates_count", 0)
        raw_insights.append({
            "type": "data_quality",
            "title": "Insufficient Date Coverage for Trend Analysis",
            "description": (
                f"Observed data contains {distinct_count} distinct calendar date(s); "
                "at least 2 distinct dates are required for historical time-series analysis."
            ),
            "metric": "date",
            "evidence": {
                "distinct_dates_count": distinct_count,
                "required_minimum_dates": 2,
            },
        })

    # -------------------------------------------------------------------------
    # 2. Campaign Performance Insights
    # -------------------------------------------------------------------------
    conv_ranking = rankings.get("by_conversions", {})
    top_conv_list = conv_ranking.get("top", [])
    if top_conv_list:
        top_conv = top_conv_list[0]
        if top_conv.get("conversions", 0) > 0:
            raw_insights.append({
                "type": "campaign_performance",
                "title": f"Top Conversion Driver: {top_conv['campaign_name']}",
                "description": (
                    f"'{top_conv['campaign_name']}' generated the highest conversion volume with "
                    f"{top_conv['conversions']} conversions from ${top_conv.get('spend', 0.0):.2f} spend."
                ),
                "metric": "conversions",
                "evidence": {
                    "campaign_name": top_conv["campaign_name"],
                    "conversions": top_conv["conversions"],
                    "spend": top_conv.get("spend", 0.0),
                },
            })

    # Check for zero-conversion spend (pure acquisition waste)
    # Search campaigns evaluated that had spend > 0 but 0 conversions
    bottom_conv_list = conv_ranking.get("bottom", [])
    zero_conv_campaigns = [
        c for c in bottom_conv_list
        if c.get("conversions", 0) == 0 and c.get("spend", 0.0) > 0.0
    ]
    # Sort deterministically by spend descending, then campaign_name
    zero_conv_campaigns = sorted(
        zero_conv_campaigns,
        key=lambda c: (-c.get("spend", 0.0), str(c.get("campaign_name", ""))),
    )
    if zero_conv_campaigns:
        waste_c = zero_conv_campaigns[0]
        raw_insights.append({
            "type": "campaign_performance",
            "title": f"Zero-Conversion Spend: {waste_c['campaign_name']}",
            "description": (
                f"'{waste_c['campaign_name']}' recorded ${waste_c['spend']:.2f} in spend "
                "with 0 conversions achieved."
            ),
            "metric": "spend",
            "evidence": {
                "campaign_name": waste_c["campaign_name"],
                "spend": waste_c["spend"],
                "conversions": 0,
            },
        })

    # -------------------------------------------------------------------------
    # 3. Cost Efficiency Insights
    # -------------------------------------------------------------------------
    cpa_ranking = rankings.get("by_cpa", {})
    top_cpa_list = cpa_ranking.get("top", [])
    bottom_cpa_list = cpa_ranking.get("bottom", [])

    if top_cpa_list:
        best_cpa = top_cpa_list[0]
        if best_cpa.get("cpa") is not None and best_cpa.get("conversions", 0) > 0:
            raw_insights.append({
                "type": "cost_efficiency",
                "title": f"Lowest Cost per Acquisition: {best_cpa['campaign_name']}",
                "description": (
                    f"'{best_cpa['campaign_name']}' achieved the most cost-effective acquisition "
                    f"at ${best_cpa['cpa']:.2f} per conversion ({best_cpa['conversions']} conversions)."
                ),
                "metric": "cpa",
                "evidence": {
                    "campaign_name": best_cpa["campaign_name"],
                    "cpa": best_cpa["cpa"],
                    "spend": best_cpa.get("spend", 0.0),
                    "conversions": best_cpa["conversions"],
                },
            })

    if bottom_cpa_list:
        worst_cpa = bottom_cpa_list[-1]
        best_cpa_name = top_cpa_list[0]["campaign_name"] if top_cpa_list else None
        # Only emit high CPA insight if distinct from the best CPA campaign
        if (
            worst_cpa.get("cpa") is not None
            and worst_cpa.get("campaign_name") != best_cpa_name
        ):
            raw_insights.append({
                "type": "cost_efficiency",
                "title": f"Highest Cost per Acquisition: {worst_cpa['campaign_name']}",
                "description": (
                    f"'{worst_cpa['campaign_name']}' recorded the highest cost per acquisition "
                    f"at ${worst_cpa['cpa']:.2f} per conversion."
                ),
                "metric": "cpa",
                "evidence": {
                    "campaign_name": worst_cpa["campaign_name"],
                    "cpa": worst_cpa["cpa"],
                    "spend": worst_cpa.get("spend", 0.0),
                    "conversions": worst_cpa.get("conversions", 0),
                },
            })

    # -------------------------------------------------------------------------
    # 4. Revenue Efficiency Insights (Only if Revenue is Tracked)
    # -------------------------------------------------------------------------
    roas_ranking = rankings.get("by_roas", {})
    top_roas_list = roas_ranking.get("top", [])
    bottom_roas_list = roas_ranking.get("bottom", [])

    if top_roas_list:
        top_roas = top_roas_list[0]
        if top_roas.get("roas") is not None and top_roas.get("spend", 0.0) > 0.0:
            raw_insights.append({
                "type": "revenue_efficiency",
                "title": f"Top Return on Ad Spend: {top_roas['campaign_name']}",
                "description": (
                    f"'{top_roas['campaign_name']}' delivered the highest return on ad spend "
                    f"at {top_roas['roas']:.2f}x ROAS (${top_roas.get('revenue', 0.0):.2f} revenue from "
                    f"${top_roas.get('spend', 0.0):.2f} spend)."
                ),
                "metric": "roas",
                "evidence": {
                    "campaign_name": top_roas["campaign_name"],
                    "roas": top_roas["roas"],
                    "revenue": top_roas.get("revenue"),
                    "spend": top_roas.get("spend", 0.0),
                },
            })

    if bottom_roas_list:
        bottom_roas = bottom_roas_list[-1]
        top_roas_name = top_roas_list[0]["campaign_name"] if top_roas_list else None
        # Only emit bottom ROAS if distinct from top ROAS
        if (
            bottom_roas.get("roas") is not None
            and bottom_roas.get("campaign_name") != top_roas_name
        ):
            raw_insights.append({
                "type": "revenue_efficiency",
                "title": f"Lowest Return on Ad Spend: {bottom_roas['campaign_name']}",
                "description": (
                    f"'{bottom_roas['campaign_name']}' recorded the lowest return on ad spend "
                    f"at {bottom_roas['roas']:.2f}x ROAS."
                ),
                "metric": "roas",
                "evidence": {
                    "campaign_name": bottom_roas["campaign_name"],
                    "roas": bottom_roas["roas"],
                    "revenue": bottom_roas.get("revenue"),
                    "spend": bottom_roas.get("spend", 0.0),
                },
            })

    # -------------------------------------------------------------------------
    # 5. Dimensional Performance Observations
    # -------------------------------------------------------------------------
    dim_breakdowns = trends.get("dimension_breakdowns", {})
    for dim in SUPPORTED_DIMENSIONS:
        if dim not in dim_breakdowns:
            continue
        dim_data = dim_breakdowns[dim]
        categories = sorted(dim_data.keys(), key=str)
        # Require at least 2 distinct categories for meaningful dimensional comparison
        if len(categories) < 2:
            continue

        dim_label = DIMENSION_LABELS.get(dim, dim.replace("_", " ").title())

        # Find top conversion volume category within dimension
        sorted_by_conv = sorted(
            categories,
            key=lambda c: (-dim_data[c].get("conversions", 0), str(c)),
        )
        top_cat = sorted_by_conv[0]
        top_cat_data = dim_data[top_cat]
        if top_cat_data.get("conversions", 0) > 0:
            raw_insights.append({
                "type": "dimensional",
                "title": f"Leading {dim_label} by Conversions: {top_cat}",
                "description": (
                    f"Within {dim_label.lower()}, '{top_cat}' led with {top_cat_data['conversions']} "
                    f"conversions (${top_cat_data.get('spend', 0.0):.2f} spend)."
                ),
                "metric": "conversions",
                "evidence": {
                    "dimension": dim,
                    "category": top_cat,
                    "conversions": top_cat_data["conversions"],
                    "spend": top_cat_data.get("spend", 0.0),
                },
            })

        # Find lowest CPA category within dimension (categories with conversions > 0)
        cpa_categories = [c for c in categories if dim_data[c].get("cpa") is not None]
        if len(cpa_categories) >= 2:
            sorted_by_cpa = sorted(
                cpa_categories,
                key=lambda c: (dim_data[c]["cpa"], str(c)),
            )
            best_cpa_cat = sorted_by_cpa[0]
            worst_cpa_cat = sorted_by_cpa[-1]

            if best_cpa_cat != worst_cpa_cat:
                best_data = dim_data[best_cpa_cat]
                raw_insights.append({
                    "type": "dimensional",
                    "title": f"Most Cost-Effective {dim_label}: {best_cpa_cat}",
                    "description": (
                        f"Within {dim_label.lower()}, '{best_cpa_cat}' achieved the lowest CPA at "
                        f"${best_data['cpa']:.2f} per conversion."
                    ),
                    "metric": "cpa",
                    "evidence": {
                        "dimension": dim,
                        "category": best_cpa_cat,
                        "cpa": best_data["cpa"],
                        "spend": best_data.get("spend", 0.0),
                        "conversions": best_data.get("conversions", 0),
                    },
                })

    # -------------------------------------------------------------------------
    # 6. Historical Time-Series Observations
    # -------------------------------------------------------------------------
    if ts_data.get("has_time_series") is True and ts_data.get("timeline"):
        timeline = ts_data["timeline"]
        if len(timeline) >= 2:
            first_day = timeline[0]
            last_day = timeline[-1]
            distinct_days = ts_data.get("distinct_dates_count", len(timeline))

            raw_insights.append({
                "type": "time_series",
                "title": f"Timeline Progression: {first_day['date']} to {last_day['date']}",
                "description": (
                    f"Across {distinct_days} observed dates between {first_day['date']} and {last_day['date']}, "
                    f"daily spend was ${first_day.get('spend', 0.0):.2f} initially and ${last_day.get('spend', 0.0):.2f} on the final date, "
                    f"with conversions shifting from {first_day.get('conversions', 0)} to {last_day.get('conversions', 0)}."
                ),
                "metric": "conversions",
                "evidence": {
                    "start_date": first_day["date"],
                    "start_spend": first_day.get("spend", 0.0),
                    "start_conversions": first_day.get("conversions", 0),
                    "end_date": last_day["date"],
                    "end_spend": last_day.get("spend", 0.0),
                    "end_conversions": last_day.get("conversions", 0),
                    "observed_dates_count": distinct_days,
                },
            })

            # Check peak conversion date if conversions > 0
            sorted_by_day_conv = sorted(
                timeline,
                key=lambda d: (-d.get("conversions", 0), str(d.get("date", ""))),
            )
            peak_day = sorted_by_day_conv[0]
            if peak_day.get("conversions", 0) > 0:
                raw_insights.append({
                    "type": "time_series",
                    "title": f"Peak Conversion Date: {peak_day['date']}",
                    "description": (
                        f"The highest daily conversion volume occurred on {peak_day['date']} "
                        f"with {peak_day['conversions']} conversions recorded (${peak_day.get('spend', 0.0):.2f} spend)."
                    ),
                    "metric": "conversions",
                    "evidence": {
                        "date": peak_day["date"],
                        "conversions": peak_day["conversions"],
                        "spend": peak_day.get("spend", 0.0),
                    },
                })

    # -------------------------------------------------------------------------
    # Format and Assign Deterministic Sequential IDs
    # -------------------------------------------------------------------------
    insights: List[Dict[str, Any]] = []
    seen_signatures = set()

    for idx, item in enumerate(raw_insights, 1):
        # Prevent any duplicate signature (type, title, metric)
        sig = (item["type"], item["title"], item["metric"])
        if sig in seen_signatures:
            continue
        seen_signatures.add(sig)

        formatted_item = {
            "id": f"insight-{len(insights) + 1:03d}",
            "type": item["type"],
            "title": item["title"],
            "description": item["description"],
            "metric": item["metric"],
            "evidence": item["evidence"],
        }
        insights.append(formatted_item)

    return insights
