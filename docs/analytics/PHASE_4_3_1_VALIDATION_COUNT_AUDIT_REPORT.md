# Market Orbit — Phase 4.3.1: Walk-Forward Evaluation Count and Alignment Audit Report

**Status:** Completed  
**Author:** Senior Time-Series Validation Engineer  
**Date:** 2026-10-14  
**Target Repository:** `market-orbit`  
**Git Branch:** `analytics`  
**Base Commit:** `336a4e8` (*"harden Phase 4.2 baseline forecasting contracts for missing metric semantics, SMA-7 contiguity, and count validation"*)  

---

## 1. Executive Summary

Phase 4.3.1 was executed as a narrowly scoped mathematical correctness audit of Market Orbit's Phase 4.3 walk-forward temporal validation implementation. The audit verified:
1. **The Origin-Generation Algorithm:** Validated that expanding-window origin generation accurately identifies origins starting from `min_train_dates` and steps forward until the final observed date ($D_{N-1}$).
2. **The 28-Date Reference Case & Horizon Truncation:** Confirmed that for a 28-date fixture with `min_train_dates=14`, `horizon=7`, and `step=1`, exactly 14 origins are produced. The future horizons near the dataset boundary progressively truncate, yielding **exactly 77 evaluated forecast-actual pairs** per eligible model and metric (not 98, which was an un-truncated $14 \times 7$ illustrative placeholder in the Phase 4.3 report schema).
3. **Calendar Date Alignment & Gap Handling:** Confirmed that forecast dates are aligned with actual observations on the exact same calendar date. Unobserved calendar dates (gaps) are omitted from scoring and never zero-filled or substituted.
4. **Point-Weighted Pooled Error Aggregation:** Confirmed that MAE, RMSE, and WAPE are pooled across all evaluated forecast points from all eligible origins, preventing distortion caused by unweighted averages of origins with unequal sample sizes.
5. **Leakage Safety & Revenue Completeness:** Confirmed that training slices contain records dated strictly on or before their origin, and revenue is evaluated only when both the training split and evaluation actuals satisfy revenue completeness.

All 50 forecasting tests passed (`pytest analytics/tests/test_forecasting.py -v`). The full test suite passed with **209 passing tests** and zero failures (`pytest`).

---

## 2. Walk-Forward Origin-Generation Algorithm

Let $D_0, D_1, \dots, D_{N-1}$ be the sorted distinct calendar dates observed in the input dataset ($N = \text{total\_valid\_dates}$).

```python
origin_indices: List[int] = []
curr_k = min_train_dates - 1
while curr_k < total_valid_dates - 1:
    origin_indices.append(curr_k)
    curr_k += step
```

### Algorithm Properties
1. **Initial Origin ($k = \text{min\_train\_dates} - 1$):**
   The training split $D_0, \dots, D_k$ contains exactly $\text{min\_train\_dates}$ distinct dates.
2. **Origin Stepping ($k \leftarrow k + \text{step}$):**
   Advances the origin index strictly by `step` observed calendar dates.
3. **Termination Guard ($k < N - 1$):**
   An origin at index $k = N - 1$ corresponds to the final date in the dataset. Because $D_{N-1}$ has zero future dates in the dataset, its forecast cannot be evaluated against actuals. Therefore, origins terminate at $k < N - 1$.
4. **Insufficient History Guard ($N \le \text{min\_train\_dates}$):**
   If $N \le \text{min\_train\_dates}$, zero walk-forward origins can be evaluated against future actuals. The function returns `is_available = False` with `status = "insufficient_history"`.

---

## 3. The 28-Date Reference Case Verification

A deterministic fixture was constructed with 28 consecutive calendar dates (August 1 to August 28, 2026), all five additive metrics (`spend`, `conversions`, `clicks`, `impressions`, `revenue`) present and valid on every date, and complete revenue tracking (`revenue_complete = True`). Parameters: `horizon=7`, `min_train_dates=14`, `step=1`.

### Origin and Evaluation Point Breakdown

| Origin Index | Origin Date ($D_k$) | Training Dates | Forecast Window ($D_k + 1 \dots D_k + 7$) | Dataset Overlap | Evaluated Points Count |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **0** | 2026-08-14 | Aug 1–14 (14 dates) | 2026-08-15 to 2026-08-21 | Aug 15–21 | **7** |
| **1** | 2026-08-15 | Aug 1–15 (15 dates) | 2026-08-16 to 2026-08-22 | Aug 16–22 | **7** |
| **2** | 2026-08-16 | Aug 1–16 (16 dates) | 2026-08-17 to 2026-08-23 | Aug 17–23 | **7** |
| **3** | 2026-08-17 | Aug 1–17 (17 dates) | 2026-08-18 to 2026-08-24 | Aug 18–24 | **7** |
| **4** | 2026-08-18 | Aug 1–18 (18 dates) | 2026-08-19 to 2026-08-25 | Aug 19–25 | **7** |
| **5** | 2026-08-19 | Aug 1–19 (19 dates) | 2026-08-20 to 2026-08-26 | Aug 20–26 | **7** |
| **6** | 2026-08-20 | Aug 1–20 (20 dates) | 2026-08-21 to 2026-08-27 | Aug 21–27 | **7** |
| **7** | 2026-08-21 | Aug 1–21 (21 dates) | 2026-08-22 to 2026-08-28 | Aug 22–28 | **7** |
| **8** | 2026-08-22 | Aug 1–22 (22 dates) | 2026-08-23 to 2026-08-29 | Aug 23–28 (Aug 29 unobserved) | **6** |
| **9** | 2026-08-23 | Aug 1–23 (23 dates) | 2026-08-24 to 2026-08-30 | Aug 24–28 (Aug 29–30 unobserved) | **5** |
| **10** | 2026-08-24 | Aug 1–24 (24 dates) | 2026-08-25 to 2026-08-31 | Aug 25–28 (Aug 29–31 unobserved) | **4** |
| **11** | 2026-08-25 | Aug 1–25 (25 dates) | 2026-08-26 to 2026-09-01 | Aug 26–28 (Aug 29–Sep 1 unobserved) | **3** |
| **12** | 2026-08-26 | Aug 1–26 (26 dates) | 2026-08-27 to 2026-09-02 | Aug 27–28 (Aug 29–Sep 2 unobserved) | **2** |
| **13** | 2026-08-27 | Aug 1–27 (27 dates) | 2026-08-28 to 2026-09-03 | Aug 28 only (Aug 29–Sep 3 unobserved) | **1** |
| **Total** | — | — | — | — | **77** |

### Expected vs. Actual Counts
- **Total Origins Generated:** Expected: **14**, Actual: **14**.
- **Evaluated Points Count (per model/metric):**
  $$\text{Total Points} = (8 \times 7) + 6 + 5 + 4 + 3 + 2 + 1 = 56 + 21 = \mathbf{77}$$
  - `naive_persistence`: **77**
  - `simple_moving_average_7d`: **77**
  - `seasonal_naive_7d`: **77**
- **Discrepancy in Phase 4.3 Report Schema Example:**
  The schema illustration in `PHASE_4_3_WALK_FORWARD_VALIDATION_REPORT.md` had used $14 \times 7 = 98$ as an illustrative placeholder. The audit confirmed that the underlying implementation in `analytics/forecasting/validation.py` correctly and strictly evaluated **77 points**. The report schema example has been corrected from 98 to 77 to accurately represent the mathematical reality of horizon truncation near the dataset boundary.

---

## 4. Origin & Horizon Alignment Audit

1. **Leakage Isolation:** Each training slice is strictly filtered to records where `_parsed_date <= origin_date`. Future records are excluded before calling `prepare_daily_series` or `forecast_baselines`.
2. **Exact Calendar Match:** Forecast point on date $D$ is matched only to actuals on date $D$. Forecast points falling outside the dataset (e.g. Day 29–34) are omitted from scoring.
3. **No Synthetic Zero-Filling:** Unobserved test dates are never filled with zero or interpolated from adjacent dates.
4. **Independent Model Eligibility:** Model eligibility is evaluated independently at each origin:
   - Naive persistence is eligible at all 14 origins.
   - SMA-7 is eligible at all 14 origins (7 consecutive calendar days exist prior to every origin).
   - Seasonal naive is eligible at all 14 origins (14 consecutive calendar days exist prior to every origin).
   - When calendar gaps are introduced, SMA-7 and Seasonal Naive are flagged ineligible with explicit reasons, while Naive persistence remains eligible.
5. **Repeated Actual Date Evaluation:** A date like Day 16 is evaluated in Origin 0 (as horizon step 2) and Origin 1 (as horizon step 1). Each evaluation contributes its respective error to the pooled metric, adhering to standard rolling-origin backtesting methodology.

---

## 5. Error Metric Aggregation Audit

### Point-Weighted Pooled vs. Unweighted Origin Average
The audit verified that error metrics are computed from pooled underlying error sums across all evaluated points:
$$\text{MAE} = \frac{\sum_{i=1}^P |y_{pred, i} - y_{act, i}|}{P}$$
$$\text{RMSE} = \sqrt{\frac{\sum_{i=1}^P (y_{pred, i} - y_{act, i})^2}{P}}$$
$$\text{WAPE} = \left(\frac{\sum_{i=1}^P |y_{pred, i} - y_{act, i}|}{\sum_{i=1}^P |y_{act, i}|}\right) \times 100$$

### Hand-Calculable Proof (Test 48)
- Origin 1 evaluates 2 test points with errors 10.0 and 20.0 ($\text{MAE}_{\text{orig1}} = 15.0$).
- Origin 2 evaluates 1 test point with error 10.0 ($\text{MAE}_{\text{orig2}} = 10.0$).
- **Unweighted Origin Average:** $(15.0 + 10.0) / 2 = 12.5$.
- **Point-Weighted Pooled MAE:** $(10.0 + 20.0 + 10.0) / 3 = 40.0 / 3 = 13.3333$.
- The implementation strictly computes **13.3333** ($\neq 12.5$), mathematically proving point-weighted pooling.
- **Zero-Point Metrics:** When a metric has 0 evaluated points (e.g. untracked clicks), MAE, RMSE, and WAPE are strictly `None` with `wape_status = "no_evaluated_points"`. No scores are fabricated.

---

## 6. Verification and Regression Testing

### 6.1 Test Suite Expansion
Added Tests 47–50 to [analytics/tests/test_forecasting.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/tests/test_forecasting.py):
- **Test 47 (`test_walk_forward_28_date_reference_case`):** Verifies the 28-date reference case with 14 origins, truncated horizons (from 7 down to 1), and exactly 77 evaluated points per model and metric.
- **Test 48 (`test_walk_forward_pooled_vs_unweighted_origin_aggregation`):** Hand-calculable test mathematically verifying point-weighted pooled error aggregation over unweighted origin averages.
- **Test 49 (`test_walk_forward_multi_origin_repeated_date_evaluation`):** Verifies independent rolling-origin evaluations of repeated calendar dates.
- **Test 50 (`test_walk_forward_untracked_metric_zero_points_no_scores`):** Verifies that untracked metrics produce 0 evaluated points and strictly `None` error metrics.

### 6.2 Actual Command Outputs

#### 1. Forecasting Test Suite (50 passed)
```bash
$ pytest analytics/tests/test_forecasting.py -v
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-8.3.4, pluggy-1.6.0
collected 50 items

analytics/tests/test_forecasting.py::test_valid_dates_and_chronological_ordering PASSED [  2%]
analytics/tests/test_forecasting.py::test_strict_date_parsing_and_invalid_date_exclusion_diagnostics PASSED [  4%]
analytics/tests/test_forecasting.py::test_duplicate_date_aggregation PASSED [  6%]
analytics/tests/test_forecasting.py::test_empty_input_and_missing_date_column PASSED [  8%]
analytics/tests/test_forecasting.py::test_no_valid_dates PASSED          [ 10%]
analytics/tests/test_forecasting.py::test_contiguous_vs_non_contiguous_dates PASSED [ 12%]
analytics/tests/test_forecasting.py::test_observed_zeros_vs_unresolved_date_gaps PASSED [ 14%]
analytics/tests/test_forecasting.py::test_no_unjustified_zero_filling_or_interpolation PASSED [ 16%]
analytics/tests/test_forecasting.py::test_optional_clicks_and_impressions PASSED [ 18%]
analytics/tests/test_forecasting.py::test_complete_untracked_partially_missing_and_invalid_revenue PASSED [ 20%]
analytics/tests/test_forecasting.py::test_deterministic_repeated_calls PASSED [ 22%]
analytics/tests/test_forecasting.py::test_caller_dataframe_immutability PASSED [ 24%]
analytics/tests/test_forecasting.py::test_strict_json_serialization_allow_nan_false PASSED [ 26%]
analytics/tests/test_forecasting.py::test_regression_phase_1_to_3_analytics_unchanged PASSED [ 28%]
analytics/tests/test_forecasting.py::test_seasonal_dates_diagnostic_14_contiguous_days PASSED [ 30%]
analytics/tests/test_forecasting.py::test_naive_persistence_values_and_dates PASSED [ 32%]
analytics/tests/test_forecasting.py::test_sma_7_eligibility_and_exact_calculations PASSED [ 34%]
analytics/tests/test_forecasting.py::test_seasonal_naive_eligibility_14_contiguous_dates PASSED [ 36%]
analytics/tests/test_forecasting.py::test_seasonal_naive_rejection_of_14_rows_with_calendar_gaps PASSED [ 38%]
analytics/tests/test_forecasting.py::test_baselines_empty_input_missing_date_and_insufficient_history PASSED [ 40%]
analytics/tests/test_forecasting.py::test_baselines_revenue_semantics_complete_untracked_partial_invalid PASSED [ 42%]
analytics/tests/test_forecasting.py::test_baselines_observed_zero_vs_unresolved_gaps PASSED [ 44%]
analytics/tests/test_forecasting.py::test_baselines_optional_clicks_impressions PASSED [ 46%]
analytics/tests/test_forecasting.py::test_baselines_invalid_horizon_rejection PASSED [ 48%]
analytics/tests/test_forecasting.py::test_baselines_deterministic_repeated_calls PASSED [ 50%]
analytics/tests/test_forecasting.py::test_baselines_caller_dataframe_immutability PASSED [ 52%]
analytics/tests/test_forecasting.py::test_baselines_strict_json_serialization_allow_nan_false PASSED [ 54%]
analytics/tests/test_forecasting.py::test_duplicate_date_revenue_uncertainty_preservation PASSED [ 56%]
analytics/tests/test_forecasting.py::test_sma_7_rejection_on_window_calendar_gaps PASSED [ 58%]
analytics/tests/test_forecasting.py::test_sma_7_metric_specific_unusable_observations PASSED [ 60%]
analytics/tests/test_forecasting.py::test_count_metric_validation_negative_fractional_non_finite_booleans PASSED [ 62%]
analytics/tests/test_forecasting.py::test_sma_7_count_rounding_policy_explicit_verification PASSED [ 64%]
analytics/tests/test_forecasting.py::test_seasonal_naive_metric_specific_unavailability PASSED [ 66%]
analytics/tests/test_forecasting.py::test_negative_spend_and_currency_validation PASSED [ 68%]
analytics/tests/test_forecasting.py::test_full_json_serialization_with_null_and_zero_metrics PASSED [ 70%]
analytics/tests/test_forecasting.py::test_walk_forward_hand_calculable_metrics PASSED [ 72%]
analytics/tests/test_forecasting.py::test_walk_forward_seasonal_naive_eligibility_and_calculation PASSED [ 74%]
analytics/tests/test_forecasting.py::test_walk_forward_leakage_safety_future_isolation PASSED [ 76%]
analytics/tests/test_forecasting.py::test_walk_forward_parameter_validation PASSED [ 78%]
analytics/tests/test_forecasting.py::test_walk_forward_insufficient_history_and_empty_inputs PASSED [ 80%]
analytics/tests/test_forecasting.py::test_walk_forward_calendar_gaps_and_missing_eval_dates PASSED [ 82%]
analytics/tests/test_forecasting.py::test_walk_forward_wape_zero_denominator PASSED [ 84%]
analytics/tests/test_forecasting.py::test_walk_forward_revenue_completeness PASSED [ 86%]
analytics/tests/test_forecasting.py::test_walk_forward_metric_specific_evaluation_counts PASSED [ 88%]
analytics/tests/test_forecasting.py::test_walk_forward_immutability_and_determinism PASSED [ 90%]
analytics/tests/test_forecasting.py::test_walk_forward_package_export PASSED [ 92%]
analytics/tests/test_forecasting.py::test_walk_forward_28_date_reference_case PASSED [ 94%]
analytics/tests/test_forecasting.py::test_walk_forward_pooled_vs_unweighted_origin_aggregation PASSED [ 96%]
analytics/tests/test_forecasting.py::test_walk_forward_multi_origin_repeated_date_evaluation PASSED [ 98%]
analytics/tests/test_forecasting.py::test_walk_forward_untracked_metric_zero_points_no_scores PASSED [100%]

============================= 50 passed in 1.01s ==============================
```

#### 2. Full Test Suite (209 passed)
```bash
$ pytest
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-8.3.4, pluggy-1.6.0
collected 209 items

analytics\tests\test_ai.py ..                                            [  0%]
analytics\tests\test_forecasting.py .................................... [ 18%]
..............                                                           [ 24%]
analytics\tests\test_insights.py ..............                          [ 31%]
analytics\tests\test_metrics.py ............                             [ 37%]
analytics\tests\test_preprocessing.py ..............                     [ 44%]
analytics\tests\test_ranking.py ............                             [ 49%]
analytics\tests\test_segment_portfolio.py ..................             [ 58%]
analytics\tests\test_segmentation.py ...........                         [ 63%]
analytics\tests\test_trends.py .........................                 [ 75%]
backend\tests\test_auth.py ...                                           [ 77%]
backend\tests\test_campaign_service.py ........                          [ 80%]
backend\tests\test_compatibility.py ...                                  [ 82%]
backend\tests\test_results.py ....................                       [ 91%]
backend\tests\test_upload.py .............                               [ 98%]
backend\tests\test_validation.py ....                                    [100%]

======================= 209 passed, 6 warnings in 2.48s =======================
```

---

## 7. Modified Files & Git Working Tree Status

```bash
$ git status --short
 M analytics/forecasting/__init__.py
 M analytics/tests/test_forecasting.py
 M docs/analytics/PHASE_4_3_WALK_FORWARD_VALIDATION_REPORT.md
?? analytics/forecasting/validation.py
?? docs/analytics/PHASE_4_3_1_VALIDATION_COUNT_AUDIT_REPORT.md
```

- [analytics/forecasting/validation.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/forecasting/validation.py): Walk-forward validation engine.
- [analytics/forecasting/__init__.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/forecasting/__init__.py): Exposes `validate_baselines`.
- [analytics/tests/test_forecasting.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/tests/test_forecasting.py): Added Tests 47–50 verifying 28-date reference counts, pooled aggregation, and zero-point handling.
- [docs/analytics/PHASE_4_3_WALK_FORWARD_VALIDATION_REPORT.md](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/docs/analytics/PHASE_4_3_WALK_FORWARD_VALIDATION_REPORT.md): Corrected illustrative points evaluated from 98 to 77.
- [docs/analytics/PHASE_4_3_1_VALIDATION_COUNT_AUDIT_REPORT.md](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/docs/analytics/PHASE_4_3_1_VALIDATION_COUNT_AUDIT_REPORT.md): This report.

---

## 8. Audit Conclusion and Sign-Off

The walk-forward evaluation engine in `analytics/forecasting/validation.py` is mathematically correct:
1. The 28-date reference case correctly and deterministically produces **14 origins and 77 evaluated forecast-actual pairs** per eligible model and metric.
2. Horizon truncation near the dataset boundary is correctly enforced without synthesizing or interpolating data.
3. Metric aggregation strictly uses the point-weighted pooled error methodology.
4. No data leakage or unauthorized modifications exist.
