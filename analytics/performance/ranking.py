import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional


def _aggregate_campaign(name: str, group: pd.DataFrame) -> Dict[str, Any]:
    """
    Aggregates metrics for a single campaign group following Market Orbit data contract rules.
    Preserves missing revenue semantics and avoids division-by-zero errors.
    """
    # 1. Spend: numeric sum, default missing to 0.0
    if "spend" in group.columns:
        spend = round(float(pd.to_numeric(group["spend"], errors="coerce").fillna(0.0).sum()), 2)
    else:
        spend = 0.0

    # 2. Conversions: integer sum, default missing to 0
    if "conversions" in group.columns:
        conversions = int(pd.to_numeric(group["conversions"], errors="coerce").fillna(0).sum())
    else:
        conversions = 0

    # 3. Clicks: integer sum, default missing to 0
    if "clicks" in group.columns:
        clicks = int(pd.to_numeric(group["clicks"], errors="coerce").fillna(0).sum())
    else:
        clicks = 0

    # 4. Impressions: integer sum, default missing to 0
    if "impressions" in group.columns:
        impressions = int(pd.to_numeric(group["impressions"], errors="coerce").fillna(0).sum())
    else:
        impressions = 0

    # 5. Revenue aggregation
    # Strict missing revenue rules:
    # - If column missing or all rows NaN/None -> None
    # - If partially missing (any row NaN/None) -> None (incomplete revenue convention)
    # - If all rows present and numeric -> round(sum, 2)
    revenue: Optional[float] = None
    if "revenue" in group.columns:
        rev_series = group["revenue"]
        if rev_series.isna().all():
            revenue = None
        elif rev_series.isna().any():
            revenue = None
        else:
            rev_num = pd.to_numeric(rev_series, errors="coerce")
            if rev_num.isna().any():
                revenue = None
            else:
                revenue = round(float(rev_num.sum()), 2)

    # 6. Derived KPIs
    # CPA: spend / conversions (undefined when conversions == 0)
    cpa: Optional[float] = (
        round(float(spend / conversions), 2) if conversions > 0 else None
    )

    # CPC: spend / clicks (undefined when clicks == 0)
    cpc: Optional[float] = (
        round(float(spend / clicks), 2) if clicks > 0 else None
    )

    # CTR: clicks / impressions * 100 (undefined when impressions == 0)
    ctr: Optional[float] = (
        round(float((clicks / impressions) * 100.0), 2) if impressions > 0 else None
    )

    # Conversion Rate: conversions / clicks * 100 (undefined when clicks == 0)
    conversion_rate: Optional[float] = (
        round(float((conversions / clicks) * 100.0), 2) if clicks > 0 else None
    )

    # ROAS: revenue / spend (undefined when revenue is None or spend == 0)
    roas: Optional[float] = (
        round(float(revenue / spend), 2)
        if revenue is not None and spend > 0.0
        else None
    )

    # ROI: (revenue - spend) / spend * 100 (undefined when revenue is None or spend == 0)
    roi: Optional[float] = (
        round(float(((revenue - spend) / spend) * 100.0), 2)
        if revenue is not None and spend > 0.0
        else None
    )

    return {
        "campaign_name": name,
        "spend": spend,
        "conversions": conversions,
        "clicks": clicks,
        "impressions": impressions,
        "revenue": revenue,
        "cpa": cpa,
        "cpc": cpc,
        "ctr": ctr,
        "conversion_rate": conversion_rate,
        "roas": roas,
        "roi": roi,
    }


def aggregate_campaigns(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Groups records by campaign_name and aggregates core and derived marketing metrics.
    Strictly preserves None for missing/untracked revenue and avoids division by zero.
    Returns campaigns sorted alphabetically by campaign_name.
    """
    if df is None or df.empty or "campaign_name" not in df.columns:
        return []

    valid_mask = (
        df["campaign_name"].notna()
        & (df["campaign_name"].astype(str).str.strip() != "")
        & (df["campaign_name"].astype(str).str.lower() != "nan")
    )
    filtered_df = df[valid_mask].copy()
    if filtered_df.empty:
        return []

    filtered_df["campaign_name"] = filtered_df["campaign_name"].astype(str).str.strip()

    campaigns = [
        _aggregate_campaign(name, group)
        for name, group in filtered_df.groupby("campaign_name", sort=False)
    ]

    return sorted(campaigns, key=lambda c: str(c["campaign_name"]))


def rank_campaigns(
    df: pd.DataFrame, top_n: int = 5
) -> Dict[str, Any]:
    """
    Ranks campaigns across multiple marketing performance dimensions.

    Returns:
        Dict with:
        - 'by_roas': top and bottom campaigns with valid ROAS.
        - 'by_cpa': most efficient (lowest CPA) and least efficient (highest CPA) campaigns with valid CPA.
        - 'by_conversions': top and bottom campaigns by conversion volume.
        - 'summary': evaluation summary counts.
        - 'top': backward-compatible top campaigns.
        - 'bottom': backward-compatible bottom campaigns.
    """
    empty_result = {
        "top": [],
        "bottom": [],
        "by_roas": {"top": [], "bottom": []},
        "by_cpa": {"top": [], "bottom": []},
        "by_conversions": {"top": [], "bottom": []},
        "summary": {
            "total_campaigns_evaluated": 0,
            "total_campaigns": 0,
            "campaigns_with_roas": 0,
            "campaigns_with_cpa": 0,
        },
    }

    if df is None or df.empty or "campaign_name" not in df.columns or top_n <= 0:
        return empty_result

    campaigns = aggregate_campaigns(df)
    if not campaigns:
        return empty_result

    total_evaluated = len(campaigns)

    # 1. by_roas: strictly filter to campaigns with valid ROAS
    roas_campaigns = [c for c in campaigns if c["roas"] is not None]
    sorted_roas = sorted(
        roas_campaigns,
        key=lambda c: (-c["roas"], str(c["campaign_name"])),
    )
    by_roas_top = sorted_roas[:top_n]
    by_roas_bottom = sorted_roas[-top_n:] if sorted_roas else []

    # 2. by_cpa: strictly filter to campaigns with valid CPA (conversions > 0)
    cpa_campaigns = [c for c in campaigns if c["cpa"] is not None]
    sorted_cpa = sorted(
        cpa_campaigns,
        key=lambda c: (c["cpa"], str(c["campaign_name"])),
    )
    by_cpa_top = sorted_cpa[:top_n]
    by_cpa_bottom = sorted_cpa[-top_n:] if sorted_cpa else []

    # 3. by_conversions: rank by conversion volume (descending)
    sorted_conv = sorted(
        campaigns,
        key=lambda c: (-c["conversions"], str(c["campaign_name"])),
    )
    by_conv_top = sorted_conv[:top_n]
    by_conv_bottom = sorted_conv[-top_n:] if sorted_conv else []

    # 4. Backward compatibility for top-level 'top' and 'bottom':
    # When valid ROAS campaigns exist, match by_roas.
    # When no campaigns have valid ROAS (e.g. untracked revenue), fallback to
    # CPA efficiency / conversion volume ranking per Analytics Data Contract.
    if roas_campaigns:
        compat_top = by_roas_top
        compat_bottom = by_roas_bottom
    elif cpa_campaigns:
        sorted_fallback = sorted(
            campaigns,
            key=lambda c: (
                c["cpa"] if c["cpa"] is not None else float("inf"),
                -c["conversions"],
                str(c["campaign_name"]),
            ),
        )
        compat_top = sorted_fallback[:top_n]
        compat_bottom = sorted_fallback[-top_n:] if sorted_fallback else []
    else:
        sorted_fallback = sorted(
            campaigns,
            key=lambda c: (
                -c["conversions"],
                -c["spend"],
                str(c["campaign_name"]),
            ),
        )
        compat_top = sorted_fallback[:top_n]
        compat_bottom = sorted_fallback[-top_n:] if sorted_fallback else []

    return {
        "top": compat_top,
        "bottom": compat_bottom,
        "by_roas": {"top": by_roas_top, "bottom": by_roas_bottom},
        "by_cpa": {"top": by_cpa_top, "bottom": by_cpa_bottom},
        "by_conversions": {"top": by_conv_top, "bottom": by_conv_bottom},
        "summary": {
            "total_campaigns_evaluated": total_evaluated,
            "total_campaigns": total_evaluated,
            "campaigns_with_roas": len(roas_campaigns),
            "campaigns_with_cpa": len(cpa_campaigns),
        },
    }

