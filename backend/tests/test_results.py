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


def test_get_kpis():
    dataset = SimpleNamespace(user_id="user-1")
    existing_result = SimpleNamespace(
        kpis={
            "total_spend": 500.0,
            "total_conversions": 10,
            "total_clicks": 100,
            "total_impressions": 1000,
            "total_revenue": 1500.0,
            "cpa": 50.0,
            "cpc": 5.0,
            "conversion_rate": 10.0,
            "ctr": 10.0,
            "roas": 3.0,
            "roi": 200.0,
            "avg_cpa": 50.0,
            "avg_cpc": 5.0,
            "avg_conversion_rate": 10.0,
            "overall_roas": 3.0,
        },
        rankings={"top": [], "bottom": []},
        trends={"channel_breakdown": {}},
        ai_recommendations=[],
    )

    db = SimpleNamespace(
        query=lambda model: SimpleNamespace(
            filter=lambda condition: SimpleNamespace(
                first=lambda: dataset if model.__name__ == "Dataset" else None,
                order_by=lambda condition: SimpleNamespace(
                    first=lambda: existing_result
                ),
            )
        )
    )

    kpis = AnalysisService.get_kpis("dataset-1", "user-1", db)
    assert kpis["total_spend"] == 500.0
    assert kpis["total_conversions"] == 10
    assert kpis["cpa"] == 50.0
    assert "rankings" not in kpis
    assert "trends" not in kpis


def test_analysis_with_zero_campaigns():
    dataset = SimpleNamespace(user_id="user-1")

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
                all=lambda: []
            )
        )
    )

    saved_records = []
    db = SimpleNamespace(
        query=lambda model: (
            dataset_query
            if model.__name__ == "Dataset"
            else analysis_result_query
            if model.__name__ == "AnalysisResult"
            else campaign_query
        ),
        add=lambda obj: saved_records.append(obj),
        commit=lambda: None,
        refresh=lambda obj: None,
    )

    result = AnalysisService.get_results(
        "dataset-empty",
        "user-1",
        db,
    )

    assert result["dataset_id"] == "dataset-empty"
    assert result["kpis"]["total_spend"] == 0.0
    assert result["kpis"]["total_conversions"] == 0
    assert result["kpis"]["total_revenue"] is None
    assert result["kpis"]["roas"] is None
    assert result["rankings"] == {"top": [], "bottom": []}
    assert result["trends"] == {"channel_breakdown": {}}
    assert isinstance(result["ai_recommendations"], list)
    assert len(saved_records) == 1


def test_analysis_persistence_rollback_on_db_error():
    dataset = SimpleNamespace(user_id="user-1")
    campaign = SimpleNamespace(
        campaign_name="Campaign A",
        channel="Google Ads",
        impressions=100,
        clicks=10,
        spend=50,
        conversions=1,
        revenue=100,
        date=None,
        location=None,
        age_group=None,
        customer_segment=None,
        device=None,
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

    class FailingDB:
        def __init__(self):
            self.rolled_back = False

        def query(self, model):
            if model.__name__ == "Dataset":
                return dataset_query
            if model.__name__ == "AnalysisResult":
                return analysis_result_query
            return campaign_query

        def add(self, obj):
            pass

        def commit(self):
            raise RuntimeError("Database connection lost during commit")

        def refresh(self, obj):
            pass

        def rollback(self):
            self.rolled_back = True

    db = FailingDB()

    with pytest.raises(RuntimeError) as exc_info:
        AnalysisService.get_results("dataset-1", "user-1", db)

    assert "Database connection lost" in str(exc_info.value)
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
        rankings={"top": [{"campaign_name": "Camp1", "roas": 4.0}], "bottom": []},
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

    fake_db = SimpleNamespace(
        query=lambda model: (
            dataset_query
            if model.__name__ == "Dataset"
            else analysis_result_query
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
        assert validated.kpis["total_spend"] == 200.0
        assert validated.kpis["roas"] == 4.0
        assert validated.rankings["top"][0]["campaign_name"] == "Camp1"
        assert len(validated.ai_recommendations) == 1
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
        assert validated.kpis["total_spend"] == 400.0
        assert validated.kpis["total_conversions"] == 25
        assert validated.kpis["total_revenue"] == 1200.0
        assert validated.kpis["roas"] == 3.0
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

    fake_db = SimpleNamespace(
        query=lambda model: (
            dataset_query
            if model.__name__ == "Dataset"
            else analysis_result_query
        )
    )

    app.dependency_overrides[get_current_user] = lambda: fake_user
    app.dependency_overrides[get_db] = lambda: fake_db

    try:
        response = test_client.get("/api/v1/results/dataset-1/kpis")
        assert response.status_code == 200
        data = response.json()
        validated = KpiResponse.model_validate(data)
        assert validated.total_spend == 300.0
        assert validated.total_conversions == 10
        assert validated.total_revenue == 900.0
        assert validated.cpa == 30.0
        assert validated.roas == 3.0
        assert validated.avg_cpa == 30.0
        assert validated.overall_roas == 3.0
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