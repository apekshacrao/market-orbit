# Implementation Report: Phase 1 — Step 1.3
## Implement Analytics Schemas & Preprocessing

**Document Version:** 1.0  
**Date:** September 17, 2026  
**Track:** Analytics & AI Architecture  
**Lead:** Vishal S Naik (Analytics & AI Track)  
**Status:** Successfully Implemented & Verified (16/16 Unit Tests Passing)  

---

## SECTION 1 — PRE-IMPLEMENTATION INSPECTION

### 1.1 Existing Files & Structure
Prior to this step, the `analytics/` package contained:
- `analytics/schemas/result_schema.py`: Contained only `AnalyticsOutput` for post-analysis response formatting.
- `analytics/schemas/__init__.py`: Only exported `AnalyticsOutput`. No input validation model existed.
- `analytics/preprocessing/cleaner.py`: Standardized column names, but filled missing `revenue` with `0.0`, fabricating revenue metrics.
- `analytics/preprocessing/normalizer.py`: Cast columns to numeric using `fillna(0)`, destroying null revenue indicators.
- `analytics/preprocessing/validators.py`: Required `["campaign_name", "channel", "spend", "revenue"]`, rejecting any dataset where revenue was not tracked.
- `analytics/tests/test_preprocessing.py`: Contained a single `assert True` placeholder stub.

### 1.2 Identified Issues
1. **Fabricated Revenue:** Both `cleaner.py` and `normalizer.py` coerced null/missing revenue into `0.0`. This made untracked revenue indistinguishable from actual zero-revenue campaigns, causing false ROAS (`0.0x`) and false ROI (`-100%`) calculations.
2. **Missing Input Schema:** No Pydantic input model existed to validate campaign records upon backend handoff.
3. **No Support for Demographics and Dates:** Optional fields (`date`, `location`, `age_group`, `customer_segment`, `device`) were not accounted for in preprocessing or validation.
4. **No Protection Against Negative Metrics:** Negative values for spend, conversions, impressions, and clicks were neither checked nor rejected.

---

## SECTION 2 — IMPLEMENTATION PLAN

| File Action | Target File | Purpose & Rationale |
| :--- | :--- | :--- |
| **CREATE** | `analytics/schemas/campaign_schema.py` | Implement `CampaignInputRecord` with strict Pydantic v2 validation (mandatory fields, non-negative checks, ISO-8601 date validation, and nullable revenue/demographics). |
| **MODIFY** | `analytics/schemas/__init__.py` | Export `CampaignInputRecord` alongside `AnalyticsOutput`. |
| **MODIFY** | `analytics/preprocessing/validators.py` | Refactor `validate_dataset` to use `MANDATORY_COLUMNS = ["campaign_name", "channel", "spend", "conversions"]`, support both `list[dict]` and `pd.DataFrame`, and return row-level validation errors. |
| **MODIFY** | `analytics/preprocessing/cleaner.py` | Refactor `clean_dataset` to accept `list[dict]` or `pd.DataFrame`, convert to DataFrame internally without modifying input records, and preserve `np.nan` / `None` for untracked revenue, date, and demographics. |
| **MODIFY** | `analytics/preprocessing/normalizer.py` | Refactor `normalize_metrics` to cast metrics safely without filling null revenue with zero. |
| **MODIFY** | `analytics/preprocessing/__init__.py` | Export updated functions and column constants (`MANDATORY_COLUMNS`, `OPTIONAL_COLUMNS`). |
| **MODIFY** | `analytics/tests/test_preprocessing.py` | Implement 12 comprehensive test scenarios verifying all data contract requirements. |

---

## SECTION 3 — IMPLEMENTATION SUMMARY

### 3.1 Input Model: `CampaignInputRecord`
Implemented in [analytics/schemas/campaign_schema.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/schemas/campaign_schema.py):
- **Mandatory Fields:**
  - `campaign_name` (`str`): Non-empty string validation.
  - `channel` (`str`): Non-empty string validation.
  - `spend` (`float`): Enforced `ge=0.0`.
  - `conversions` (`int`): Enforced `ge=0` (treated as leads).
- **Optional Performance Fields:**
  - `impressions` (`Optional[int] = 0`): Enforced `ge=0`.
  - `clicks` (`Optional[int] = 0`): Enforced `ge=0`.
  - `revenue` (`Optional[float] = None`): Enforced `ge=0.0` when provided; defaults to `None` if missing/untracked.
- **Optional Dimensions:**
  - `date` (`Optional[str] = None`): Custom validator enforces valid `YYYY-MM-DD` calendar date format; empty strings normalize to `None`.
  - `location`, `age_group`, `customer_segment`, `device` (`Optional[str] = None`): Whitespace trimmed; empty strings normalize to `None`.

### 3.2 Preprocessing Engine: `cleaner.py` & `normalizer.py`
- Implemented deep-copy mechanism to prevent mutation of the input list of dictionaries.
- Implemented Pandas DataFrame conversion preserving `np.nan` for missing revenue.
- Ensured missing optional columns (`date`, `location`, etc.) are created with `None` if missing from input, ensuring schema consistency across downstream analytics.

### 3.3 Validation Layer: `validators.py`
- Aligned `MANDATORY_COLUMNS` to `["campaign_name", "channel", "spend", "conversions"]`.
- Added multi-type support accepting either `list[dict]` or `pd.DataFrame`.
- Validates row-level schema against `CampaignInputRecord` and returns structured validation dictionaries:
  `{"is_valid": bool, "missing_columns": list[str], "errors": list[str], "validated_records": list[CampaignInputRecord]}`.

---

## SECTION 4 — TEST RESULTS

### 4.1 Test Execution
Command executed: `python -m pytest analytics/tests/test_preprocessing.py -v` followed by `python -m pytest analytics/tests -v`.

### 4.2 Test Suite Breakdown

| # | Test Name | Target Behavior | Result |
| :---: | :--- | :--- | :---: |
| 1 | `test_valid_record_all_fields` | Valid record with all mandatory + optional fields | **PASSED** |
| 2 | `test_valid_record_without_revenue` | Valid record where `revenue` is omitted; preserves `NaN` | **PASSED** |
| 3 | `test_valid_record_without_demographics` | Valid record without demographic attributes; preserves `None` | **PASSED** |
| 4 | `test_valid_record_without_date` | Valid record without date; preserves `None` | **PASSED** |
| 5 | `test_missing_mandatory_field` | Rejects records missing mandatory fields (e.g., `channel`) | **PASSED** |
| 6 | `test_negative_spend` | Rejects `spend < 0.0` with clear validation error | **PASSED** |
| 7 | `test_negative_conversions` | Rejects `conversions < 0` with clear validation error | **PASSED** |
| 8 | `test_invalid_date_format` | Rejects non-ISO date formats (e.g., `"06-01-2026"`) | **PASSED** |
| 9 | `test_revenue_equal_to_zero` | Preserves actual zero revenue (`0.0`) as distinct from untracked | **PASSED** |
| 10 | `test_revenue_equal_to_null` | Preserves untracked revenue (`None`) as `NaN` (does not zero-fill) | **PASSED** |
| 11 | `test_preservation_of_optional_fields` | Verifies full preservation across cleaner & normalizer | **PASSED** |
| 12 | `test_list_of_dictionaries_input_conversion` | Converts `list[dict]` to `pd.DataFrame` without mutating input | **PASSED** |

### 4.3 Full Suite Summary
- **Total Tests Collected:** 16
- **Total Passed:** 16
- **Total Failed:** 0
- **Execution Time:** 0.63s

---

## SECTION 5 — CONTRACT COMPLIANCE

| Requirement | Contract Specification | Implementation Status | Verification |
| :--- | :--- | :---: | :--- |
| **Mandatory Fields** | `campaign_name`, `channel`, `spend`, `conversions` | **COMPLIANT** | Enforced in `CampaignInputRecord` and `validators.py`. |
| **Optional Fields** | `impressions`, `clicks`, `revenue`, `date`, demographics | **COMPLIANT** | Model defaults provided; cleaner ensures columns exist. |
| **Nullable Revenue** | `None` means untracked; `0.0` means zero revenue | **COMPLIANT** | `cleaner.py` and `normalizer.py` strictly preserve `NaN`/`None`. |
| **Nullable Date** | `YYYY-MM-DD` validated if present; `None` if omitted | **COMPLIANT** | Verified via `test_invalid_date_format` & `test_valid_record_without_date`. |
| **Demographic Preservation** | `location`, `age_group`, `customer_segment`, `device` | **COMPLIANT** | Preserved without fabrication or string truncation. |
| **List-of-Dicts Input** | Direct JSON list accepted | **COMPLIANT** | Verified via `test_list_of_dictionaries_input_conversion`. |
| **DataFrame Conversion** | Converted internally with consistent types | **COMPLIANT** | Cleaned DataFrame returned with normalized types. |

---

## SECTION 6 — BACKEND COORDINATION

The Analytics layer now accepts the confirmed data contract. The following updates must be coordinated with Sushanth for backend alignment:

1. **Update Backend Upload Validation (`backend/app/services/validation_service.py`):**
   - Remove `"revenue"` from `REQUIRED_COLUMNS` so datasets without revenue pass backend validation.
   - Update `backend/tests/test_validation.py` to reflect optional revenue.
2. **Database Schema & Ingestion Updates:**
   - Add `date DATE NULL` column to `campaigns` table.
   - Add nullable demographic columns (`location`, `age_group`, `customer_segment`, `device`) to `campaigns` table.
   - Update `CampaignService.import_campaigns` to parse and store `date` and demographic fields from CSV.
3. **Backend-to-Analytics Data Handoff:**
   - In `backend/app/services/analysis_service.py`, query `Campaign` records, serialize to `list[dict]`, and pass directly to `analytics.preprocessing.clean_dataset(records)`.

---

## SECTION 7 — RECOMMENDED NEXT STEP

Proceed to:

**Phase 1 — Step 1.4: Refactor KPI Engine & Derived Metrics**
1. Update `analytics/kpi/metrics.py` to:
   - Calculate CPA using `conversions` ($ \text{CPA} = \frac{\text{spend}}{\text{conversions}} $).
   - Calculate Conversion Rate using `clicks` ($ \frac{\text{conversions}}{\text{clicks}} $).
   - Calculate ROAS and ROI conditionally only when `revenue` is non-null. If revenue is `None`, return `None` for ROAS/ROI instead of fabricating `0.0`.
   - Implement ROI formula ($ \frac{\text{revenue} - \text{spend}}{\text{spend}} \times 100 $).
2. Write unit tests for KPI calculations in `analytics/tests/test_metrics.py`.
