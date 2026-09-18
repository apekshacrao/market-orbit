# Implementation Report: Phase 1 — Step 1.4
## KPI Engine & Derived Metrics Implementation

**Document Version:** 1.0  
**Date:** September 17, 2026  
**Track:** Analytics & AI Architecture  
**Lead:** Vishal S Naik (Analytics & AI Track)  
**Status:** Successfully Implemented & Verified (27/27 Unit Tests Passing)  

---

## 1. Files Modified

In strict accordance with the scope rules, only the following two files were modified:

1. [analytics/kpi/metrics.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/kpi/metrics.py):
   - Refactored `calculate_kpis(df: pd.DataFrame)` to conform to the confirmed data contract.
   - Added dynamic revenue availability check (`has_revenue`).
   - Guarded all metric formulas against zero division.
   - Scaled `conversion_rate` and `ctr` to percentages ($\times 100$).
   - Added Return on Investment (`roi`) formula.
   - Provided canonical keys alongside backward-compatible aliases.
2. [analytics/tests/test_metrics.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/tests/test_metrics.py):
   - Replaced placeholder stub with 12 comprehensive unit test scenarios.

*(Zero backend, frontend, database, Groq AI, ranking, or API files were modified).*

---

## 2. Implementation Summary

- **Signature Preservation:** Maintained `calculate_kpis(df: pd.DataFrame) -> Dict[str, Any]` without breaking changes.
- **Dynamic Revenue Availability Detection:**
  - Revenue is treated as available **only** when `"revenue"` exists in `df.columns` and contains at least one non-null value (`df["revenue"].notna().any()`).
  - Missing or entirely-null revenue sets `total_revenue = None`, `roas = None`, and `roi = None` (never converting missing revenue into `0.0` or fabricating fake ROAS).
  - Explicit `0.0` revenue is treated as valid revenue, calculating `roas = 0.0` and `roi = -100.0%`.
- **Zero-Denominator Protections:**
  - `conversions <= 0` $\rightarrow$ `cpa = 0.0` (zero division guarded).
  - `clicks <= 0` $\rightarrow$ `cpc = 0.0` and `conversion_rate = 0.0` (zero division guarded).
  - `impressions <= 0` $\rightarrow$ `ctr = 0.0` (zero division guarded).
  - `spend <= 0` $\rightarrow$ `roas = 0.0` and `roi = 0.0` (zero division guarded when revenue is available).
- **Rounding and Typing:**
  - Monetary values, ratios, and percentages are rounded to 2 decimal places.
  - All return values are cast to standard Python primitives (`int`, `float`, or `None`), eliminating all `NaN` and `Infinity` occurrences.
- **Dual-Key Compatibility:**
  - Outputs canonical keys: `total_spend`, `total_revenue`, `cpa`, `cpc`, `conversion_rate`, `ctr`, `roas`, `roi`.
  - Outputs backward-compatible aliases: `avg_cpa = cpa`, `avg_cpc = cpc`, `avg_conversion_rate = conversion_rate`, `overall_roas = roas`.

---

## 3. KPI Formulas Implemented

$$\text{CPA} = \frac{\text{total\_spend}}{\text{total\_conversions}} \quad (\text{if conversions} > 0, \text{else } 0.0)$$

$$\text{CPC} = \frac{\text{total\_spend}}{\text{total\_clicks}} \quad (\text{if clicks} > 0, \text{else } 0.0)$$

$$\text{Conversion Rate} = \left(\frac{\text{total\_conversions}}{\text{total\_clicks}}\right) \times 100 \quad (\text{if clicks} > 0, \text{else } 0.0)$$

$$\text{CTR} = \left(\frac{\text{total\_clicks}}{\text{total\_impressions}}\right) \times 100 \quad (\text{if impressions} > 0, \text{else } 0.0)$$

$$\text{ROAS} = \frac{\text{total\_revenue}}{\text{total\_spend}} \quad (\text{None if revenue missing; } 0.0 \text{ if spend} \le 0)$$

$$\text{ROI} = \left(\frac{\text{total\_revenue} - \text{total\_spend}}{\text{total\_spend}}\right) \times 100 \quad (\text{None if revenue missing; } 0.0 \text{ if spend} \le 0)$$

---

## 4. Test Cases Added ([`analytics/tests/test_metrics.py`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/tests/test_metrics.py))

| # | Test Function | Purpose / Validation Logic |
| :---: | :--- | :--- |
| 1 | `test_kpis_complete_dataset` | Verifies all aggregates and KPIs on a benchmark 2-campaign dataset. |
| 2 | `test_kpis_missing_revenue` | Tests both missing column and all-`NaN` column; verifies `total_revenue`, `roas`, and `roi` return `None`. |
| 3 | `test_kpis_explicit_zero_revenue` | Verifies `0.0` revenue yields `roas = 0.0` and `roi = -100.0%`. |
| 4 | `test_cpa_zero_conversions` | Verifies `cpa = 0.0` without `ZeroDivisionError` when conversions are zero. |
| 5 | `test_cpc_zero_clicks` | Verifies `cpc = 0.0` without `ZeroDivisionError` when clicks are zero. |
| 6 | `test_conversion_rate_percentage` | Verifies percentage scaling ($25 / 500 \times 100 = 5.0\%$, not $0.05$). |
| 7 | `test_conversion_rate_zero_clicks` | Verifies `conversion_rate = 0.0` without `ZeroDivisionError` when clicks are zero. |
| 8 | `test_ctr_percentage` | Verifies percentage scaling ($150 / 10000 \times 100 = 1.5\%$, not $0.015$). |
| 9 | `test_ctr_zero_impressions` | Verifies `ctr = 0.0` without `ZeroDivisionError` when impressions are zero. |
| 10 | `test_roi_positive_and_negative` | Verifies positive ROI ($+150.0\%$) and negative ROI ($-60.0\%$). |
| 11 | `test_backward_compatible_aliases` | Verifies exact equality between canonical keys and aliases (`roas == overall_roas`, etc.). |
| 12 | `test_empty_dataframe` | Verifies empty DataFrame returns structured zeroed and `None` metrics without exceptions. |

---

## 5. Test Results

### 5.1 KPI Metrics Suite
Executed: `python -m pytest analytics/tests/test_metrics.py -v`
```
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-9.1.1, pluggy-1.6.0
collected 12 items

analytics/tests/test_metrics.py::test_kpis_complete_dataset PASSED       [  8%]
analytics/tests/test_metrics.py::test_kpis_missing_revenue PASSED        [ 16%]
analytics/tests/test_metrics.py::test_kpis_explicit_zero_revenue PASSED  [ 25%]
analytics/tests/test_metrics.py::test_cpa_zero_conversions PASSED        [ 33%]
analytics/tests/test_metrics.py::test_cpc_zero_clicks PASSED             [ 41%]
analytics/tests/test_metrics.py::test_conversion_rate_percentage PASSED  [ 50%]
analytics/tests/test_metrics.py::test_conversion_rate_zero_clicks PASSED [ 58%]
analytics/tests/test_metrics.py::test_ctr_percentage PASSED              [ 66%]
analytics/tests/test_metrics.py::test_ctr_zero_impressions PASSED        [ 75%]
analytics/tests/test_metrics.py::test_roi_positive_and_negative PASSED   [ 83%]
analytics/tests/test_metrics.py::test_backward_compatible_aliases PASSED [ 91%]
analytics/tests/test_metrics.py::test_empty_dataframe PASSED             [100%]

============================= 12 passed in 0.55s ==============================
```

### 5.2 Complete Analytics Test Suite
Executed: `python -m pytest analytics/tests -v`
```
============================= 27 passed in 0.69s ==============================
```
- **Total Tests Executed:** 27
- **Total Passed:** **27**
- **Total Failed:** **0**

---

## 6. Failures or Unresolved Issues

- **None.** All 27 tests across schemas, preprocessing, and the KPI calculation engine passed with 100% success.

---

## 7. Confirmation of Scope Boundaries

- **Backend files modified:** **0**
- **Frontend files modified:** **0**
- **Database schemas modified:** **0**
- **Groq AI / Ranking modules modified:** **0**
