from types import SimpleNamespace

import pytest

from app.services.analysis_service import AnalysisService


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