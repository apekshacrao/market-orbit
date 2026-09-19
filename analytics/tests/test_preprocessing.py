import copy
import pytest
import pandas as pd
import numpy as np
from pydantic import ValidationError

from analytics.schemas.campaign_schema import CampaignInputRecord
from analytics.preprocessing.validators import validate_dataset
from analytics.preprocessing.cleaner import clean_dataset
from analytics.preprocessing.normalizer import normalize_metrics


# 1. Valid record with all fields
def test_valid_record_all_fields():
    record = {
        "campaign_name": "Summer Sale 2026",
        "channel": "Google Ads",
        "spend": 1200.50,
        "conversions": 85,
        "impressions": 50000,
        "clicks": 2500,
        "revenue": 4500.00,
        "date": "2026-06-01",
        "location": "North America",
        "age_group": "25-34",
        "customer_segment": "High Intent",
        "device": "Mobile",
    }
    model = CampaignInputRecord(**record)
    assert model.campaign_name == "Summer Sale 2026"
    assert model.spend == 1200.50
    assert model.conversions == 85
    assert model.revenue == 4500.00
    assert model.date == "2026-06-01"
    assert model.location == "North America"

    val_res = validate_dataset([record])
    assert val_res["is_valid"] is True
    assert len(val_res["validated_records"]) == 1


# 2. Valid record without revenue
def test_valid_record_without_revenue():
    record = {
        "campaign_name": "Lead Gen Campaign",
        "channel": "LinkedIn",
        "spend": 800.0,
        "conversions": 40,
    }
    model = CampaignInputRecord(**record)
    assert model.revenue is None

    val_res = validate_dataset([record])
    assert val_res["is_valid"] is True
    assert val_res["validated_records"][0].revenue is None

    df = clean_dataset([record])
    assert "revenue" in df.columns
    assert pd.isna(df["revenue"].iloc[0])


# 3. Valid record without demographic fields
def test_valid_record_without_demographics():
    record = {
        "campaign_name": "Brand Campaign",
        "channel": "Meta Ads",
        "spend": 500.0,
        "conversions": 20,
        "revenue": 1000.0,
        "date": "2026-06-02",
    }
    model = CampaignInputRecord(**record)
    assert model.location is None
    assert model.age_group is None
    assert model.customer_segment is None
    assert model.device is None

    df = clean_dataset([record])
    assert df["location"].iloc[0] is None
    assert df["device"].iloc[0] is None


# 4. Valid record without date
def test_valid_record_without_date():
    record = {
        "campaign_name": "Always-on Retargeting",
        "channel": "Meta Ads",
        "spend": 300.0,
        "conversions": 15,
    }
    model = CampaignInputRecord(**record)
    assert model.date is None

    val_res = validate_dataset([record])
    assert val_res["is_valid"] is True

    df = clean_dataset([record])
    assert df["date"].iloc[0] is None


# 5. Missing mandatory field
def test_missing_mandatory_field():
    record = {
        "campaign_name": "Incomplete Campaign",
        "spend": 500.0,
        "conversions": 10,
    }
    with pytest.raises(ValidationError):
        CampaignInputRecord(**record)

    val_res = validate_dataset([record])
    assert val_res["is_valid"] is False
    assert any("channel" in err for err in val_res["errors"])


# 6. Negative spend
def test_negative_spend():
    record = {
        "campaign_name": "Bad Spend",
        "channel": "Google Ads",
        "spend": -100.0,
        "conversions": 5,
    }
    with pytest.raises(ValidationError) as exc:
        CampaignInputRecord(**record)
    assert "greater than or equal to 0" in str(exc.value)

    val_res = validate_dataset([record])
    assert val_res["is_valid"] is False
    assert any("spend" in err for err in val_res["errors"])


# 7. Negative conversions
def test_negative_conversions():
    record = {
        "campaign_name": "Bad Conversions",
        "channel": "Google Ads",
        "spend": 100.0,
        "conversions": -5,
    }
    with pytest.raises(ValidationError) as exc:
        CampaignInputRecord(**record)
    assert "greater than or equal to 0" in str(exc.value)

    val_res = validate_dataset([record])
    assert val_res["is_valid"] is False
    assert any("conversions" in err for err in val_res["errors"])


# 8. Invalid date format
def test_invalid_date_format():
    record = {
        "campaign_name": "Bad Date",
        "channel": "Google Ads",
        "spend": 100.0,
        "conversions": 5,
        "date": "06-01-2026",  # Invalid, not YYYY-MM-DD
    }
    with pytest.raises(ValidationError) as exc:
        CampaignInputRecord(**record)
    assert "YYYY-MM-DD" in str(exc.value)

    val_res = validate_dataset([record])
    assert val_res["is_valid"] is False
    assert any("date" in err for err in val_res["errors"])


# 9. Revenue equal to zero
def test_revenue_equal_to_zero():
    record = {
        "campaign_name": "Zero Revenue Push",
        "channel": "Meta Ads",
        "spend": 250.0,
        "conversions": 10,
        "revenue": 0.0,
    }
    model = CampaignInputRecord(**record)
    assert model.revenue == 0.0
    assert model.revenue is not None

    df = clean_dataset([record])
    assert df["revenue"].iloc[0] == 0.0
    assert not pd.isna(df["revenue"].iloc[0])


# 10. Revenue equal to null
def test_revenue_equal_to_null():
    record = {
        "campaign_name": "Untracked Revenue Campaign",
        "channel": "Google Ads",
        "spend": 350.0,
        "conversions": 12,
        "revenue": None,
    }
    model = CampaignInputRecord(**record)
    assert model.revenue is None

    df = clean_dataset([record])
    # Revenue must remain NaN/None, not converted to 0.0
    assert pd.isna(df["revenue"].iloc[0])


# 11. Preservation of optional fields
def test_preservation_of_optional_fields():
    records = [
        {
            "campaign_name": "Omnichannel 1",
            "channel": "TikTok",
            "spend": 400.0,
            "conversions": 18,
            "impressions": 15000,
            "clicks": 600,
            "revenue": 1200.0,
            "date": "2026-07-01",
            "location": "APAC",
            "age_group": "18-24",
            "customer_segment": "GenZ",
            "device": "Mobile",
        }
    ]
    df = clean_dataset(records)
    norm = normalize_metrics(df)
    assert norm["impressions"].iloc[0] == 15000
    assert norm["clicks"].iloc[0] == 600
    assert norm["revenue"].iloc[0] == 1200.0
    assert norm["date"].iloc[0] == "2026-07-01"
    assert norm["location"].iloc[0] == "APAC"
    assert norm["age_group"].iloc[0] == "18-24"
    assert norm["customer_segment"].iloc[0] == "GenZ"
    assert norm["device"].iloc[0] == "Mobile"


# 12. List-of-dictionaries input conversion
def test_list_of_dictionaries_input_conversion():
    records = [
        {
            "campaign_name": "Campaign A",
            "channel": "Google",
            "spend": 100.0,
            "conversions": 5,
            "revenue": 300.0,
        },
        {
            "campaign_name": "Campaign B",
            "channel": "Meta",
            "spend": 200.0,
            "conversions": 8,
            "revenue": None,
        },
    ]
    original_copy = copy.deepcopy(records)

    df = clean_dataset(records)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert list(df["campaign_name"]) == ["Campaign A", "Campaign B"]
    assert df["spend"].dtype in (float, np.float64)
    assert df["conversions"].dtype in (int, np.int64, np.int32)
    assert df["revenue"].iloc[0] == 300.0
    assert pd.isna(df["revenue"].iloc[1])
    assert records == original_copy


# 13. Date object compatibility (SQLAlchemy datetime.date support)
def test_valid_record_with_date_object():
    import datetime
    record = {
        "campaign_name": "Date Object Campaign",
        "channel": "Google Ads",
        "spend": 500.0,
        "conversions": 10,
        "date": datetime.date(2026, 9, 18),
    }
    model = CampaignInputRecord(**record)
    assert model.date == "2026-09-18"
    assert isinstance(model.date, str)

    val_res = validate_dataset([record])
    assert val_res["is_valid"] is True
    assert val_res["validated_records"][0].date == "2026-09-18"


# 14. Datetime object compatibility
def test_valid_record_with_datetime_object():
    import datetime
    record = {
        "campaign_name": "Datetime Object Campaign",
        "channel": "Meta Ads",
        "spend": 400.0,
        "conversions": 8,
        "date": datetime.datetime(2026, 9, 18, 14, 30, 0),
    }
    model = CampaignInputRecord(**record)
    assert model.date == "2026-09-18"
    assert isinstance(model.date, str)

    val_res = validate_dataset([record])
    assert val_res["is_valid"] is True
    assert val_res["validated_records"][0].date == "2026-09-18"
