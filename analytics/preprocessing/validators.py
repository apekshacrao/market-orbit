import pandas as pd
from typing import List, Dict, Any, Union
from pydantic import ValidationError

from analytics.schemas.campaign_schema import CampaignInputRecord

MANDATORY_COLUMNS = ["campaign_name", "channel", "spend", "conversions"]
OPTIONAL_COLUMNS = [
    "date",
    "revenue",
    "impressions",
    "clicks",
    "location",
    "age_group",
    "customer_segment",
    "device",
]


def validate_dataset(
    data: Union[List[Dict[str, Any]], pd.DataFrame]
) -> Dict[str, Any]:
    """
    Validates campaign dataset against the Analytics Data Contract.
    Accepts either a list of dictionary records or a Pandas DataFrame.
    """
    errors: List[str] = []
    missing_columns: List[str] = []
    validated_records: List[CampaignInputRecord] = []

    if data is None:
        return {
            "is_valid": False,
            "missing_columns": MANDATORY_COLUMNS,
            "errors": ["Input data is None"],
            "validated_records": [],
        }

    # If DataFrame, check column presence first
    if isinstance(data, pd.DataFrame):
        if data.empty:
            return {
                "is_valid": False,
                "missing_columns": [],
                "errors": ["Dataset contains no records"],
                "validated_records": [],
            }

        # Normalize column names for check
        df_cols = [str(c).strip().lower().replace(" ", "_") for c in data.columns]
        missing_columns = [col for col in MANDATORY_COLUMNS if col not in df_cols]

        if missing_columns:
            for col in missing_columns:
                errors.append(f"Missing mandatory column: {col}")
            return {
                "is_valid": False,
                "missing_columns": missing_columns,
                "errors": errors,
                "validated_records": [],
            }

        # Convert DataFrame to list of dicts for row-level validation
        df_clean = data.copy()
        df_clean.columns = df_cols
        # Replace NaN with None so Pydantic receives None
        records = df_clean.where(pd.notnull(df_clean), None).to_dict(orient="records")
    elif isinstance(data, list):
        if len(data) == 0:
            return {
                "is_valid": False,
                "missing_columns": [],
                "errors": ["Dataset contains no records"],
                "validated_records": [],
            }
        records = data
    else:
        return {
            "is_valid": False,
            "missing_columns": [],
            "errors": [f"Unsupported input type: {type(data).__name__}. Expected list[dict] or DataFrame"],
            "validated_records": [],
        }

    # Validate each row against CampaignInputRecord
    for idx, row in enumerate(records):
        row_clean = {
            str(k).strip().lower().replace(" ", "_"): v
            for k, v in row.items()
        }

        # Check for mandatory keys in row
        row_missing = [col for col in MANDATORY_COLUMNS if col not in row_clean or row_clean[col] is None]
        if row_missing:
            for col in row_missing:
                errors.append(f"Row {idx + 1}: Missing mandatory field '{col}'")
            continue

        try:
            record_obj = CampaignInputRecord(**row_clean)
            validated_records.append(record_obj)
        except ValidationError as e:
            for err in e.errors():
                field = ".".join(str(loc) for loc in err["loc"])
                msg = err["msg"]
                errors.append(f"Row {idx + 1} field '{field}': {msg}")
        except Exception as ex:
            errors.append(f"Row {idx + 1}: Unexpected error: {str(ex)}")

    return {
        "is_valid": len(errors) == 0,
        "missing_columns": missing_columns,
        "errors": errors,
        "validated_records": validated_records if len(errors) == 0 else [],
    }
