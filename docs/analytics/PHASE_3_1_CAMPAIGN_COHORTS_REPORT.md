# Market Orbit — Phase 3.1 Implementation Report: Campaign Performance Cohorts

**Document Version:** 1.0  
**Date:** September 19, 2026  
**Track:** Analytics & AI Architecture  
**Lead:** Vishal S Naik (Analytics & AI Track)  
**Collaborators:** Sushanth S (Backend & Database Track), Apeksha C Rao (Frontend Track)  
**Status:** Verification & Implementation Complete  

---

## 1. Executive Summary

Phase 3.1 implements campaign performance cohort classification for Market Orbit within a dedicated module: [`analytics/segmentation/cohorts.py`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/segmentation/cohorts.py).

Operating strictly on campaign-level advertising data, the engine partitions campaigns into four mutually exclusive, collectively exhaustive performance cohorts based on conversion volume and cost-per-acquisition (CPA) efficiency relative to empirical dataset medians and portfolio benchmarks.

### Key Deliverables:
1. **Quadrant Cohort Engine (`classify_campaign_cohorts`):** Accepts campaign dataFrames and classifies each campaign into one of four deterministic cohorts:
   - `scale_ready`: High conversion volume ($\ge \text{median}$) + Low CPA ($\le \text{portfolio CPA}$).
   - `volume_driver`: High conversion volume ($\ge \text{median}$) + High CPA ($> \text{portfolio CPA}$).
   - `efficiency_niche`: Low conversion volume ($< \text{median}$) + Low CPA ($\le \text{portfolio CPA}$).
   - `budget_drain`: Low conversion volume ($< \text{median}$) + High CPA ($> \text{portfolio CPA}$), OR zero conversions.
2. **Deterministic Empirical Baselines:** Calculates portfolio CPA as $\sum \text{spend} / \sum \text{conversions}$ and conversion threshold via standard statistical median for both odd and even counts.
3. **Precedence Rules & Zero-Conversion Safeguards:** Campaigns with positive spend and zero conversions are unconditionally routed to `budget_drain`. Undefined CPA is never treated as zero.
4. **Data Contract & Revenue Semantics:** Reuses `aggregate_campaigns()` from [`analytics/performance/ranking.py`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/performance/ranking.py). Missing revenue remains strictly `None`; ROAS is never fabricated.
5. **Deterministic Ordering:** Campaigns within cohorts are sorted predictably using secondary campaign name tie-breakers.

---

## 2. Files Created and Modified

| File Path | Action | Description |
| :--- | :---: | :--- |
| [`analytics/segmentation/cohorts.py`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/segmentation/cohorts.py) | **Created** | Core cohort engine implementing `classify_campaign_cohorts()`, calculating standard medians, portfolio CPA, and partitioning campaigns into 4 cohorts. |
| [`analytics/segmentation/__init__.py`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/segmentation/__init__.py) | **Created** | Package entry point exposing `classify_campaign_cohorts`. |
| [`analytics/tests/test_segmentation.py`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/tests/test_segmentation.py) | **Created** | 11 focused unit tests covering cohort definitions, odd/even medians, ties, zero conversions, single campaigns, missing revenue, and JSON hygiene. |
| [`docs/analytics/PHASE_3_1_CAMPAIGN_COHORTS_REPORT.md`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/docs/analytics/PHASE_3_1_CAMPAIGN_COHORTS_REPORT.md) | **Created** | Phase 3.1 implementation and verification report. |

No pre-existing modules were modified. The Phase 1 KPI engine, Phase 2.1 ranking engine, Phase 2.2/2.3 trend engine, Phase 2.4 deterministic insight engine, and backend services remain completely untouched.

---

## 3. Function Signature and Output Contract

### Function Signature:
```python
def classify_campaign_cohorts(df: pd.DataFrame) -> Dict[str, Any]
```

### Output JSON Schema:
```json
{
  "summary": {
    "total_campaigns": 4,
    "scale_ready_count": 1,
    "volume_driver_count": 1,
    "efficiency_niche_count": 1,
    "budget_drain_count": 1
  },
  "cohorts": {
    "scale_ready": [
      {
        "campaign_name": "Scale Ready Camp",
        "spend": 200.0,
        "conversions": 40,
        "cpa": 5.0,
        "roas": 3.0
      }
    ],
    "volume_driver": [
      {
        "campaign_name": "Volume Driver Camp",
        "spend": 450.0,
        "conversions": 30,
        "cpa": 15.0,
        "roas": 2.0
      }
    ],
    "efficiency_niche": [
      {
        "campaign_name": "Efficiency Niche Camp",
        "spend": 160.0,
        "conversions": 20,
        "cpa": 8.0,
        "roas": 1.88
      }
    ],
    "budget_drain": [
      {
        "campaign_name": "Budget Drain Camp",
        "spend": 190.0,
        "conversions": 10,
        "cpa": 19.0,
        "roas": 0.53
      }
    ]
  }
}
```

---

## 4. Classification Rules & Mathematical Integrity

```
                                    Conversion Volume
                                           ▲
                                           │
                    Volume Driver          │          Scale Ready
           (High Volume / High CPA)        │    (High Volume / Low CPA)
                                           │
         ──────────────────────────────────┼──────────────────────────────────► Cost Efficiency
                                           │                                   (CPA <= Portfolio CPA)
                    Budget Drain           │        Efficiency Niche
         (Low Volume / High CPA or Zero)   │    (Low Volume / Low CPA)
                                           │
```

### Precedence & Decision Rules:
1. **Portfolio CPA Calculation:**
   $$\text{portfolio\_cpa} = \frac{\sum \text{spend}}{\sum \text{conversions}} \quad (\text{if } \sum \text{conversions} > 0 \text{ else None})$$
2. **Median Conversion Calculation:**
   Standard statistical median on sorted conversion counts.
3. **Precedence Rule 1 (Zero Conversions / Undefined CPA):**
   - Campaigns with `conversions == 0` have undefined CPA (`None`).
   - Positive spend with zero conversions represents pure budget drain and is unconditionally assigned to **`budget_drain`**.
   - Zero-spend zero-conversion campaigns have zero output and are deterministically assigned to **`budget_drain`**.
4. **Precedence Rule 2 (Quadrant Classification for Positive Conversions):**
   When `conversions > 0` and `portfolio_cpa` is valid:
   - `conversions >= median` and `cpa <= portfolio_cpa` $\implies$ **`scale_ready`**
   - `conversions >= median` and `cpa > portfolio_cpa` $\implies$ **`volume_driver`**
   - `conversions < median` and `cpa <= portfolio_cpa` $\implies$ **`efficiency_niche`**
   - `conversions < median` and `cpa > portfolio_cpa` $\implies$ **`budget_drain`**
5. **Threshold Ties:**
   - $\text{conversions} = \text{median}$: Treated as high volume ($\ge \text{median}$).
   - $\text{cpa} = \text{portfolio\_cpa}$: Treated as cost-efficient ($\le \text{portfolio\_cpa}$).
6. **Cohort Sorting:**
   - `scale_ready` & `efficiency_niche`: Sorted by `cpa` ascending, tie-breaker `campaign_name`.
   - `volume_driver`: Sorted by `conversions` descending, tie-breaker `campaign_name`.
   - `budget_drain`: Sorted by `spend` descending (wasted spend prioritisation), tie-breaker `campaign_name`.

---

## 5. Test Suite Verification

### 1. Focused Cohort Tests (`analytics/tests/test_segmentation.py`):
```text
pytest analytics/tests/test_segmentation.py -v

analytics/tests/test_segmentation.py::test_classification_all_four_cohorts PASSED [  9%]
analytics/tests/test_segmentation.py::test_median_calculation_odd_and_even_counts PASSED [ 18%]
analytics/tests/test_segmentation.py::test_conversion_count_ties_at_median PASSED [ 27%]
analytics/tests/test_segmentation.py::test_positive_spend_zero_conversions_always_budget_drain PASSED [ 36%]
analytics/tests/test_segmentation.py::test_zero_portfolio_conversions_and_undefined_cpa PASSED [ 45%]
analytics/tests/test_segmentation.py::test_zero_spend_campaigns_and_single_campaign_dataset PASSED [ 54%]
analytics/tests/test_segmentation.py::test_missing_and_null_revenue_no_fabricated_roas PASSED [ 63%]
analytics/tests/test_segmentation.py::test_empty_input_and_missing_required_columns PASSED [ 72%]
analytics/tests/test_segmentation.py::test_deterministic_ordering_and_repeated_calls PASSED [ 81%]
analytics/tests/test_segmentation.py::test_exactly_one_cohort_assignment_per_campaign PASSED [ 90%]
analytics/tests/test_segmentation.py::test_strict_json_serialization_allow_nan_false PASSED [100%]

============================= 11 passed in 0.66s ==============================
```

### 2. Full Regression Test Suite (`pytest`):
```text
collected 141 items

analytics\tests\test_ai.py ..                                            [  1%]
analytics\tests\test_insights.py ..............                          [ 11%]
analytics\tests\test_metrics.py ............                             [ 19%]
analytics\tests\test_preprocessing.py ..............                     [ 29%]
analytics\tests\test_ranking.py ............                             [ 38%]
analytics\tests\test_segmentation.py ...........                         [ 46%]
analytics\tests\test_trends.py .........................                 [ 63%]
backend\tests\test_auth.py ...                                           [ 65%]
backend\tests\test_campaign_service.py ........                          [ 71%]
backend\tests\test_compatibility.py ...                                  [ 73%]
backend\tests\test_results.py ....................                       [ 87%]
backend\tests\test_upload.py .............                               [ 97%]
backend\tests\test_validation.py ....                                    [100%]

======================= 141 passed, 6 warnings in 2.16s =======================
```

---

## 6. Downstream Compatibility & Invariants

1. **Phase 1 KPI Engine (`calculate_kpis`):** Unaltered (12/12 tests passing).
2. **Phase 2.1 Campaign Ranking (`rank_campaigns`):** Unaltered (12/12 tests passing).
3. **Phase 2.2 Time Series & Phase 2.3 Breakdowns (`analyze_trends`):** Unaltered (25/25 tests passing).
4. **Phase 2.4 Deterministic Insights (`generate_insights`):** Unaltered (14/14 tests passing).
5. **Strict JSON Hygiene:** Verified via `json.dumps(result, allow_nan=False)` across all edge cases (zero conversions, single campaigns, empty inputs).
6. **Backend Services & DB:** Untouched. No database migrations or API redesigns introduced.
