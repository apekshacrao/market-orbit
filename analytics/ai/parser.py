"""
Structured response parser and validator for Market Orbit AI recommendations.

Phase 5.4: Converts raw LLM output into validated RecommendationBatch objects,
enforcing strict JSON decoding, single markdown code-fence removal, non-finite numeric
rejection, controlled category/source attribution, and all-or-nothing batch validation.
"""

import json
import re
from typing import Any, Dict, List, Optional, Union
from pydantic import ValidationError

from analytics.ai.schemas import (
    RecommendationCategory,
    RecommendationItem,
    RecommendationBatch,
    RecommendationSource,
    SupportingEvidence,
)


class RecommendationParserError(ValueError):
    """Base exception for all AI recommendation response parsing and validation errors."""


class ResponseParsingError(RecommendationParserError):
    """Raised when raw LLM response text cannot be parsed as valid strict JSON."""


class ResponseValidationError(RecommendationParserError):
    """Raised when parsed JSON does not conform to the canonical recommendation contract."""


def extract_json_payload(raw_text: str) -> str:
    """
    Extracts the JSON payload from raw LLM text, stripping a single surrounding
    Markdown code fence if present.

    Args:
        raw_text: Raw string returned by model.

    Returns:
        Cleaned JSON string ready for parsing.

    Raises:
        ResponseParsingError: If text is empty or has a malformed markdown fence.
    """
    if not isinstance(raw_text, str):
        raise ResponseParsingError(
            f"Expected string input from LLM, got {type(raw_text).__name__}."
        )

    text = raw_text.strip()
    if not text:
        raise ResponseParsingError("Raw response text is empty or whitespace-only.")

    # Check for single surrounding markdown code fence
    if text.startswith("```"):
        # Match opening fence ``` or ```json or ```JSON with optional whitespace and newline
        match = re.match(r"^```(?:json|JSON)?\s*\n", text)
        if match:
            if not text.endswith("```"):
                raise ResponseParsingError(
                    "Malformed markdown code fence: Opening fence found without matching closing fence."
                )
            opening_len = match.end()
            inner = text[opening_len:-3].strip()
            if not inner:
                raise ResponseParsingError("Empty JSON content inside markdown code fence.")
            return inner
        else:
            # Single-line or irregular fence without trailing newline after opening fence
            if text.endswith("```") and len(text) >= 6:
                stripped = text[3:-3].strip()
                if stripped.lower().startswith("json"):
                    stripped = stripped[4:].strip()
                if not stripped:
                    raise ResponseParsingError("Empty JSON content inside markdown code fence.")
                return stripped
            raise ResponseParsingError("Malformed markdown code fence structure.")

    return text


def _reject_constant(val: str) -> None:
    """JSON parse_constant handler that strictly forbids NaN, Infinity, and -Infinity."""
    raise ResponseParsingError(
        f"Non-finite numeric constant '{val}' (NaN or Infinity) is forbidden in recommendation payloads."
    )


def parse_recommendations(
    raw_text: str,
    expected_source: Optional[Union[RecommendationSource, str]] = None,
    enforce_source: bool = True,
    dataset_id: Optional[str] = None,
) -> RecommendationBatch:
    """
    Parses and strictly validates raw LLM output against the canonical RecommendationBatch contract.

    Validation Rules:
    1. Extracts JSON payload, stripping a single surrounding markdown code fence if present.
    2. Strictly decodes JSON, forbidding non-finite constants (NaN, Infinity).
    3. Accepts top-level JSON list or object with 'recommendations' list.
    4. Handles empty recommendation lists as valid empty batches.
    5. Rejects unexpected top-level structures (primitives, dicts without 'recommendations').
    6. Validates every item against RecommendationItem schema (all-or-nothing policy).
    7. Validates that categories match RecommendationCategory enum members.
    8. Enforces honest source attribution against expected_source (preventing false groq_llm claims).
    9. Validates supporting evidence, ensuring finite numbers and non-empty metrics.
    10. Synchronizes legacy description with rationale without losing distinction.

    Args:
        raw_text: Raw text string returned by the LLM.
        expected_source: Expected RecommendationSource enum or string (e.g. RecommendationSource.GROQ_LLM).
        enforce_source: If True, validates item source against expected_source.
        dataset_id: Optional dataset UUID to attach to the batch.

    Returns:
        Validated RecommendationBatch instance.

    Raises:
        ResponseParsingError: If text is malformed, not valid JSON, or contains non-finite numbers.
        ResponseValidationError: If payload violates the canonical contract, contains invalid enums,
                                 or has missing required fields.
    """
    cleaned_text = extract_json_payload(raw_text)

    try:
        decoded = json.loads(cleaned_text, parse_constant=_reject_constant)
    except json.JSONDecodeError as exc:
        raise ResponseParsingError(f"Failed to parse JSON response: {exc}") from exc
    except ResponseParsingError:
        raise
    except Exception as exc:
        raise ResponseParsingError(f"Unexpected error decoding JSON: {exc}") from exc

    # Parse expected source enum
    resolved_expected_source: Optional[RecommendationSource] = None
    if expected_source is not None:
        if isinstance(expected_source, RecommendationSource):
            resolved_expected_source = expected_source
        elif isinstance(expected_source, str):
            try:
                cleaned_source = expected_source.lower().strip().replace(" ", "_").replace("-", "_")
                resolved_expected_source = RecommendationSource(cleaned_source)
            except ValueError:
                raise ResponseValidationError(f"Invalid expected_source: '{expected_source}'.")

    # Inspect top-level structure
    batch_dataset_id = dataset_id
    batch_generated_at = None

    if isinstance(decoded, list):
        items = decoded
    elif isinstance(decoded, dict):
        if "recommendations" not in decoded:
            raise ResponseValidationError(
                "Unexpected top-level dictionary structure: expected 'recommendations' key."
            )
        raw_items = decoded["recommendations"]
        if not isinstance(raw_items, list):
            raise ResponseValidationError(
                f"Field 'recommendations' must be a list, got {type(raw_items).__name__}."
            )
        items = raw_items
        if not batch_dataset_id and "dataset_id" in decoded:
            batch_dataset_id = str(decoded["dataset_id"])
        if "generated_at" in decoded:
            batch_generated_at = str(decoded["generated_at"])
    else:
        raise ResponseValidationError(
            f"Unexpected top-level JSON type: expected list or object with 'recommendations', got {type(decoded).__name__}."
        )

    # Empty recommendation list is valid
    if not items:
        return RecommendationBatch(
            recommendations=[],
            dataset_id=batch_dataset_id,
            generated_at=batch_generated_at,
        )

    # Validate each item with all-or-nothing policy
    validated_items: List[RecommendationItem] = []
    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            raise ResponseValidationError(
                f"Recommendation at index {idx} must be an object/dict, got {type(item).__name__}."
            )

        item_copy = dict(item)

        # Source attribution enforcement
        item_source_raw = item_copy.get("source")
        if enforce_source and resolved_expected_source is not None:
            if item_source_raw is None:
                # If omitted, assign expected source
                item_copy["source"] = resolved_expected_source
            else:
                # If provided, verify it matches expected source
                try:
                    cleaned_s = str(item_source_raw).lower().strip().replace(" ", "_").replace("-", "_")
                    parsed_item_source = RecommendationSource(cleaned_s)
                except ValueError:
                    raise ResponseValidationError(
                        f"Recommendation at index {idx} contains invalid source: '{item_source_raw}'."
                    )
                if parsed_item_source != resolved_expected_source:
                    raise ResponseValidationError(
                        f"Source attribution mismatch at index {idx}: expected '{resolved_expected_source.value}', "
                        f"but model returned '{parsed_item_source.value}'."
                    )

        # Validate item against Pydantic RecommendationItem schema
        try:
            validated_item = RecommendationItem.model_validate(item_copy)
        except ValidationError as exc:
            errors = exc.errors()
            error_details = "; ".join(
                f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}" for err in errors
            )
            raise ResponseValidationError(
                f"Validation failed for recommendation at index {idx} ({item_copy.get('id', f'idx-{idx}')}): {error_details}"
            ) from exc
        except ValueError as exc:
            raise ResponseValidationError(
                f"Validation error for recommendation at index {idx}: {exc}"
            ) from exc

        validated_items.append(validated_item)

    return RecommendationBatch(
        recommendations=validated_items,
        dataset_id=batch_dataset_id,
        generated_at=batch_generated_at,
    )


def parse_recommendation_list(
    raw_text: str,
    expected_source: Optional[Union[RecommendationSource, str]] = None,
    enforce_source: bool = True,
    dataset_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Parses raw LLM text into a list of serialized recommendation dictionaries.

    Suitable for immediate database persistence in AnalysisResult.ai_recommendations
    and backend API responses.
    """
    batch = parse_recommendations(
        raw_text=raw_text,
        expected_source=expected_source,
        enforce_source=enforce_source,
        dataset_id=dataset_id,
    )
    return batch.to_list()
