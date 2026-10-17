# Market Orbit — Phase 3.2: Segment Portfolio Profiling & Efficiency Indexing Report

## 1. Executive Summary
Phase 3.2 extends Market Orbit's deterministic segmentation analytics by introducing segment portfolio profiling and efficiency indexing in a dedicated module (`analytics/segmentation/portfolio.py`). It calculates portfolio-share metrics, conversion-efficiency ratios, and CPA index metrics across marketer-supplied `customer_segment` values, adhering strictly to deterministic computation, complete revenue semantics, zero-denominator safeguards, and strict JSON serialization.

---

## 2. Files Created or Modified

1. **`analytics/segmentation/portfolio.py`** (Created):
   - Implements `profile_segment_portfolio(df: pd.DataFrame) -> Dict[str, Any]`.
   - Cleans segment labels using established sentinels (`None`, `""`, `"nan"`, `"none"`, `"nat"`, `"null"`).
   - Computes whole-portfolio denominators (`total_spend`, `total_conversions`, `portfolio_revenue`, `portfolio_cpa`).
   - Calculates per-segment spend, conversions, revenue, CPA, ROAS, `share_of_spend`, `share_of_conversions`, `share_of_revenue`, `conversion_efficiency_ratio`, and `cpa_index`.

2. **`analytics/segmentation/__init__.py`** (Modified):
   - Exports `profile_segment_portfolio` alongside `classify_campaign_cohorts`.

3. **`analytics/segmentation/cohorts.py`** (Modified):
   - Re-exports `profile_segment_portfolio` for flexible caller import paths while leaving `classify_campaign_cohorts` completely untouched.

4. **`analytics/tests/test_segment_portfolio.py`** (Created):
   - Comprehensive 16-test suite covering all specified requirements and mathematical edge cases.

---

## 3. Function Signature and Output Contract

### Entry Point
```python
def profile_segment_portfolio(df: pd.DataFrame) -> Dict[str, Any]:
```

### Schema
```json
{
  "is_available": true,
  "total_segments": 2,
  "segments": {
    "Enterprise": {
      "spend": 500.0,
      "conversions": 50,
      "revenue": 1500.0,
      "cpa": 10.0,
      "roas": 3.0,
      "share_of_spend": 50.0,
      "share_of_conversions": 50.0,
      "share_of_revenue": 30.0,
      "conversion_efficiency_ratio": 1.0,
      "cpa_index": 100.0
    },
    "SMB": {
      "spend": 500.0,
      "conversions": 50,
      "revenue": 3500.0,
      "cpa": 10.0,
      "roas": 7.0,
      "share_of_spend": 50.0,
      "share_of_conversions": 50.0,
      "share_of_revenue": 70.0,
      "conversion_efficiency_ratio": 1.0,
      "cpa_index": 100.0
    }
  }
}
```

When no usable segments exist (`df` is None, empty, missing `customer_segment` column, or all segment values are missing/blank/sentinels):
```json
{
  "is_available": false,
  "total_segments": 0,
  "segments": {}
}
```

---

## 4. Denominator and Missing-Data Policies

1. **Portfolio Denominator Consistency**:
   - Denominators (`total_spend`, `total_conversions`, `portfolio_revenue`, `portfolio_cpa`) are calculated across the entire dataset `df`.
   - Unlabeled/unsegmented rows are excluded from the `segments` map.
   - If only partial rows are labeled, the segment shares sum to the labeled portion of the portfolio (e.g. 80% if 20% of spend is unlabeled). This avoids silently presenting partial coverage as full coverage.

2. **Revenue Completeness**:
   - `portfolio_revenue` requires complete tracking across all rows without missing/null values or non-numeric strings.
   - If portfolio revenue is incomplete or untracked, `share_of_revenue` is returned as `None` for all segments.
   - If a specific segment contains missing revenue, its `revenue`, `roas`, and `share_of_revenue` are `None`.
   - Explicit zero revenue (`0.0`) is preserved and distinguished from untracked revenue (`None`).
   - If total portfolio revenue is explicitly `0.0`, `share_of_revenue` is `None` to prevent `0/0` division.

3. **Zero Denominator Guards**:
   - If `total_spend == 0.0`: `share_of_spend` is `None`, and `conversion_efficiency_ratio` is `None`.
   - If `total_conversions == 0`: `share_of_conversions`, `conversion_efficiency_ratio`, `cpa`, and `cpa_index` are `None`.
   - If `segment_spend == 0.0`: `share_of_spend` is `0.0`, `conversion_efficiency_ratio` is `None` (division by 0 spend share avoided).
   - If `portfolio_cpa == 0.0` or `portfolio_cpa is None`: `cpa_index` is `None`.
   - No `NaN` or `Infinity` values are produced; all output satisfies `json.dumps(result, allow_nan=False)`.

4. **Segment Labels**:
   - Marketer-supplied target audience values are cleaned using string trimming.
   - Sentinels (`""`, `"nan"`, `"none"`, `"nat"`, `"null"`, case-insensitive) and nulls are stripped.
   - Segment keys in `segments` are deterministically sorted in ascending alphabetical order.

---

## 5. Test Suite Verification

### Focused Tests (`analytics/tests/test_segment_portfolio.py`)
16/16 tests passed:
- `test_spend_and_conversion_share_exact`: PASSED
- `test_revenue_shares_with_complete_revenue`: PASSED
- `test_missing_and_partially_missing_revenue`: PASSED
- `test_explicit_zero_revenue_vs_untracked`: PASSED
- `test_conversion_efficiency_ratios_above_below_equal_one`: PASSED
- `test_cpa_index_below_above_equal_one_hundred`: PASSED
- `test_zero_total_spend`: PASSED
- `test_zero_total_conversions`: PASSED
- `test_zero_or_undefined_portfolio_cpa`: PASSED
- `test_missing_customer_segment_column`: PASSED
- `test_null_blank_sentinel_segment_labels`: PASSED
- `test_partial_segment_label_coverage_and_denominator_consistency`: PASSED
- `test_empty_input_and_single_segment_input`: PASSED
- `test_deterministic_ordering_and_repeated_call_consistency`: PASSED
- `test_strict_json_serialization_allow_nan_false`: PASSED
- `test_regression_existing_cohort_entrypoint`: PASSED

### Cohort Regression Tests (`analytics/tests/test_segmentation.py`)
11/11 tests passed.

### Full Repository Test Suite (`pytest`)
157/157 tests passed (0 failures, 6 third-party library deprecation warnings).

---

## 6. Scope Boundaries & Next Phase
- Phase 3.2 is complete and self-contained.
- No cross-tabulation, AI recommendations, backend API modifications, or database changes were made.
