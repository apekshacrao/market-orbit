# Analytics KPI Output Contract & Backend Handoff Specification

**Document Version:** 1.0  
**Date:** September 17, 2026  
**Track:** Analytics & AI Architecture  
**Lead:** Vishal S Naik (Analytics & AI Track)  
**Collaborator:** Sushanth S (Backend & Database Track)  
**Status:** Finalized Output Specification for Backend Integration  

---

## SECTION A — CURRENT KPI OUTPUT STRUCTURE

The Analytics KPI Engine in [analytics/kpi/metrics.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/kpi/metrics.py) returns a flat Python dictionary containing **15 keys** partitioned into three categories:

```python
{
    # 1. Core Aggregate Counts & Totals (5 keys)
    "total_spend": float,              # Mandatory: sum(spend)
    "total_conversions": int,          # Mandatory: sum(conversions) (treated as leads)
    "total_clicks": int,               # Optional aggregate: sum(clicks)
    "total_impressions": int,          # Optional aggregate: sum(impressions)
    "total_revenue": Optional[float],  # Nullable: sum(revenue) if tracked, else None

    # 2. Canonical KPI Metrics (6 keys)
    "cpa": float,                      # Total Spend / Total Conversions
    "cpc": float,                      # Total Spend / Total Clicks
    "conversion_rate": float,          # (Total Conversions / Total Clicks) * 100
    "ctr": float,                      # (Total Clicks / Total Impressions) * 100
    "roas": Optional[float],           # Total Revenue / Total Spend (None if untracked)
    "roi": Optional[float],            # ((Total Revenue - Total Spend) / Total Spend) * 100 (None if untracked)

    # 3. Backward-Compatible Aliases (4 keys)
    "avg_cpa": float,                  # Identical to cpa
    "avg_cpc": float,                  # Identical to cpc
    "avg_conversion_rate": float,      # Identical to conversion_rate
    "overall_roas": Optional[float],   # Identical to roas
}
```

### JSON Serializability
- **100% Native JSON Compliant:** Every value is a standard Python `float`, `int`, or `None`.
- There are **no `NaN`**, **no `Infinity`**, and no custom NumPy/Pandas objects returned. Standard `json.dumps()` or FastAPI's `jsonable_encoder` will serialize it directly into PostgreSQL `JSONB`.

---

## SECTION B — RECOMMENDED CANONICAL JSON RESPONSE EXAMPLES

### Case 1: Complete Dataset with Revenue (E-Commerce / Direct Revenue Tracked)
```json
{
  "total_spend": 1250.00,
  "total_conversions": 85,
  "total_clicks": 2100,
  "total_impressions": 45000,
  "total_revenue": 4800.00,
  "cpa": 14.71,
  "cpc": 0.60,
  "conversion_rate": 4.05,
  "ctr": 4.67,
  "roas": 3.84,
  "roi": 284.00,
  "avg_cpa": 14.71,
  "avg_cpc": 0.60,
  "avg_conversion_rate": 4.05,
  "overall_roas": 3.84
}
```

### Case 2: Dataset Without Revenue (Lead Generation / Brand Awareness)
*When revenue is omitted or entirely `null` in the uploaded dataset, revenue metrics return `null`:*
```json
{
  "total_spend": 2400.00,
  "total_conversions": 48,
  "total_clicks": 520,
  "total_impressions": 18000,
  "total_revenue": null,
  "cpa": 50.00,
  "cpc": 4.62,
  "conversion_rate": 9.23,
  "ctr": 2.89,
  "roas": null,
  "roi": null,
  "avg_cpa": 50.00,
  "avg_cpc": 4.62,
  "avg_conversion_rate": 9.23,
  "overall_roas": null
}
```

### Case 3: Dataset with Explicit Zero Revenue ($0 Earned)
*When revenue is explicitly provided as `0.0`, revenue metrics evaluate to real values (not `null`):*
```json
{
  "total_spend": 500.00,
  "total_conversions": 10,
  "total_clicks": 100,
  "total_impressions": 5000,
  "total_revenue": 0.00,
  "cpa": 50.00,
  "cpc": 5.00,
  "conversion_rate": 10.00,
  "ctr": 2.00,
  "roas": 0.00,
  "roi": -100.00,
  "avg_cpa": 50.00,
  "avg_cpc": 5.00,
  "avg_conversion_rate": 10.00,
  "overall_roas": 0.00
}
```

---

## SECTION C — KPI FIELD-BY-FIELD SPECIFICATION

| Field Name | JSON Type | Nullable? | Mathematical Formula | Zero-Denominator Behavior | Description |
| :--- | :---: | :---: | :--- | :--- | :--- |
| `total_spend` | `number` | **No** | $\sum \text{spend}$ | Returns `0.0` if empty | Total campaign expenditure in USD ($ \ge 0.0 $). |
| `total_conversions` | `integer` | **No** | $\sum \text{conversions}$ | Returns `0` if empty | Total conversions / leads ($ \ge 0 $). |
| `total_clicks` | `integer` | **No** | $\sum \text{clicks}$ | Returns `0` if empty | Total user ad clicks ($ \ge 0 $). |
| `total_impressions` | `integer` | **No** | $\sum \text{impressions}$ | Returns `0` if empty | Total ad views/impressions ($ \ge 0 $). |
| `total_revenue` | `number` | **Yes** | $\sum \text{revenue}$ (if present) | Returns `None` if untracked | Total attributed revenue. `null` if missing; `0.0` if actual zero. |
| `cpa` | `number` | **No** | $\frac{\text{total\_spend}}{\text{total\_conversions}}$ | If $\text{conversions} \le 0 \rightarrow 0.0$ | Cost Per Acquisition (equivalent to Cost Per Lead). |
| `cpc` | `number` | **No** | $\frac{\text{total\_spend}}{\text{total\_clicks}}$ | If $\text{clicks} \le 0 \rightarrow 0.0$ | Cost Per Click. |
| `conversion_rate` | `number` | **No** | $\frac{\text{total\_conversions}}{\text{total\_clicks}} \times 100$ | If $\text{clicks} \le 0 \rightarrow 0.0$ | Click-to-Conversion rate expressed as a percentage ($5.0 = 5\%$). |
| `ctr` | `number` | **No** | $\frac{\text{total\_clicks}}{\text{total\_impressions}} \times 100$ | If $\text{impressions} \le 0 \rightarrow 0.0$ | Click-Through Rate expressed as a percentage ($1.5 = 1.5\%$). |
| `roas` | `number` | **Yes** | $\frac{\text{total\_revenue}}{\text{total\_spend}}$ | If $\text{spend} \le 0 \rightarrow 0.0$; If untracked $\rightarrow \text{null}$ | Return on Ad Spend ratio ($3.5 = 3.5\times$). `null` if revenue untracked. |
| `roi` | `number` | **Yes** | $\frac{\text{total\_revenue} - \text{total\_spend}}{\text{total\_spend}} \times 100$ | If $\text{spend} \le 0 \rightarrow 0.0$; If untracked $\rightarrow \text{null}$ | Return on Investment percentage ($150.0 = 150\%$). `null` if untracked. |
| `avg_cpa` | `number` | **No** | Alias for `cpa` | Same as `cpa` | Backward-compatibility alias for backend `KpiResponse`. |
| `avg_cpc` | `number` | **No** | Alias for `cpc` | Same as `cpc` | Backward-compatibility alias for backend `KpiResponse`. |
| `avg_conversion_rate` | `number` | **No** | Alias for `conversion_rate` | Same as `conversion_rate` | Backward-compatibility alias for backend `KpiResponse`. |
| `overall_roas` | `number` | **Yes** | Alias for `roas` | Same as `roas` | Backward-compatibility alias for backend `KpiResponse`. |

---

## SECTION D — REVENUE HANDLING RULES

1. **Detection Rule:** Revenue is evaluated as available **if and only if** `"revenue"` exists in `df.columns` and contains at least one non-null value (`df["revenue"].notna().any()`).
2. **Untracked Revenue Rule:** When revenue is omitted or entirely null:
   - `total_revenue = None`
   - `roas = None`
   - `roi = None`
   - **No fabrication:** The engine never coerces missing revenue into `0.0`.
3. **Explicit Zero Revenue Rule:** If a dataset explicitly provides `revenue: 0.0`:
   - `total_revenue = 0.0`
   - `roas = 0.0`
   - `roi = -100.0`
4. **Zero Spend Protection:** If revenue is tracked but `total_spend <= 0.0`:
   - `roas = 0.0` (prevents division by zero)
   - `roi = 0.0` (prevents division by zero)

---

## SECTION E — BACKWARD COMPATIBILITY CONSIDERATIONS

The current backend schema [backend/app/schemas/result.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/schemas/result.py) was drafted prior to the finalized data contract and expects:
- `avg_cpa`
- `avg_conversion_rate`
- `overall_roas`
- `total_spend`
- `total_revenue`

Because the Analytics Engine outputs **both** the canonical contract keys (`cpa`, `conversion_rate`, `roas`, `roi`, `cpc`, `ctr`) and the legacy aliases (`avg_cpa`, `avg_conversion_rate`, `overall_roas`, `avg_cpc`), **the Analytics output is 100% backward compatible**. Backend code can consume either set of keys without key errors.

---

## SECTION F — EXACT BACKEND CHANGES SUSHANTH WILL NEED TO MAKE

To finalize the integration and prevent API validation crashes, Sushanth needs to implement three specific adjustments:

### 1. Update `KpiResponse` Schema ([`backend/app/schemas/result.py`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/schemas/result.py#L4-L9))
Currently, `total_revenue` and `overall_roas` are mandatory `float`. When revenue is missing, FastAPI will throw a `500 Internal Server Error` during validation.
**Change Required:**
```python
class KpiResponse(BaseModel):
    total_spend: float
    total_conversions: Optional[int] = 0
    total_clicks: Optional[int] = 0
    total_impressions: Optional[int] = 0
    total_revenue: Optional[float] = None          # MUST be nullable
    cpa: Optional[float] = None
    cpc: Optional[float] = None
    conversion_rate: Optional[float] = None
    ctr: Optional[float] = None
    roas: Optional[float] = None                   # MUST be nullable
    roi: Optional[float] = None                    # MUST be nullable

    # Backward-compatible aliases
    avg_cpa: Optional[float] = None
    avg_cpc: Optional[float] = None
    avg_conversion_rate: Optional[float] = None
    overall_roas: Optional[float] = None
```

### 2. Update Backend Ingestion Validation ([`backend/app/services/validation_service.py`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/services/validation_service.py#L6-L11))
- Change `REQUIRED_COLUMNS` from `{"campaign_name", "channel", "spend", "revenue"}` to:
  ```python
  REQUIRED_COLUMNS = {"campaign_name", "channel", "spend", "conversions"}
  ```
- Remove `"revenue"` as mandatory so CSVs without revenue can be uploaded.

### 3. Wire `AnalysisService` to the Analytics Engine ([`backend/app/services/analysis_service.py`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/services/analysis_service.py))
- Query the `Campaign` records from PostgreSQL for `dataset_id`.
- Convert records to a list of dicts: `[c.__dict__ for c in campaigns]`.
- Clean records via `analytics.preprocessing.clean_dataset(records)`.
- Compute KPIs via `analytics.kpi.calculate_kpis(cleaned_df)`.
- Save the resulting dictionary to `AnalysisResult.kpis` JSONB column.

---

## SECTION G — UNRESOLVED QUESTIONS & RISKS

1. **Frontend CamelCase Mismatch Risk:**
   - Frontend [KpiCards.jsx](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/frontend/src/components/dashboard/KpiCards.jsx#L5-L9) and [analysis.js](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/frontend/src/types/analysis.js#L2-L8) currently look for `totalSpend`, `totalRevenue`, `overallRoas`, `avgConversionRate`, `avgCpa`.
   - Backend and Analytics currently use `snake_case`.
   - *Recommendation:* Apeksha (Frontend) should update the frontend formatters/fetchers to consume snake_case keys directly, or add a frontend response transformer.
2. **Frontend Percentage Symbol Rendering:**
   - `conversion_rate` and `ctr` are now scaled by $100$ (e.g., `4.05` instead of `0.0405`).
   - The Frontend team should be notified so they do not multiply by 100 a second time.
3. **Database Nullable `revenue`:**
   - Sushanth must ensure that when CSV rows omit revenue, the PostgreSQL `campaigns.revenue` column stores `NULL` rather than defaulting to `0.00`.
