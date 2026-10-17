# Market Orbit — Phase 4.2.1: Baseline Forecasting Contract Audit and Corrections Report

**Status:** Completed  
**Author:** Senior Time-Series Forecasting Engineer  
**Date:** 2026-10-14  
**Target Repository:** `market-orbit`  
**Git Branch:** `analytics`  
**Base Commit:** `4c58c55` (*"implement Phase 4.2 deterministic baseline forecasting models"*)  

---

## 1. Executive Summary

Phase 4.2.1 was executed as a narrowly scoped contract hardening task on the Phase 4.2 baseline forecasting subsystem. The audit identified and resolved four critical correctness defects that previously allowed synthetic zero-filling, non-contiguous rolling window averaging, and improper coercions of missing/invalid count observations.

### Summary of Audit Findings and Hardening Fixes
1. **Missing Metric Semantics:** An absent or invalid `clicks`, `impressions`, `spend`, `conversions`, or `revenue` metric is no longer silently converted into integer or float `0`. Untracked/missing metrics evaluate to `None` in daily aggregations, project as JSON-compliant `null` in baseline forecasts, and are flagged deterministically via model-level `metric_status` and `metric_reasons`. Explicitly observed zeros (e.g. `clicks: 0`, `spend: 0.0`) are preserved.
2. **Strict SMA-7 Calendar Window Contiguity:** SMA-7 now strictly requires seven consecutive calendar dates immediately preceding the forecast origin ($D_T - 6, \dots, D_T$). If calendar gaps exist within this recent 7-day window, SMA-7 is marked `is_eligible = False` with `ineligibility_reason` explicitly citing calendar gaps, rather than silently averaging scattered observed dates. If the 7 dates are contiguous but a specific metric contains unobserved or invalid values, that metric evaluates to `null` with `metric_status = "unavailable"`, while remaining valid metrics compute their rolling means.
3. **Count Metric Validation & Rounding Policy:** Historical count metrics (`conversions`, `clicks`, `impressions`) now reject missing values, non-numeric strings, booleans (`True`/`False`), non-finite values (`inf`, `-inf`, `nan`), negative values (`< 0`), and fractional counts (e.g. `12.5`). Negative values are never clipped to zero. For valid count forecasts in SMA-7, outputs are strictly non-negative integers rounded via standard round-half-to-even (`round(mean_val)`), eliminating systematic upward bias.
4. **Contract Invariance:** Naive persistence and 7-day seasonal naive baseline mathematical formulas remain unchanged for valid data. Seasonal naive continues to require at least 14 contiguous calendar dates. The Phase 4.1 revenue completeness contract is preserved: incomplete, untracked, or invalid revenue produces strictly `null` forecasts across all baseline models.

All 35 forecasting tests passed (`pytest analytics/tests/test_forecasting.py -v`). The full test suite passed with 194 passing tests and zero failures (`pytest`).

---

## 2. Audit of Existing Phase 4.2 Implementation

| Component | Pre-Audit Behavior (Phase 4.2) | Audit Finding | Correction (Phase 4.2.1) |
| :--- | :--- | :--- | :--- |
| **`data_prep.py` Missing Columns** | Omitted `clicks` or `impressions` defaulted to `0` via `.fillna(0).sum()`. | **Defect:** Untracked metrics were indistinguishable from days with genuine 0 clicks/impressions. | Absent columns or rows evaluate to `None`; explicit zeros evaluate to `0`. |
| **`data_prep.py` Count Validation** | Used `pd.to_numeric(errors="coerce").fillna(0)`. | **Defect:** Negative counts (e.g. `-5`), fractional counts (`1.5`), and corrupted values silently became `0`. | Hardened validation: checks `math.isfinite()`, `val >= 0`, and `f.is_integer()`. Rejects booleans and negative values to `None`. |
| **`baselines.py` SMA-7 Window** | Emitted warning for non-contiguous 7-day windows but still averaged 7 scattered dates. | **Defect:** Violated standard moving-average contract; averaged non-adjacent dates as if contiguous. | Strictly requires 7 consecutive calendar dates preceding forecast origin; marks `is_eligible = False` if gaps exist. |
| **`baselines.py` SMA-7 Metric Usability** | Assumed count metrics were always non-null integers. | **Defect:** If any observation in the 7-day window was missing/unusable, it defaulted to 0 or threw errors. | Evaluates usability per metric. If any day in the 7-day window is `None`, that metric forecasts as `None` with `metric_status="unavailable"`. |
| **`baselines.py` Model Structure** | Output dictionary lacked metric-level eligibility and status breakdown. | **Defect:** Callers could not programmatically distinguish why a particular metric was `null`. | Added `metric_status` (`"available"`, `"unavailable"`, `"ineligible"`) and `metric_reasons` to all models. |
| **`test_forecasting.py` Legacy Tests** | Tests 9 and 23 explicitly asserted that omitted clicks/impressions became `0`. | **Defect:** Test suite encoded synthetic zero-filling behavior conflicting with core domain requirements. | Tests updated to assert `None` (JSON `null`) and verified against explicit zeros. |

---

## 3. Detailed Specifications & Implemented Policies

### 3.1 Metric Missing-Versus-Zero Policy
- **Count Metrics (`conversions`, `clicks`, `impressions`):**
  - Evaluated via `_aggregate_count_metric(grp, col)`.
  - If column is absent or any row on date $d$ contains missing (`None`/`NaN`), boolean, non-numeric string, negative (`< 0`), fractional (`not f.is_integer()`), or non-finite (`inf`, `-inf`), the aggregated daily value is `None`.
  - If all rows on date $d$ are valid non-negative integer counts, the value is summed to `int`.
  - Explicit observed zero (`0` or `0.0`) is preserved as `0`.
- **Currency Metrics (`spend`, `revenue`):**
  - Evaluated via `_aggregate_currency_metric(grp, col)`.
  - If column is absent or any row on date $d$ contains missing, boolean, non-numeric string, negative (`< 0.0`), or non-finite, the aggregated daily value is `None`.
  - If all rows on date $d$ are valid non-negative numbers, the value is summed and rounded to 2 decimals (`float`).
- **Revenue Completeness Contract:**
  - `revenue_complete` is `True` if and only if `"revenue"` is in `valid_df.columns`, `valid_df` is non-empty, and every record satisfies `_is_valid_currency_value(v)`.
  - If `revenue_complete` is `False`, all baseline models output `null` (`None`) for revenue across all forecast dates.

### 3.2 SMA-7 Eligibility & Window Policy
- **Calendar Contiguity Guard:**
  - Identifies the 7 most recent daily observations: `sma_window = series[-7:]`.
  - Validates that `window_dates` consists of 7 consecutive calendar dates without any gaps: $(D_T - D_{T-6}).\text{days} == 6$ and $(D_i - D_{i-1}).\text{days} == 1$ for all $i$.
  - If calendar gaps exist:
    - `sma_7["is_eligible"] = False`
    - `sma_7["forecast"] = []`
    - `sma_7["ineligibility_reason"] = "SMA-7 requires 7 consecutive calendar dates immediately preceding the forecast origin; calendar gaps detected in the recent 7-day window."`
    - `sma_7["metric_status"] = {m: "ineligible" for m in SUPPORTED_METRICS}`
    - `sma_7["metric_reasons"] = {m: sma_reason for m in SUPPORTED_METRICS}`
- **Metric-Level Usability Guard (when calendar window is contiguous):**
  - For each metric $m \in [\text{"spend"}, \text{"conversions"}, \text{"clicks"}, \text{"impressions"}, \text{"revenue"}]$:
    - If all 7 observations are valid (non-`None`) and revenue completeness satisfied:
      - `metric_status[m] = "available"`
      - `metric_reasons[m] = None`
      - Forecast values computed as rolling 7-day mean.
    - If one or more observations in the 7-day window is `None` (or for revenue, if `revenue_complete` is False):
      - `metric_status[m] = "unavailable"`
      - `metric_reasons[m] = "SMA-7 forecast for '{m}' is unavailable due to missing or invalid observations in the recent 7-day window."`
      - Forecast values set to `None` (JSON `null`) for all forecast horizon points.

### 3.3 Count Metric Rounding Policy
- In SMA-7, the 7-day arithmetic mean of integer counts is frequently fractional.
- **Rounding Policy:** Python's standard `round(mean_val)` (round-half-to-even, IEEE 754 standard banking rounding), clamped to non-negative integer `int(max(0, round(mean_val)))`.
- **Properties:**
  - Strictly deterministic.
  - Produces non-negative integer values (`int`).
  - Unbiased: avoids systematic upward accumulation over time.
  - Verified by hand-calculable test cases (e.g. $73/7 = 10.428 \to 10$, $74/7 = 10.571 \to 11$, $1/7 = 0.143 \to 0$, $4/7 = 0.571 \to 1$).

### 3.4 Naive & Seasonal Naive Behavior under Phase 4.2.1
- **Naive Persistence:**
  - Evaluates latest observation `last_obs = series[-1]`.
  - For each metric $m$, if `last_obs[m]` is not `None` (and for revenue, `revenue_complete` is True), forecasts `last_obs[m]` with `metric_status[m] = "available"`.
  - If `last_obs[m]` is `None`, forecasts `None` with `metric_status[m] = "unavailable"`.
- **Seven-Day Seasonal Naive (SNaive-7):**
  - Requires at least 14 observed dates and that the most recent 14 dates are strictly contiguous calendar days.
  - Evaluates the recent 7-day seasonal cycle `recent_7 = series[-7:]`.
  - For each metric $m$, if any day in `recent_7` has `None` (or for revenue, `not revenue_complete`), that metric is marked `metric_status[m] = "unavailable"`, and all forecast points for that metric are `None`.

---

## 4. Verification and Regression Testing

### 4.1 Explanations for Updated Existing Tests
- **`test_optional_clicks_and_impressions` (Test 9):**
  - *Previous expectation:* Asserted `res["series"][0]["clicks"] == 0` when clicks/impressions columns were omitted.
  - *Why incorrect:* Conflated untracked data with zero activity, misleading downstream models into predicting zero rather than recognizing data absence.
  - *Updated expectation:* Asserts `res["series"][0]["clicks"] is None` and `res["series"][0]["impressions"] is None`, and asserts `0` when explicit zeros are provided.
- **`test_baselines_optional_clicks_impressions` (Test 23):**
  - *Previous expectation:* Asserted `pt["clicks"] == 0` in naive and SMA-7 forecasts when clicks was omitted.
  - *Why incorrect:* Synthetically generated zero forecasts for metrics that were never tracked in historical data.
  - *Updated expectation:* Asserts `pt["clicks"] is None`, `pt["impressions"] is None, and verifies `metric_status["clicks"] == "unavailable"`.

### 4.2 New Regression Tests Added (Tests 29–35)
- **Test 29 (`test_sma_7_rejection_on_window_calendar_gaps`):** 7 observed dates spanning 8 calendar days (Aug 7 missing). Verifies SMA-7 is marked `is_eligible = False`, `forecast = []`, and `metric_status = "ineligible"`, while Naive remains eligible.
- **Test 30 (`test_sma_7_metric_specific_unusable_observations`):** 7 contiguous dates where `spend` and `conversions` are valid, `clicks` is missing on Day 4, and `impressions` is corrupted on Day 7. Verifies `spend`/`conversions` forecast valid means, while `clicks`/`impressions` forecast strictly `None` with `unavailable` status.
- **Test 31 (`test_count_metric_validation_negative_fractional_non_finite_booleans`):** Verifies rejection to `None` for negative (`-5`), fractional (`12.5`), non-finite (`inf`), boolean (`True`), and unparseable strings, while preserving explicit `0`.
- **Test 32 (`test_sma_7_count_rounding_policy_explicit_verification`):** Tests exact integer conversions for sums $73 \to 10$, $74 \to 11$, $1 \to 0$, $4 \to 1$.
- **Test 33 (`test_seasonal_naive_metric_specific_unavailability`):** 14 contiguous days with missing conversions on Day 10. Verifies seasonal naive stays eligible for spend/clicks, while conversions forecasts as `None`.
- **Test 34 (`test_negative_spend_and_currency_validation`):** Verifies rejection to `None` for negative and NaN spend.
- **Test 35 (`test_full_json_serialization_with_null_and_zero_metrics`):** Verifies `json.dumps(result, allow_nan=False)` serializes mixed null, zero, and active metric forecasts into compliant JSON literals (`null` and `0`).

### 4.3 Actual Command Outputs
```bash
$ pytest analytics/tests/test_forecasting.py -v
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-8.3.4, pluggy-1.6.0
collected 35 items

analytics/tests/test_forecasting.py::test_valid_dates_and_chronological_ordering PASSED [  2%]
analytics/tests/test_forecasting.py::test_strict_date_parsing_and_invalid_date_exclusion_diagnostics PASSED [  5%]
analytics/tests/test_forecasting.py::test_duplicate_date_aggregation PASSED [  8%]
analytics/tests/test_forecasting.py::test_empty_input_and_missing_date_column PASSED [ 11%]
analytics/tests/test_forecasting.py::test_no_valid_dates PASSED          [ 14%]
analytics/tests/test_forecasting.py::test_contiguous_vs_non_contiguous_dates PASSED [ 17%]
analytics/tests/test_forecasting.py::test_observed_zeros_vs_unresolved_date_gaps PASSED [ 20%]
analytics/tests/test_forecasting.py::test_no_unjustified_zero_filling_or_interpolation PASSED [ 22%]
analytics/tests/test_forecasting.py::test_optional_clicks_and_impressions PASSED [ 25%]
analytics/tests/test_forecasting.py::test_complete_untracked_partially_missing_and_invalid_revenue PASSED [ 28%]
analytics/tests/test_forecasting.py::test_deterministic_repeated_calls PASSED [ 31%]
analytics/tests/test_forecasting.py::test_caller_dataframe_immutability PASSED [ 34%]
analytics/tests/test_forecasting.py::test_strict_json_serialization_allow_nan_false PASSED [ 37%]
analytics/tests/test_forecasting.py::test_regression_phase_1_to_3_analytics_unchanged PASSED [ 40%]
analytics/tests/test_forecasting.py::test_seasonal_dates_diagnostic_14_contiguous_days PASSED [ 42%]
analytics/tests/test_forecasting.py::test_naive_persistence_values_and_dates PASSED [ 45%]
analytics/tests/test_forecasting.py::test_sma_7_eligibility_and_exact_calculations PASSED [ 48%]
analytics/tests/test_forecasting.py::test_seasonal_naive_eligibility_14_contiguous_dates PASSED [ 51%]
analytics/tests/test_forecasting.py::test_seasonal_naive_rejection_of_14_rows_with_calendar_gaps PASSED [ 54%]
analytics/tests/test_forecasting.py::test_baselines_empty_input_missing_date_and_insufficient_history PASSED [ 57%]
analytics/tests/test_forecasting.py::test_baselines_revenue_semantics_complete_untracked_partial_invalid PASSED [ 60%]
analytics/tests/test_forecasting.py::test_baselines_observed_zero_vs_unresolved_gaps PASSED [ 62%]
analytics/tests/test_forecasting.py::test_baselines_optional_clicks_impressions PASSED [ 65%]
analytics/tests/test_forecasting.py::test_baselines_invalid_horizon_rejection PASSED [ 68%]
analytics/tests/test_forecasting.py::test_baselines_deterministic_repeated_calls PASSED [ 71%]
analytics/tests/test_forecasting.py::test_baselines_caller_dataframe_immutability PASSED [ 74%]
analytics/tests/test_forecasting.py::test_baselines_strict_json_serialization_allow_nan_false PASSED [ 77%]
analytics/tests/test_forecasting.py::test_duplicate_date_revenue_uncertainty_preservation PASSED [ 80%]
analytics/tests/test_forecasting.py::test_sma_7_rejection_on_window_calendar_gaps PASSED [ 82%]
analytics/tests/test_forecasting.py::test_sma_7_metric_specific_unusable_observations PASSED [ 85%]
analytics/tests/test_forecasting.py::test_count_metric_validation_negative_fractional_non_finite_booleans PASSED [ 88%]
analytics/tests/test_forecasting.py::test_sma_7_count_rounding_policy_explicit_verification PASSED [ 91%]
analytics/tests/test_forecasting.py::test_seasonal_naive_metric_specific_unavailability PASSED [ 94%]
analytics/tests/test_forecasting.py::test_negative_spend_and_currency_validation PASSED [ 97%]
analytics/tests/test_forecasting.py::test_full_json_serialization_with_null_and_zero_metrics PASSED [100%]

============================= 35 passed in 0.77s ==============================
```

```bash
$ pytest
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-8.3.4, pluggy-1.6.0
collected 194 items

analytics\tests\test_ai.py ..                                            [  1%]
analytics\tests\test_forecasting.py ...................................  [ 19%]
analytics\tests\test_insights.py ..............                          [ 26%]
analytics\tests\test_metrics.py ............                             [ 32%]
analytics\tests\test_preprocessing.py ..............                     [ 39%]
analytics\tests\test_ranking.py ............                             [ 45%]
analytics\tests\test_segment_portfolio.py ..................             [ 55%]
analytics\tests\test_segmentation.py ...........                         [ 60%]
analytics\tests\test_trends.py .........................                 [ 73%]
backend\tests\test_auth.py ...                                           [ 75%]
backend\tests\test_campaign_service.py ........                          [ 79%]
backend\tests\test_compatibility.py ...                                  [ 80%]
backend\tests\test_results.py ....................                       [ 91%]
backend\tests\test_upload.py .............                               [ 97%]
backend\tests\test_validation.py ....                                    [100%]

======================= 194 passed, 6 warnings in 4.02s =======================
```

---

## 5. Modified Files & Git Working Tree

### Working Tree Status
```
$ git status --short
 M analytics/forecasting/baselines.py
 M analytics/forecasting/data_prep.py
 M analytics/tests/test_forecasting.py
?? docs/analytics/PHASE_4_2_1_BASELINE_CONTRACT_HARDENING_REPORT.md
```

### File Modification Inventory
1. `analytics/forecasting/data_prep.py`:
   - Added `_is_valid_count_value(val)` and `_is_valid_currency_value(val)` validation helpers.
   - Replaced silent zero-filling (`.fillna(0)`) with `_aggregate_count_metric` and `_aggregate_currency_metric`.
   - Updated `revenue_complete` verification to inspect all rows for valid non-negative numbers.
   - Added `metric_availability` diagnostic dictionary to `metadata`.
2. `analytics/forecasting/baselines.py`:
   - Replaced permissive SMA-7 warning with strict rejection of calendar gaps in the 7-day window.
   - Added metric-level usability evaluation (`metric_status`, `metric_reasons`) across all baseline models.
   - Replaced silent zero fallbacks with `None` (JSON `null`) for unavailable metrics.
   - Implemented standard round-half-to-even integer rounding for count metric forecasts.
3. `analytics/tests/test_forecasting.py`:
   - Updated legacy Tests 9 and 23 to enforce missing-vs-zero semantics.
   - Added Tests 29–35 covering calendar gaps, metric-specific invalid values, count validation, count rounding, and JSON serialization.

---

## 6. Boundaries and Operational Limitations

1. **Deterministic Baseline Scope Only:** Phase 4.2.1 remains strictly limited to deterministic baseline forecasts. No evaluation metrics (MAPE, MAE, RMSE), backtesting splits, or AI narrative explanations have been implemented.
2. **Calendar Gap Inelasticity for SMA-7:** By design, SMA-7 does not perform linear interpolation or synthetic date imputation. If any calendar date is missing in the 7 days prior to forecast origin, SMA-7 is declared ineligible.
3. **No Database or API Modifications:** All changes remain within the pure analytics functional library. Backend schemas, database models, and API endpoints remain untouched.

---

## 7. Phase 4.2.1 Completion Sign-Off

The Phase 4.2 baseline forecasting contract audit and hardening is complete, verified, and free of regressions. The codebase adheres strictly to the missing-versus-zero contract, calendar contiguity requirements, and count validation policies.
