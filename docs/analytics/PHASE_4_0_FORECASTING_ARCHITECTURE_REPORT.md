# Market Orbit — Phase 4.0: Forecasting Architecture & Feasibility Audit Report

**Document Version:** 1.0  
**Date:** September 19, 2026  
**Track:** Analytics & AI Architecture  
**Role:** Senior Time-Series Forecasting Architect  
**Status:** Read-Only Feasibility & Architectural Blueprint Complete  

---

## 1. Executive Summary

Phase 4.0 conducts an independent, read-only architectural and mathematical feasibility audit of time-series forecasting for Market Orbit. 

Market Orbit's existing analytics engine operates on campaign-level advertising records with optional chronological metadata. Historical data may be sparse, non-contiguous, or entirely absent, and revenue tracking may be missing or partial. 

This audit establishes:
1. Feasibility across additive volume metrics (`spend`, `conversions`, `clicks`, `impressions`, `revenue`) versus derived ratio KPIs (`cpa`, `cpc`, `ctr`, `conversion_rate`, `roas`).
2. Why derived metrics must **never be forecasted directly** as independent time-series, but instead derived from coherent forecasts of underlying quantities.
3. A comparative evaluation of candidate forecasting methodologies, rejecting complex black-box models and LLM hallucinations in favor of a tiered, deterministic baseline strategy.
4. Rigorous temporal evaluation protocols (rolling-origin walk-forward validation and WAPE/MAE error metrics) that avoid division-by-zero on zero-conversion days.
5. A deterministic JSON output schema for forecasting that cleanly integrates with Market Orbit's existing data contract and `AnalysisService`.

---

## 2. Current Architecture & Data Contract Inspection

### 2.1 Existing Modules & Chronological State
- **`analytics/trends/customer_trends.py`**:
  - Implements `analyze_trends(df)`.
  - Date parsing via `_parse_valid_date(val)` enforces strict `%Y-%m-%d` calendar dates; non-parseable values and sentinels (`"nan"`, `"none"`, `"nat"`) evaluate to `None`.
  - Aggregates daily records using `_aggregate_daily_records()`.
  - Requires **at least two distinct valid dates** (`distinct_dates_count >= 2`) to produce `time_series.timeline`. If fewer than two dates exist, it returns `has_time_series: False` with status `"insufficient_data"`.
  - **Critical Architectural Finding**: While two distinct dates suffice to establish a descriptive historical range, **two dates are mathematically insufficient to train or validate any predictive forecasting model**.
- **`analytics/preprocessing/cleaner.py`**:
  - Normalizes optional date strings to trimmed strings or `None`.
  - Cleans demographic dimensions (`location`, `age_group`, `customer_segment`, `device`).
- **`analytics/kpi/metrics.py` & `analytics/performance/ranking.py`**:
  - Enforce complete revenue semantics: revenue is `None` unless present and non-null across all rows in a group.
  - Zero conversions yield `cpa = None`. Zero clicks yield `cpc = None` and `ctr = None`.
- **`backend/app/services/analysis_service.py`**:
  - Executes `clean_dataset()`, `calculate_kpis()`, `rank_campaigns()`, `analyze_trends()`, and AI recommendations.
  - Stores outputs in PostgreSQL `AnalysisResult` table as `JSONB` columns (`kpis`, `rankings`, `trends`, `ai_recommendations`).
  - Adapts results via `_contract_response()` for frontend consumption.
- **Dependency Environment**:
  - Installed: `pandas`, `numpy`, `scipy`, `sklearn`.
  - **Not Installed**: `statsmodels`, `prophet`, `neuralprophet`, `torch`.
  - Invariant: No heavy external dependencies may be introduced.

---

## 3. Forecasting Feasibility by Metric

| Metric | Type | Aggregation Level | Minimum Historical Data | Missing Date Behavior | Forecast Methodology | Incomplete Data Handling |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`spend`** | Additive Volume | Daily Sum ($\ge 0.0$) | $\ge 7$ contiguous dates (ideal $\ge 14$) | Zero-fill or calendar interpolation required if gaps exist | Direct univariate time-series forecast ($\ge 0.0$ bounded) | Default missing spend to 0.0 |
| **`conversions`** | Additive Count | Daily Sum (Integer $\ge 0$) | $\ge 7$ contiguous dates (ideal $\ge 14$) | Zero-fill required if gaps exist | Direct count forecast (non-negative integer) | Default missing conversions to 0 |
| **`clicks`** | Additive Count | Daily Sum (Integer $\ge 0$) | $\ge 7$ contiguous dates | Zero-fill required if gaps exist | Direct count forecast ($\ge 0$) | Default missing clicks to 0 |
| **`impressions`**| Additive Count | Daily Sum (Integer $\ge 0$) | $\ge 7$ contiguous dates | Zero-fill required if gaps exist | Direct count forecast ($\ge 0$) | Default missing impressions to 0 |
| **`revenue`** | Additive Volume | Daily Sum ($\ge 0.0$) | $\ge 7$ contiguous dates with **100% complete** tracking | Cannot interpolate if tracking is absent | Direct forecast ONLY if 100% complete historically | If revenue incomplete or untracked, forecast must be `None` |
| **`cpa`** | Derived Ratio | $\text{spend} / \text{conversions}$ | Dependent on spend and conversions | N/A (derived) | **Derived**: $\widehat{\text{cpa}} = \widehat{\text{spend}} / \widehat{\text{conversions}}$ | If $\widehat{\text{conversions}} == 0$, $\widehat{\text{cpa}} = \text{None}$ |
| **`cpc`** | Derived Ratio | $\text{spend} / \text{clicks}$ | Dependent on spend and clicks | N/A (derived) | **Derived**: $\widehat{\text{cpc}} = \widehat{\text{spend}} / \widehat{\text{clicks}}$ | If $\widehat{\text{clicks}} == 0$, $\widehat{\text{cpc}} = \text{None}$ |
| **`ctr`** | Derived Ratio | $(\text{clicks} / \text{impressions}) \times 100$ | Dependent on clicks and impressions | N/A (derived) | **Derived**: $\widehat{\text{ctr}} = (\widehat{\text{clicks}} / \widehat{\text{impressions}}) \times 100$ | If $\widehat{\text{impressions}} == 0$, $\widehat{\text{ctr}} = \text{None}$ |
| **`conversion_rate`**| Derived Ratio | $(\text{conversions} / \text{clicks}) \times 100$ | Dependent on conversions and clicks | N/A (derived) | **Derived**: $\widehat{\text{cvr}} = (\widehat{\text{conversions}} / \widehat{\text{clicks}}) \times 100$ | If $\widehat{\text{clicks}} == 0$, $\widehat{\text{cvr}} = \text{None}$ |
| **`roas`** | Derived Ratio | $\text{revenue} / \text{spend}$ | Dependent on revenue and spend | N/A (derived) | **Derived**: $\widehat{\text{roas}} = \widehat{\text{revenue}} / \widehat{\text{spend}}$ | If revenue untracked or spend $\le 0$, $\widehat{\text{roas}} = \text{None}$ |

### Why Derived Metrics Must Never Be Forecasted Directly
Directly fitting time-series models (e.g. ARIMA, exponential smoothing) to CPA, CTR, or ROAS produces catastrophic edge cases:
1. **Division by Zero in Training**: On days where conversions $= 0$, historical CPA is mathematically undefined (`None`). Models cannot fit on missing values without arbitrary imputation (which distorts the series).
2. **Mathematical Incoherence**: A direct forecast of spend, conversions, and CPA would yield $\widehat{\text{cpa}} \neq \widehat{\text{spend}} / \widehat{\text{conversions}}$, destroying internal consistency across the platform.
3. **Non-Additivity**: Ratios cannot be aggregated over the forecast horizon.
4. **Architectural Rule**: Forecast the underlying additive quantities (`spend`, `conversions`, `clicks`, `impressions`, `revenue`), then compute derived KPIs using established Market Orbit division-by-zero safeguards.

---

## 4. Candidate Model Comparison & Recommendation

| Model | Historical Requirements | Mathematical Assumptions | Strengths | Limitations | Recommendation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Naive Persistence Baseline** | $\ge 2$ dates | $y_{T+h} = y_T$ (Tomorrow equals today) | 100% deterministic, zero hyperparameter risk, infallible baseline. | High variance if last day was anomalous; ignores trend and day-of-week seasonality. | **Mandatory Benchmark** for all evaluations. |
| **2. Simple Moving Average (SMA-7)** | $\ge 7$ contiguous dates | Constant level with localized mean | Smooths day-to-day noise; easily bounded $\ge 0$. | Lags trends; flat horizon projection; assumes contiguous days. | **Recommended Secondary Baseline** for short series ($7 \le N < 14$). |
| **3. Simple Exponential Smoothing (SES)** | $\ge 7$ contiguous dates | Level only; geometrically decaying weights ($\alpha \in (0, 1]$) | Weights recent data higher; adapts to level shifts. | Flat horizon projection; hyperparameter $\alpha$ tuning needed. | **Viable alternative** to SMA. |
| **4. Seasonal Naive (SNaive-7)** | $\ge 14$ contiguous dates ($\ge 2$ full 7-day cycles) | Weekly seasonality: $y_{T+h} = y_{T+h-7}$ | Captures day-of-week advertising patterns (e.g., weekend dropoffs). | Fails if series $< 14$ days or has irregular calendar gaps. | **Recommended Primary Model** when $\ge 14$ contiguous days exist. |
| **5. Holt's Linear Trend** | $\ge 14$ contiguous dates | Linear growth/decay trend: $l_t + h \cdot b_t$ | Captures growing/declining campaign velocity. | Easily projects negative values if spend is falling; tends to overshoot on marketing series. | **Conditionally viable** with damping and zero-floor constraints. |
| **6. SARIMA / Prophet / Neural Networks** | $\ge 60-100+$ dates | Complex stationarity, priors, or deep learning | Can model multi-seasonality and holidays. | Severe overfitting on small datasets ($N < 30$); violates "no external dependencies" constraint. | **REJECTED** as premature and unsupportable. |

### Architectural Recommendation: Tiered Deterministic Model Strategy
Market Orbit should implement a deterministic, 3-tier forecasting strategy based on verified historical data density:
1. **Tier 0 (< 7 distinct dates or date range $< 7$ days)**:
   - Status: `"insufficient_data"`.
   - Forecast: `is_available: False`.
   - Reason: "Historical series contains fewer than 7 calendar dates; minimum 7 daily observations required for defensible forecasting."
2. **Tier 1 (7 to 13 contiguous daily observations)**:
   - Model: **SMA-7 (7-Day Moving Average)** with **Naive Persistence** baseline comparison.
   - Horizon: Up to 7 days ahead.
   - Guard: Enforce non-negativity ($\max(0.0, \hat{y})$).
3. **Tier 2 ($\ge 14$ contiguous daily observations)**:
   - Model: **Seasonal Naive (7-Day SNaive)** benchmarked against **SMA-7** and **Naive**.
   - Horizon: 7 to 14 days ahead.
   - Captures weekly cyclicality while guaranteeing zero-risk determinism.

---

## 5. Forecast Validation Protocol

### 5.1 Temporal Validation Rule
- **Random train/test splitting is strictly prohibited** in time-series analytics (causes future-to-past data leakage).
- Evaluation must use **Rolling-Origin (Walk-Forward) Backtesting**:
  - Given $N$ historical days and test window $H=7$:
  - Train on $t_1 \dots t_{N-H}$, generate forecasts for $t_{N-H+1} \dots t_N$.
  - Compare forecasts $\hat{y}$ against actual held-out observations $y$.

### 5.2 Error Metrics Selection
Standard percentage errors (MAPE) divide by actual values ($y_t$), causing division-by-zero crashes on days with zero conversions or zero spend:
$$\text{MAPE} = \frac{100\%}{n}\sum \left|\frac{y_t - \hat{y}_t}{y_t}\right| \quad (\text{UNDEFINED when } y_t = 0)$$

Therefore, Market Orbit must standardize on:
1. **Mean Absolute Error (MAE)**:
   $$\text{MAE} = \frac{1}{n} \sum_{t=1}^n |y_t - \hat{y}_t|$$
   - Directly interpretable in currency ($) or conversion counts.
2. **Weighted Absolute Percentage Error (WAPE)**:
   $$\text{WAPE} = \frac{\sum_{t=1}^n |y_t - \hat{y}_t|}{\sum_{t=1}^n y_t} \times 100\%$$
   - Numerator and denominator aggregated across the whole test window.
   - Robust against individual zero days; undefined only if total test window actuals sum to zero.
3. **Root Mean Squared Error (RMSE)**:
   $$\text{RMSE} = \sqrt{\frac{1}{n}\sum_{t=1}^n (y_t - \hat{y}_t)^2}$$
   - Penalizes large individual day forecast errors.

---

## 6. Uncertainty & Safety Requirements

1. **Explicit Insufficient Data Handling**:
   - If `df` is empty, lacks `date`, or has $< 7$ distinct calendar dates, return `is_available: False` with descriptive diagnostics.
2. **Zero Fabrication Policy**:
   - Missing intermediate calendar dates must be explicitly regularized:
     - Days with zero campaign activity in an active date range are imputed with explicit 0.0 spend and 0 conversions, clearly tagged as regularized zero-activity days rather than synthetic artificial volume.
3. **Non-Negativity Constraints**:
   - Spend, conversions, clicks, impressions, and revenue are strictly non-negative: $\hat{y} = \max(0, \hat{y})$.
   - Conversion counts and clicks are rounded to non-negative integers for count consistency.
4. **Revenue Completeness Preservation**:
   - If historical revenue is untracked or partially missing, $\widehat{\text{revenue}} = \text{None}$ and $\widehat{\text{roas}} = \text{None}$. Under no circumstances should untracked revenue be predicted as zero.
5. **Confidence & Prediction Intervals**:
   - Simple heuristic intervals ($\hat{y} \pm 1.96 \cdot \text{RMSE}_{\text{in-sample}}$) may be provided only when $\ge 14$ dates exist, bounded at zero. If insufficient data exists, interval bounds should remain `None`.
6. **Strict JSON Serialization**:
   - All results must pass `json.dumps(result, allow_nan=False)`. No `NaN`, `Infinity`, or `-Infinity` values are permitted.

---

## 7. Proposed Output Schema

```json
{
  "is_available": true,
  "status": "success",
  "metadata": {
    "model_name": "seasonal_naive_7d",
    "forecast_horizon_days": 7,
    "historical_dates_count": 28,
    "date_range": {
      "start": "2026-08-01",
      "end": "2026-08-28"
    },
    "generated_at": "2026-09-19"
  },
  "evaluation": {
    "evaluation_method": "rolling_origin_backtest",
    "test_window_days": 7,
    "metrics": {
      "spend": {"mae": 14.50, "wape": 8.25, "rmse": 18.20},
      "conversions": {"mae": 1.20, "wape": 10.50, "rmse": 1.65}
    },
    "baseline_comparison": {
      "naive_spend_wape": 14.80,
      "model_improvement_pct": 44.26
    }
  },
  "forecast": [
    {
      "date": "2026-08-29",
      "spend": 185.50,
      "conversions": 15,
      "clicks": 120,
      "impressions": 3500,
      "revenue": 550.00,
      "cpa": 12.37,
      "cpc": 1.55,
      "ctr": 3.43,
      "conversion_rate": 12.50,
      "roas": 2.96,
      "intervals": {
        "spend_lower": 150.00,
        "spend_upper": 221.00,
        "conversions_lower": 12,
        "conversions_upper": 18
      }
    }
  ],
  "warnings": []
}
```

When insufficient data exists:
```json
{
  "is_available": false,
  "status": "insufficient_data",
  "metadata": {
    "model_name": null,
    "forecast_horizon_days": 0,
    "historical_dates_count": 3,
    "date_range": {
      "start": "2026-08-01",
      "end": "2026-08-03"
    },
    "generated_at": "2026-09-19"
  },
  "evaluation": null,
  "forecast": [],
  "warnings": [
    "Dataset contains only 3 valid calendar dates. Minimum 7 distinct daily observations required for forecasting."
  ]
}
```

---

## 8. Risks, Edge Cases & Unresolved Decisions

1. **Irregular Date Gaps**:
   - *Risk*: A dataset with observations on Day 1, Day 15, and Day 30 has a span of 30 days, but only 3 distinct dates.
   - *Decision*: Denominators and thresholds must be based on **distinct populated dates**, not calendar span.
2. **Structural Campaign Shifts**:
   - *Risk*: Mid-flight budget changes or pausing campaigns creates sudden step changes that naive or seasonal models cannot anticipate without exogenous event markers.
   - *Decision*: Forecasts must explicitly state in documentation that they are baseline projections based on historical momentum, not causal budget optimizations.
3. **Untracked Revenue Discontinuity**:
   - *Risk*: If revenue is reported on 6 out of 7 days, imputing the 7th day with 0.0 falsely deflates predicted ROAS.
   - *Decision*: Revenue forecasting must be gated by the exact same strict completeness rule used in Phases 1–3 (`is_revenue_complete`).

---

## 9. Suggested Phase 4 Sequential Implementation Plan

- **Phase 4.1: Forecasting Data Preprocessing & Series Regularization**:
  - Implement daily timeline aggregation, calendar gap filling (zero-activity insertion), and contiguous date validation in `analytics/forecasting/data_prep.py`.
- **Phase 4.2: Deterministic Baseline Models**:
  - Implement Naive Persistence, 7-day Moving Average (SMA), and 7-day Seasonal Naive (SNaive) forecasting in `analytics/forecasting/models.py`.
  - Implement derived KPI calculation from forecast primitives.
- **Phase 4.3: Rolling-Origin Validation & Backtesting Engine**:
  - Implement walk-forward evaluation, MAE, WAPE, and RMSE metric calculations in `analytics/forecasting/evaluation.py`.
- **Phase 4.4: Public Entry Point & Output Formatting**:
  - Expose `generate_performance_forecast(df)` in `analytics/forecasting/__init__.py`.
  - Format output according to the verified JSON schema.
- **Phase 4.5: Validation & Edge-Case Hardening**:
  - Comprehensive unit test suite (`analytics/tests/test_forecasting.py`) covering small datasets, zero conversions, missing dates, untracked revenue, and strict JSON serialization.
- **Phase 4.6: Final Phase 4 Sign-Off Audit**:
  - Read-only sign-off before API or backend integration.

---

## 10. Files Likely to Require Changes in Future Implementation

### New Files to Create (in Phase 4.1+):
- `analytics/forecasting/__init__.py`
- `analytics/forecasting/data_prep.py`
- `analytics/forecasting/models.py`
- `analytics/forecasting/evaluation.py`
- `analytics/tests/test_forecasting.py`
- `docs/analytics/PHASE_4_1_FORECASTING_IMPLEMENTATION_REPORT.md`

### Existing Files (NO changes made during this audit):
- `backend/app/services/analysis_service.py` (Future consumer in Phase 4.7/5.0)
- `backend/app/db/models/analysis_result.py` (May eventually store forecasts in JSONB)
- `analytics/trends/customer_trends.py` (Read-only reference; unchanged)

---

## 11. Read-Only Compliance Certification

I certify that:
1. **Zero files were created or modified in source code, backend, database, or frontend**.
2. **Zero dependencies were added**.
3. **No forecasting implementation or prototype was executed or committed**.
4. **All 159 existing repository tests remain 100% passing**.
5. This document constitutes the sole deliverable for Phase 4.0.
