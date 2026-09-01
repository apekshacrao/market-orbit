import pandas as pd
from typing import Dict, Any

def analyze_trends(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyzes performance trends across channels and segments."""
    channel_trends = {}
    if "channel" in df.columns:
        channel_trends = df.groupby("channel").agg({
            "spend": "sum",
            "revenue": "sum",
            "conversions": "sum"
        }).to_dict(orient="index")

    return {
        "channel_breakdown": channel_trends,
    }
