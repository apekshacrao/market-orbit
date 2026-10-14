from pathlib import Path
import sys
from unittest.mock import MagicMock
import httpx
import pytest
from pydantic import ValidationError
import groq

from analytics.ai.groq_client import (
    GroqClient,
    DEFAULT_GROQ_MODEL,
    DEFAULT_GROQ_TIMEOUT,
    DEFAULT_GROQ_MAX_RETRIES,
    GroqClientError,
    GroqConfigurationError,
    GroqAuthenticationError,
    GroqRateLimitError,
    GroqTimeoutError,
    GroqConnectionError,
    GroqEmptyResponseError,
    GroqAPIError,
    load_groq_config,
)
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
    assert hasattr(ai_package, "GroqConfigurationError")
    assert hasattr(ai_package, "GroqAuthenticationError")
    assert hasattr(ai_package, "GroqRateLimitError")
    assert hasattr(ai_package, "GroqTimeoutError")
    assert hasattr(ai_package, "GroqConnectionError")
    assert hasattr(ai_package, "GroqEmptyResponseError")
    assert hasattr(ai_package, "GroqAPIError")
    assert hasattr(ai_package, "DEFAULT_GROQ_MODEL")
    assert hasattr(ai_package, "DEFAULT_GROQ_TIMEOUT")
    assert hasattr(ai_package, "DEFAULT_GROQ_MAX_RETRIES")
    assert hasattr(ai_package, "load_groq_config")


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


# ---------------------------------------------------------------------------
# 9. Phase 5.2: GroqClient & Provider Configuration Tests
# ---------------------------------------------------------------------------

def test_client_initialization_defaults(monkeypatch):
    """Verify GroqClient initializes with default model, timeout, and retries."""
    monkeypatch.setenv("GROQ_API_KEY", "test_key_abc123")
    client = GroqClient()

    assert client.model == DEFAULT_GROQ_MODEL
    assert client.timeout == DEFAULT_GROQ_TIMEOUT
    assert client.max_retries == DEFAULT_GROQ_MAX_RETRIES
    assert client.is_configured is True


def test_client_initialization_explicit_params():
    """Verify GroqClient accepts explicit configuration parameters."""
    client = GroqClient(
        api_key="explicit_key_456",
        model="llama-3.1-8b-instant",
        timeout=8.5,
        max_retries=3,
    )

    assert client.model == "llama-3.1-8b-instant"
    assert client.timeout == 8.5
    assert client.max_retries == 3
    assert client.is_configured is True


def test_client_invalid_timeout_and_retries():
    """Verify GroqClient rejects non-positive timeouts and negative retries."""
    with pytest.raises(GroqConfigurationError, match="positive number of seconds"):
        GroqClient(api_key="key", timeout=0.0)

    with pytest.raises(GroqConfigurationError, match="positive number of seconds"):
        GroqClient(api_key="key", timeout=-2.5)

    with pytest.raises(GroqConfigurationError, match="non-negative integer"):
        GroqClient(api_key="key", max_retries=-1)


def test_client_missing_key_behavior(monkeypatch):
    """Verify behavior when GROQ_API_KEY is missing or empty."""
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    # Ensure config loading resolves to empty key
    monkeypatch.setattr("analytics.ai.groq_client.load_groq_config", lambda: {
        "api_key": "",
        "model": DEFAULT_GROQ_MODEL,
        "timeout": DEFAULT_GROQ_TIMEOUT,
        "max_retries": DEFAULT_GROQ_MAX_RETRIES,
    })

    client = GroqClient(api_key="")
    assert client.is_configured is False

    with pytest.raises(GroqConfigurationError, match="GROQ_API_KEY is not configured"):
        _ = client.client

    with pytest.raises(GroqConfigurationError, match="GROQ_API_KEY is not configured"):
        client.chat_completion([{"role": "user", "content": "test"}])


def test_client_repr_and_str_redact_secrets():
    """Verify __repr__ and __str__ never display the real API key."""
    secret_key = "gsk_super_secret_production_key_xyz123"
    client = GroqClient(api_key=secret_key, model="llama-3.3-70b-versatile")

    repr_str = repr(client)
    str_str = str(client)

    assert secret_key not in repr_str
    assert secret_key not in str_str
    assert "gsk_" not in repr_str
    assert "configured=True" in repr_str


def test_load_groq_config_environment_precedence(monkeypatch):
    """Verify load_groq_config prioritizes direct environment variables."""
    monkeypatch.setenv("GROQ_API_KEY", "env_override_key")
    monkeypatch.setenv("GROQ_MODEL", "mixtral-8x7b-32768")
    monkeypatch.setenv("GROQ_TIMEOUT", "25.0")
    monkeypatch.setenv("GROQ_MAX_RETRIES", "4")

    config = load_groq_config()
    assert config["api_key"] == "env_override_key"
    assert config["model"] == "mixtral-8x7b-32768"
    assert config["timeout"] == 25.0
    assert config["max_retries"] == 4


def test_chat_completion_success_mocked():
    """Verify chat_completion successfully extracts response content from a mocked Groq provider."""
    client = GroqClient(api_key="mock_test_key_123")

    mock_sdk_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Actionable recommendation generated by LLM."
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_sdk_client.chat.completions.create.return_value = mock_response

    client._client = mock_sdk_client

    messages = [{"role": "user", "content": "Analyze marketing spend."}]
    result = client.chat_completion(messages, temperature=0.1)

    assert result == "Actionable recommendation generated by LLM."
    mock_sdk_client.chat.completions.create.assert_called_once_with(
        messages=messages,
        model=DEFAULT_GROQ_MODEL,
        temperature=0.1,
    )


def test_chat_completion_connection_reuse():
    """Verify GroqClient reuses the underlying client instance across multiple requests."""
    client = GroqClient(api_key="mock_test_key_123")

    mock_choice = MagicMock()
    mock_choice.message.content = "Response content"
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    mock_sdk_client = MagicMock()
    mock_sdk_client.chat.completions.create.return_value = mock_response

    client._client = mock_sdk_client

    res1 = client.chat_completion([{"role": "user", "content": "1"}])
    res2 = client.chat_completion([{"role": "user", "content": "2"}])

    assert res1 == "Response content"
    assert res2 == "Response content"
    assert mock_sdk_client.chat.completions.create.call_count == 2
    # Verify underlying client was not re-instantiated
    assert client._client is mock_sdk_client


def test_chat_completion_invalid_messages():
    """Verify chat_completion rejects invalid messages arguments."""
    client = GroqClient(api_key="mock_key")
    with pytest.raises(ValueError, match="non-empty list"):
        client.chat_completion([])

    with pytest.raises(ValueError, match="non-empty list"):
        client.chat_completion("not a list")  # type: ignore


@pytest.mark.parametrize("empty_payload", [
    MagicMock(choices=[]),
    MagicMock(choices=[MagicMock(message=None)]),
    MagicMock(choices=[MagicMock(message=MagicMock(content=""))]),
    MagicMock(choices=[MagicMock(message=MagicMock(content="   "))]),
])
def test_chat_completion_empty_response_handling(empty_payload):
    """Verify GroqEmptyResponseError is raised when the provider returns empty or malformed choices."""
    client = GroqClient(api_key="mock_key")
    mock_sdk_client = MagicMock()
    mock_sdk_client.chat.completions.create.return_value = empty_payload
    client._client = mock_sdk_client

    with pytest.raises(GroqEmptyResponseError):
        client.chat_completion([{"role": "user", "content": "test"}])


def test_chat_completion_authentication_error():
    """Verify AuthenticationError is mapped to GroqAuthenticationError with sanitized message."""
    client = GroqClient(api_key="gsk_secret_auth_token_999")
    req = httpx.Request("POST", "https://api.groq.com/chat/completions")
    res = httpx.Response(401, request=req)

    mock_sdk_client = MagicMock()
    mock_sdk_client.chat.completions.create.side_effect = groq.AuthenticationError(
        "Invalid API key gsk_secret_auth_token_999 provided",
        response=res,
        body=None,
    )
    client._client = mock_sdk_client

    with pytest.raises(GroqAuthenticationError) as exc_info:
        client.chat_completion([{"role": "user", "content": "test"}])

    error_str = str(exc_info.value)
    assert "gsk_secret_auth_token_999" not in error_str
    assert "[REDACTED_API_KEY]" in error_str


def test_chat_completion_rate_limit_error():
    """Verify RateLimitError is mapped to GroqRateLimitError."""
    client = GroqClient(api_key="mock_key")
    req = httpx.Request("POST", "https://api.groq.com/chat/completions")
    res = httpx.Response(429, request=req)

    mock_sdk_client = MagicMock()
    mock_sdk_client.chat.completions.create.side_effect = groq.RateLimitError(
        "Rate limit exceeded (TPM)",
        response=res,
        body=None,
    )
    client._client = mock_sdk_client

    with pytest.raises(GroqRateLimitError, match="Rate limit exceeded"):
        client.chat_completion([{"role": "user", "content": "test"}])


def test_chat_completion_timeout_error():
    """Verify APITimeoutError is mapped to GroqTimeoutError."""
    client = GroqClient(api_key="mock_key")
    req = httpx.Request("POST", "https://api.groq.com/chat/completions")

    mock_sdk_client = MagicMock()
    mock_sdk_client.chat.completions.create.side_effect = groq.APITimeoutError(request=req)
    client._client = mock_sdk_client

    with pytest.raises(GroqTimeoutError):
        client.chat_completion([{"role": "user", "content": "test"}])


def test_chat_completion_connection_error():
    """Verify APIConnectionError is mapped to GroqConnectionError."""
    client = GroqClient(api_key="mock_key")
    req = httpx.Request("POST", "https://api.groq.com/chat/completions")

    mock_sdk_client = MagicMock()
    mock_sdk_client.chat.completions.create.side_effect = groq.APIConnectionError(request=req)
    client._client = mock_sdk_client

    with pytest.raises(GroqConnectionError):
        client.chat_completion([{"role": "user", "content": "test"}])


def test_chat_completion_api_and_server_error():
    """Verify InternalServerError and BadRequestError are mapped to GroqAPIError."""
    client = GroqClient(api_key="mock_key")
    req = httpx.Request("POST", "https://api.groq.com/chat/completions")
    res_500 = httpx.Response(500, request=req)

    mock_sdk_client = MagicMock()
    mock_sdk_client.chat.completions.create.side_effect = groq.InternalServerError(
        "Groq internal processing error",
        response=res_500,
        body=None,
    )
    client._client = mock_sdk_client

    with pytest.raises(GroqAPIError, match="internal processing error"):
        client.chat_completion([{"role": "user", "content": "test"}])


def test_error_sanitization_masks_api_keys():
    """Verify error sanitization scrubs raw API keys and standard Groq key patterns."""
    client = GroqClient(api_key="custom_secret_key_777")
    raw_message = "Failed for custom_secret_key_777 with token gsk_abcdef1234567890qwerty"
    sanitized = client._sanitize(raw_message)

    assert "custom_secret_key_777" not in sanitized
    assert "gsk_abcdef1234567890qwerty" not in sanitized
    assert sanitized.count("[REDACTED_API_KEY]") == 2


def test_generate_recommendations_compatibility_mode():
    """Verify generate_recommendations preserves compatibility without claiming live LLM inference."""
    client = GroqClient()
    recs = client.generate_recommendations({}, {})

    assert isinstance(recs, list)
    assert len(recs) == 2
    for item in recs:
        assert "title" in item
        assert "action" in item
        assert "description" in item
        # Explicit source attribution
        assert item.get("source") == "deterministic_fallback"
