# Market Orbit — Phase 4.2: Deterministic Baseline Forecasting Models Report

**Document Version:** 1.0  
**Date:** September 19, 2026  
**Track:** Analytics & AI Architecture  
**Role:** Senior Time-Series Forecasting Engineer  
**Status:** Implementation & Verification Complete  

---

## 1. Executive Summary

Phase 4.2 implements Market Orbit's deterministic baseline forecasting models in `analytics/forecasting/baselines.py`. Consuming the prepared daily time series from Phase 4.1 (`prepare_daily_series`), this module evaluates model eligibility and generates forecasts for three foundational baselines:
1. **Naive Persistence Baseline (`naive`)**: Projects the latest valid observed value forward.
2. **Simple Moving Average (`sma_7`)**: Projects the unweighted 7-day rolling mean forward.
3. **Seven-Day Seasonal Naive (`seasonal_naive`)**: Replicates the day-of-week cyclical pattern from the preceding week.

All forecasts operate exclusively on additive metrics (`spend`, `conversions`, `clicks`, `impressions`, `revenue`). Incomplete or untracked revenue is strictly preserved as `None` in forecast outputs, and unobserved calendar gaps are never fabricated as zero activity.

---

## 2. Files Created or Modified

1. **`analytics/forecasting/baselines.py`** *(Created)*:
   - Implements `forecast_baselines(df: pd.DataFrame, horizon: int = 7) -> Dict[str, Any]`.
   - Validates `horizon` parameter as a positive integer.
   - Evaluates dataset eligibility against the Phase 4.0 density thresholds.
   - Computes deterministic baseline forecasts across additive metrics.
2. **`analytics/forecasting/__init__.py`** *(Modified)*:
   - Exposes public entry point: `forecast_baselines`.
3. **`analytics/tests/test_forecasting.py`** *(Modified)*:
   - Expanded from 15 to 28 unit and regression tests covering all model eligibility checks, calendar gap rejections, revenue completeness rules, invalid parameter handling, and data immutability.
4. **`docs/analytics/PHASE_4_2_BASELINE_FORECASTING_REPORT.md`** *(Created)*:
   - This implementation and verification report.

---

## 3. Public Function Signature and Output Schema

### Public Entry Point
```python
def forecast_baselines(df: pd.DataFrame, horizon: int = 7) -> Dict[str, Any]:
```

### Output Schema
```json
{
  "is_available": true,
  "status": "ready",
  "horizon": 7,
  "metadata": {
    "start_date": "2026-08-01",
    "end_date": "2026-08-14",
    "forecast_start_date": "2026-08-15",
    "forecast_end_date": "2026-08-21",
    "historical_dates_count": 14,
    "calendar_span_days": 14,
    "is_contiguous": true,
    "contiguous_dates_count": 14,
    "has_minimum_dates": true,
    "has_seasonal_dates": true,
    "revenue_complete": true
  },
  "models": {
    "naive": {
      "is_eligible": true,
      "model_name": "naive_persistence",
      "forecast": [
        {
          "date": "2026-08-15",
          "spend": 240.00,
          "conversions": 14,
          "clicks": 70,
          "impressions": 1400,
          "revenue": 480.00
        }
      ],
      "ineligibility_reason": null
    },
    "sma_7": {
      "is_eligible": true,
      "model_name": "simple_moving_average_7d",
      "forecast": [
        {
          "date": "2026-08-15",
          "spend": 210.00,
          "conversions": 11,
          "clicks": 55,
          "impressions": 1100,
          "revenue": 420.00
        }
      ],
      "ineligibility_reason": null
    },
    "seasonal_naive": {
      "is_eligible": true,
      "model_name": "seasonal_naive_7d",
      "forecast": [
        {
          "date": "2026-08-15",
          "spend": 180.00,
          "conversions": 8,
          "clicks": 40,
          "impressions": 800,
          "revenue": 360.00
        }
      ],
      "ineligibility_reason": null
    }
  },
  "revenue_complete": true,
  "warnings": []
}
```

When input is empty, date column is missing, or historical count is $< 7$ dates:
```json
{
  "is_available": false,
  "status": "insufficient_history",
  "horizon": 7,
  "metadata": {
    "start_date": "2026-08-01",
    "end_date": "2026-08-04",
    "forecast_start_date": null,
    "forecast_end_date": null,
    "historical_dates_count": 4,
    "calendar_span_days": 4,
    "is_contiguous": true,
    "contiguous_dates_count": 4,
    "has_minimum_dates": false,
    "has_seasonal_dates": false,
    "revenue_complete": false
  },
  "models": {
    "naive": {
      "is_eligible": false,
      "model_name": "naive_persistence",
      "forecast": [],
      "ineligibility_reason": "Insufficient historical observations; minimum 7 distinct daily records required."
    },
    "sma_7": {
      "is_eligible": false,
      "model_name": "simple_moving_average_7d",
      "forecast": [],
      "ineligibility_reason": "Insufficient historical observations; minimum 7 distinct daily records required."
    },
    "seasonal_naive": {
      "is_eligible": false,
      "model_name": "seasonal_naive_7d",
      "forecast": [],
      "ineligibility_reason": "Seasonal naive requires at least 14 contiguous calendar days immediately preceding the forecast horizon."
    }
  },
  "revenue_complete": false,
  "warnings": [
    "Historical series contains 4 distinct date(s); minimum 7 distinct daily observations required for reliable forecasting."
  ]
}
```

---

## 4. Exact Mathematical Formulas & Eligibility Rules

### 1. Naive Persistence (`naive_persistence`)
- **Formula**:
  For forecast day $t \in [1, \text{horizon}]$:
  $$\hat{y}_{T+t} = y_T$$
  where $y_T$ represents the latest observed historical value.
- **Dates**:
  $$D_{T+t} = D_T + t \text{ calendar days}$$
- **Eligibility**:
  Requires at least 7 distinct historical observations (`has_minimum_dates = True`).
- **Gaps**: Does not interpolate or assume unobserved dates are zero.

### 2. Simple Moving Average (`simple_moving_average_7d`)
- **Formula**:
  For forecast day $t \in [1, \text{horizon}]$:
  $$\hat{y}_{T+t} = \frac{1}{7} \sum_{i=0}^6 y_{T-i}$$
  Float metrics (`spend`, `revenue`) are rounded to 2 decimals; count metrics (`conversions`, `clicks`, `impressions`) are rounded to non-negative integers (`int(round(max(0, val)))`).
- **Eligibility**:
  Requires at least 7 observed daily records (`len(series) >= 7`).
- **Gap Policy**:
  If the recent 7-day window contains calendar gaps, the average is calculated over the 7 most recent observed days, and an explicit warning is attached to the output preserving data-quality transparency.

### 3. Seven-Day Seasonal Naive (`seasonal_naive_7d`)
- **Formula**:
  For forecast day $t \in [1, \text{horizon}]$:
  $$\hat{y}_{T+t} = y_{T - 7 + ((t - 1) \pmod 7 + 1)}$$
  Replicates the exact observed metric value from the corresponding day of the week 7 days prior.
- **Eligibility**:
  Strictly requires:
  1. At least 14 observed daily records (`len(series) >= 14`).
  2. The most recent 14 records must be **genuinely contiguous calendar days**: $(D_T - D_{T-13}).\text{days} == 13$.
- **Rejection Policy**:
  If a dataset has 14 rows but contains calendar gaps in the recent 14-day history, `seasonal_naive` is **declined** (`is_eligible = False`), with an explicit ineligibility reason explaining the calendar gap.

---

## 5. Metric-Level Missing-Value & Revenue-Completeness Behavior

1. **Additive Metrics Only**:
   - Only `spend`, `conversions`, `clicks`, `impressions`, and `revenue` are forecasted.
   - Derived ratios (`cpa`, `cpc`, `ctr`, `conversion_rate`, `roas`, `roi`) are **not forecasted** in this phase.
2. **Revenue Completeness**:
   - If historical revenue is incomplete, partially missing, or contains non-numeric strings, `revenue_complete` is `False`.
   - When `revenue_complete == False`, all forecast points across all models carry `revenue: null`/`None`.
   - An explicit warning is attached to the output: `"Revenue forecasting is unavailable because historical revenue tracking is incomplete or untracked."`
   - Explicit historical `0.0` revenue is treated as tracked and complete zero revenue.
3. **Optional Clicks & Impressions**:
   - If clicks or impressions are absent from the historical records, they default to 0 and are forecasted as 0.
4. **Horizon Validation**:
   - Parameter `horizon` is strictly validated as a positive integer ($> 0$).
   - Values such as `0`, `-1`, `True`, `False`, `"7"`, `7.5`, and `None` raise `ValueError` immediately without silent coercion.

---

## 6. Verification & Test Suite Results

### Focused Forecasting Tests (`pytest analytics/tests/test_forecasting.py -v`)
```
analytics/tests/test_forecasting.py::test_valid_dates_and_chronological_ordering PASSED [  3%]
analytics/tests/test_forecasting.py::test_strict_date_parsing_and_invalid_date_exclusion_diagnostics PASSED [  7%]
analytics/tests/test_forecasting.py::test_duplicate_date_aggregation PASSED [ 10%]
analytics/tests/test_forecasting.py::test_empty_input_and_missing_date_column PASSED [ 14%]
analytics/tests/test_forecasting.py::test_no_valid_dates PASSED          [ 17%]
analytics/tests/test_forecasting.py::test_contiguous_vs_non_contiguous_dates PASSED [ 21%]
analytics/tests/test_forecasting.py::test_observed_zeros_vs_unresolved_date_gaps PASSED [ 25%]
analytics/tests/test_forecasting.py::test_no_unjustified_zero_filling_or_interpolation PASSED [ 28%]
analytics/tests/test_forecasting.py::test_optional_clicks_and_impressions PASSED [ 32%]
analytics/tests/test_forecasting.py::test_complete_untracked_partially_missing_and_invalid_revenue PASSED [ 35%]
analytics/tests/test_forecasting.py::test_deterministic_repeated_calls PASSED [ 39%]
analytics/tests/test_forecasting.py::test_caller_dataframe_immutability PASSED [ 42%]
analytics/tests/test_forecasting.py::test_strict_json_serialization_allow_nan_false PASSED [ 46%]
analytics/tests/test_regression_phase_1_to_3_analytics_unchanged PASSED [ 50%]
analytics/tests/test_seasonal_dates_diagnostic_14_contiguous_days PASSED [ 53%]
analytics/tests/test_naive_persistence_values_and_dates PASSED [ 57%]
analytics/tests/test_sma_7_eligibility_and_exact_calculations PASSED [ 60%]
analytics/tests/test_seasonal_naive_eligibility_14_contiguous_dates PASSED [ 64%]
analytics/tests/test_seasonal_naive_rejection_of_14_rows_with_calendar_gaps PASSED [ 67%]
analytics/tests/test_baselines_empty_input_missing_date_and_insufficient_history PASSED [ 71%]
analytics/tests/test_baselines_revenue_semantics_complete_untracked_partial_invalid PASSED [ 75%]
analytics/tests/test_baselines_observed_zero_vs_unresolved_gaps PASSED [ 78%]
analytics/tests/test_baselines_optional_clicks_impressions PASSED [ 82%]
analytics/tests/test_baselines_invalid_horizon_rejection PASSED [ 85%]
analytics/tests/test_baselines_deterministic_repeated_calls PASSED [ 89%]
analytics/tests/test_baselines_caller_dataframe_immutability PASSED [ 92%]
analytics/tests/test_baselines_strict_json_serialization_allow_nan_false PASSED [ 96%]
analytics/tests/test_duplicate_date_revenue_uncertainty_preservation PASSED [100%]

============================= 28 passed in 1.08s ==============================
```

### Full Repository Test Suite (`pytest`)
```
collected 187 items

analytics\tests\test_ai.py ..                                            [  1%]
analytics\tests\test_forecasting.py ............................         [ 16%]
analytics\tests\test_insights.py ..............                          [ 23%]
analytics\tests\test_metrics.py ............                             [ 29%]
analytics\tests\test_preprocessing.py ..............                     [ 37%]
analytics\tests\test_ranking.py ............                             [ 43%]
analytics\tests\test_segment_portfolio.py ..................             [ 53%]
analytics\tests\test_segmentation.py ...........                         [ 59%]
analytics\tests\test_trends.py .........................                 [ 72%]
backend\tests\test_auth.py ...                                           [ 74%]
backend\tests\test_campaign_service.py ........                          [ 78%]
backend\tests\test_compatibility.py ...                                  [ 80%]
backend\tests\test_results.py ....................                       [ 90%]
backend\tests\test_upload.py .............                               [ 97%]
backend\tests\test_validation.py ....                                    [100%]

======================= 187 passed, 6 warnings in 2.43s =======================
```

---

## 7. Invariant & Contract Confirmations

- **No Backtesting or Model Selection**: No error evaluation, rolling origin backtesting, or automatic model selection was implemented.
- **No Backend or Frontend Integration**: `AnalysisService`, database models, API schemas, and frontend views were not touched.
- **Phase 1–3 Invariance**: All KPI metrics, campaign ranking, historical trend analysis, deterministic insights, campaign cohorts, and segment portfolio profiling continue to pass without modification.
- **Caller Immutability**: Verified with `pd.testing.assert_frame_equal`.
- **Strict JSON Compliance**: Outputs pass `json.dumps(result, allow_nan=False)`.

---

## 8. Git Status & History

- **Branch**: `analytics`
- **Latest Prior Commit**: `e7ed291` (`implement Phase 4.1 forecasting data preprocessing and series regularization`)
- **Working Tree**:
  ```
  M analytics/forecasting/__init__.py
  M analytics/tests/test_forecasting.py
  ?? analytics/forecasting/baselines.py
  ?? docs/analytics/PHASE_4_2_BASELINE_FORECASTING_REPORT.md
  ```

Phase 4.2 is complete and verified. Ready for review.
