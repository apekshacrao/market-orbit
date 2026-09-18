from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict


class CampaignInputRecord(BaseModel):
    """
    Validated campaign input record schema.
    Supports mandatory core performance metrics and nullable optional dimensions.
    """
    model_config = ConfigDict(extra="ignore")

    # Mandatory core fields
    campaign_name: str = Field(..., description="Name or identifier of the campaign")
    channel: str = Field(..., description="Marketing channel or platform")
    spend: float = Field(..., ge=0.0, description="Total campaign spend in USD (must be >= 0.0)")
    conversions: int = Field(..., ge=0, description="Total conversion count treated as leads (must be >= 0)")

    # Optional performance metrics
    impressions: Optional[int] = Field(default=0, ge=0, description="Total ad impressions (must be >= 0)")
    clicks: Optional[int] = Field(default=0, ge=0, description="Total link clicks (must be >= 0)")
    revenue: Optional[float] = Field(default=None, ge=0.0, description="Attributed revenue in USD (None if untracked, >= 0.0 if tracked)")

    # Optional date and demographic dimensions
    date: Optional[str] = Field(default=None, description="Campaign record date in YYYY-MM-DD format")
    location: Optional[str] = Field(default=None, description="Geographic location or region")
    age_group: Optional[str] = Field(default=None, description="Target age bracket")
    customer_segment: Optional[str] = Field(default=None, description="Target customer cohort/segment")
    device: Optional[str] = Field(default=None, description="Device category")

    @field_validator("campaign_name", "channel")
    @classmethod
    def validate_non_empty_string(cls, v: str, info) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError(f"'{info.field_name}' must be a non-empty string")
        return v.strip()

    @field_validator("date")
    @classmethod
    def validate_date_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        if isinstance(v, str):
            v_clean = v.strip()
            if not v_clean:
                return None
            try:
                datetime.strptime(v_clean, "%Y-%m-%d")
                return v_clean
            except ValueError:
                raise ValueError("Date must be a valid calendar date in 'YYYY-MM-DD' format")
        raise ValueError("Date must be a string in 'YYYY-MM-DD' format")

    @field_validator("location", "age_group", "customer_segment", "device")
    @classmethod
    def clean_optional_strings(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        if isinstance(v, str):
            v_clean = v.strip()
            return v_clean if v_clean else None
        return str(v)
