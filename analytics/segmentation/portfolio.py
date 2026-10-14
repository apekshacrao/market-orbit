"""
Segment portfolio profiling and efficiency indexing for Market Orbit analytics.

Calculates descriptive portfolio-share metrics, conversion-efficiency ratios,
and CPA index metrics across marketer-supplied customer_segment dimensions.
"""

from typing import Dict, Any, Optional
import pandas as pd
import numpy as np


def profile_segment_portfolio(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes descriptive segment portfolio shares and relative efficiency indices
    across available customer_segment categories.

    Args:
        df: Pandas DataFrame containing campaign records with optional 'customer_segment',
            'spend', 'conversions', and 'revenue'.

    Returns:
        Dict with:
        - 'is_available': bool indicating whether usable customer segments exist.
        - 'total_segments': int count of usable customer segments.
        - 'segments': deterministic mapping of segment name to profile metrics:
            - 'spend': float
            - 'conversions': int
            - 'revenue': Optional[float]
            - 'cpa': Optional[float]
            - 'roas': Optional[float]
            - 'share_of_spend': Optional[float] (% of total portfolio spend)
            - 'share_of_conversions': Optional[float] (% of total portfolio conversions)
            - 'share_of_revenue': Optional[float] (% of total portfolio revenue)
            - 'conversion_efficiency_ratio': Optional[float] (conversion share / spend share)
            - 'cpa_index': Optional[float] (segment CPA / portfolio CPA * 100)
    """
    unavailable_result = {
        "is_available": False,
        "total_segments": 0,
        "segments": {},
    }

    if df is None or df.empty or "customer_segment" not in df.columns:
        return unavailable_result

    # 1. Clean and filter segment labels using established sentinel rules
    # Exclude None, whitespace, "nan", "none", "nat", "null"
    seg_series = df["customer_segment"].apply(
        lambda v: str(v).strip()
        if pd.notnull(v) and str(v).strip() != "" and str(v).strip().lower() not in ("nan", "none", "nat", "null")
        else None
    )

    usable_mask = seg_series.notna()
    if not usable_mask.any():
        return unavailable_result

    # 2. Portfolio Denominators across the full dataset (ensures denominator consistency)
    total_spend = (
        round(float(pd.to_numeric(df["spend"], errors="coerce").fillna(0.0).sum()), 2)
        if "spend" in df.columns
        else 0.0
    )
    total_conversions = (
        int(pd.to_numeric(df["conversions"], errors="coerce").fillna(0).sum())
        if "conversions" in df.columns
        else 0
    )

    portfolio_cpa: Optional[float] = (
        round(float(total_spend / total_conversions), 2)
        if total_conversions > 0
        else None
    )

    # Portfolio revenue completeness: must be present and complete across all rows
    portfolio_revenue: Optional[float] = None
    if "revenue" in df.columns:
        rev_series = df["revenue"]
        if not rev_series.isna().all() and not rev_series.isna().any():
            rev_num = pd.to_numeric(rev_series, errors="coerce")
            if not rev_num.isna().any():
                portfolio_revenue = round(float(rev_num.sum()), 2)

    # 3. Aggregate each segment group
    df_usable = df[usable_mask].copy()
    df_usable["_clean_segment"] = seg_series[usable_mask]

    segments_output: Dict[str, Dict[str, Any]] = {}
    sorted_segment_names = sorted(df_usable["_clean_segment"].unique(), key=str)

    for seg_name in sorted_segment_names:
        seg_group = df_usable[df_usable["_clean_segment"] == seg_name]

        # Core segment metrics
        seg_spend = (
            round(float(pd.to_numeric(seg_group["spend"], errors="coerce").fillna(0.0).sum()), 2)
            if "spend" in seg_group.columns
            else 0.0
        )
        seg_conversions = (
            int(pd.to_numeric(seg_group["conversions"], errors="coerce").fillna(0).sum())
            if "conversions" in seg_group.columns
            else 0
        )

        # Segment revenue completeness
        seg_revenue: Optional[float] = None
        if "revenue" in seg_group.columns:
            s_rev_series = seg_group["revenue"]
            if not s_rev_series.isna().all() and not s_rev_series.isna().any():
                s_rev_num = pd.to_numeric(s_rev_series, errors="coerce")
                if not s_rev_num.isna().any():
                    seg_revenue = round(float(s_rev_num.sum()), 2)

        # Derived segment KPIs
        seg_cpa: Optional[float] = (
            round(float(seg_spend / seg_conversions), 2)
            if seg_conversions > 0
            else None
        )
        seg_roas: Optional[float] = (
            round(float(seg_revenue / seg_spend), 2)
            if seg_revenue is not None and seg_spend > 0.0
            else None
        )

        # 4. Portfolio Share Metrics
        share_of_spend: Optional[float] = (
            round(float((seg_spend / total_spend) * 100.0), 2)
            if total_spend > 0.0
            else None
        )
        share_of_conversions: Optional[float] = (
            round(float((seg_conversions / total_conversions) * 100.0), 2)
            if total_conversions > 0
            else None
        )

        # Share of revenue: only when complete revenue tracked and total revenue > 0
        share_of_revenue: Optional[float] = None
        if (
            seg_revenue is not None
            and portfolio_revenue is not None
            and portfolio_revenue > 0.0
        ):
            share_of_revenue = round(
                float((seg_revenue / portfolio_revenue) * 100.0), 2
            )

        # 5. Efficiency Indices
        conversion_efficiency_ratio: Optional[float] = None
        if (
            share_of_spend is not None
            and share_of_spend > 0.0
            and share_of_conversions is not None
        ):
            conversion_efficiency_ratio = round(
                float(share_of_conversions / share_of_spend), 2
            )

        cpa_index: Optional[float] = None
        if (
            seg_cpa is not None
            and portfolio_cpa is not None
            and portfolio_cpa > 0.0
        ):
            cpa_index = round(float((seg_cpa / portfolio_cpa) * 100.0), 2)

        segments_output[seg_name] = {
            "spend": seg_spend,
            "conversions": seg_conversions,
            "revenue": seg_revenue,
            "cpa": seg_cpa,
            "roas": seg_roas,
            "share_of_spend": share_of_spend,
            "share_of_conversions": share_of_conversions,
            "share_of_revenue": share_of_revenue,
            "conversion_efficiency_ratio": conversion_efficiency_ratio,
            "cpa_index": cpa_index,
        }

    return {
        "is_available": True,
        "total_segments": len(segments_output),
        "segments": segments_output,
    }
