import pandas as pd
from typing import Dict, Any

def calculate_kpis(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculates marketing KPIs: ROAS, CPA, CPC, CTR, Conversion Rate."""
    total_spend = df["spend"].sum() if "spend" in df else 0.0
    total_revenue = df["revenue"].sum() if "revenue" in df else 0.0
    total_clicks = df["clicks"].sum() if "clicks" in df else 0
    total_impressions = df["impressions"].sum() if "impressions" in df else 0
    total_conversions = df["conversions"].sum() if "conversions" in df else 0

    return {
        "total_spend": float(total_spend),
        "total_revenue": float(total_revenue),
        "overall_roas": float(total_revenue / total_spend) if total_spend > 0 else 0.0,
        "ctr": float(total_clicks / total_impressions) if total_impressions > 0 else 0.0,
        "avg_cpc": float(total_spend / total_clicks) if total_clicks > 0 else 0.0,
        "avg_cpa": float(total_spend / total_conversions) if total_conversions > 0 else 0.0,
        "conversion_rate": float(total_conversions / total_clicks) if total_clicks > 0 else 0.0,
    }
