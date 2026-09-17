# KPI Engine & Derived Metrics Plan: Phase 1 — Step 1.4

**Document Version:** 1.0  
**Date:** September 17, 2026  
**Track:** Analytics & AI Architecture  
**Lead:** Vishal S Naik (Analytics & AI Track)  
**Status:** Inspection & Design Complete — Awaiting Approval  

---

## SECTION 1 — EXISTING KPI IMPLEMENTATION

The current KPI calculation logic is defined in [analytics/kpi/metrics.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/kpi/metrics.py):

```python
def calculate_kpis(df: pd.DataFrame) -> Dict[str, Any]:
    total_spend = df["spend"].sum() if "spend" in df else 0.0
    total_revenue = df["revenue"].sum() if "revenue" in df else 0.0
    total_clicks = df["clicks"].sum() if "clicks" in df else 0
    total_impressions = df["impressions"].sum() if "impressions" in df else 0
    total_conversions = df["conversions"].sum() if "conversions" in df else 0

    return {
        "total_spend": float(total_spend),
        "total_revenue": float(total_revenue),
        "overall_roas": float(total_revenue / total_spend) if total_spend > 0 else 0.0,
        "ctr": float(total_clicks / total_impressions) if total_impressions > 0 else 0.0,
        "avg_cpc": float(total_spend / total_clicks) if total_clicks > 0 else 0.0,
        "avg_cpa": float(total_spend / total_conversions) if total_conversions > 0 else 0.0,
        "conversion_rate": float(total_conversions / total_clicks) if total_clicks > 0 else 0.0,
    }
```

- **Module Entrypoint:** [analytics/kpi/__init__.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/kpi/__init__.py) exports `calculate_kpis`.
- **Test Suite Status:** [analytics/tests/test_metrics.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/tests/test_metrics.py) contains a placeholder stub (`assert True`).

---

## SECTION 2 — CONTRACT COMPLIANCE

Comparing current code against the confirmed KPI definitions:

| Metric | Confirmed Contract Formula | Existing Code Implementation | Compliance Status |
| :--- | :--- | :--- | :---: |
| **CPA** | $\frac{\text{Total Spend}}{\text{Total Conversions}}$ (Conversions as leads; zero-guard) | `total_spend / total_conversions if total_conversions > 0 else 0.0` | **COMPLIANT** (Key named `avg_cpa`) |
| **Conversion Rate** | $\frac{\text{Total Conversions}}{\text{Total Clicks}} \times 100$ (Percentage) | `total_conversions / total_clicks` (Decimal fraction) | **NON-COMPLIANT** (Missing $\times 100$ scaling) |
| **CTR** | $\frac{\text{Total Clicks}}{\text{Total Impressions}} \times 100$ (Percentage) | `total_clicks / total_impressions` (Decimal fraction) | **NON-COMPLIANT** (Missing $\times 100$ scaling) |
| **CPC** | $\frac{\text{Total Spend}}{\text{Total Clicks}}$ (Zero-guard) | `total_spend / total_clicks if total_clicks > 0 else 0.0` | **COMPLIANT** (Key named `avg_cpc`) |
| **ROAS** | $\frac{\text{Revenue}}{\text{Spend}}$ (**Must return `None` if revenue is missing**) | `total_revenue / total_spend if total_spend > 0 else 0.0` | **CRITICAL VIOLATION** (Fabricates `0.0` when revenue is missing) |
| **ROI** | $\frac{\text{Revenue} - \text{Spend}}{\text{Spend}} \times 100$ (**Must return `None` if revenue is missing**) | **Not implemented** | **NON-COMPLIANT** (Completely missing) |

---

## SECTION 3 — ISSUES AND RISKS

1. **Fabricated Revenue and ROAS Values:**
   - In Pandas, calling `df["revenue"].sum()` on all-`NaN` series evaluates to `0.0`.
   - Consequently, when revenue is untracked, existing code sets `total_revenue = 0.0` and `overall_roas = 0.0`.
   - **Contract Violation:** Untracked revenue datasets must return `total_revenue: None`, `overall_roas: None`, and `roi: None`.
2. **Missing ROI Formula:**
   - Return on Investment (ROI) is defined in the project PDF, README, and Step 1.2 Data Contract, but completely absent from [analytics/kpi/metrics.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/kpi/metrics.py).
3. **Percentage Scaling vs. Decimal Fraction Mismatch:**
   - `conversion_rate` and `ctr` are currently returned as decimal fractions (e.g., `0.045` and `0.02`).
   - The contract specifies percentage scaling ($\times 100$) (e.g., `4.5` and `2.0`).
4. **Key Naming Inconsistencies Across Stack:**
   - Analytics output: `avg_cpa`, `avg_cpc`, `overall_roas`, `conversion_rate`, `ctr`.
   - Contract names: `cpa`, `cpc`, `roas`, `conversion_rate`, `ctr`, `roi`.
   - Backend [KpiResponse](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/schemas/result.py#L4-L9): `total_spend`, `total_revenue`, `overall_roas`, `avg_conversion_rate`, `avg_cpa`.
   - Frontend [analysis.js](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/frontend/src/types/analysis.js): `totalSpend`, `totalRevenue`, `overallRoas`, `avgConversionRate`, `avgCpa`.
   - *Mitigation:* Analytics will return canonical contract keys while providing backward-compatible aliases.
5. **Backend Schema Validation Crash Risk:**
   - In `backend/app/schemas/result.py`, `total_revenue` and `overall_roas` are typed as mandatory `float`. If Analytics returns `None` for missing revenue, backend Pydantic validation will fail unless coordinated with Sushanth (Section 7).

---

## SECTION 4 — PROPOSED KPI DESIGN

### Function Signature
```python
def calculate_kpis(df: pd.DataFrame) -> Dict[str, Any]:
```

### 1. Revenue Availability Determination
```python
# Revenue is considered available only if column exists and contains non-null data
has_revenue = "revenue" in df.columns and df["revenue"].notna().any()
```

### 2. Metric Computation & Guard Logic

| Metric | Condition | Output Value | Guard Condition |
| :--- | :--- | :--- | :--- |
| `total_spend` | Always | `round(float(df["spend"].sum()), 2)` | Default to `0.0` if empty |
| `total_conversions` | Always | `int(df["conversions"].sum())` | Default to `0` if empty |
| `total_clicks` | Always | `int(df["clicks"].sum())` | Default to `0` if empty |
| `total_impressions`| Always | `int(df["impressions"].sum())` | Default to `0` if empty |
| `total_revenue` | `if has_revenue` else `None` | `round(float(df["revenue"].dropna().sum()), 2)` | `None` when untracked; `0.0` if explicitly zero |
| `cpa` | Always | `round(total_spend / total_conversions, 2)` | If `conversions <= 0` $\rightarrow$ `0.0` |
| `cpc` | Always | `round(total_spend / total_clicks, 2)` | If `clicks <= 0` $\rightarrow$ `0.0` |
| `conversion_rate` | Always | `round((total_conversions / total_clicks) * 100, 2)` | If `clicks <= 0` $\rightarrow$ `0.0` |
| `ctr` | Always | `round((total_clicks / total_impressions) * 100, 2)` | If `impressions <= 0` $\rightarrow$ `0.0` |
| `roas` | `if has_revenue` else `None` | `round(total_revenue / total_spend, 2)` | If `spend <= 0` $\rightarrow$ `0.0` |
| `roi` | `if has_revenue` else `None` | `round(((total_revenue - total_spend) / total_spend) * 100, 2)` | If `spend <= 0` $\rightarrow$ `0.0` |

### 3. Canonical & Aliased Return Dictionary
```python
return {
    "total_spend": total_spend,
    "total_revenue": total_revenue,
    "cpa": cpa,
    "avg_cpa": cpa,                         # Backward-compatible alias
    "cpc": cpc,
    "avg_cpc": cpc,                         # Backward-compatible alias
    "conversion_rate": conversion_rate,
    "avg_conversion_rate": conversion_rate, # Backward-compatible alias
    "ctr": ctr,
    "roas": roas,
    "overall_roas": roas,                   # Backward-compatible alias
    "roi": roi,
}
```

---

## SECTION 5 — TEST PLAN

The following 12 unit tests will be implemented in [analytics/tests/test_metrics.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/tests/test_metrics.py):

1. `test_kpis_complete_dataset`: Verifies spend, revenue, CPA, CPC, CTR, Conversion Rate, ROAS, and ROI on a benchmark dataset.
2. `test_kpis_missing_revenue`: Verifies `total_revenue`, `roas`, and `roi` return `None` (not `0.0` or `-100.0%`) when revenue is `NaN`.
3. `test_kpis_explicit_zero_revenue`: Verifies that when revenue is explicitly `0.0`, `total_revenue = 0.0`, `roas = 0.0`, and `roi = -100.0%`.
4. `test_cpa_zero_conversions`: Verifies `cpa = 0.0` without `ZeroDivisionError` when conversions are zero.
5. `test_cpc_zero_clicks`: Verifies `cpc = 0.0` without `ZeroDivisionError` when clicks are zero.
6. `test_conversion_rate_percentage`: Verifies percentage scaling (e.g., 50 conversions / 1000 clicks = `5.0%`).
7. `test_conversion_rate_zero_clicks`: Verifies `conversion_rate = 0.0` without `ZeroDivisionError` when clicks are zero.
8. `test_ctr_percentage`: Verifies percentage scaling (e.g., 200 clicks / 10,000 impressions = `2.0%`).
9. `test_ctr_zero_impressions`: Verifies `ctr = 0.0` without `ZeroDivisionError` when impressions are zero.
10. `test_roi_positive_and_negative`: Verifies positive ROI ($ \text{Spend}=\$1000, \text{Rev}=\$2500 \rightarrow 150.0\% $) and negative ROI ($ \text{Spend}=\$1000, \text{Rev}=\$400 \rightarrow -60.0\% $).
11. `test_backward_compatible_aliases`: Verifies both canonical keys (`roas`, `cpa`) and aliases (`overall_roas`, `avg_cpa`) exist with identical values.
12. `test_empty_dataframe`: Verifies graceful return of zeroed/null metrics on an empty DataFrame without raising exceptions.

---

## SECTION 6 — IMPLEMENTATION PLAN

Files to be modified upon approval:

1. **Modify:** [analytics/kpi/metrics.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/kpi/metrics.py)
   - Implement `has_revenue` detection.
   - Implement percentage scaling for `conversion_rate` and `ctr`.
   - Implement `roi` calculation.
   - Guard against zero denominators.
   - Return canonical contract keys and backward-compatible aliases.
2. **Modify:** [analytics/tests/test_metrics.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/tests/test_metrics.py)
   - Replace placeholder stub with the 12 unit tests described in Section 5.
3. **Execute & Verify:**
   - Run `python -m pytest analytics/tests/test_metrics.py -v`.
   - Run full suite: `python -m pytest analytics/tests -v`.

---

## SECTION 7 — BACKEND/FRONTEND DEPENDENCIES

1. **For Sushanth (Backend):**
   - In [backend/app/schemas/result.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/schemas/result.py), update `KpiResponse` to support optional revenue:
     ```python
     class KpiResponse(BaseModel):
         total_spend: float
         total_revenue: Optional[float] = None
         overall_roas: Optional[float] = None
         roi: Optional[float] = None
         avg_conversion_rate: float
         avg_cpa: float
     ```
2. **For Apeksha (Frontend):**
   - In [frontend/src/components/dashboard/KpiCards.jsx](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/frontend/src/components/dashboard/KpiCards.jsx), handle null revenue and ROAS gracefully:
     - If `kpis.totalRevenue == null`, display `"N/A"` instead of `"$0"`.
     - If `kpis.overallRoas == null`, display `"N/A"` instead of `"0.0x"`.
     - `Conversion Rate` and `CTR` will be formatted as percentages (`5.0%`).

---

## SECTION 8 — NEXT STEPS

Upon your approval, we will proceed immediately to:
1. Update `analytics/kpi/metrics.py` with the approved KPI engine design.
2. Implement and execute the 12 unit tests in `analytics/tests/test_metrics.py`.
