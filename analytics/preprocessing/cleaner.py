import pandas as pd

def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Cleans raw campaign dataframe, handles nulls and whitespace."""
    cleaned = df.copy()
    cleaned.columns = [c.strip().lower().replace(" ", "_") for c in cleaned.columns]
    cleaned = cleaned.fillna({
        "impressions": 0,
        "clicks": 0,
        "spend": 0.0,
        "conversions": 0,
        "revenue": 0.0
    })
    return cleaned
