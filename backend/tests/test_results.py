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
            else campaign_query
        )
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