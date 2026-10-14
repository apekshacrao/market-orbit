"""
Campaign performance cohort classification for Market Orbit analytics.

Implements deterministic quadrant-based cohort classification across marketing campaigns
based on conversion volume and CPA efficiency relative to empirical dataset medians and
portfolio CPA benchmarks.
"""

from typing import Dict, Any, List, Optional
import pandas as pd

from analytics.performance.ranking import aggregate_campaigns
from analytics.segmentation.portfolio import profile_segment_portfolio


def classify_campaign_cohorts(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Classifies marketing campaigns into four deterministic performance cohorts:
    - 'scale_ready': conversions >= median conversions, valid CPA <= portfolio CPA
    - 'volume_driver': conversions >= median conversions, valid CPA > portfolio CPA
    - 'efficiency_niche': conversions < median conversions, valid CPA <= portfolio CPA
    - 'budget_drain': conversions < median conversions with valid CPA > portfolio CPA,
                      OR zero conversions (positive spend waste or zero-spend inactive)

    Args:
        df: Pandas DataFrame containing campaign records with mandatory 'campaign_name',
            'spend', 'conversions', and optional 'revenue', 'clicks', 'impressions'.

    Returns:
        Dict with:
        - 'summary': count summary across total campaigns and individual cohorts.
        - 'cohorts': list of classified campaign objects partitioned into four cohorts:
                     'scale_ready', 'volume_driver', 'efficiency_niche', 'budget_drain'.
    """
    empty_result = {
        "summary": {
            "total_campaigns": 0,
            "scale_ready_count": 0,
            "volume_driver_count": 0,
            "efficiency_niche_count": 0,
            "budget_drain_count": 0,
        },
        "cohorts": {
            "scale_ready": [],
            "volume_driver": [],
            "efficiency_niche": [],
            "budget_drain": [],
        },
    }

    if df is None or df.empty or "campaign_name" not in df.columns:
        return empty_result

    # Reuse established campaign aggregation logic from ranking module
    raw_campaigns = aggregate_campaigns(df)
    if not raw_campaigns:
        return empty_result

    total_campaigns = len(raw_campaigns)

    # 1. Calculate Portfolio CPA (total spend / total conversions)
    total_spend = sum(c["spend"] for c in raw_campaigns)
    total_conversions = sum(c["conversions"] for c in raw_campaigns)

    portfolio_cpa: Optional[float] = (
        round(float(total_spend / total_conversions), 2)
        if total_conversions > 0
        else None
    )

    # 2. Calculate Standard Statistical Median Campaign Conversion Count
    sorted_convs = sorted(c["conversions"] for c in raw_campaigns)
    n = len(sorted_convs)
    if n % 2 == 1:
        median_conversions = float(sorted_convs[n // 2])
    else:
        median_conversions = float(
            (sorted_convs[n // 2 - 1] + sorted_convs[n // 2]) / 2.0
        )

    # 3. Classify Each Campaign into Exactly One Cohort
    cohorts: Dict[str, List[Dict[str, Any]]] = {
        "scale_ready": [],
        "volume_driver": [],
        "efficiency_niche": [],
        "budget_drain": [],
    }

    for c in raw_campaigns:
        entry = {
            "campaign_name": c["campaign_name"],
            "spend": c["spend"],
            "conversions": c["conversions"],
            "cpa": c["cpa"],
            "roas": c["roas"],
        }

        conversions = c["conversions"]
        cpa = c["cpa"]

        # Precedence Rule 1: Zero-conversion campaigns have undefined CPA.
        # Under definition 4, positive spend with zero conversions enters budget_drain.
        # Zero-spend zero-conversion campaigns also have undefined CPA and zero volume,
        # and are deterministically assigned to budget_drain.
        if conversions == 0 or cpa is None or portfolio_cpa is None:
            cohorts["budget_drain"].append(entry)
            continue

        # Quadrant classification for campaigns with valid CPA (conversions > 0)
        is_high_volume = conversions >= median_conversions
        is_cost_efficient = cpa <= portfolio_cpa

        if is_high_volume and is_cost_efficient:
            cohorts["scale_ready"].append(entry)
        elif is_high_volume and not is_cost_efficient:
            cohorts["volume_driver"].append(entry)
        elif not is_high_volume and is_cost_efficient:
            cohorts["efficiency_niche"].append(entry)
        else:
            cohorts["budget_drain"].append(entry)

    # 4. Deterministic Sorting Within Each Cohort
    # Scale ready: sorted by CPA ascending (most cost-effective first), tie-breaker campaign_name
    cohorts["scale_ready"] = sorted(
        cohorts["scale_ready"],
        key=lambda item: (item["cpa"] if item["cpa"] is not None else float("inf"), str(item["campaign_name"])),
    )
    # Volume driver: sorted by conversions descending (highest volume first), tie-breaker campaign_name
    cohorts["volume_driver"] = sorted(
        cohorts["volume_driver"],
        key=lambda item: (-item["conversions"], str(item["campaign_name"])),
    )
    # Efficiency niche: sorted by CPA ascending (lowest CPA first), tie-breaker campaign_name
    cohorts["efficiency_niche"] = sorted(
        cohorts["efficiency_niche"],
        key=lambda item: (item["cpa"] if item["cpa"] is not None else float("inf"), str(item["campaign_name"])),
    )
    # Budget drain: sorted by spend descending (highest wasted spend first), tie-breaker campaign_name
    cohorts["budget_drain"] = sorted(
        cohorts["budget_drain"],
        key=lambda item: (-item["spend"], str(item["campaign_name"])),
    )

    summary = {
        "total_campaigns": total_campaigns,
        "scale_ready_count": len(cohorts["scale_ready"]),
        "volume_driver_count": len(cohorts["volume_driver"]),
        "efficiency_niche_count": len(cohorts["efficiency_niche"]),
        "budget_drain_count": len(cohorts["budget_drain"]),
    }

    return {
        "summary": summary,
        "cohorts": cohorts,
    }
