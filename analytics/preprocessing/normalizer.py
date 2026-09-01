import pandas as pd

def normalize_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Ensures numeric metric columns are correctly cast."""
    norm = df.copy()
    numeric_cols = ["impressions", "clicks", "spend", "conversions", "revenue"]
    for col in numeric_cols:
        if col in norm.columns:
            norm[col] = pd.to_numeric(norm[col], errors="coerce").fillna(0)
    return norm
