import copy
from typing import List, Dict, Any, Union
import pandas as pd
import numpy as np


def clean_dataset(data: Union[List[Dict[str, Any]], pd.DataFrame]) -> pd.DataFrame:
    """
    Cleans raw campaign dataset, standardizes column headers, casts core types,
    and strictly preserves missing-value semantics for optional fields (revenue, date, demographics).
    Accepts either list[dict] or pd.DataFrame.
    """
    if data is None:
        raise ValueError("Input data cannot be None")

    if isinstance(data, list):
        if len(data) == 0:
            return pd.DataFrame()
        # Avoid modifying original input records by deep-copying
        records = copy.deepcopy(data)
        df = pd.DataFrame(records)
    elif isinstance(data, pd.DataFrame):
        if data.empty:
            return pd.DataFrame()
        df = data.copy()
    else:
        raise TypeError(
            f"Unsupported data type: {type(data).__name__}. Expected list[dict] or DataFrame."
        )

    # Normalize column names: strip, lowercase, replace spaces with underscores
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]

    # Required mandatory string columns: clean whitespace
    if "campaign_name" in df.columns:
        df["campaign_name"] = df["campaign_name"].astype(str).str.strip()
    if "channel" in df.columns:
        df["channel"] = df["channel"].astype(str).str.strip()

    # Core performance metrics: default missing to 0 / 0.0
    if "spend" in df.columns:
        df["spend"] = pd.to_numeric(df["spend"], errors="coerce").fillna(0.0)
    if "conversions" in df.columns:
        df["conversions"] = pd.to_numeric(df["conversions"], errors="coerce").fillna(0).astype(int)
    if "impressions" in df.columns:
        df["impressions"] = pd.to_numeric(df["impressions"], errors="coerce").fillna(0).astype(int)
    if "clicks" in df.columns:
        df["clicks"] = pd.to_numeric(df["clicks"], errors="coerce").fillna(0).astype(int)

    # CRITICAL: Revenue must NOT be filled with 0.0 when missing!
    # Nullable revenue is preserved as NaN / None
    if "revenue" in df.columns:
        df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce")
    else:
        # If column was entirely omitted in input, create it with NaN to maintain schema consistency
        df["revenue"] = np.nan

    # Optional date: preserve string or None, strip whitespace
    if "date" in df.columns:
        df["date"] = df["date"].apply(
            lambda v: str(v).strip()
            if pd.notnull(v) and str(v).strip() != "" and str(v).lower() not in ("nan", "none")
            else None
        )
    else:
        df["date"] = None

    # Optional demographic fields: preserve strings or None
    for demo_col in ["location", "age_group", "customer_segment", "device"]:
        if demo_col in df.columns:
            df[demo_col] = df[demo_col].apply(
                lambda v: str(v).strip()
                if pd.notnull(v) and str(v).strip() != "" and str(v).lower() not in ("nan", "none")
                else None
            )
        else:
            df[demo_col] = None

    return df
