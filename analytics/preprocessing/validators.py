import pandas as pd
from typing import List, Dict, Any

REQUIRED_COLUMNS = ["campaign_name", "channel", "spend", "revenue"]

def validate_dataset(df: pd.DataFrame) -> Dict[str, Any]:
    """Validates that required columns exist and data types are valid."""
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    return {
        "is_valid": len(missing) == 0,
        "missing_columns": missing,
        "errors": [f"Missing required column: {c}" for c in missing]
    }
