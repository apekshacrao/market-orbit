from pathlib import Path
import sys
import pytest
from pydantic import ValidationError

from analytics.ai.groq_client import GroqClient
from analytics.ai.prompts import RECOMMENDATION_PROMPT_TEMPLATE
from analytics.insights.generator import generate_insights
from analytics.ai.schemas import (
    RecommendationCategory,
    RecommendationSource,
    SupportingEvidence,
    RecommendationItem,
    RecommendationBatch,
    RecommendationResponse,
    normalize_recommendation,
)
import analytics.ai as ai_package


# ---------------------------------------------------------------------------
# 1. Existing Module Baseline Tests
# ---------------------------------------------------------------------------

def test_ai_placeholder():
    """Original baseline placeholder test."""
    assert True


def test_ai_module_exports_and_functionality():
    """Verify that existing and new AI module entry points are exported and callable."""
    assert callable(generate_insights)
    assert callable(GroqClient)
    assert isinstance(RECOMMENDATION_PROMPT_TEMPLATE, str)
    assert issubclass(RecommendationItem, object)
    assert issubclass(RecommendationBatch, object)
    assert RecommendationResponse is RecommendationBatch
    # Verify package-level exports on analytics.ai
    assert hasattr(ai_package, "RecommendationCategory")
    assert hasattr(ai_package, "RecommendationSource")
    assert hasattr(ai_package, "SupportingEvidence")
    assert hasattr(ai_package, "RecommendationItem")
    assert hasattr(ai_package, "RecommendationBatch")
    assert hasattr(ai_package, "RecommendationResponse")
    assert hasattr(ai_package, "normalize_recommendation")


# ---------------------------------------------------------------------------
# 2. Valid Recommendation Acceptance
# ---------------------------------------------------------------------------

def test_valid_recommendation_item_full():
    """Verify acceptance of a fully populated, valid recommendation."""
    evidence = SupportingEvidence(
        metric="roas",
        observed_value=4.25,
        campaign_name="Search_Brand_Top",
        dimension="device",
        dimension_value="Mobile",
        benchmark_value=3.0,
        context={"conversions": 120, "spend": 450.0},
    )
    rec = RecommendationItem(
        id="rec-001",
        category=RecommendationCategory.CHANNEL_SCALING,
        title="Scale Mobile Search Channel",
        action="Increase budget by 15% on high-performing mobile search campaigns.",
        rationale="Mobile search campaigns demonstrate 4.25x ROAS against the 3.0x target.",
        supporting_evidence=evidence,
        limitations=["Assumes stable CPM on increased budget."],
        source=RecommendationSource.GROQ_LLM,
    )

    assert rec.id == "rec-001"
    assert rec.category == RecommendationCategory.CHANNEL_SCALING
    assert rec.category.value == "channel_scaling"
    assert rec.source == RecommendationSource.GROQ_LLM
    assert rec.source.value == "groq_llm"
    assert rec.title == "Scale Mobile Search Channel"
    assert rec.action.startswith("Increase budget")
    assert rec.description == rec.rationale
    assert rec.supporting_evidence is not None
    assert rec.supporting_evidence.observed_value == 4.25
    assert len(rec.limitations) == 1


def test_valid_recommendation_item_minimal():
    """Verify minimal valid recommendation without optional evidence or limitations."""
    rec = RecommendationItem(
        id="rec-002",
        category=RecommendationCategory.BUDGET_ALLOCATION,
        title="Reallocate Summer Budget",
        action="Shift underutilized budget to top campaigns.",
        rationale="Reallocating underutilized budget optimizes portfolio return.",
        source=RecommendationSource.DETERMINISTIC_FALLBACK,
    )

    assert rec.id == "rec-002"
    assert rec.supporting_evidence is None
    assert rec.limitations == []
    assert rec.description == rec.rationale
    assert rec.source == RecommendationSource.DETERMINISTIC_FALLBACK


def test_controlled_category_coverage():
    """Verify all 5 controlled categories are supported."""
    categories = [
        RecommendationCategory.BUDGET_ALLOCATION,
        RecommendationCategory.CREATIVE_OPTIMIZATION,
        RecommendationCategory.CHANNEL_SCALING,
        RecommendationCategory.WASTE_REDUCTION,
        RecommendationCategory.DATA_TRACKING,
    ]
    assert len(categories) == 5

    for cat in categories:
        rec = RecommendationItem(
            id=f"rec-{cat.value}",
            category=cat,
            title="Sample Title",
            action="Sample Action",
            rationale="Sample Rationale",
            source=RecommendationSource.DETERMINISTIC_FALLBACK,
        )
        assert rec.category == cat


def test_controlled_source_coverage():
    """Verify controlled sources: groq_llm and deterministic_fallback."""
    for src in [RecommendationSource.GROQ_LLM, RecommendationSource.DETERMINISTIC_FALLBACK]:
        rec = RecommendationItem(
            id="rec-src-test",
            category=RecommendationCategory.BUDGET_ALLOCATION,
            title="Title",
            action="Action",
            rationale="Rationale",
            source=src,
        )
        assert rec.source == src


# ---------------------------------------------------------------------------
# 3. Validation Errors: Missing and Malformed Fields
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("missing_field", ["id", "category", "title", "action", "rationale", "source"])
def test_missing_required_fields_rejection(missing_field: str):
    """Verify validation error when any required field is missing."""
    valid_data = {
        "id": "rec-003",
        "category": "budget_allocation",
        "title": "Valid Title",
        "action": "Valid Action",
        "rationale": "Valid Rationale",
        "source": "deterministic_fallback",
    }
    del valid_data[missing_field]

    with pytest.raises(ValidationError):
        RecommendationItem.model_validate(valid_data)


@pytest.mark.parametrize("empty_field", ["id", "title", "action", "rationale"])
def test_empty_string_required_fields_rejection(empty_field: str):
    """Verify that empty or whitespace-only required strings are rejected."""
    valid_data = {
        "id": "rec-003",
        "category": "budget_allocation",
        "title": "Valid Title",
        "action": "Valid Action",
        "rationale": "Valid Rationale",
        "source": "deterministic_fallback",
    }
    valid_data[empty_field] = "   "

    with pytest.raises(ValidationError):
        RecommendationItem.model_validate(valid_data)


def test_invalid_category_rejection():
    """Verify that unknown categories are rejected."""
    with pytest.raises(ValidationError):
        RecommendationItem(
            id="rec-bad-cat",
            category="unsupported_category",  # type: ignore
            title="Title",
            action="Action",
            rationale="Rationale",
            source=RecommendationSource.DETERMINISTIC_FALLBACK,
        )


def test_invalid_source_rejection():
    """Verify that uncontrolled sources are rejected."""
    with pytest.raises(ValidationError):
        RecommendationItem(
            id="rec-bad-src",
            category=RecommendationCategory.BUDGET_ALLOCATION,
            title="Title",
            action="Action",
            rationale="Rationale",
            source="untrusted_ai_model",  # type: ignore
        )


# ---------------------------------------------------------------------------
# 4. Numeric Evidence Validation & Non-Finite Number Rejection
# ---------------------------------------------------------------------------

def test_evidence_rejects_nan():
    """Verify that NaN values in observed_value or benchmark_value are rejected."""
    with pytest.raises(ValidationError):
        SupportingEvidence(metric="roas", observed_value=float("nan"))

    with pytest.raises(ValidationError):
        SupportingEvidence(metric="roas", benchmark_value=float("nan"))


def test_evidence_rejects_inf():
    """Verify that positive and negative infinity values are rejected."""
    with pytest.raises(ValidationError):
        SupportingEvidence(metric="roas", observed_value=float("inf"))

    with pytest.raises(ValidationError):
        SupportingEvidence(metric="roas", observed_value=float("-inf"))


def test_evidence_rejects_nan_in_context():
    """Verify that NaN or infinity inside evidence context dictionary is rejected."""
    with pytest.raises(ValidationError):
        SupportingEvidence(metric="spend", context={"bad_metric": float("nan")})

    with pytest.raises(ValidationError):
        SupportingEvidence(metric="spend", context={"bad_metric": float("inf")})


def test_evidence_metric_required_and_stripped():
    """Verify metric cannot be empty or whitespace."""
    with pytest.raises(ValidationError):
        SupportingEvidence(metric="  ")

    evidence = SupportingEvidence(metric="  ROAS  ", observed_value=3.2)
    assert evidence.metric == "roas"


def test_evidence_missing_optional_values_not_fabricated():
    """Verify missing optional values stay None and are not populated with invented numbers."""
    evidence = SupportingEvidence(metric="conversions")
    assert evidence.metric == "conversions"
    assert evidence.observed_value is None
    assert evidence.campaign_name is None
    assert evidence.dimension is None
    assert evidence.dimension_value is None
    assert evidence.benchmark_value is None
    assert evidence.context is None


# ---------------------------------------------------------------------------
# 5. Limitations Validation
# ---------------------------------------------------------------------------

def test_limitations_valid_and_cleaned():
    """Verify limitations list cleans whitespace and defaults properly."""
    rec = RecommendationItem(
        id="rec-lim-1",
        category=RecommendationCategory.WASTE_REDUCTION,
        title="Pause Waste",
        action="Pause campaign",
        rationale="High CPA with zero conversions",
        limitations=["  High seasonal volatility in segment  ", "Competitor sale active"],
        source=RecommendationSource.DETERMINISTIC_FALLBACK,
    )
    assert rec.limitations == [
        "High seasonal volatility in segment",
        "Competitor sale active",
    ]


def test_limitations_rejects_empty_strings():
    """Verify limitations list rejects empty string items."""
    with pytest.raises(ValidationError):
        RecommendationItem(
            id="rec-lim-bad",
            category=RecommendationCategory.WASTE_REDUCTION,
            title="Pause Waste",
            action="Pause campaign",
            rationale="High CPA with zero conversions",
            limitations=["Valid limitation", "   "],
            source=RecommendationSource.DETERMINISTIC_FALLBACK,
        )


def test_limitations_rejects_non_list():
    """Verify limitations rejects non-list input."""
    with pytest.raises(ValidationError):
        RecommendationItem(
            id="rec-lim-bad2",
            category=RecommendationCategory.WASTE_REDUCTION,
            title="Pause Waste",
            action="Pause campaign",
            rationale="High CPA",
            limitations="string is not a list",  # type: ignore
            source=RecommendationSource.DETERMINISTIC_FALLBACK,
        )


# ---------------------------------------------------------------------------
# 6. JSON Round-Trip Serialization
# ---------------------------------------------------------------------------

def test_json_round_trip_serialization():
    """Verify that serialization to JSON and deserialization reproduces exact models."""
    evidence = SupportingEvidence(
        metric="cpa",
        observed_value=54.20,
        campaign_name="Summer_Promo",
        dimension="location",
        dimension_value="North",
        benchmark_value=40.0,
        context={"conversions": 10, "spend": 542.0},
    )
    original = RecommendationItem(
        id="rec-roundtrip-01",
        category=RecommendationCategory.WASTE_REDUCTION,
        title="Reduce CPA on Summer Promo",
        action="Narrow geographic targeting to profitable regions.",
        rationale="Observed CPA ($54.20) exceeds target benchmark ($40.00).",
        supporting_evidence=evidence,
        limitations=["Requires minimum 50 conversions for statistical power."],
        source=RecommendationSource.GROQ_LLM,
    )

    json_str = original.to_json()
    assert isinstance(json_str, str)
    assert "NaN" not in json_str
    assert "Infinity" not in json_str

    deserialized = RecommendationItem.model_validate_json(json_str)
    assert deserialized.id == original.id
    assert deserialized.category == original.category
    assert deserialized.title == original.title
    assert deserialized.action == original.action
    assert deserialized.rationale == original.rationale
    assert deserialized.source == original.source
    assert deserialized.limitations == original.limitations
    assert deserialized.supporting_evidence is not None
    assert deserialized.supporting_evidence.observed_value == 54.20
    assert deserialized.supporting_evidence.context is not None
    assert deserialized.supporting_evidence.context["spend"] == 542.0


# ---------------------------------------------------------------------------
# 7. RecommendationBatch / Container Model
# ---------------------------------------------------------------------------

def test_recommendation_batch_empty():
    """Verify empty RecommendationBatch."""
    batch = RecommendationBatch()
    assert batch.recommendations == []
    assert batch.dataset_id is None
    assert batch.to_list() == []


def test_recommendation_batch_multiple_items():
    """Verify batch with multiple items serializes cleanly."""
    rec1 = RecommendationItem(
        id="rec-b-01",
        category=RecommendationCategory.BUDGET_ALLOCATION,
        title="Title 1",
        action="Action 1",
        rationale="Rationale 1",
        source=RecommendationSource.DETERMINISTIC_FALLBACK,
    )
    rec2 = RecommendationItem(
        id="rec-b-02",
        category=RecommendationCategory.CREATIVE_OPTIMIZATION,
        title="Title 2",
        action="Action 2",
        rationale="Rationale 2",
        source=RecommendationSource.GROQ_LLM,
    )

    batch = RecommendationBatch(
        recommendations=[rec1, rec2],
        dataset_id="dataset-test-123",
        generated_at="2026-10-14T21:40:00Z",
    )

    assert len(batch.recommendations) == 2
    raw_list = batch.to_list()
    assert isinstance(raw_list, list)
    assert len(raw_list) == 2
    assert raw_list[0]["id"] == "rec-b-01"
    assert raw_list[1]["category"] == "creative_optimization"

    # Test batch JSON round-trip
    batch_json = batch.to_json()
    deserialized_batch = RecommendationBatch.model_validate_json(batch_json)
    assert len(deserialized_batch.recommendations) == 2
    assert deserialized_batch.dataset_id == "dataset-test-123"


# ---------------------------------------------------------------------------
# 8. Backward Compatibility & Normalization Adapter
# ---------------------------------------------------------------------------

def test_legacy_shape_normalization():
    """Verify legacy {'title', 'description', 'action'} dicts are normalized into valid RecommendationItem."""
    legacy_data = {
        "title": "Scale High-ROAS Campaigns",
        "description": "Increase budget for top-performing channels demonstrating ROAS > 3.0x.",
        "action": "Increase Budget by 20%",
    }

    item = normalize_recommendation(legacy_data, default_id="rec-legacy-001")
    assert item.id == "rec-legacy-001"
    assert item.title == "Scale High-ROAS Campaigns"
    assert item.action == "Increase Budget by 20%"
    assert item.rationale == legacy_data["description"]
    assert item.description == legacy_data["description"]
    # Inferred from 'Scale'
    assert item.category == RecommendationCategory.CHANNEL_SCALING
    # Marked as deterministic fallback (not fabricated as LLM)
    assert item.source == RecommendationSource.DETERMINISTIC_FALLBACK
    assert item.supporting_evidence is None
    assert item.limitations == []


def test_legacy_pause_creative_normalization():
    """Verify second legacy mock shape ('Pause Underperforming Creatives') normalizes properly."""
    legacy_data = {
        "title": "Pause Underperforming Creatives",
        "description": "Reallocate spend from campaigns with high CPA and low conversion rates.",
        "action": "Pause Low-Performing Ad Sets",
    }

    item = normalize_recommendation(legacy_data)
    assert item.title == "Pause Underperforming Creatives"
    assert item.category == RecommendationCategory.CREATIVE_OPTIMIZATION
    assert item.source == RecommendationSource.DETERMINISTIC_FALLBACK


def test_groq_client_mock_batch_normalization():
    """Verify current GroqClient mock output can be normalized into RecommendationBatch."""
    client = GroqClient()
    mock_recs = client.generate_recommendations({}, {})
    assert len(mock_recs) == 2

    batch = RecommendationBatch.from_list(mock_recs, dataset_id="mock-ds")
    assert len(batch.recommendations) == 2
    for item in batch.recommendations:
        assert isinstance(item, RecommendationItem)
        assert item.source == RecommendationSource.DETERMINISTIC_FALLBACK
        assert item.description is not None
        assert item.action is not None


def test_normalize_malformed_legacy_rejection():
    """Verify normalize_recommendation rejects invalid payloads."""
    with pytest.raises(ValueError):
        normalize_recommendation("not a dict")  # type: ignore

    with pytest.raises(ValueError):
        normalize_recommendation({"title": "", "action": "Act", "description": "Desc"})

    with pytest.raises(ValueError):
        normalize_recommendation({"title": "T", "action": "", "description": "Desc"})

    with pytest.raises(ValueError):
        normalize_recommendation({"title": "T", "action": "Act"})


def test_backend_response_compatibility():
    """Verify that RecommendationBatch.to_list() satisfies backend AnalysisResultResponse."""
    backend_path = str(Path(__file__).resolve().parents[2] / "backend")
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)

    try:
        # pyrefly: ignore [missing-import]
        from app.schemas.result import AnalysisResultResponse
    except ImportError:
        pytest.skip("Backend schemas not available")

    rec = RecommendationItem(
        id="rec-compat-001",
        category=RecommendationCategory.BUDGET_ALLOCATION,
        title="Reallocate Budget",
        action="Shift 10% budget",
        rationale="Budget rebalancing",
        source=RecommendationSource.DETERMINISTIC_FALLBACK,
    )
    batch = RecommendationBatch(recommendations=[rec])

    response_data = {
        "dataset_id": "test-dataset",
        "kpis": {
            "totalSpend": 1000.0,
            "totalRevenue": 2500.0,
            "overallRoas": 2.5,
            "avgConversionRate": 0.05,
            "avgCpa": 20.0,
        },
        "performance": [],
        "topCampaigns": [],
        "bottomCampaigns": [],
        "trends": [],
        "recommendations": batch.to_list(),
    }

    validated_response = AnalysisResultResponse.model_validate(response_data)
    assert len(validated_response.recommendations) == 1
    assert validated_response.recommendations[0]["id"] == "rec-compat-001"
    assert validated_response.recommendations[0]["description"] == "Budget rebalancing"
