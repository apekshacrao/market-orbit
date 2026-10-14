# Market Orbit — Phase 2.1 Implementation Report: Advanced Campaign Comparison and Ranking

**Document Version:** 1.0  
**Date:** September 19, 2026  
**Track:** Analytics & AI Architecture  
**Lead:** Vishal S Naik (Analytics & AI Track)  
**Collaborators:** Sushanth S (Backend & Database Track), Apeksha C Rao (Frontend Track)  
**Status:** Verification & Implementation Complete  

---

## 1. Executive Summary

Phase 2.1 delivers multi-metric campaign comparison and ranking for the Market Orbit analytics engine while strictly preserving the Phase 1 KPI contract and downstream API compatibility.

### Key Deliverables:
1. **Multi-Metric Campaign Aggregation (`aggregate_campaigns`):** Groups dataset records by `campaign_name` and calculates complete performance metrics: spend, conversions, clicks, impressions, revenue, CPA, CPC, CTR, conversion rate, ROAS, and ROI.
2. **Multi-Metric Ranking Engine (`rank_campaigns`):** Provides structured ranking groups:
   - `by_roas`: Top and bottom campaigns by ROAS (strictly excluding campaigns with untracked/unavailable revenue or zero spend).
   - `by_cpa`: Top efficiency (lowest CPA with conversions $> 0$) and least efficient campaigns with valid CPA.
   - `by_conversions`: Campaigns ranked by conversion volume (highest to lowest).
   - `summary`: Evaluated campaign counts and valid metric distributions.
3. **Missing Revenue & Zero Denominator Protection:** Eliminates the legacy bug where `revenue.sum()` converted `NaN` to `0.0`. Explicit `0.0` revenue is kept distinguishable from untracked revenue (`None`). Zero denominators for CPA, CPC, CTR, conversion rate, ROAS, and ROI return `None` rather than dividing by zero or raising `ZeroDivisionError`/`inf`.
4. **Deterministic Tie-Breaking:** All rankings employ alphabetical tie-breaking on `campaign_name` ascending to produce stable, reproducible results.
5. **Backward Compatibility:** Preserves root-level `top` and `bottom` outputs, falling back to CPA/conversions ranking when all revenue is untracked to maintain full compatibility with `AnalysisService._contract_response`.

---

## 2. Files Changed & Scope Review

| File Path | Action | Description |
| :--- | :---: | :--- |
| [`analytics/performance/ranking.py`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/performance/ranking.py) | **Modified** | Implemented `_aggregate_campaign()`, `aggregate_campaigns()`, and multi-metric `rank_campaigns()`. |
| [`analytics/tests/test_ranking.py`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/tests/test_ranking.py) | **Modified** | Replaced placeholder test with 12 unit tests verifying aggregation, all ranking groups, edge cases, and compatibility. |

**Scope Enforcement:** No other files in the workspace (KPI engine, cleaner, validators, backend, database, schemas, routes, or frontend) were modified.

---

## 3. Previous vs. Implemented Behavior

| Capability | Previous Implementation | Implemented Phase 2.1 Behavior |
| :--- | :--- | :--- |
| **Ranking Metric** | Single metric: ROAS only. | Multi-metric: `by_roas`, `by_cpa`, `by_conversions`. |
| **Revenue Aggregation** | Used pandas `.agg({"revenue": "sum"})`, turning all-null revenue into `0.0`. | Preserves `None` when revenue is entirely untracked or partially missing. |
| **Explicit Zero Revenue** | Conflated with missing revenue (both evaluated as `0.0`). | Explicit `0.0` produces `roas: 0.0` and `roi: -100.0%`, keeping it distinguishable from untracked `None`. |
| **ROAS Filtering** | Included untracked campaigns with fabricated `0.0` ROAS. | Strictly excludes campaigns with unavailable ROAS from `by_roas`. |
| **Zero Conversions** | Handled ambiguously or caused zero-cost confusion. | Undefined CPA returns `None` and is excluded from `by_cpa`. |
| **Zero Clicks** | Not handled; potential division by zero. | Returns `None` for CPC and conversion rate. |
| **Zero Impressions** | Not handled. | Returns `None` for CTR (`0.0` when clicks = 0 and impressions > 0). |
| **Zero Spend** | Handled with inline ternary to `0.0`. | Returns `None` for ROAS and ROI to prevent falsified performance. |
| **Tie-Breaking** | Unstable (relied on grouping sequence). | Deterministic ordering using `campaign_name` ascending. |
| **Caller Compatibility** | Returned `{"top": [...], "bottom": [...]}`. | Retains `top` and `bottom` keys while appending `by_roas`, `by_cpa`, `by_conversions`, and `summary`. |

---

## 4. Multi-Metric Ranking Output Schema

### Response Structure Specification:
```json
{
  "top": [ ... ],
  "bottom": [ ... ],
  "by_roas": {
    "top": [ ... ],
    "bottom": [ ... ]
  },
  "by_cpa": {
    "top": [ ... ],
    "bottom": [ ... ]
  },
  "by_conversions": {
    "top": [ ... ],
    "bottom": [ ... ]
  },
  "summary": {
    "total_campaigns_evaluated": 2,
    "total_campaigns": 2,
    "campaigns_with_roas": 2,
    "campaigns_with_cpa": 2
  }
}
```

### Representative Example:
```json
{
  "top": [
    {
      "campaign_name": "Summer Search Ads",
      "spend": 1200.0,
      "conversions": 80,
      "clicks": 1600,
      "impressions": 32000,
      "revenue": 4800.0,
      "cpa": 15.0,
      "cpc": 0.75,
      "ctr": 5.0,
      "conversion_rate": 5.0,
      "roas": 4.0,
      "roi": 300.0
    }
  ],
  "bottom": [
    {
      "campaign_name": "Retargeting Display",
      "spend": 800.0,
      "conversions": 20,
      "clicks": 400,
      "impressions": 10000,
      "revenue": 1000.0,
      "cpa": 40.0,
      "cpc": 2.0,
      "ctr": 4.0,
      "conversion_rate": 5.0,
      "roas": 1.25,
      "roi": 25.0
    }
  ],
  "by_roas": {
    "top": [
      {
        "campaign_name": "Summer Search Ads",
        "spend": 1200.0,
        "conversions": 80,
        "clicks": 1600,
        "impressions": 32000,
        "revenue": 4800.0,
        "cpa": 15.0,
        "cpc": 0.75,
        "ctr": 5.0,
        "conversion_rate": 5.0,
        "roas": 4.0,
        "roi": 300.0
      }
    ],
    "bottom": [
      {
        "campaign_name": "Retargeting Display",
        "spend": 800.0,
        "conversions": 20,
        "clicks": 400,
        "impressions": 10000,
        "revenue": 1000.0,
        "cpa": 40.0,
        "cpc": 2.0,
        "ctr": 4.0,
        "conversion_rate": 5.0,
        "roas": 1.25,
        "roi": 25.0
      }
    ]
  },
  "by_cpa": {
    "top": [
      {
        "campaign_name": "Summer Search Ads",
        "spend": 1200.0,
        "conversions": 80,
        "clicks": 1600,
        "impressions": 32000,
        "revenue": 4800.0,
        "cpa": 15.0,
        "cpc": 0.75,
        "ctr": 5.0,
        "conversion_rate": 5.0,
        "roas": 4.0,
        "roi": 300.0
      }
    ],
    "bottom": [
      {
        "campaign_name": "Retargeting Display",
        "spend": 800.0,
        "conversions": 20,
        "clicks": 400,
        "impressions": 10000,
        "revenue": 1000.0,
        "cpa": 40.0,
        "cpc": 2.0,
        "ctr": 4.0,
        "conversion_rate": 5.0,
        "roas": 1.25,
        "roi": 25.0
      }
    ]
  },
  "by_conversions": {
    "top": [
      {
        "campaign_name": "Summer Search Ads",
        "spend": 1200.0,
        "conversions": 80,
        "clicks": 1600,
        "impressions": 32000,
        "revenue": 4800.0,
        "cpa": 15.0,
        "cpc": 0.75,
        "ctr": 5.0,
        "conversion_rate": 5.0,
        "roas": 4.0,
        "roi": 300.0
      }
    ],
    "bottom": [
      {
        "campaign_name": "Retargeting Display",
        "spend": 800.0,
        "conversions": 20,
        "clicks": 400,
        "impressions": 10000,
        "revenue": 1000.0,
        "cpa": 40.0,
        "cpc": 2.0,
        "ctr": 4.0,
        "conversion_rate": 5.0,
        "roas": 1.25,
        "roi": 25.0
      }
    ]
  },
  "summary": {
    "total_campaigns_evaluated": 2,
    "total_campaigns": 2,
    "campaigns_with_roas": 2,
    "campaigns_with_cpa": 2
  }
}
```

---

## 5. Revenue & Zero-Denominator Rules

1. **All-Null Revenue:**
   - If `revenue` is missing or `NaN` across all rows of a campaign, aggregated `revenue` is `None`.
   - `roas` and `roi` are `None`.
   - The campaign is excluded from `by_roas`.
2. **Explicit Zero Revenue:**
   - If recorded revenue is explicitly `0.0` (with `spend > 0.0`), `revenue` is `0.0`, `roas` is `0.0`, and `roi` is `-100.0`.
   - Remains distinct from missing revenue and is included in `by_roas`.
3. **Partially Missing Revenue (Campaign Level):**
   - Follows the existing backend contract established in `AnalysisService._contract_response` (`complete_revenue`): if any row for a campaign has missing revenue, the campaign's aggregated revenue is treated as incomplete (`None`).
   - `roas` and `roi` are set to `None`, avoiding synthetic under-performance calculations.
4. **Zero Conversions ($conversions = 0$):**
   - $\text{CPA}$ returns `None` (preventing division-by-zero or misleading $0 CPA).
   - Excluded from `by_cpa` efficiency rankings.
5. **Zero Clicks ($clicks = 0$):**
   - $\text{CPC}$ and $\text{Conversion Rate}$ return `None`.
6. **Zero Impressions ($impressions = 0$):**
   - $\text{CTR}$ returns `None` (returns `0.0` when clicks = 0 and impressions > 0).
7. **Zero Spend ($spend = 0.0$):**
   - $\text{ROAS}$ and $\text{ROI}$ return `None` (preventing `inf`/`NaN`). Excluded from `by_roas`.

---

## 6. Test Suite Verification

### Focused Ranking Unit Tests (`analytics/tests/test_ranking.py`):
```text
pytest analytics/tests/test_ranking.py -v

analytics/tests/test_ranking.py::test_correct_campaign_aggregation PASSED         [  8%]
analytics/tests/test_ranking.py::test_roas_ranking_and_exclusion_of_unavailable_roas PASSED [ 16%]
analytics/tests/test_ranking.py::test_cpa_ranking_and_exclusion_of_undefined_cpa PASSED [ 25%]
analytics/tests/test_ranking.py::test_conversion_volume_ranking PASSED           [ 33%]
analytics/tests/test_ranking.py::test_zero_conversions_and_zero_clicks PASSED   [ 41%]
analytics/tests/test_ranking.py::test_zero_spend PASSED                          [ 50%]
analytics/tests/test_ranking.py::test_missing_revenue_versus_explicitly_zero_revenue PASSED [ 58%]
analytics/tests/test_ranking.py::test_all_null_revenue_aggregation PASSED        [ 66%]
analytics/tests/test_ranking.py::test_partially_missing_revenue_aggregation PASSED [ 75%]
analytics/tests/test_ranking.py::test_deterministic_ordering_on_metric_ties PASSED [ 83%]
analytics/tests/test_ranking.py::test_empty_input_and_missing_optional_columns PASSED [ 91%]
analytics/tests/test_ranking.py::test_backward_compatibility_top_and_bottom PASSED [100%]

============================= 12 passed in 1.11s ==============================
```

### Full Repository Regression Test Suite (`pytest`):
```text
collected 91 items

analytics\tests\test_ai.py .                                             [  1%]
analytics\tests\test_metrics.py ............                             [ 14%]
analytics\tests\test_preprocessing.py ..............                     [ 29%]
analytics\tests\test_ranking.py ............                             [ 42%]
analytics\tests\test_trends.py .                                         [ 43%]
backend\tests\test_auth.py ...                                           [ 47%]
backend\tests\test_campaign_service.py ........                          [ 56%]
backend\tests\test_compatibility.py ...                                  [ 59%]
backend\tests\test_results.py ....................                       [ 81%]
backend\tests\test_upload.py .............                               [ 95%]
backend\tests\test_validation.py ....                                    [100%]

======================= 91 passed, 6 warnings in 2.19s ========================
```

---

## 7. Unresolved Design Decisions & Future Roadmap

1. **Composite Relative Performance Index (RPI):**
   - In accordance with the prompt guidelines, no arbitrary weighting or composite scoring model was introduced.
   - *Recommendation for Phase 3:* Introduce a normalized, user-configurable weighted composite index combining ROAS percentile rank, CPA efficiency rank, and conversion volume rank.
2. **Partially Missing Revenue Policy:**
   - Currently treats partially missing revenue as incomplete (`None`). If future requirements require partial sum calculation, a separate configuration flag (e.g., `allow_partial_revenue=True`) should be explicitly defined in the data contract.
