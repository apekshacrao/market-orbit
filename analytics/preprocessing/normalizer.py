import pandas as pd


def normalize_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensures numeric metric columns are correctly cast while strictly preserving null revenue.
    Does NOT convert missing revenue to 0.0.
    """
    if df.empty:
        return df

    norm = df.copy()

    # Core integer metrics cast to integer with fillna(0)
    for col in ["impressions", "clicks", "conversions"]:
        if col in norm.columns:
            norm[col] = pd.to_numeric(norm[col], errors="coerce").fillna(0).astype(int)

    if "spend" in norm.columns:
        norm["spend"] = pd.to_numeric(norm["spend"], errors="coerce").fillna(0.0).astype(float)

    # CRITICAL: Revenue must preserve NaN if untracked / null (do not fillna with 0)
    if "revenue" in norm.columns:
        norm["revenue"] = pd.to_numeric(norm["revenue"], errors="coerce")

    return norm
