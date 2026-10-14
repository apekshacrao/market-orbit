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


def test_contract_response_preserves_campaign_names_with_spaces():
    result = AnalysisService._contract_response(
        "dataset-1",
        {
            "total_spend": 1750.0,
            "total_revenue": 4200.0,
            "overall_roas": 2.4,
            "avg_conversion_rate": 3.8,
            "avg_cpa": 42.5,
        },
        {
            "top": [{
                "campaign_name": "Email Campaign",
                "spend": 750.0,
                "revenue": 2400.0,
                "roas": 3.2,
            }],
            "bottom": [
                {
                    "campaign_name": "Email Campaign",
                    "spend": 750.0,
                    "revenue": 2400.0,
                    "roas": 3.2,
                },
                {
                    "campaign_name": "Brand Awareness",
                    "spend": 1000.0,
                    "revenue": 1800.0,
                    "roas": 1.8,
                },
            ],
        },
        [
            {
                "campaign_name": "Email Campaign",
                "spend": 750.0,
                "revenue": 2400.0,
                "conversions": 18,
                "date": "2026-10-01",
            },
            {
                "campaign_name": "Brand Awareness",
                "spend": 1000.0,
                "revenue": 1800.0,
                "conversions": 23,
                "date": "2026-10-02",
            },
        ],
        [],
    )

    assert result["topCampaigns"][0]["campaignName"] == "Email Campaign"
    assert [item["campaignName"] for item in result["bottomCampaigns"]] == [
        "Email Campaign",
        "Brand Awareness",
    ]
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


def test_get_kpis_returns_contract_fields_from_cached_analysis():
    dataset = SimpleNamespace(user_id="user-1")
    cached = SimpleNamespace(
        kpis={"total_spend": 500.0, "total_revenue": 1500.0,
              "overall_roas": 3.0, "avg_conversion_rate": 10.0, "avg_cpa": 50.0},
        rankings={"top": [], "bottom": []}, trends={}, ai_recommendations=[],
    )
    query_results = {
        "Dataset": SimpleNamespace(filter=lambda _: SimpleNamespace(first=lambda: dataset)),
        "AnalysisResult": SimpleNamespace(filter=lambda _: SimpleNamespace(
            order_by=lambda _: SimpleNamespace(first=lambda: cached)
        )),
        "Campaign": SimpleNamespace(filter=lambda _: SimpleNamespace(
            order_by=lambda _: SimpleNamespace(all=lambda: [])
        )),
    }
    db = SimpleNamespace(query=lambda model: query_results[model.__name__])
    assert AnalysisService.get_kpis("dataset-1", "user-1", db) == {
        "totalSpend": 500.0, "totalRevenue": 1500.0, "overallRoas": 3.0,
        "avgConversionRate": 10.0, "avgCpa": 50.0,
    }


def test_analysis_with_zero_campaigns_returns_empty_contract_lists():
    dataset = SimpleNamespace(user_id="user-1")
    saved_records = []
    query_results = {
        "Dataset": SimpleNamespace(filter=lambda _: SimpleNamespace(first=lambda: dataset)),
        "AnalysisResult": SimpleNamespace(filter=lambda _: SimpleNamespace(
            order_by=lambda _: SimpleNamespace(first=lambda: None)
        )),
        "Campaign": SimpleNamespace(filter=lambda _: SimpleNamespace(
            order_by=lambda _: SimpleNamespace(all=lambda: [])
        )),
    }
    db = SimpleNamespace(
        query=lambda model: query_results[model.__name__],
        add=lambda obj: saved_records.append(obj), commit=lambda: None, refresh=lambda obj: None,
    )
    result = AnalysisService.get_results("dataset-empty", "user-1", db)
    assert result["dataset_id"] == "dataset-empty"
    assert result["kpis"] == {
        "totalSpend": 0.0, "totalRevenue": None, "overallRoas": None,
        "avgConversionRate": 0.0, "avgCpa": 0.0,
    }
    assert result["performance"] == []
    assert result["topCampaigns"] == []
    assert result["bottomCampaigns"] == []
    assert result["trends"] == []
    assert isinstance(result["recommendations"], list)
    assert len(saved_records) == 1


def test_analysis_persistence_rollback_on_db_error():
    dataset = SimpleNamespace(user_id="user-1")
    campaign = SimpleNamespace(
        campaign_name="Campaign A", channel="Google Ads", impressions=100, clicks=10,
        spend=50, conversions=1, revenue=100, date=None, location=None,
        age_group=None, customer_segment=None, device=None,
    )
    query_results = {
        "Dataset": SimpleNamespace(filter=lambda _: SimpleNamespace(first=lambda: dataset)),
        "AnalysisResult": SimpleNamespace(filter=lambda _: SimpleNamespace(
            order_by=lambda _: SimpleNamespace(first=lambda: None)
        )),
        "Campaign": SimpleNamespace(filter=lambda _: SimpleNamespace(
            order_by=lambda _: SimpleNamespace(all=lambda: [campaign])
        )),
    }
    class FailingDB:
        rolled_back = False
        def query(self, model): return query_results[model.__name__]
        def add(self, obj): pass
        def commit(self): raise RuntimeError("Database connection lost during commit")
        def refresh(self, obj): pass
        def rollback(self): self.rolled_back = True
    db = FailingDB()
    import pytest
    with pytest.raises(RuntimeError, match="Database connection lost"):
        AnalysisService.get_results("dataset-1", "user-1", db)
    assert db.rolled_back is True


# ==========================================
# FastAPI TestClient Integration Tests
# ==========================================

from fastapi.testclient import TestClient
from app.main import app
from app.dependencies.auth import get_current_user, get_db
from app.schemas.result import AnalysisResultResponse, KpiResponse


@pytest.fixture
def test_client():
    return TestClient(app)


def test_api_get_results_unauthenticated(test_client):
    app.dependency_overrides.clear()
    response = test_client.get("/api/v1/results/dataset-1")
    assert response.status_code == 401


def test_api_get_results_not_found(test_client):
    fake_user = SimpleNamespace(id="user-1", is_active=True)
    fake_db = SimpleNamespace(
        query=lambda model: SimpleNamespace(
            filter=lambda condition: SimpleNamespace(first=lambda: None)
        )
    )

    app.dependency_overrides[get_current_user] = lambda: fake_user
    app.dependency_overrides[get_db] = lambda: fake_db

    try:
        response = test_client.get("/api/v1/results/non-existent")
        assert response.status_code == 404
        assert response.json()["detail"] == "Dataset not found"
    finally:
        app.dependency_overrides.clear()


def test_api_get_results_forbidden(test_client):
    fake_user = SimpleNamespace(id="user-1", is_active=True)
    dataset = SimpleNamespace(id="dataset-1", user_id="user-2")
    fake_db = SimpleNamespace(
        query=lambda model: SimpleNamespace(
            filter=lambda condition: SimpleNamespace(first=lambda: dataset)
        )
    )

    app.dependency_overrides[get_current_user] = lambda: fake_user
    app.dependency_overrides[get_db] = lambda: fake_db

    try:
        response = test_client.get("/api/v1/results/dataset-1")
        assert response.status_code == 403
        assert response.json()["detail"] == "You do not have access to this dataset"
    finally:
        app.dependency_overrides.clear()


def test_api_get_results_cached_reuse(test_client):
    fake_user = SimpleNamespace(id="user-1", is_active=True)
    dataset = SimpleNamespace(id="dataset-1", user_id="user-1")
    existing_result = SimpleNamespace(
        kpis={
            "total_spend": 200.0,
            "total_conversions": 15,
            "total_clicks": 150,
            "total_impressions": 1500,
            "total_revenue": 800.0,
            "cpa": 13.33,
            "cpc": 1.33,
            "conversion_rate": 10.0,
            "ctr": 10.0,
            "roas": 4.0,
            "roi": 300.0,
        },
        rankings={"top": [{"campaign_name": "Camp1", "spend": 200.0, "revenue": 800.0, "roas": 4.0}], "bottom": []},
        trends={"channel_breakdown": {"Google": {"spend": 200.0, "revenue": 800.0, "conversions": 15}}},
        ai_recommendations=[{"title": "Scale High-ROAS Campaigns", "action": "Increase Budget"}],
    )

    dataset_query = SimpleNamespace(
        filter=lambda condition: SimpleNamespace(first=lambda: dataset)
    )
    analysis_result_query = SimpleNamespace(
        filter=lambda condition: SimpleNamespace(
            order_by=lambda condition: SimpleNamespace(first=lambda: existing_result)
        )
    )

    campaign_query = SimpleNamespace(
        filter=lambda condition: SimpleNamespace(
            order_by=lambda condition: SimpleNamespace(all=lambda: [])
        )
    )
    fake_db = SimpleNamespace(
        query=lambda model: (
            dataset_query if model.__name__ == "Dataset"
            else analysis_result_query if model.__name__ == "AnalysisResult"
            else campaign_query
        )
    )

    app.dependency_overrides[get_current_user] = lambda: fake_user
    app.dependency_overrides[get_db] = lambda: fake_db

    try:
        response = test_client.get("/api/v1/results/dataset-1")
        assert response.status_code == 200
        data = response.json()
        validated = AnalysisResultResponse.model_validate(data)
        assert validated.dataset_id == "dataset-1"
        assert validated.kpis.totalSpend == 200.0
        assert validated.kpis.overallRoas == 4.0
        assert validated.topCampaigns[0].campaignName == "Camp1"
        assert len(validated.recommendations) == 1
    finally:
        app.dependency_overrides.clear()


def test_api_get_results_newly_computed(test_client):
    fake_user = SimpleNamespace(id="user-1", is_active=True)
    dataset = SimpleNamespace(id="dataset-new", user_id="user-1")
    campaign = SimpleNamespace(
        campaign_name="Summer Promotion",
        channel="Meta Ads",
        impressions=5000,
        clicks=250,
        spend=400,
        conversions=25,
        revenue=1200,
        date="2026-09-19",
        location="Mumbai",
        age_group="25-34",
        customer_segment="Returning",
        device="Desktop",
    )

    dataset_query = SimpleNamespace(
        filter=lambda condition: SimpleNamespace(first=lambda: dataset)
    )
    analysis_result_query = SimpleNamespace(
        filter=lambda condition: SimpleNamespace(
            order_by=lambda condition: SimpleNamespace(first=lambda: None)
        )
    )
    campaign_query = SimpleNamespace(
        filter=lambda condition: SimpleNamespace(
            order_by=lambda condition: SimpleNamespace(all=lambda: [campaign])
        )
    )

    added_objects = []
    fake_db = SimpleNamespace(
        query=lambda model: (
            dataset_query
            if model.__name__ == "Dataset"
            else analysis_result_query
            if model.__name__ == "AnalysisResult"
            else campaign_query
        ),
        add=lambda obj: added_objects.append(obj),
        commit=lambda: None,
        refresh=lambda obj: None,
    )

    app.dependency_overrides[get_current_user] = lambda: fake_user
    app.dependency_overrides[get_db] = lambda: fake_db

    try:
        response = test_client.get("/api/v1/results/dataset-new")
        assert response.status_code == 200
        data = response.json()
        validated = AnalysisResultResponse.model_validate(data)
        assert validated.dataset_id == "dataset-new"
        assert validated.kpis.totalSpend == 400.0
        assert validated.kpis.totalRevenue == 1200.0
        assert validated.kpis.overallRoas == 3.0
        assert validated.performance[0].campaignName == "Summer Promotion"
        assert validated.trends[0].conversions == 25
        assert len(added_objects) == 1
    finally:
        app.dependency_overrides.clear()


def test_api_get_kpis_endpoint_success(test_client):
    fake_user = SimpleNamespace(id="user-1", is_active=True)
    dataset = SimpleNamespace(id="dataset-1", user_id="user-1")
    existing_result = SimpleNamespace(
        kpis={
            "total_spend": 300.0,
            "total_conversions": 10,
            "total_clicks": 60,
            "total_impressions": 600,
            "total_revenue": 900.0,
            "cpa": 30.0,
            "cpc": 5.0,
            "conversion_rate": 16.67,
            "ctr": 10.0,
            "roas": 3.0,
            "roi": 200.0,
            "avg_cpa": 30.0,
            "avg_cpc": 5.0,
            "avg_conversion_rate": 16.67,
            "overall_roas": 3.0,
        },
        rankings={},
        trends={},
        ai_recommendations=[],
    )

    dataset_query = SimpleNamespace(
        filter=lambda condition: SimpleNamespace(first=lambda: dataset)
    )
    analysis_result_query = SimpleNamespace(
        filter=lambda condition: SimpleNamespace(
            order_by=lambda condition: SimpleNamespace(first=lambda: existing_result)
        )
    )

    campaign_query = SimpleNamespace(
        filter=lambda condition: SimpleNamespace(
            order_by=lambda condition: SimpleNamespace(all=lambda: [])
        )
    )
    fake_db = SimpleNamespace(
        query=lambda model: (
            dataset_query
            if model.__name__ == "Dataset"
            else analysis_result_query
            if model.__name__ == "AnalysisResult"
            else campaign_query
        )
    )

    app.dependency_overrides[get_current_user] = lambda: fake_user
    app.dependency_overrides[get_db] = lambda: fake_db

    try:
        response = test_client.get("/api/v1/results/dataset-1/kpis")
        assert response.status_code == 200
        data = response.json()
        validated = KpiResponse.model_validate(data)
        assert validated.totalSpend == 300.0
        assert validated.totalRevenue == 900.0
        assert validated.avgConversionRate == 16.67
        assert validated.avgCpa == 30.0
        assert validated.overallRoas == 3.0
    finally:
        app.dependency_overrides.clear()


def test_api_get_kpis_not_found(test_client):
    fake_user = SimpleNamespace(id="user-1", is_active=True)
    fake_db = SimpleNamespace(
        query=lambda model: SimpleNamespace(
            filter=lambda condition: SimpleNamespace(first=lambda: None)
        )
    )

    app.dependency_overrides[get_current_user] = lambda: fake_user
    app.dependency_overrides[get_db] = lambda: fake_db

    try:
        response = test_client.get("/api/v1/results/missing-id/kpis")
        assert response.status_code == 404
        assert response.json()["detail"] == "Dataset not found"
    finally:
        app.dependency_overrides.clear()


def test_api_get_kpis_forbidden(test_client):
    fake_user = SimpleNamespace(id="user-1", is_active=True)
    dataset = SimpleNamespace(id="dataset-1", user_id="user-other")
    fake_db = SimpleNamespace(
        query=lambda model: SimpleNamespace(
            filter=lambda condition: SimpleNamespace(first=lambda: dataset)
        )
    )

    app.dependency_overrides[get_current_user] = lambda: fake_user
    app.dependency_overrides[get_db] = lambda: fake_db

    try:
        response = test_client.get("/api/v1/results/dataset-1/kpis")
        assert response.status_code == 403
        assert response.json()["detail"] == "You do not have access to this dataset"
    finally:
        app.dependency_overrides.clear()


# ===========================================================================
# Phase 5.7: End-to-End AI Integration & Verification Tests
# ===========================================================================

def _make_mock_db_and_campaigns():
    dataset = SimpleNamespace(id="dataset-p57", user_id="user-1")
    campaign1 = SimpleNamespace(
        campaign_name="Alpha", channel="Google Ads", impressions=1000, clicks=100,
        spend=200.0, conversions=20, revenue=600.0, date="2026-01-01",
        location="US", age_group="25-34", customer_segment="B2C", device="Mobile",
    )
    campaign2 = SimpleNamespace(
        campaign_name="Beta", channel="Facebook", impressions=500, clicks=50,
        spend=100.0, conversions=0, revenue=0.0, date="2026-01-02",
        location="UK", age_group="35-44", customer_segment="B2B", device="Desktop",
    )
    saved_records = []

    dataset_query = SimpleNamespace(filter=lambda condition: SimpleNamespace(first=lambda: dataset))
    analysis_result_query = SimpleNamespace(filter=lambda cond: SimpleNamespace(order_by=lambda c: SimpleNamespace(first=lambda: None)))
    campaign_query = SimpleNamespace(filter=lambda cond: SimpleNamespace(order_by=lambda c: SimpleNamespace(all=lambda: [campaign1, campaign2])))

    mock_db = SimpleNamespace(
        query=lambda model: (
            dataset_query if model.__name__ == "Dataset"
            else analysis_result_query if model.__name__ == "AnalysisResult"
            else campaign_query
        ),
        add=lambda obj: saved_records.append(obj),
        commit=lambda: None,
        refresh=lambda obj: None,
        rollback=lambda: None,
    )
    return mock_db, saved_records


def test_analysis_service_uses_recommendation_service_fallback():
    """Verify AnalysisService.get_results uses RecommendationService and saves deterministic fallback when unconfigured."""
    db, saved_records = _make_mock_db_and_campaigns()

    result = AnalysisService.get_results(
        dataset_id="dataset-p57",
        current_user_id="user-1",
        db=db,
    )

    assert AnalysisResultResponse.model_validate(result)
    assert len(saved_records) == 1
    persisted = saved_records[0]
    assert persisted.ai_recommendations is not None
    assert len(persisted.ai_recommendations) > 0

    # Verify all recommendations are attributed to deterministic fallback
    for item in persisted.ai_recommendations:
        assert item["source"] == "deterministic_fallback"
        assert "title" in item
        assert "action" in item
        assert "category" in item

    # Verify response matches persisted records
    assert result["recommendations"] == persisted.ai_recommendations


def test_analysis_service_uses_recommendation_service_live_mocked():
    """Verify AnalysisService.get_results uses RecommendationService and saves live LLM recommendations when mocked."""
    db, saved_records = _make_mock_db_and_campaigns()

    mock_llm_json = """[
        {
            "id": "rec-live-001",
            "category": "channel_scaling",
            "title": "Scale High-Performing Alpha",
            "action": "Increase daily spend on Alpha by 20%.",
            "rationale": "Alpha delivers 3.0x ROAS with $10 CPA.",
            "supporting_evidence": {
                "metric": "roas",
                "observed_value": 3.0,
                "campaign_name": "Alpha"
            },
            "limitations": ["Assumes constant marginal ROAS"],
            "source": "groq_llm"
        }
    ]"""

    from analytics.ai.groq_client import GroqClient
    from analytics.ai.service import RecommendationService

    client = GroqClient(api_key="gsk_mock_test_key_abc123")
    client.chat_completion = lambda **kwargs: mock_llm_json
    service = RecommendationService(client=client)

    result = AnalysisService.get_results(
        dataset_id="dataset-p57",
        current_user_id="user-1",
        db=db,
        recommendation_service=service,
    )

    assert AnalysisResultResponse.model_validate(result)
    assert len(saved_records) == 1
    persisted = saved_records[0]
    assert len(persisted.ai_recommendations) == 1
    assert persisted.ai_recommendations[0]["id"] == "rec-live-001"
    assert persisted.ai_recommendations[0]["source"] == "groq_llm"
    assert persisted.ai_recommendations[0]["category"] == "channel_scaling"
    assert result["recommendations"] == persisted.ai_recommendations


def test_analysis_service_provider_error_falls_back_gracefully():
    """Verify AnalysisService falls back to deterministic recommendations upon Groq provider error."""
    db, saved_records = _make_mock_db_and_campaigns()

    from analytics.ai.groq_client import GroqClient, GroqRateLimitError
    from analytics.ai.service import RecommendationService

    client = GroqClient(api_key="gsk_mock_test_key_abc123")
    def fail_chat(**kwargs):
        raise GroqRateLimitError("Rate limit exceeded 429")
    client.chat_completion = fail_chat
    service = RecommendationService(client=client)

    result = AnalysisService.get_results(
        dataset_id="dataset-p57",
        current_user_id="user-1",
        db=db,
        recommendation_service=service,
    )

    assert AnalysisResultResponse.model_validate(result)
    assert len(saved_records) == 1
    persisted = saved_records[0]
    assert len(persisted.ai_recommendations) > 0
    assert persisted.ai_recommendations[0]["source"] == "deterministic_fallback"


def test_analysis_service_parsing_error_falls_back_gracefully():
    """Verify AnalysisService falls back to deterministic recommendations upon LLM malformed JSON."""
    db, saved_records = _make_mock_db_and_campaigns()

    from analytics.ai.groq_client import GroqClient
    from analytics.ai.service import RecommendationService

    client = GroqClient(api_key="gsk_mock_test_key_abc123")
    client.chat_completion = lambda **kwargs: "Sorry, I cannot produce JSON right now."
    service = RecommendationService(client=client)

    result = AnalysisService.get_results(
        dataset_id="dataset-p57",
        current_user_id="user-1",
        db=db,
        recommendation_service=service,
    )

    assert AnalysisResultResponse.model_validate(result)
    assert len(saved_records) == 1
    persisted = saved_records[0]
    assert len(persisted.ai_recommendations) > 0
    assert persisted.ai_recommendations[0]["source"] == "deterministic_fallback"


def test_analysis_service_validation_error_falls_back_gracefully():
    """Verify AnalysisService falls back to deterministic recommendations upon schema contract violation."""
    db, saved_records = _make_mock_db_and_campaigns()

    from analytics.ai.groq_client import GroqClient
    from analytics.ai.service import RecommendationService

    invalid_schema_json = """[
        {
            "id": "rec-bad",
            "category": "not_a_real_category",
            "title": "Invalid Category",
            "action": "Do something",
            "rationale": "Because reasons",
            "source": "groq_llm"
        }
    ]"""

    client = GroqClient(api_key="gsk_mock_test_key_abc123")
    client.chat_completion = lambda **kwargs: invalid_schema_json
    service = RecommendationService(client=client)

    result = AnalysisService.get_results(
        dataset_id="dataset-p57",
        current_user_id="user-1",
        db=db,
        recommendation_service=service,
    )

    assert AnalysisResultResponse.model_validate(result)
    assert len(saved_records) == 1
    persisted = saved_records[0]
    assert len(persisted.ai_recommendations) > 0
    assert persisted.ai_recommendations[0]["source"] == "deterministic_fallback"


def test_analysis_service_programming_error_propagates():
    """Verify unexpected programming errors inside recommendation service are not swallowed."""
    db, saved_records = _make_mock_db_and_campaigns()

    class BrokenService:
        def get_recommendation_list(self, **kwargs):
            raise TypeError("Unexpected bug inside recommendation logic")

    with pytest.raises(TypeError, match="Unexpected bug"):
        AnalysisService.get_results(
            dataset_id="dataset-p57",
            current_user_id="user-1",
            db=db,
            recommendation_service=BrokenService(),
        )

