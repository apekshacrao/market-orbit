from types import SimpleNamespace

import pytest

from app.services.analysis_service import AnalysisService
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
    assert result["kpis"]["total_spend"] == 500.0
    assert result["kpis"]["total_conversions"] == 10
    assert result["kpis"]["total_clicks"] == 100
    assert result["kpis"]["total_revenue"] == 1500.0
    assert result["kpis"]["cpa"] == 50.0
    assert result["kpis"]["roas"] == 3.0


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

    assert result["kpis"]["total_spend"] == 500.0
    assert result["kpis"]["total_conversions"] == 10
    assert result["kpis"]["total_revenue"] is None
    assert result["kpis"]["roas"] is None


def test_existing_analysis_result_is_reused():
    dataset = SimpleNamespace(user_id="user-1")

    existing_result = SimpleNamespace(
        kpis={
            "total_spend": 1000.0,
            "total_conversions": 20,
        },
        rankings={
            "top": ["Campaign A"],
            "bottom": ["Campaign B"],
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

    db = SimpleNamespace(
        query=lambda model: (
            dataset_query
            if model.__name__ == "Dataset"
            else analysis_result_query
        )
    )

    result = AnalysisService.get_results(
        "dataset-1",
        "user-1",
        db,
    )

    assert result["dataset_id"] == "dataset-1"
    assert result["kpis"]["total_spend"] == 1000.0
    assert result["kpis"]["total_conversions"] == 20
    assert result["rankings"]["top"] == ["Campaign A"]
    assert result["ai_recommendations"][0]["title"] == "Test recommendation"

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