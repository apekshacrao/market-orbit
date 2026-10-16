"""Opt-in PostgreSQL JSONB integration coverage for Phase 6 analytics caching."""

import os
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.models.analysis_result import AnalysisResult
from app.db.models.campaign import Campaign
from app.db.models.dataset import Dataset
from app.db.models.user import User
from app.services.analysis_service import AnalysisService


TEST_DATABASE_NAME = "market_orbit_phase6_jsonb_test"
ALLOWED_TEST_HOSTS = {"localhost", "127.0.0.1", "::1"}


def _validated_test_url():
    """Return only a validated dedicated test URL; never fall back to app settings."""
    url_value = os.environ.get("PHASE6_TEST_DATABASE_URL")
    if not url_value:
        pytest.fail("PHASE6_TEST_DATABASE_URL is required for this integration test")

    try:
        url = make_url(url_value)
    except Exception:
        pytest.fail("PHASE6_TEST_DATABASE_URL is not a valid SQLAlchemy URL")

    if not url.drivername.startswith("postgresql"):
        pytest.fail("PHASE6_TEST_DATABASE_URL must use PostgreSQL")
    if (url.host or "").lower() not in ALLOWED_TEST_HOSTS:
        pytest.fail("PHASE6_TEST_DATABASE_URL host is not an approved local host")
    if url.database != TEST_DATABASE_NAME:
        pytest.fail("PHASE6_TEST_DATABASE_URL does not target the approved test database")

    return url


def _jsonb_test_payload():
    return {
        "channel_breakdown": {
            "Search": {"spend": 125.5, "revenue": None, "conversions": 4}
        },
        "time_series": {
            "has_time_series": False,
            "timeline": [],
            "status": "insufficient_data",
        },
        "dimension_breakdowns": {
            "customer_segment": {
                "Returning": {"spend": 125.5, "conversions": 4}
            }
        },
        "segmentation": {
            "cohorts": {
                "summary": {
                    "total_campaigns": 1,
                    "scale_ready_count": 1,
                    "volume_driver_count": 0,
                    "efficiency_niche_count": 0,
                    "budget_drain_count": 0,
                },
                "cohorts": {
                    "scale_ready": [{
                        "campaign_name": "Phase 6 test campaign",
                        "spend": 125.5,
                        "conversions": 4,
                        "cpa": 31.38,
                        "roas": None,
                    }],
                    "volume_driver": [],
                    "efficiency_niche": [],
                    "budget_drain": [],
                },
            },
            "segment_portfolio": {
                "is_available": True,
                "total_segments": 1,
                "segments": {
                    "Returning": {
                        "spend": 125.5,
                        "conversions": 4,
                        "revenue": None,
                        "cpa": 31.38,
                        "roas": None,
                        "share_of_spend": 100.0,
                        "share_of_conversions": 100.0,
                        "share_of_revenue": None,
                        "conversion_efficiency_ratio": 1.0,
                        "cpa_index": 100.0,
                    }
                },
            },
        },
        "forecasting": {
            "is_available": False,
            "status": "no_valid_dates",
            "parameters": {"horizon": 7, "min_train_dates": 14, "step": 1},
            "historical_coverage": {
                "start_date": None,
                "end_date": None,
                "historical_dates_count": 0,
                "missing_dates_count": 0,
            },
            "forecasts": {
                "is_available": False,
                "models": {
                    "naive": {
                        "is_eligible": False,
                        "forecast": [],
                        "metric_status": {"revenue": "ineligible"},
                    }
                },
            },
            "validation": {
                "is_available": False,
                "status": "no_valid_dates",
                "models": {"naive": {"metrics": {"revenue": {"mae": None}}}},
            },
            "revenue_complete": False,
            "warnings": ["No valid calendar dates were available."],
        },
    }


def _validate_existing_tables(engine):
    """Reject incompatible pre-existing tables before create_all can do DDL."""
    inspector = inspect(engine)
    required_tables = (User, Dataset, Campaign, AnalysisResult)

    for model in required_tables:
        table = model.__table__
        if not inspector.has_table(table.name):
            continue

        existing_columns = {
            column["name"] for column in inspector.get_columns(table.name)
        }
        required_columns = {column.name for column in table.columns}
        missing_columns = sorted(required_columns - existing_columns)
        if missing_columns:
            pytest.fail(
                f"Existing table '{table.name}' is incompatible with its ORM model; "
                f"missing required columns: {', '.join(missing_columns)}"
            )


def test_phase6_jsonb_round_trip_and_cached_analytics_reuse(monkeypatch):
    # Validate before engine creation, connection, DDL, or writes.
    test_url = _validated_test_url()
    engine = create_engine(test_url, pool_pre_ping=True, hide_parameters=True)
    TestSession = sessionmaker(bind=engine, expire_on_commit=False)

    run_id = str(uuid4())
    user_id = str(uuid4())
    dataset_id = str(uuid4())
    campaign_id = str(uuid4())
    result_id = str(uuid4())
    payload = _jsonb_test_payload()
    rows_may_exist = False

    try:
        # Inspect pre-existing tables before create_all can issue any DDL.
        _validate_existing_tables(engine)

        # Create only the four ORM tables used by these rows and the cache path.
        Base.metadata.create_all(
            bind=engine,
            tables=[User.__table__, Dataset.__table__, Campaign.__table__, AnalysisResult.__table__],
        )

        session = TestSession()
        try:
            # Mark rows eligible for ID-scoped cleanup before the first flush.
            rows_may_exist = True
            session.add(
                User(
                    id=user_id,
                    email=f"phase6-jsonb-{run_id}@example.invalid",
                    hashed_password="test-only-not-a-credential",
                    full_name="Phase 6 JSONB Integration Test",
                )
            )
            session.flush()

            session.add(
                Dataset(
                    id=dataset_id,
                    user_id=user_id,
                    filename="phase6-jsonb-test.csv",
                    file_path="/phase6-jsonb-test.csv",
                    status="PENDING",
                    row_count=1,
                )
            )
            session.flush()

            session.add_all([
                Campaign(
                    id=campaign_id,
                    dataset_id=dataset_id,
                    campaign_name="Phase 6 test campaign",
                    channel="Search",
                    impressions=100,
                    clicks=10,
                    spend=125.5,
                    conversions=4,
                    revenue=None,
                    date=None,
                    customer_segment="Returning",
                ),
                AnalysisResult(
                    id=result_id,
                    dataset_id=dataset_id,
                    kpis={"total_spend": 125.5, "total_revenue": None},
                    rankings={"top": [], "bottom": []},
                    trends=payload,
                    ai_recommendations=[],
                ),
            ])
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

        # A fresh session forces PostgreSQL JSONB decoding for the equality check.
        session = TestSession()
        try:
            loaded = session.get(AnalysisResult, result_id)
            assert loaded is not None
            assert loaded.trends == payload
            assert loaded.trends["channel_breakdown"] == payload["channel_breakdown"]
            assert loaded.trends["time_series"] == payload["time_series"]
            assert loaded.trends["dimension_breakdowns"] == payload["dimension_breakdowns"]
            assert loaded.trends["segmentation"] == payload["segmentation"]
            assert loaded.trends["forecasting"] == payload["forecasting"]

            def unexpected_recompute(*args, **kwargs):
                raise AssertionError("Cached analytics should not be recomputed")

            monkeypatch.setattr(
                "app.services.analysis_service.classify_campaign_cohorts",
                unexpected_recompute,
            )
            monkeypatch.setattr(
                "app.services.analysis_service.profile_segment_portfolio",
                unexpected_recompute,
            )
            monkeypatch.setattr(
                "app.services.analysis_service.run_forecasting_analysis",
                unexpected_recompute,
            )

            response = AnalysisService.get_results(
                dataset_id=dataset_id,
                current_user_id=user_id,
                db=session,
            )
            assert response["segmentation"] == payload["segmentation"]
            assert response["forecasting"] == payload["forecasting"]
        finally:
            session.close()
    finally:
        try:
            if rows_may_exist:
                cleanup_session = TestSession()
                try:
                    cleanup_session.query(AnalysisResult).filter(
                        AnalysisResult.id == result_id
                    ).delete(synchronize_session=False)
                    cleanup_session.query(Campaign).filter(
                        Campaign.id == campaign_id
                    ).delete(synchronize_session=False)
                    cleanup_session.query(Dataset).filter(
                        Dataset.id == dataset_id
                    ).delete(synchronize_session=False)
                    cleanup_session.query(User).filter(
                        User.id == user_id
                    ).delete(synchronize_session=False)
                    cleanup_session.commit()
                except Exception:
                    cleanup_session.rollback()
                    raise
                finally:
                    cleanup_session.close()
        finally:
            engine.dispose()
