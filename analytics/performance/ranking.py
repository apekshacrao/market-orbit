import pandas as pd
from typing import Dict, Any, List

def rank_campaigns(df: pd.DataFrame, top_n: int = 5) -> Dict[str, List[Dict[str, Any]]]:
    """Ranks campaigns by ROAS and overall efficiency."""
    if df.empty or "campaign_name" not in df.columns:
        return {"top": [], "bottom": []}

    grouped = df.groupby("campaign_name").agg({
        "spend": "sum",
        "revenue": "sum",
        "conversions": "sum"
    }).reset_index()

    grouped["roas"] = grouped.apply(
        lambda r: (r["revenue"] / r["spend"]) if r["spend"] > 0 else 0.0, axis=1
    )

    sorted_df = grouped.sort_values(by="roas", ascending=False)
    top = sorted_df.head(top_n).to_dict(orient="records")
    bottom = sorted_df.tail(top_n).to_dict(orient="records")

    return {"top": top, "bottom": bottom}
