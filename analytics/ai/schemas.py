"""
Validated Pydantic models and schemas for AI recommendations and supporting evidence.

Phase 5.1: Defines a strict, validated contract for recommendation output,
controlled category/source vocabularies, non-finite numeric rejection, and backward compatibility.
"""

from enum import Enum
import math
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator


class RecommendationCategory(str, Enum):
    """Controlled vocabulary for recommendation operational categories."""
    BUDGET_ALLOCATION = "budget_allocation"
    CREATIVE_OPTIMIZATION = "creative_optimization"
    CHANNEL_SCALING = "channel_scaling"
    WASTE_REDUCTION = "waste_reduction"
    DATA_TRACKING = "data_tracking"


class RecommendationSource(str, Enum):
    """
    Controlled vocabulary distinguishing verified LLM output from deterministic fallback.

    Must ONLY be marked GROQ_LLM when generated through real LLM inference.
    """
    GROQ_LLM = "groq_llm"
    DETERMINISTIC_FALLBACK = "deterministic_fallback"


class SupportingEvidence(BaseModel):
    """
    Verifiable observation supporting a recommendation.

    Grounds recommendations in observed metrics, campaign identifiers, or dimensions
    without requiring unavailable values or inventing benchmarks.
    """
    metric: str
    observed_value: Optional[float] = None
    campaign_name: Optional[str] = None
    dimension: Optional[str] = None
    dimension_value: Optional[str] = None
    benchmark_value: Optional[float] = None
    context: Optional[Dict[str, Any]] = None

    @field_validator("metric")
    @classmethod
    def validate_metric(cls, v: str) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("Metric name must be a non-empty string.")
        return v.strip().lower()

    @field_validator("observed_value", "benchmark_value", mode="before")
    @classmethod
    def validate_finite_number(cls, v: Any, info) -> Optional[float]:
        if v is None:
            return None
        try:
            val = float(v)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Numeric evidence for '{info.field_name}' must be a valid number, got {v!r}") from exc
        if math.isnan(val) or math.isinf(val):
            raise ValueError(f"Numeric evidence for '{info.field_name}' must be finite (NaN and Inf are not permitted).")
        return val

    @field_validator("campaign_name", "dimension", "dimension_value")
    @classmethod
    def validate_optional_strings(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        if not isinstance(v, str) or not v.strip():
            return None
        return v.strip()

    @field_validator("context", mode="before")
    @classmethod
    def validate_context(cls, v: Any) -> Optional[Dict[str, Any]]:
        if v is None:
            return None
        if not isinstance(v, dict):
            raise ValueError("Context must be a dictionary.")
        for key, val in v.items():
            if isinstance(val, (float, int)) and not isinstance(val, bool):
                if math.isnan(val) or math.isinf(val):
                    raise ValueError(f"Context metric '{key}' must be finite (NaN and Inf are not permitted).")
        return v

    def to_dict(self) -> Dict[str, Any]:
        """Serialize evidence to dictionary."""
        return self.model_dump(mode="json")


class RecommendationItem(BaseModel):
    """
    Validated recommendation contract adhering to Phase 5.1 requirements.

    Fields:
    - id: Deterministic/unique recommendation identifier
    - category: Controlled category (budget_allocation, creative_optimization, etc.)
    - title: Brief descriptive title
    - action: Specific actionable directive
    - rationale: Evidence-grounded rationale explaining the action
    - supporting_evidence: Optional verifiable observation or list of observations
    - limitations: Known limitations or risks associated with the recommendation
    - source: Controlled source (groq_llm or deterministic_fallback)
    - description: Optional legacy alias kept in sync with rationale for backward compatibility
    """
    id: str
    category: RecommendationCategory
    title: str
    action: str
    rationale: str
    supporting_evidence: Optional[SupportingEvidence] = None
    limitations: List[str] = Field(default_factory=list)
    source: RecommendationSource
    description: Optional[str] = None

    @field_validator("supporting_evidence", mode="before")
    @classmethod
    def validate_supporting_evidence(cls, v: Any) -> Any:
        if isinstance(v, list):
            if not v:
                return None
            return v[0]
        return v

    @field_validator("id", "title", "action", "rationale")
    @classmethod
    def validate_required_strings(cls, v: str, info) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError(f"Field '{info.field_name}' must be a non-empty string.")
        return v.strip()

    @field_validator("category", mode="before")
    @classmethod
    def validate_category(cls, v: Any) -> Any:
        if isinstance(v, str):
            cleaned = v.strip().lower().replace(" ", "_").replace("-", "_")
            for cat in RecommendationCategory:
                if cleaned == cat.value:
                    return cat
            # Return cleaned string so Pydantic's enum validator produces standard message on failure
            return cleaned
        return v

    @field_validator("source", mode="before")
    @classmethod
    def validate_source(cls, v: Any) -> Any:
        if isinstance(v, str):
            cleaned = v.strip().lower().replace(" ", "_").replace("-", "_")
            if cleaned in ("groq_llm", "groq", "llm"):
                return RecommendationSource.GROQ_LLM
            if cleaned in ("deterministic_fallback", "deterministic", "fallback"):
                return RecommendationSource.DETERMINISTIC_FALLBACK
            return cleaned
        return v

    @field_validator("limitations", mode="before")
    @classmethod
    def validate_limitations(cls, v: Any) -> List[str]:
        if v is None:
            return []
        if not isinstance(v, list):
            raise ValueError("Field 'limitations' must be a list of strings.")
        cleaned = []
        for item in v:
            if not isinstance(item, str) or not item.strip():
                raise ValueError("All limitations must be non-empty strings.")
            cleaned.append(item.strip())
        return cleaned

    @model_validator(mode="after")
    def sync_description(self) -> "RecommendationItem":
        # Ensure description is populated for backward compatibility with legacy consumers
        if not self.description:
            self.description = self.rationale
        return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert recommendation to a JSON-serializable dictionary."""
        return self.model_dump(mode="json")

    def to_json(self, indent: Optional[int] = None) -> str:
        """Convert recommendation to a JSON string."""
        return self.model_dump_json(indent=indent)


class RecommendationBatch(BaseModel):
    """Container model representing a collection of recommendations and optional metadata."""
    recommendations: List[RecommendationItem] = Field(default_factory=list)
    dataset_id: Optional[str] = None
    generated_at: Optional[str] = None

    def to_list(self) -> List[Dict[str, Any]]:
        """Serialize recommendations to a list of dictionaries."""
        return [rec.model_dump(mode="json") for rec in self.recommendations]

    def to_json(self, indent: Optional[int] = None) -> str:
        """Serialize batch to a JSON string."""
        return self.model_dump_json(indent=indent)

    @classmethod
    def from_list(
        cls,
        items: List[Dict[str, Any]],
        dataset_id: Optional[str] = None,
        source: Optional[Union[RecommendationSource, str]] = None,
    ) -> "RecommendationBatch":
        """Build and validate a RecommendationBatch from raw dictionaries."""
        normalized = []
        for idx, item in enumerate(items, 1):
            normalized.append(
                normalize_recommendation(
                    item,
                    default_id=f"rec-{idx:03d}",
                    default_source=source or RecommendationSource.DETERMINISTIC_FALLBACK,
                )
            )
        return cls(recommendations=normalized, dataset_id=dataset_id)


# Alias for compatibility with differing naming preferences
RecommendationResponse = RecommendationBatch


def _infer_category(title: str, action: str) -> RecommendationCategory:
    """Heuristic fallback category inference for legacy recommendation dictionaries."""
    combined = f"{title} {action}".lower()
    if any(k in combined for k in ("track", "revenue", "data", "missing")):
        return RecommendationCategory.DATA_TRACKING
    if any(k in combined for k in ("creative", "ad set", "copy", "visual")):
        return RecommendationCategory.CREATIVE_OPTIMIZATION
    if any(k in combined for k in ("pause", "waste", "underperforming", "drain")):
        return RecommendationCategory.WASTE_REDUCTION
    if any(k in combined for k in ("scale", "channel", "expand", "volume")):
        return RecommendationCategory.CHANNEL_SCALING
    return RecommendationCategory.BUDGET_ALLOCATION


def normalize_recommendation(
    data: Dict[str, Any],
    default_source: RecommendationSource = RecommendationSource.DETERMINISTIC_FALLBACK,
    default_id: Optional[str] = None,
) -> RecommendationItem:
    """
    Normalizes a recommendation dictionary (legacy or current) into a validated RecommendationItem.

    Handles legacy shapes like:
    {"title": "...", "description": "...", "action": "..."}
    by mapping description to rationale and assigning deterministic defaults without fabricating evidence.
    """
    if not isinstance(data, dict):
        raise ValueError(f"Recommendation payload must be a dictionary, got {type(data).__name__}")

    # Check if data already conforms to the full modern schema
    has_full_contract = (
        "id" in data
        and "category" in data
        and "rationale" in data
        and "source" in data
    )

    if has_full_contract:
        return RecommendationItem.model_validate(data)

    # Legacy shape adaptation
    title = data.get("title")
    action = data.get("action")
    if not title or not isinstance(title, str) or not title.strip():
        raise ValueError("Recommendation title must be a non-empty string.")
    if not action or not isinstance(action, str) or not action.strip():
        raise ValueError("Recommendation action must be a non-empty string.")

    rationale = data.get("rationale") or data.get("description")
    if not rationale or not isinstance(rationale, str) or not rationale.strip():
        raise ValueError("Recommendation rationale or description must be a non-empty string.")

    rec_id = data.get("id") or default_id or f"rec-legacy-{abs(hash(title)) % 10000:04d}"
    category = data.get("category") or _infer_category(title, action)
    source = data.get("source") or default_source
    limitations = data.get("limitations") or []
    supporting_evidence = data.get("supporting_evidence")

    payload = {
        "id": rec_id,
        "category": category,
        "title": title.strip(),
        "action": action.strip(),
        "rationale": rationale.strip(),
        "description": data.get("description") or rationale.strip(),
        "supporting_evidence": supporting_evidence,
        "limitations": limitations,
        "source": source,
    }
    return RecommendationItem.model_validate(payload)
