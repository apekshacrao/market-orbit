import pandas as pd
from typing import Dict, Any, Optional


def calculate_kpis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculates marketing performance KPIs and aggregate metrics based on the Analytics Data Contract.

    Handles missing revenue, zero denominators, percentage scaling, and provides both
    canonical keys and backward-compatible aliases.
    """
    if df is None or df.empty:
        return {
            "total_spend": 0.0,
            "total_conversions": 0,
            "total_clicks": 0,
            "total_impressions": 0,
            "total_revenue": None,
            "cpa": 0.0,
            "avg_cpa": 0.0,
            "cpc": 0.0,
            "avg_cpc": 0.0,
            "conversion_rate": 0.0,
            "avg_conversion_rate": 0.0,
            "ctr": 0.0,
            "roas": None,
            "overall_roas": None,
            "roi": None,
        }

    # Core aggregate metrics
    total_spend: float = round(
        float(df["spend"].dropna().sum()) if "spend" in df.columns else 0.0, 2
    )
    total_conversions: int = int(
        df["conversions"].dropna().sum() if "conversions" in df.columns else 0
    )
    total_clicks: int = int(
        df["clicks"].dropna().sum() if "clicks" in df.columns else 0
    )
    total_impressions: int = int(
        df["impressions"].dropna().sum() if "impressions" in df.columns else 0
    )

    # Revenue availability check: column must exist and have at least one non-null value
    has_revenue: bool = "revenue" in df.columns and bool(df["revenue"].notna().any())

    total_revenue: Optional[float] = None
    roas: Optional[float] = None
    roi: Optional[float] = None

    if has_revenue:
        total_revenue = round(float(df["revenue"].dropna().sum()), 2)
        if total_spend > 0.0:
            roas = round(float(total_revenue / total_spend), 2)
            roi = round(float(((total_revenue - total_spend) / total_spend) * 100.0), 2)
        else:
            roas = 0.0
            roi = 0.0

    # Derived non-revenue KPIs
    cpa: float = (
        round(float(total_spend / total_conversions), 2)
        if total_conversions > 0
        else 0.0
    )
    cpc: float = (
        round(float(total_spend / total_clicks), 2)
        if total_clicks > 0
        else 0.0
    )
    conversion_rate: float = (
        round(float((total_conversions / total_clicks) * 100.0), 2)
        if total_clicks > 0
        else 0.0
    )
    ctr: float = (
        round(float((total_clicks / total_impressions) * 100.0), 2)
        if total_impressions > 0
        else 0.0
    )

    return {
        # Core aggregates
        "total_spend": total_spend,
        "total_conversions": total_conversions,
        "total_clicks": total_clicks,
        "total_impressions": total_impressions,
        "total_revenue": total_revenue,
        # Canonical KPI metrics
        "cpa": cpa,
        "cpc": cpc,
        "conversion_rate": conversion_rate,
        "ctr": ctr,
        "roas": roas,
        "roi": roi,
        # Backward-compatible aliases
        "avg_cpa": cpa,
        "avg_cpc": cpc,
        "avg_conversion_rate": conversion_rate,
        "overall_roas": roas,
    }
