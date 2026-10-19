# Market Orbit — Phase 2.4 Implementation Report: Deterministic Evidence-Based Insights

**Document Version:** 1.0  
**Date:** September 19, 2026  
**Track:** Analytics & AI Architecture  
**Lead:** Vishal S Naik (Analytics & AI Track)  
**Collaborators:** Sushanth S (Backend & Database Track), Apeksha C Rao (Frontend Track)  
**Status:** Verification & Implementation Complete  

---

## 1. Executive Summary

Phase 2.4 establishes a deterministic, evidence-based insight-generation layer for Market Orbit in `analytics/insights/generator.py`. This engine translates raw marketing metrics, campaign rankings, chronological trends, and multi-dimensional breakdowns into structured, plain-language business insights without reliance on non-deterministic external LLMs or black-box heuristics.

Every generated insight is backed by verified source metrics, strictly preserving mathematical integrity, preventing hallucinations, and safeguarding downstream JSON persistence.

### Key Deliverables:
1. **Deterministic Insight Engine (`generate_insights`):** Accepts pre-computed `kpis`, `rankings`, and `trends` (or raw `df`) and produces structured, prioritized insight objects.
2. **Multi-Category Coverage:** Identifies observations across:
   - **Data Quality & Limitations:** Flags untracked revenue, partially missing revenue, or insufficient calendar dates.
   - **Campaign Performance:** Detects leading conversion drivers and zero-conversion spend waste.
   - **Cost Efficiency:** Identifies lowest and highest CPA campaigns when conversion data exists.
   - **Revenue Efficiency:** Highlights highest and lowest ROAS performers exclusively when revenue is tracked.
   - **Dimensional Performance:** Identifies top-converting categories and lowest-CPA categories across locations, age groups, customer segments, and devices.
   - **Historical Time Series:** Highlights timeline progression between observed dates and peak conversion dates when $\ge 2$ dates are available.
3. **Structured Evidence Binding:** Every insight includes an `evidence` dictionary containing exact source values from analytics calculations, enabling immediate user verification.
4. **Data Integrity & Zero-Denominator Safety:** Completely eliminates `NaN` and `Infinity` risk; undefinable metrics (e.g. CPA when conversions = 0) return JSON `null` and do not generate false performance claims.
5. **Deduplication & Contradiction Guards:** Prevents duplicate insight signatures and ensures single-campaign datasets never label the same campaign as both top and bottom performer.

---

## 2. Files Changed & Scope Review

| File Path | Action | Description |
| :--- | :---: | :--- |
| [`analytics/insights/generator.py`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/insights/generator.py) | **Created** | Core deterministic insight engine implementing `generate_insights()` with rule-based heuristics across data quality, volume, CPA, ROAS, dimensions, and timeline. |
| [`analytics/insights/__init__.py`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/insights/__init__.py) | **Created** | Package entry point exporting `generate_insights`. |
| [`analytics/ai/__init__.py`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/ai/__init__.py) | **Modified** | Re-exported `generate_insights` alongside `GroqClient` for centralized AI/insight module access. |
| [`analytics/tests/test_insights.py`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/tests/test_insights.py) | **Created** | 14 comprehensive unit tests verifying evidence accuracy, waste detection, cost efficiency, revenue constraints, dimensional comparisons, time-series progression, deterministic ordering, and JSON serialization. |
| [`analytics/tests/test_ai.py`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/tests/test_ai.py) | **Modified** | Added export verification for `generate_insights` from `analytics.ai` while preserving existing placeholder test. |
| [`docs/analytics/PHASE_2_4_DETERMINISTIC_INSIGHTS_REPORT.md`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/docs/analytics/PHASE_2_4_DETERMINISTIC_INSIGHTS_REPORT.md) | **Created** | Phase 2.4 implementation and verification report. |

**Scope Enforcement:** The Phase 1 KPI engine ([`metrics.py`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/kpi/metrics.py)), Phase 2.1 ranking engine ([`ranking.py`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/performance/ranking.py)), Phase 2.2/2.3 trend engine ([`customer_trends.py`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/trends/customer_trends.py)), backend routes, database models, and migrations were left untouched.

---

## 3. Previous vs. Implemented Behavior

| Capability | Previous Implementation | Implemented Phase 2.4 Behavior |
| :--- | :--- | :--- |
| **Insight Generation** | Static mock list in `groq_client.py` with hardcoded strings. | Fully deterministic, mathematical insight generator grounded in validated analytics data. |
| **Evidence Binding** | None; mock recommendations had no evidence payload. | Every insight includes an `evidence` object with exact numerical inputs from rankings/trends/KPIs. |
| **Revenue Safeguards** | None; hardcoded recommendations mentioned ROAS regardless of data presence. | ROAS/ROI insights are strictly suppressed if revenue is untracked; an explicit `data_quality` insight is emitted. |
| **Waste Detection** | Generic text ("Pause underperforming creatives"). | Explicit detection of positive-spend campaigns with zero conversions, specifying wasted spend amount. |
| **Dimensional Insights** | None. | Cross-category comparisons within `location`, `age_group`, `customer_segment`, and `device` for conversion leaders and lowest CPA. |
| **Timeline Progression** | None. | Verifiable progression between first and last observed dates and peak conversion day identification. |
| **Contradiction Guards** | None. | Single-campaign datasets are prevented from appearing as both top and bottom performer. |

---

## 4. Insight Output Schema

The `generate_insights()` function returns a list of dictionaries with the following contract:

```json
[
  {
    "id": "insight-001",
    "type": "data_quality",
    "title": "Revenue Tracking Incomplete",
    "description": "Revenue data is untracked across campaigns, preventing portfolio-level ROAS and ROI calculations.",
    "metric": "revenue",
    "evidence": {
      "total_revenue": null,
      "total_spend": 500.0,
      "campaigns_evaluated": 2
    }
  },
  {
    "id": "insight-002",
    "type": "campaign_performance",
    "title": "Top Conversion Driver: Summer Launch",
    "description": "'Summer Launch' generated the highest conversion volume with 40 conversions from $400.00 spend.",
    "metric": "conversions",
    "evidence": {
      "campaign_name": "Summer Launch",
      "conversions": 40,
      "spend": 400.0
    }
  },
  {
    "id": "insight-003",
    "type": "cost_efficiency",
    "title": "Lowest Cost per Acquisition: Summer Launch",
    "description": "'Summer Launch' achieved the most cost-effective acquisition at $10.00 per conversion (40 conversions).",
    "metric": "cpa",
    "evidence": {
      "campaign_name": "Summer Launch",
      "cpa": 10.0,
      "spend": 400.0,
      "conversions": 40
    }
  },
  {
    "id": "insight-004",
    "type": "dimensional",
    "title": "Leading Location by Conversions: US",
    "description": "Within location, 'US' led with 30 conversions ($300.00 spend).",
    "metric": "conversions",
    "evidence": {
      "dimension": "location",
      "category": "US",
      "conversions": 30,
      "spend": 300.0
    }
  },
  {
    "id": "insight-005",
    "type": "time_series",
    "title": "Timeline Progression: 2026-09-01 to 2026-09-10",
    "description": "Across 3 observed dates between 2026-09-01 and 2026-09-10, daily spend was $100.00 initially and $200.00 on the final date, with conversions shifting from 5 to 15.",
    "metric": "conversions",
    "evidence": {
      "start_date": "2026-09-01",
      "start_spend": 100.0,
      "start_conversions": 5,
      "end_date": "2026-09-10",
      "end_spend": 200.0,
      "end_conversions": 15,
      "observed_dates_count": 3
    }
  }
]
```

---

## 5. Insight Generation Rules & Evidence Binding

### Category 1: Data Quality & Limitations (`type: "data_quality"`)
1. **Untracked Revenue:**
   - *Condition:* Total campaigns $> 0$ and `total_revenue is None`.
   - *Evidence:* `{"total_revenue": None, "total_spend": spend, "campaigns_evaluated": n}`.
2. **Partial Revenue Tracking:**
   - *Condition:* Total campaigns $> 0$, `total_revenue is not None`, but `campaigns_with_roas < total_campaigns`.
   - *Evidence:* `{"tracked_campaigns_count": count, "total_campaigns": n, "observed_revenue": revenue}`.
3. **Insufficient Date Coverage:**
   - *Condition:* `time_series.status == "insufficient_data"` with total campaigns $> 0$.
   - *Evidence:* `{"distinct_dates_count": count, "required_minimum_dates": 2}`.

### Category 2: Campaign Performance (`type: "campaign_performance"`)
1. **Top Conversion Driver:**
   - *Condition:* Top campaign from `rankings["by_conversions"]["top"]` has `conversions > 0`.
   - *Evidence:* `{"campaign_name": name, "conversions": count, "spend": spend}`.
2. **Zero-Conversion Waste:**
   - *Condition:* Evaluated campaigns with `spend > 0.0` and `conversions == 0`. Ranked deterministically by spend descending.
   - *Evidence:* `{"campaign_name": name, "spend": spend, "conversions": 0}`.

### Category 3: Cost Efficiency (`type: "cost_efficiency"`)
1. **Lowest CPA:**
   - *Condition:* Campaign with lowest valid CPA (conversions $> 0$).
   - *Evidence:* `{"campaign_name": name, "cpa": cpa, "spend": spend, "conversions": conversions}`.
2. **Highest CPA Inefficiency:**
   - *Condition:* Campaign with highest valid CPA, distinct from lowest CPA campaign.
   - *Evidence:* `{"campaign_name": name, "cpa": cpa, "spend": spend, "conversions": conversions}`.

### Category 4: Revenue Efficiency (`type: "revenue_efficiency"`)
1. **Highest ROAS Performer:**
   - *Condition:* Campaign with highest valid ROAS from `rankings["by_roas"]["top"]` (spend $> 0$).
   - *Evidence:* `{"campaign_name": name, "roas": roas, "revenue": revenue, "spend": spend}`.
2. **Lowest ROAS Performer:**
   - *Condition:* Campaign with lowest valid ROAS, distinct from top ROAS campaign.
   - *Evidence:* `{"campaign_name": name, "roas": roas, "revenue": revenue, "spend": spend}`.

### Category 5: Dimensional Performance (`type: "dimensional"`)
1. **Leading Category by Volume:**
   - *Condition:* Dimension has $\ge 2$ categories; top category by conversions has `conversions > 0`.
   - *Evidence:* `{"dimension": dim, "category": cat, "conversions": conv, "spend": spend}`.
2. **Most Cost-Effective Category (Lowest CPA):**
   - *Condition:* Dimension has $\ge 2$ categories with valid CPA. Lowest CPA category is distinct from highest CPA category.
   - *Evidence:* `{"dimension": dim, "category": cat, "cpa": cpa, "spend": spend, "conversions": conv}`.

### Category 6: Historical Time Series (`type: "time_series"`)
1. **Timeline Progression:**
   - *Condition:* `time_series.has_time_series == True` and `len(timeline) >= 2`.
   - *Evidence:* First date metrics vs last date metrics and observed date count.
2. **Peak Conversion Date:**
   - *Condition:* Highest daily conversion volume in timeline ($conversions > 0$).
   - *Evidence:* `{"date": date, "conversions": conv, "spend": spend}`.

---

## 6. Test Suite Verification

### 1. Focused Insight Unit Tests (`analytics/tests/test_insights.py`):
```text
pytest analytics/tests/test_insights.py -v

analytics/tests/test_insights.py::test_campaign_performance_insights_valid_evidence PASSED [  7%]
analytics/tests/test_insights.py::test_zero_conversion_waste_detection PASSED             [ 14%]
analytics/tests/test_insights.py::test_cost_efficiency_lowest_and_highest_cpa PASSED      [ 21%]
analytics/tests/test_insights.py::test_roas_revenue_efficiency_complete_revenue PASSED    [ 28%]
analytics/tests/test_insights.py::test_untracked_and_partially_missing_revenue PASSED     [ 35%]
analytics/tests/test_insights.py::test_historical_time_series_observations_valid_dates PASSED [ 42%]
analytics/tests/test_insights.py::test_insufficient_time_series_coverage PASSED          [ 50%]
analytics/tests/test_insights.py::test_dimensional_insights_multiple_categories PASSED    [ 57%]
analytics/tests/test_insights.py::test_missing_and_single_category_dimensions PASSED     [ 64%]
analytics/tests/test_insights.py::test_empty_datasets_and_undefined_metrics PASSED        [ 71%]
analytics/tests/test_insights.py::test_deterministic_ordering_and_output_stability PASSED [ 78%]
analytics/tests/test_insights.py::test_duplicate_and_contradiction_prevention PASSED     [ 85%]
analytics/tests/test_insights.py::test_strict_json_serialization_allow_nan_false PASSED  [ 92%]
analytics/tests/test_insights.py::test_backward_compatibility_with_cleaned_analytics_pipeline PASSED [100%]

============================= 14 passed in 0.99s ==============================
```

### 2. Full Regression Suite Across Repository (`pytest`):
```text
collected 130 items

analytics\tests\test_ai.py ..                                            [  1%]
analytics\tests\test_insights.py ..............                          [ 12%]
analytics\tests\test_metrics.py ............                             [ 21%]
analytics\tests\test_preprocessing.py ..............                     [ 32%]
analytics\tests\test_ranking.py ............                             [ 41%]
analytics\tests\test_trends.py .........................                 [ 60%]
backend\tests\test_auth.py ...                                           [ 63%]
backend\tests\test_campaign_service.py ........                          [ 69%]
backend\tests\test_compatibility.py ...                                  [ 71%]
backend\tests\test_results.py ....................                       [ 86%]
backend\tests\test_upload.py .............                               [ 96%]
backend\tests\test_validation.py ....                                    [100%]

======================= 130 passed, 6 warnings in 2.28s =======================
```

---

## 7. Downstream Compatibility & Invariants

1. **Phase 1 KPI Engine (`calculate_kpis`):** Unaltered (12/12 tests passing).
2. **Phase 2.1 Campaign Ranking (`rank_campaigns`):** Unaltered (12/12 tests passing).
3. **Phase 2.2 Time Series & Phase 2.3 Breakdowns (`analyze_trends`):** Unaltered (25/25 tests passing).
4. **Backend `AnalysisService` Pipeline:** Unbroken. `GroqClient` mock recommendations continue to satisfy legacy API contracts without regression.
5. **Strict JSON Hygiene:** Verified via `json.dumps(..., allow_nan=False)` across all edge cases (zero spend, null revenue, zero conversions, missing dates).
