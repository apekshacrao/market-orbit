from types import SimpleNamespace

import pytest

from app.services.analysis_service import AnalysisService
from app.schemas.result import AnalysisResultResponse
from unittest.mock import patch

def test_dataset_not_found():
    db = SimpleNamespace(
        query=lambda model: SimpleNamespace(
            filter=lambda condition: SimpleNamespace(
                first=lambda: None
            )
        )
    )

    with pytest.raises(Exception) as error:
        AnalysisService.get_results(
            "dataset-1",
            "user-1",
            db,
        )

    assert error.value.status_code == 404


def test_dataset_access_denied():
    dataset = SimpleNamespace(user_id="user-2")

    db = SimpleNamespace(
        query=lambda model: SimpleNamespace(
            filter=lambda condition: SimpleNamespace(
                first=lambda: dataset
            )
        )
    )

    with pytest.raises(Exception) as error:
        AnalysisService.get_results(
            "dataset-1",
            "user-1",
            db,
        )

    assert error.value.status_code == 403


def test_dataset_access_allowed():
    dataset = SimpleNamespace(user_id="user-1")

    campaign = SimpleNamespace(
        campaign_name="Campaign A",
        channel="Google Ads",
        impressions=1000,
        clicks=100,
        spend=500,
        conversions=10,
        revenue=1500,
        date=None,
        location=None,
        age_group=None,
        customer_segment=None,
        device=None,
    )

    dataset_query = SimpleNamespace(
        filter=lambda condition: SimpleNamespace(
            first=lambda: dataset
        )
    )

    analysis_result_query = SimpleNamespace(
        filter=lambda condition: SimpleNamespace(
            order_by=lambda condition: SimpleNamespace(
                first=lambda: None
            )
        )
    )

    campaign_query = SimpleNamespace(
        filter=lambda condition: SimpleNamespace(
            order_by=lambda condition: SimpleNamespace(
                all=lambda: [campaign]
            )
        )
    )

    db = SimpleNamespace(
        query=lambda model: (
            dataset_query
            if model.__name__ == "Dataset"
            else analysis_result_query
            if model.__name__ == "AnalysisResult"
            else campaign_query
        ),
        add=lambda obj: None,
        commit=lambda: None,
        refresh=lambda obj: None,
    )

    result = AnalysisService.get_results(
        "dataset-1",
        "user-1",
        db,
    )

    assert result["dataset_id"] == "dataset-1"
    assert result["kpis"] == {
        "totalSpend": 500.0, "totalRevenue": 1500.0, "overallRoas": 3.0,
        "avgConversionRate": 10.0, "avgCpa": 50.0,
    }
    assert result["performance"] == [{
        "campaignName": "Campaign A", "spend": 500.0,
        "revenue": 1500.0, "roas": 3.0,
    }]
    assert result["topCampaigns"][0]["campaignName"] == "Campaign A"
    assert result["bottomCampaigns"][0]["campaignName"] == "Campaign A"
    assert AnalysisResultResponse.model_validate(result)


def test_analysis_with_missing_revenue():
    dataset = SimpleNamespace(user_id="user-1")

    campaign = SimpleNamespace(
        campaign_name="Campaign A",
        channel="Google Ads",
        impressions=1000,
        clicks=100,
        spend=500,
        conversions=10,
        revenue=None,
        date=None,
        location=None,
        age_group=None,
        customer_segment=None,
        device=None,
    )

    dataset_query = SimpleNamespace(
        filter=lambda condition: SimpleNamespace(
            first=lambda: dataset
        )
    )

    analysis_result_query = SimpleNamespace(
        filter=lambda condition: SimpleNamespace(
            order_by=lambda condition: SimpleNamespace(
                first=lambda: None
            )
        )
    )

    campaign_query = SimpleNamespace(
        filter=lambda condition: SimpleNamespace(
            order_by=lambda condition: SimpleNamespace(
                all=lambda: [campaign]
            )
        )
    )

    db = SimpleNamespace(
        query=lambda model: (
            dataset_query
            if model.__name__ == "Dataset"
            else analysis_result_query
            if model.__name__ == "AnalysisResult"
            else campaign_query
        ),
        add=lambda obj: None,
        commit=lambda: None,
        refresh=lambda obj: None,
    )

    result = AnalysisService.get_results(
        "dataset-1",
        "user-1",
        db,
    )

    assert result["kpis"]["totalSpend"] == 500.0
    assert result["kpis"]["totalRevenue"] is None
    assert result["kpis"]["overallRoas"] is None
    assert result["performance"][0]["revenue"] is None
    assert result["topCampaigns"][0]["revenue"] is None
    assert result["topCampaigns"][0]["roas"] is None
    assert result["bottomCampaigns"][0]["revenue"] is None
    assert result["bottomCampaigns"][0]["roas"] is None


def test_existing_analysis_result_is_reused():
    dataset = SimpleNamespace(user_id="user-1")

    existing_result = SimpleNamespace(
        kpis={
            "total_spend": 1000.0,
            "total_conversions": 20,
        },
        rankings={
            "top": [{"campaign_name": "Campaign A", "spend": 100, "revenue": 250, "roas": 2.5}],
            "bottom": [{"campaign_name": "Campaign B", "spend": 100, "revenue": 50, "roas": 0.5}],
        },
        trends={
            "channel_breakdown": {},
        },
        ai_recommendations=[
            {
                "title": "Test recommendation",
            }
        ],
    )

    dataset_query = SimpleNamespace(
        filter=lambda condition: SimpleNamespace(
            first=lambda: dataset
        )
    )

    analysis_result_query = SimpleNamespace(
        filter=lambda condition: SimpleNamespace(
            order_by=lambda condition: SimpleNamespace(
                first=lambda: existing_result
            )
        )
    )

    campaign_query = SimpleNamespace(
        filter=lambda condition: SimpleNamespace(
            order_by=lambda condition: SimpleNamespace(all=lambda: [])
        )
    )
    db = SimpleNamespace(
        query=lambda model: (
            dataset_query if model.__name__ == "Dataset"
            else analysis_result_query if model.__name__ == "AnalysisResult"
            else campaign_query
        )
    )

    result = AnalysisService.get_results(
        "dataset-1",
        "user-1",
        db,
    )

    assert result["dataset_id"] == "dataset-1"
    assert result["kpis"]["totalSpend"] == 1000.0
    assert result["kpis"]["totalRevenue"] is None
    assert result["topCampaigns"][0]["campaignName"] == "Campaign A"
    assert result["bottomCampaigns"][0]["campaignName"] == "Campaign B"
    assert result["recommendations"][0]["title"] == "Test recommendation"
    assert AnalysisResultResponse.model_validate(result)

def test_analysis_passes_optional_fields_to_analytics():
    dataset = SimpleNamespace(user_id="user-1")

    campaign = SimpleNamespace(
        campaign_name="Campaign A",
        channel="Google Ads",
        impressions=1000,
        clicks=100,
        spend=500,
        conversions=10,
        revenue=1500,
        date="2026-09-18",
        location="Bengaluru",
        age_group="18-24",
        customer_segment="New Customers",
        device="Mobile",
    )

    dataset_query = SimpleNamespace(
        filter=lambda condition: SimpleNamespace(
            first=lambda: dataset
        )
    )

    analysis_result_query = SimpleNamespace(
        filter=lambda condition: SimpleNamespace(
            order_by=lambda condition: SimpleNamespace(
                first=lambda: None
            )
        )
    )

    campaign_query = SimpleNamespace(
        filter=lambda condition: SimpleNamespace(
            order_by=lambda condition: SimpleNamespace(
                all=lambda: [campaign]
            )
        )
    )

    db = SimpleNamespace(
        query=lambda model: (
            dataset_query
            if model.__name__ == "Dataset"
            else analysis_result_query
            if model.__name__ == "AnalysisResult"
            else campaign_query
        ),
        add=lambda obj: None,
        commit=lambda: None,
        refresh=lambda obj: None,
    )

    captured_data = {}

    def fake_clean_dataset(data):
        captured_data["data"] = data

        import pandas as pd
        return pd.DataFrame(data)

    with patch(
        "app.services.analysis_service.clean_dataset",
        side_effect=fake_clean_dataset,
    ):
        AnalysisService.get_results(
            "dataset-1",
            "user-1",
            db,
        )

    campaign_data = captured_data["data"][0]

    assert campaign_data["date"] == "2026-09-18"
    assert campaign_data["location"] == "Bengaluru"
    assert campaign_data["age_group"] == "18-24"
    assert campaign_data["customer_segment"] == "New Customers"
    assert campaign_data["device"] == "Mobile"


def test_analysis_serializes_date_object_to_iso_string():
    import datetime
    dataset = SimpleNamespace(user_id="user-1")

    campaign = SimpleNamespace(
        campaign_name="Campaign With Date Object",
        channel="Google Ads",
        impressions=1000,
        clicks=100,
        spend=500,
        conversions=10,
        revenue=1500,
        date=datetime.date(2026, 9, 18),
        location="Bengaluru",
        age_group="18-24",
        customer_segment="New Customers",
        device="Mobile",
    )

    dataset_query = SimpleNamespace(
        filter=lambda condition: SimpleNamespace(
            first=lambda: dataset
        )
    )

    analysis_result_query = SimpleNamespace(
        filter=lambda condition: SimpleNamespace(
            order_by=lambda condition: SimpleNamespace(
                first=lambda: None
            )
        )
    )

    campaign_query = SimpleNamespace(
        filter=lambda condition: SimpleNamespace(
            order_by=lambda condition: SimpleNamespace(
                all=lambda: [campaign]
            )
        )
    )

    db = SimpleNamespace(
        query=lambda model: (
            dataset_query
            if model.__name__ == "Dataset"
            else analysis_result_query
            if model.__name__ == "AnalysisResult"
            else campaign_query
        ),
        add=lambda obj: None,
        commit=lambda: None,
        refresh=lambda obj: None,
    )

    captured_data = {}

    def fake_clean_dataset(data):
        captured_data["data"] = data
        import pandas as pd
        return pd.DataFrame(data)

    with patch(
        "app.services.analysis_service.clean_dataset",
        side_effect=fake_clean_dataset,
    ):
        AnalysisService.get_results(
            "dataset-1",
            "user-1",
            db,
        )

    campaign_data = captured_data["data"][0]
    assert campaign_data["date"] == "2026-09-18"
    assert isinstance(campaign_data["date"], str)


def test_contract_trends_group_valid_dates_and_keep_unknown_revenue_null():
    result = AnalysisService._contract_response(
        "dataset-1",
        {"total_spend": 15, "total_revenue": None, "overall_roas": None,
         "avg_conversion_rate": 20, "avg_cpa": 3},
        {"top": [], "bottom": []},
        [
            {"campaign_name": "A", "spend": 10, "revenue": 100,
             "conversions": 2, "date": "2026-10-01"},
            {"campaign_name": "B", "spend": 5, "revenue": None,
             "conversions": 1, "date": "2026-10-01"},
            {"campaign_name": "C", "spend": 7, "revenue": 70,
             "conversions": 4, "date": "2026-10-02"},
            {"campaign_name": "No date", "spend": 8, "revenue": 80,
             "conversions": 5, "date": None},
            {"campaign_name": "Bad date", "spend": 9, "revenue": 90,
             "conversions": 6, "date": "not-a-date"},
        ],
        [],
    )

    assert result["trends"] == [
        {"date": "2026-10-01", "spend": 15.0, "revenue": None, "conversions": 3},
        {"date": "2026-10-02", "spend": 7.0, "revenue": 70.0, "conversions": 4},
    ]
    assert result["kpis"]["totalSpend"] == 15
    assert AnalysisResultResponse.model_validate(result)


def test_cached_result_uses_contract_adapter_and_dated_source_campaigns():
    dataset = SimpleNamespace(user_id="user-1")
    cached = SimpleNamespace(
        kpis={"total_spend": 20, "total_revenue": None, "roas": None,
              "avg_conversion_rate": 25, "avg_cpa": 4},
        rankings={"top": [{"campaign_name": "Cached", "spend": 20,
                           "revenue": 0, "roas": 0}], "bottom": []},
        trends={"channel_breakdown": {"ignored": {}}},
        ai_recommendations=[],
    )
    campaign = SimpleNamespace(
        campaign_name="Cached", channel="Search", impressions=10, clicks=4,
        spend=20, conversions=1, revenue=None, date="2026-10-03",
        location=None, age_group=None, customer_segment=None, device=None,
    )
    dataset_query = SimpleNamespace(filter=lambda condition: SimpleNamespace(first=lambda: dataset))
    result_query = SimpleNamespace(filter=lambda condition: SimpleNamespace(
        order_by=lambda condition: SimpleNamespace(first=lambda: cached)
    ))
    campaign_query = SimpleNamespace(filter=lambda condition: SimpleNamespace(
        order_by=lambda condition: SimpleNamespace(all=lambda: [campaign])
    ))
    db = SimpleNamespace(query=lambda model: {
        "Dataset": dataset_query, "AnalysisResult": result_query, "Campaign": campaign_query,
    }[model.__name__])

    result = AnalysisService.get_results("dataset-1", "user-1", db)
    assert result["kpis"] == {
        "totalSpend": 20, "totalRevenue": None, "overallRoas": None,
        "avgConversionRate": 25, "avgCpa": 4,
    }
    assert result["topCampaigns"][0]["revenue"] is None
    assert result["trends"] == [
        {"date": "2026-10-03", "spend": 20.0, "revenue": None, "conversions": 1}
    ]
    assert AnalysisResultResponse.model_validate(result)
