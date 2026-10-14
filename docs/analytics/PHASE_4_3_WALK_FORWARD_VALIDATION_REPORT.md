# Market Orbit — Phase 4.3: Walk-Forward Temporal Validation Report

**Status:** Completed  
**Author:** Senior Time-Series Forecasting Engineer  
**Date:** 2026-10-14  
**Target Repository:** `market-orbit`  
**Git Branch:** `analytics`  
**Base Commit:** `336a4e8` (*"harden Phase 4.2 baseline forecasting contracts for missing metric semantics, SMA-7 contiguity, and count validation"*)  

---

## 1. Executive Summary

Phase 4.3 implements a deterministic, leakage-safe walk-forward temporal validation engine for Market Orbit's baseline forecasting models (`naive_persistence`, `simple_moving_average_7d`, and `seasonal_naive_7d`). The validation system evaluates historical forecast errors without data leakage, without random or shuffled splitting, and without making forward-looking production accuracy claims or selecting a winning model.

### Key Architectural Accomplishments
1. **Zero-Leakage Expanding Windows:** Walk-forward splits are constructed strictly by temporal origin $D_k$. Preprocessing, streak calculation, metric aggregation, and baseline generation for origin $D_k$ receive only observations dated on or before $D_k$ (`_parsed_date <= D_k`). Future observations are never exposed to earlier training windows.
2. **Calendar Date Alignment & Gap Handling:** Each point in the $H$-day forecast is paired strictly with the observed actual from the exact same calendar date. If an actual date is unobserved (a future calendar gap), that point is omitted from scoring rather than fabricated or substituted.
3. **Exact Point-Weighted Pooled Error Metrics:** MAE, RMSE, and WAPE are computed across all evaluated forecast-actual pairs across all eligible origins. This eliminates distortion caused by unweighted averages of origins with unequal sample sizes.
4. **Zero-Denominator WAPE Guard:** When the sum of actual values is zero, WAPE evaluates to `null` (`None`) with explicit status `wape_status = "undefined_zero_actuals"`, preventing division-by-zero or fabricated percentage scores.
5. **Revenue Completeness Preservation:** In line with Phase 4.1 and Phase 4.2.1 contracts, revenue errors are scored if and only if the training split satisfies `revenue_complete == True` and the evaluation actual contains a valid observed revenue amount. Incomplete or untracked revenue results in strictly `null` scores and zero points evaluated.
6. **Metric-Specific Evaluation Sample Sizes:** Independent point counts are tracked for each metric (`spend`, `conversions`, `clicks`, `impressions`, `revenue`) to prevent metrics with different sample sizes from being conflated.

The full test suite passed with **205 passing tests** (46 forecasting tests) and zero failures (`pytest`).

---

## 2. Public API Contract and Signature

The validation engine is implemented in [analytics/forecasting/validation.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/forecasting/validation.py) and exported at the package root [analytics/forecasting/__init__.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/forecasting/__init__.py):

```python
def validate_baselines(
    df: pd.DataFrame,
    horizon: int = 7,
    min_train_dates: int = 14,
    step: int = 1,
) -> Dict[str, Any]:
```

### Parameter Contracts
- `horizon`: Positive integer (`int > 0`, default `7`). Number of calendar days to forecast ahead from each origin.
- `min_train_dates`: Positive integer (`int > 0`, default `14`). Minimum number of distinct historical dates required for the initial training split.
- `step`: Positive integer (`int > 0`, default `1`). Number of observed calendar dates to advance the forecast origin between successive validation splits.
- **Strict Type Validation:** All three parameters reject booleans (`True`/`False`), floats, strings, non-positives, and `None` with `ValueError`.

### Output JSON Schema
```json
{
  "is_available": true,
  "status": "ready",
  "parameters": {
    "horizon": 7,
    "min_train_dates": 14,
    "step": 1
  },
  "metadata": {
    "dataset_start_date": "2026-08-01",
    "dataset_end_date": "2026-08-28",
    "total_valid_dates": 28,
    "total_origins_generated": 14,
    "aggregation_method": "point_weighted_pooled",
    "origins": [
      {
        "origin_index": 0,
        "origin_date": "2026-08-14",
        "train_dates_count": 14,
        "train_start_date": "2026-08-01",
        "train_end_date": "2026-08-14",
        "forecast_start_date": "2026-08-15",
        "forecast_end_date": "2026-08-21",
        "observed_eval_dates_count": 7,
        "models": {
          "naive": {
            "is_eligible": true,
            "ineligibility_reason": null,
            "points_evaluated": {"spend": 7, "conversions": 7, "clicks": 7, "impressions": 7, "revenue": 7}
          },
          "sma_7": {
            "is_eligible": true,
            "ineligibility_reason": null,
            "points_evaluated": {"spend": 7, "conversions": 7, "clicks": 7, "impressions": 7, "revenue": 7}
          },
          "seasonal_naive": {
            "is_eligible": true,
            "ineligibility_reason": null,
            "points_evaluated": {"spend": 7, "conversions": 7, "clicks": 7, "impressions": 7, "revenue": 7}
          }
        }
      }
    ]
  },
  "models": {
    "naive": {
      "model_name": "naive_persistence",
      "origins_eligible": 14,
      "origins_ineligible": 0,
      "ineligibility_reasons": [],
      "metrics": {
        "spend": {
          "points_evaluated": 77,
          "mae": 15.2500,
          "rmse": 19.4500,
          "wape": 8.5200,
          "wape_status": "available"
        },
        "conversions": {
          "points_evaluated": 77,
          "mae": 1.2000,
          "rmse": 1.6500,
          "wape": 10.5000,
          "wape_status": "available"
        },
        "clicks": {"points_evaluated": 77, "mae": 5.4000, "rmse": 7.1000, "wape": 6.8000, "wape_status": "available"},
        "impressions": {"points_evaluated": 77, "mae": 120.0000, "rmse": 155.0000, "wape": 5.2000, "wape_status": "available"},
        "revenue": {"points_evaluated": 77, "mae": 45.0000, "rmse": 60.0000, "wape": 7.5000, "wape_status": "available"}
      }
    },
    "sma_7": { "...": "..." },
    "seasonal_naive": { "...": "..." }
  },
  "revenue_complete": true,
  "warnings": []
}
```

---

## 3. Walk-Forward Temporal Procedure & Error Metric Formulas

### 3.1 Expanding-Window Temporal Splitting
Let $D_0, D_1, \dots, D_{N-1}$ be the sorted distinct calendar dates observed in the input dataset ($N = \text{total\_valid\_dates}$).
1. **Initial Origin:** The first origin index is $k = \text{min\_train\_dates} - 1$ (0-indexed). At this index, the training split contains exactly $\text{min\_train\_dates}$ distinct dates ($D_0, \dots, D_k$).
2. **Origin Stepping:** The origin index advances strictly by `step`: $k \leftarrow k + \text{step}$.
3. **Stopping Condition:** The loop terminates when $k \ge N - 1$. An origin at $k = N - 1$ is the dataset's final date and has 0 future test dates, so evaluation proceeds while $k < N - 1$.
4. **Insufficient History Guard:** If $N \le \text{min\_train\_dates}$, zero walk-forward splits can have future observations. In this case, `validate_baselines` immediately returns `is_available = False` and `status = "insufficient_history"`.

### 3.2 Error Metrics & Aggregation Method
For each model and metric, let $\{(y_{pred, i}, y_{act, i})\}_{i=1}^P$ be the set of all evaluated forecast-actual pairs pooled across all eligible origins ($P = \text{points\_evaluated}$):

- **Mean Absolute Error (MAE):**
  $$\text{MAE} = \frac{1}{P} \sum_{i=1}^P |y_{pred, i} - y_{act, i}|$$
- **Root Mean Squared Error (RMSE):**
  $$\text{RMSE} = \sqrt{\frac{1}{P} \sum_{i=1}^P (y_{pred, i} - y_{act, i})^2}$$
- **Weighted Absolute Percentage Error (WAPE):**
  $$\text{WAPE} = \left(\frac{\sum_{i=1}^P |y_{pred, i} - y_{act, i}|}{\sum_{i=1}^P |y_{act, i}|}\right) \times 100$$

### 3.3 Aggregation Rationale (Point-Weighted Pooled vs. Unweighted Origin Average)
Taking an unweighted arithmetic average of per-origin MAEs or WAPEs introduces systematic bias when test horizons have unequal numbers of observed dates (e.g. origins near the end of a timeline with calendar gaps). The point-weighted pooled aggregation method (`aggregation_method = "point_weighted_pooled"`) directly aggregates the underlying error sums, ensuring that each forecast point carries equal weight in the final score.

### 3.4 Zero-Denominator and Missing-Value Policies
- **WAPE Zero Denominator:** If $\sum_{i=1}^P |y_{act, i}| == 0$, WAPE is mathematically undefined. The engine sets `wape = None` and `wape_status = "undefined_zero_actuals"`. It never fabricates a score or divides by zero.
- **Unobserved Actual Dates:** If a forecast date $D_k + \Delta$ does not exist in the dataset (a calendar gap), that point is omitted from scoring. It is never zero-filled or substituted with nearest dates.
- **Model Ineligibility:** If a model is ineligible at an origin (e.g. seasonal naive having $< 14$ contiguous days, or SMA-7 having recent calendar gaps), `origins_ineligible` increments and 0 points are evaluated for that model at that origin.

---

## 4. Verification & Test Evidence

### 4.1 Test Suite Breakdown
Eleven new comprehensive tests (Tests 36–46) were added to [analytics/tests/test_forecasting.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/tests/test_forecasting.py):
1. **Test 36 (`test_walk_forward_hand_calculable_metrics`):** 9-day dataset with 2 origins and 3 evaluated points. Hand-verified exact MAE, RMSE, and WAPE for Naive and SMA-7, and verified ineligibility of Seasonal Naive ($< 14$ dates).
2. **Test 37 (`test_walk_forward_seasonal_naive_eligibility_and_calculation`):** 16-day dataset where Seasonal Naive becomes eligible at 14 contiguous dates and evaluates valid error metrics.
3. **Test 38 (`test_walk_forward_leakage_safety_future_isolation`):** Proves that massive budget spikes on day 10 do not alter forecasts made at origin day 7.
4. **Test 39 (`test_walk_forward_parameter_validation`):** Rejects invalid parameter types (booleans, strings, floats, non-positives) for `horizon`, `min_train_dates`, and `step`.
5. **Test 40 (`test_walk_forward_insufficient_history_and_empty_inputs`):** Handles `None`, empty DataFrames, missing date columns, and datasets with $N \le \text{min\_train\_dates}$.
6. **Test 41 (`test_walk_forward_calendar_gaps_and_missing_eval_dates`):** Validates correct omission of unobserved calendar dates from evaluation actuals.
7. **Test 42 (`test_walk_forward_wape_zero_denominator`):** Confirms `wape = None` and `wape_status = "undefined_zero_actuals"` when actuals are explicitly zero.
8. **Test 43 (`test_walk_forward_revenue_completeness`):** Validates complete, untracked, and partially missing revenue handling.
9. **Test 44 (`test_walk_forward_metric_specific_evaluation_counts`):** Proves that metric sample sizes remain distinct when one metric is partially tracked.
10. **Test 45 (`test_walk_forward_immutability_and_determinism`):** Proves identical outputs across repeated calls, DataFrame immutability, and strict `allow_nan=False` JSON serialization.
11. **Test 46 (`test_walk_forward_package_export`):** Verifies that `validate_baselines` is exported from `analytics.forecasting`.

### 4.2 Actual Command Outputs

#### 1. Focused Forecasting Test Suite (46 passed)
```bash
$ pytest analytics/tests/test_forecasting.py -v
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-8.3.4, pluggy-1.6.0
collected 46 items

analytics/tests/test_forecasting.py::test_valid_dates_and_chronological_ordering PASSED [  2%]
analytics/tests/test_forecasting.py::test_strict_date_parsing_and_invalid_date_exclusion_diagnostics PASSED [  4%]
analytics/tests/test_forecasting.py::test_duplicate_date_aggregation PASSED [  6%]
analytics/tests/test_forecasting.py::test_empty_input_and_missing_date_column PASSED [  8%]
analytics/tests/test_forecasting.py::test_no_valid_dates PASSED          [ 10%]
analytics/tests/test_forecasting.py::test_contiguous_vs_non_contiguous_dates PASSED [ 13%]
analytics/tests/test_forecasting.py::test_observed_zeros_vs_unresolved_date_gaps PASSED [ 15%]
analytics/tests/test_forecasting.py::test_no_unjustified_zero_filling_or_interpolation PASSED [ 17%]
analytics/tests/test_forecasting.py::test_optional_clicks_and_impressions PASSED [ 19%]
analytics/tests/test_forecasting.py::test_complete_untracked_partially_missing_and_invalid_revenue PASSED [ 21%]
analytics/tests/test_forecasting.py::test_deterministic_repeated_calls PASSED [ 23%]
analytics/tests/test_forecasting.py::test_caller_dataframe_immutability PASSED [ 26%]
analytics/tests/test_forecasting.py::test_strict_json_serialization_allow_nan_false PASSED [ 28%]
analytics/tests/test_forecasting.py::test_regression_phase_1_to_3_analytics_unchanged PASSED [ 30%]
analytics/tests/test_forecasting.py::test_seasonal_dates_diagnostic_14_contiguous_days PASSED [ 32%]
analytics/tests/test_forecasting.py::test_naive_persistence_values_and_dates PASSED [ 34%]
analytics/tests/test_forecasting.py::test_sma_7_eligibility_and_exact_calculations PASSED [ 36%]
analytics/tests/test_forecasting.py::test_seasonal_naive_eligibility_14_contiguous_dates PASSED [ 39%]
analytics/tests/test_forecasting.py::test_seasonal_naive_rejection_of_14_rows_with_calendar_gaps PASSED [ 41%]
analytics/tests/test_forecasting.py::test_baselines_empty_input_missing_date_and_insufficient_history PASSED [ 43%]
analytics/tests/test_forecasting.py::test_baselines_revenue_semantics_complete_untracked_partial_invalid PASSED [ 45%]
analytics/tests/test_forecasting.py::test_baselines_observed_zero_vs_unresolved_gaps PASSED [ 47%]
analytics/tests/test_forecasting.py::test_baselines_optional_clicks_impressions PASSED [ 50%]
analytics/tests/test_forecasting.py::test_baselines_invalid_horizon_rejection PASSED [ 52%]
analytics/tests/test_forecasting.py::test_baselines_deterministic_repeated_calls PASSED [ 54%]
analytics/tests/test_forecasting.py::test_baselines_caller_dataframe_immutability PASSED [ 56%]
analytics/tests/test_forecasting.py::test_baselines_strict_json_serialization_allow_nan_false PASSED [ 58%]
analytics/tests/test_forecasting.py::test_duplicate_date_revenue_uncertainty_preservation PASSED [ 60%]
analytics/tests/test_forecasting.py::test_sma_7_rejection_on_window_calendar_gaps PASSED [ 63%]
analytics/tests/test_forecasting.py::test_sma_7_metric_specific_unusable_observations PASSED [ 65%]
analytics/tests/test_forecasting.py::test_count_metric_validation_negative_fractional_non_finite_booleans PASSED [ 67%]
analytics/tests/test_forecasting.py::test_sma_7_count_rounding_policy_explicit_verification PASSED [ 69%]
analytics/tests/test_forecasting.py::test_seasonal_naive_metric_specific_unavailability PASSED [ 71%]
analytics/tests/test_forecasting.py::test_negative_spend_and_currency_validation PASSED [ 73%]
analytics/tests/test_forecasting.py::test_full_json_serialization_with_null_and_zero_metrics PASSED [ 76%]
analytics/tests/test_forecasting.py::test_walk_forward_hand_calculable_metrics PASSED [ 78%]
analytics/tests/test_forecasting.py::test_walk_forward_seasonal_naive_eligibility_and_calculation PASSED [ 80%]
analytics/tests/test_forecasting.py::test_walk_forward_leakage_safety_future_isolation PASSED [ 82%]
analytics/tests/test_forecasting.py::test_walk_forward_parameter_validation PASSED [ 84%]
analytics/tests/test_forecasting.py::test_walk_forward_insufficient_history_and_empty_inputs PASSED [ 86%]
analytics/tests/test_forecasting.py::test_walk_forward_calendar_gaps_and_missing_eval_dates PASSED [ 89%]
analytics/tests/test_forecasting.py::test_walk_forward_wape_zero_denominator PASSED [ 91%]
analytics/tests/test_forecasting.py::test_walk_forward_revenue_completeness PASSED [ 93%]
analytics/tests/test_forecasting.py::test_walk_forward_metric_specific_evaluation_counts PASSED [ 95%]
analytics/tests/test_forecasting.py::test_walk_forward_immutability_and_determinism PASSED [ 97%]
analytics/tests/test_forecasting.py::test_walk_forward_package_export PASSED [100%]

============================= 46 passed in 0.88s ==============================
```

#### 2. Full Test Suite (205 passed)
```bash
$ pytest
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-8.3.4, pluggy-1.6.0
collected 205 items

analytics\tests\test_ai.py ..                                            [  0%]
analytics\tests\test_forecasting.py .................................... [ 18%]
..........                                                               [ 23%]
analytics\tests\test_insights.py ..............                          [ 30%]
analytics\tests\test_metrics.py ............                             [ 36%]
analytics\tests\test_preprocessing.py ..............                     [ 42%]
analytics\tests\test_ranking.py ............                             [ 48%]
analytics\tests\test_segment_portfolio.py ..................             [ 57%]
analytics\tests\test_segmentation.py ...........                         [ 60%]
analytics\tests\test_trends.py .........................                 [ 75%]
backend\tests\test_auth.py ...                                           [ 76%]
backend\tests\test_campaign_service.py ........                          [ 80%]
backend\tests\test_compatibility.py ...                                  [ 81%]
backend\tests\test_results.py ....................                       [ 91%]
backend\tests\test_upload.py .............                               [ 98%]
backend\tests\test_validation.py ....                                    [100%]

======================= 205 passed, 6 warnings in 2.41s =======================
```

---

## 5. Modified Files & Git Working Tree Status

### Working Tree Status
```
$ git status --short
 M analytics/forecasting/__init__.py
 M analytics/tests/test_forecasting.py
?? analytics/forecasting/validation.py
?? docs/analytics/PHASE_4_3_WALK_FORWARD_VALIDATION_REPORT.md
```

### File Inventory
1. `analytics/forecasting/validation.py` *(New)*: Implements `validate_baselines`, expanding-window temporal splitting, error metric accumulators, zero-denominator WAPE guards, and origin diagnostics.
2. `analytics/forecasting/__init__.py` *(Modified)*: Exports `validate_baselines` alongside `prepare_daily_series` and `forecast_baselines`.
3. `analytics/tests/test_forecasting.py` *(Modified)*: Added Tests 36–46 validating temporal splits, metrics calculations, leakage safety, parameter constraints, and edge cases.
4. `docs/analytics/PHASE_4_3_WALK_FORWARD_VALIDATION_REPORT.md` *(New)*: Comprehensive audit and validation report.

---

## 6. Boundaries & Operational Limitations

1. **Evaluation Layer Only:** Phase 4.3 evaluates historical forecast error. It does not select a winning model, claim production readiness, or dynamically switch models in production.
2. **MAPE Exclusion:** MAPE was intentionally excluded due to division-by-zero distortion with observed zeros; WAPE is used instead.
3. **Pure Functional Analytics Scope:** No database schemas, migrations, API endpoints, backend services, or frontend components were modified.
4. **No Dependencies Added:** Implemented strictly with Python standard library (`datetime`, `math`) and `pandas`.

---

## 7. Completion Sign-Off

Phase 4.3 is complete. The walk-forward temporal validation layer is leakage-safe, deterministic, fully tested against regression and edge cases, and ready for review.
