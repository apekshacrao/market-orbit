# Market Orbit: Phase 2 Architecture and Requirements Review

**Date:** September 19, 2026  
**Author:** Senior Software Architect & Lead Analytics Engineer (Vishal S Naik)  
**Project:** Market Orbit (AI Marketing Performance Analyzer)  
**Target Scope:** Phase 2 (Advanced Comparison, Time Trends, Dimensional Breakdowns, Evidence-Based Insights)  
**Status:** Requirements & Architectural Proposal (No Source Code Modified)  

---

## 1. Executive Summary

Market Orbit successfully verified its Phase 1 pipeline end-to-end (commit [`5bc0dee`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/docs/analytics/BACKEND_ANALYTICS_COMPATIBILITY_FIX_REPORT.md), report [`aff9c43`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/docs/analytics/PHASE_1_PIPELINE_VERIFICATION_REPORT.md)). The foundation provides stable CSV ingestion, PostgreSQL persistence, clean dataset normalization, a 15-key KPI calculation engine, JSONB result persistence, and authenticated FastAPI result delivery.

The objective of **Phase 2** is to expand analytical depth beyond basic summary KPIs into four high-impact areas:
1. **Advanced Campaign Performance Comparison** (multi-metric rankings across ROAS, CPA, CPC, conversion volume, and efficiency indices).
2. **Time-Based Trend Analysis** (chronological performance tracking, daily/weekly aggregation, and directionality analysis).
3. **Dimensional Performance Breakdowns** (dynamic grouping and attribution across populated optional dimensions: `channel`, `device`, `location`, `age_group`, `customer_segment`).
4. **Structured, Evidence-Based Analytical Insights** (deterministic heuristic insight generation coupled with guarded LLM strategic commentary).

This review assesses the current repository state, identifies gaps and technical debt (including frontend naming and percentage formatting mismatches), establishes rigorous analytical safety guardrails, and outlines an orderly, multi-disciplinary implementation plan across team owners (**Vishal S Naik** for Analytics/AI, **Sushanth S** for Backend/Database, and **Apeksha C Rao** for Frontend UI).

---

## 2. Repository Findings

The repository is organized into five primary functional directories:

```text
market-orbit/
├── analytics/           # Analytics, Preprocessing, KPI, Trends, Ranking, AI Engine
│   ├── ai/              # Groq client wrapper and prompt templates (currently stubbed)
│   ├── kpi/             # calculate_kpis() engine (complete & verified)
│   ├── performance/     # rank_campaigns() (partial, ROAS-only)
│   ├── preprocessing/   # cleaner, validators, normalizers (complete & verified)
│   ├── schemas/         # Pydantic schemas (CampaignInputRecord, AnalyticsOutput)
│   └── trends/          # analyze_trends() (partial, channel-only)
├── backend/             # FastAPI Application & PostgreSQL Layer
│   └── app/
│       ├── api/v1/      # REST routers (auth.py, uploads.py, results.py)
│       ├── core/        # Config, security, JWT helpers
│       ├── db/          # SQLAlchemy session and models (Dataset, Campaign, AnalysisResult)
│       ├── schemas/     # Pydantic request/response models
│       └── services/    # Business services (CampaignService, StorageService, AnalysisService)
├── database/            # PostgreSQL DDL and migration scripts (001-007)
├── frontend/            # React 18 + Vite SPA Dashboard
│   └── src/
│       ├── api/         # Axios-based API client (resultsApi.js, uploadApi.js)
│       ├── components/  # Dashboard widgets (KpiCards, CampaignRanking, Charts)
│       ├── hooks/       # Custom React hooks (useAnalysis.js)
│       ├── pages/       # Dashboard, Login, Register, Upload pages
│       └── utils/       # formatters.js, validation.js
└── docs/analytics/      # Architecture reviews, data contracts, and verification reports
```

### Integration Touchpoints:
- **Backend $\leftrightarrow$ Analytics:** [`AnalysisService.get_results`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/services/analysis_service.py) queries PostgreSQL [`Campaign`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/models/campaign.py) records, maps them to [`CampaignInputRecord`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/schemas/campaign_schema.py), passes them to [`clean_dataset()`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/processing/cleaner.py), and orchestrates calls to [`calculate_kpis()`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/kpi/metrics.py), [`rank_campaigns()`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/performance/ranking.py), and [`analyze_trends()`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/trends/customer_trends.py).
- **Backend $\leftrightarrow$ Database:** Analysis outputs are persisted into [`AnalysisResult.kpis`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/models/analysis_result.py), `.rankings`, `.trends`, and `.ai_recommendations` as native PostgreSQL `JSONB`.
- **Backend $\leftrightarrow$ Frontend:** Exposed via `GET /api/v1/results/{dataset_id}` returning [`AnalysisResultResponse`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/schemas/result.py).

---

## 3. Existing Analytics Capabilities

| Capability | Module & Function | Implementation Status | Phase 2 Action Required |
| :--- | :--- | :---: | :--- |
| **Data Cleaning** | [`analytics.preprocessing.cleaner.clean_dataset`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/processing/cleaner.py) | **100% Complete** | Preserve as-is. Already standardizes column headers and strictly preserves `None` for missing revenue and dimensions. |
| **KPI Engine** | [`analytics.kpi.metrics.calculate_kpis`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/kpi/metrics.py) | **100% Complete** | Preserve as-is. Computes 15 verified totals, canonical KPIs, and compatibility aliases with division-by-zero protection. |
| **Campaign Ranking** | [`analytics.performance.ranking.rank_campaigns`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/performance/ranking.py) | **Partial (25%)** | **Enhance**: Currently only groups by `campaign_name` and sorts by `roas`. Contains a bug where `revenue.sum()` turns `NaN` into `0.0`. Must be expanded to support multi-metric sorting (CPA, conversions, spend) and handle missing revenue. |
| **Trends & Breakdowns** | [`analytics.trends.customer_trends.analyze_trends`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/trends/customer_trends.py) | **Partial (20%)** | **Rebuild / Expand**: Currently only aggregates `spend`, `revenue`, and `conversions` by `channel`. Completely lacks time-series analysis (`date`) and dimensional breakdowns (`location`, `device`, `age_group`, `customer_segment`). |
| **AI Insights** | [`analytics.ai.groq_client.GroqClient`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/ai/groq_client.py) | **Stub (10%)** | **Re-architect**: Hardcoded static mock. Needs a deterministic heuristic rules engine that calculates mathematical insights first, followed by safe LLM summarization. |

---

## 4. Existing Data Contract

The canonical data contract is established in [`CampaignInputRecord`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/schemas/campaign_schema.py):

### Available Fields & Types:
- **Mandatory Core Fields:**
  - `campaign_name` (`str`, non-empty)
  - `channel` (`str`, non-empty)
  - `spend` (`float` $\ge 0.0$)
  - `conversions` (`int` $\ge 0$)
- **Optional Metrics:**
  - `impressions` (`int` $\ge 0$, default `0`)
  - `clicks` (`int` $\ge 0$, default `0`)
  - `revenue` (`Optional[float]` $\ge 0.0$, default `None`)
- **Optional Dimensions:**
  - `date` (`Optional[str]`, calendar date `YYYY-MM-DD`)
  - `location` (`Optional[str]`, sanitized string or `None`)
  - `age_group` (`Optional[str]`, sanitized string or `None`)
  - `customer_segment` (`Optional[str]`, sanitized string or `None`)
  - `device` (`Optional[str]`, sanitized string or `None`)

### Data Contract Limitations for Phase 2:
1. **Dimension Sparsity:** None of the 5 dimensions (`date`, `location`, `age_group`, `customer_segment`, `device`) are mandatory. In real-world datasets, a user may provide only `date` and `device`, or no optional dimensions at all.
2. **Date Granularity & Continuity:** Dates are daily strings (`YYYY-MM-DD`). Datasets may contain a single day, discontinuous dates, or a small number of rows spanning months. Time-series logic must not assume daily continuity without gap handling.
3. **Missing Revenue in Aggregations:** If revenue is untracked (`None`) across campaigns in a specific segment (e.g. all B2B leads in `LinkedIn`), group revenue must remain `None`, and group ROAS/ROI must remain `None` rather than falling back to `0.0`.

---

## 5. Existing API Contract

Current API endpoints defined in [`backend/app/api/v1/results.py`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/api/v1/results.py):
1. `GET /api/v1/results/{dataset_id}` $\longrightarrow$ returns [`AnalysisResultResponse`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/schemas/result.py):
   ```json
   {
     "dataset_id": "string",
     "kpis": { ... 15 KPI keys ... },
     "rankings": { "top": [...], "bottom": [...] },
     "trends": { "channel_breakdown": { ... } },
     "ai_recommendations": [ ... ]
   }
   ```
2. `GET /api/v1/results/{dataset_id}/kpis` $\longrightarrow$ returns [`KpiResponse`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/schemas/result.py) (filtered 15-key summary).

### Architectural Decision on Phase 2 Delivery Options:
We evaluated three approaches for exposing Phase 2 analytics:
- **Option A: Extend existing result JSONB directly.**  
  *Pros:* Zero backend route changes; existing frontend dashboard hook [`useAnalysis.js`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/frontend/src/hooks/useAnalysis.js) already fetches the whole bundle in one HTTP request.  
  *Cons:* Top-level payload size increases slightly as more dimensions are populated.
- **Option B: Introduce new separate top-level sections in JSONB.**  
  *Pros:* Clean separation between aggregate KPIs, dimension breakdowns, time trends, and AI insights.  
  *Cons:* Requires modifying the Pydantic schema [`AnalysisResultResponse`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/schemas/result.py).
- **Option C: Add dedicated REST endpoints for each analytic.**  
  (`GET /{id}/trends`, `GET /{id}/breakdowns`, `GET /{id}/rankings`)  
  *Pros:* Highly granular, supports lazy loading and pagination on large datasets.  
  *Cons:* Increases network roundtrips for initial dashboard render; requires separate controller and caching logic.

### Architectural Recommendation:
**Adopt a Hybrid Architecture (Option A + B with Option C aliases):**
1. **Extend JSONB Schema (Primary):** Structure the `trends` JSONB field into clean sub-objects:
   - `trends.time_series`: Array of chronological points (`date`, `spend`, `revenue`, `conversions`, `roas`, `cpa`).
   - `trends.channel_breakdown`: Existing channel aggregations (backward-compatible).
   - `trends.dimension_breakdowns`: Nested breakdowns for populated dimensions (`location`, `device`, `age_group`, `customer_segment`).
   - `rankings`: Extended to include rankings by ROAS, CPA, and conversions.
   - `ai_recommendations`: Retained for strategic insights.
2. **Backend Convenience Routes (Secondary):** Add lightweight sub-resource GET routes in [`backend/app/api/v1/results.py`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/api/v1/results.py) (`/{id}/rankings`, `/{id}/trends`, `/{id}/recommendations`) that read directly from the cached `AnalysisResult` JSONB columns. This fulfills frontend contracts already stubbed in [`frontend/src/api/resultsApi.js`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/frontend/src/api/resultsApi.js).

---

## 6. Existing Database Design

PostgreSQL table [`analysis_results`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/db/models/analysis_result.py):
```sql
CREATE TABLE IF NOT EXISTS analysis_results (
    id VARCHAR(36) PRIMARY KEY,
    dataset_id VARCHAR(36) NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    kpis JSONB,
    rankings JSONB,
    trends JSONB,
    ai_recommendations JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### Database Assessment:
- **No Schema Migrations Required:** PostgreSQL `JSONB` columns (`rankings`, `trends`, `ai_recommendations`) inherently support structured, nested objects of arbitrary depth.
- **Persistence Mechanism:** [`AnalysisService`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/services/analysis_service.py) writes and reads native Python dictionaries directly to/from these JSONB columns.
- **Indexing:** If future analytical queries need to filter inside JSONB, GIN indexes can be added on `trends` and `rankings`. However, for Phase 2's dataset-level lookup (`WHERE dataset_id = :id`), the existing B-tree index on `dataset_id` is optimal.

---

## 7. Existing Test Coverage

### Inventory:
- **Total Passing Tests:** **64/64** (35 backend, 29 analytics).
- **Backend Coverage:** Ingestion, validation, access control, caching, date string serialization, nullable revenue handling.
- **Analytics Coverage:** Preprocessing, type normalization, and KPI engine arithmetic.

### Identified Test Coverage Gaps (Phase 2):
1. [`analytics/tests/test_ranking.py`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/tests/test_ranking.py) is currently an empty placeholder (`assert True`).
2. [`analytics/tests/test_trends.py`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/tests/test_trends.py) is currently an empty placeholder (`assert True`).
3. [`analytics/tests/test_ai.py`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/tests/test_ai.py) is currently an empty placeholder (`assert True`).
4. No unit tests verify dimensional grouping with null values.
5. No unit tests verify time-series sorting and aggregation across non-contiguous dates.

---

## 8. Frontend Compatibility Findings

Detailed inspection of [`frontend/src/`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/frontend/src/) revealed several critical integration issues that must be addressed during Phase 2 frontend coordination:

### 1. Casing Mismatch (snake_case vs. camelCase)
- **Backend API returns:** `total_spend`, `total_revenue`, `overall_roas`, `avg_conversion_rate`, `avg_cpa`.
- **Frontend [`KpiCards.jsx`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/frontend/src/components/dashboard/KpiCards.jsx) expects:** `kpis.totalSpend`, `kpis.totalRevenue`, `kpis.overallRoas`, `kpis.avgConversionRate`, `kpis.avgCpa`.
- **Impact:** Currently, KPI cards render fallback values (`$0`, `0.0x`) because property names do not match.

### 2. Double Percentage Multiplication Bug
- In [`frontend/src/utils/formatters.js`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/frontend/src/utils/formatters.js):
  ```javascript
  export function formatPercentage(value) {
    return `${((value || 0) * 100).toFixed(2)}%`;
  }
  ```
- The backend KPI Engine ([`analytics/kpi/metrics.py`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/kpi/metrics.py)) **already outputs pre-scaled percentages** (e.g. `conversion_rate = 4.57`, `roi = 82.11`).
- **Impact:** If `formatPercentage(4.57)` is called, the frontend displays `457.00%`!

### 3. Campaign Ranking Property Mismatch
- [`CampaignRanking.jsx`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/frontend/src/components/dashboard/CampaignRanking.jsx) accesses `c.name`.
- [`ranking.py`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/performance/ranking.py) outputs `campaign_name`.
- **Impact:** Campaign names render as blank/undefined.

### 4. Unmapped Dashboard Props
- [`Dashboard.jsx`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/frontend/src/pages/Dashboard.jsx) passes `data?.performance` to `PerformanceChart`, but the backend returns no `performance` key.
- [`Dashboard.jsx`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/frontend/src/pages/Dashboard.jsx) passes `data?.topCampaigns` and `data?.bottomCampaigns`, but the backend returns `data?.rankings.top` and `data?.rankings.bottom`.
- [`Dashboard.jsx`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/frontend/src/pages/Dashboard.jsx) passes `data?.recommendations`, but backend returns `data?.ai_recommendations`.

---

## 9. Phase 2 Feature Gap Analysis

```
┌────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   PHASE 2 GAP ANALYSIS                                         │
├──────────────────────────────┬──────────────────────────────┬──────────────────────────────────┤
│ Proposed Scope               │ Current Repository State     │ Gap to Bridge                    │
├──────────────────────────────┼──────────────────────────────┼──────────────────────────────────┤
│ 1. Advanced Campaign         │ ranking.py only sorts by     │ Add multi-metric rankings (CPA,  │
│    Comparison                │ ROAS; converts NaN to 0.0    │ spend, conv); preserve null rev; │
│                              │                              │ add relative performance index   │
├──────────────────────────────┼──────────────────────────────┼──────────────────────────────────┤
│ 2. Time-Based Trend          │ Zero time-series logic in    │ Daily & weekly chronologies,     │
│    Analysis                  │ codebase; date ignored       │ moving averages, pacing analysis │
├──────────────────────────────┼──────────────────────────────┼──────────────────────────────────┤
│ 3. Dimensional Performance   │ Only channel groupby exists; │ Dynamic groupby for location,    │
│    Breakdowns                │ demographics ignored         │ device, age, segment; skip empty │
├──────────────────────────────┼──────────────────────────────┼──────────────────────────────────┤
│ 4. Structured Evidence-      │ Static mock in groq_client.py│ Rule-based heuristic generator   │
│    Based Insights            │ with hardcoded cards         │ backed by deterministic math     │
└──────────────────────────────┴──────────────────────────────┴──────────────────────────────────┘
```

---

## 10. Recommended Phase 2 Requirements

### Feature 2.1: Advanced Multi-Metric Campaign Comparison
- **Business Purpose:** Enable marketers to evaluate campaigns not just on top-line ROAS, but on acquisition cost (CPA), conversion volume, and click efficiency (CPC/CTR).
- **Required Input:** Cleaned DataFrame containing `campaign_name`, `channel`, `spend`, `conversions`, `clicks`, `impressions`, and nullable `revenue`.
- **Processing Logic:**
  - Group by `campaign_name` and aggregate sums.
  - Calculate per-campaign metrics: `cpa`, `cpc`, `ctr`, `conversion_rate`, `roas` (if revenue tracked), `roi` (if revenue tracked).
  - Generate rankings by primary dimensions:
    - `by_roas`: Top and bottom campaigns by ROAS (omitting campaigns where revenue is untracked).
    - `by_cpa`: Top efficiency (lowest CPA with conversions $> 0$) vs. waste (highest CPA or spend with zero conversions).
    - `by_volume`: Highest conversion generators.
- **Expected Output:**
  ```json
  {
    "by_roas": { "top": [...], "bottom": [...] },
    "by_cpa": { "top": [...], "bottom": [...] },
    "by_conversions": { "top": [...] },
    "summary": { "total_campaigns_evaluated": 12 }
  }
  ```
- **Edge Cases:** Campaigns with spend $> 0$ and conversions $= 0$ (CPA is undefined/null; flagged as wasted spend); campaigns with untracked revenue (excluded from ROAS sorting, not defaulted to 0).

---

### Feature 2.2: Chronological Time-Based Trend Analysis
- **Business Purpose:** Visualize spend velocity, conversion trajectories, and efficiency fluctuations over the campaign lifecycle.
- **Required Input:** Cleaned DataFrame with `date` column populated.
- **Processing Logic:**
  - Check whether `date` is present and has $\ge 2$ distinct valid calendar dates.
  - If date coverage $< 30\%$ of records or single-date, return `"status": "insufficient_data"`.
  - Parse dates to `datetime64`, sort chronologically.
  - Aggregate spend, conversions, clicks, impressions, and revenue by date.
  - Compute daily metrics (`cpa`, `ctr`, `roas`).
  - Calculate 7-day rolling averages if span $> 14$ days.
  - Determine overall metric trajectory (`increasing`, `decreasing`, `stable`).
- **Expected Output:**
  ```json
  {
    "has_time_series": true,
    "date_range": { "start": "2026-09-01", "end": "2026-09-20", "total_days": 20 },
    "timeline": [
      {
        "date": "2026-09-01",
        "spend": 450.0,
        "conversions": 18,
        "revenue": 1200.0,
        "cpa": 25.0,
        "roas": 2.67
      }
    ],
    "trajectory": { "spend": "increasing", "conversions": "stable", "cpa": "improving" }
  }
  ```
- **Edge Cases:** Discontinuous dates (do not interpolate missing days with synthetic spend); single-date datasets (gracefully return `has_time_series: false`).

---

### Feature 2.3: Dynamic Multi-Dimensional Performance Breakdown
- **Business Purpose:** Provide granular segment performance across channels, devices, geographic regions, age brackets, and customer segments.
- **Required Input:** Cleaned DataFrame with optional columns `channel`, `device`, `location`, `age_group`, `customer_segment`.
- **Processing Logic:**
  - For each dimension, inspect the non-null fill rate.
  - If a dimension has $> 0$ non-null values, generate a grouped breakdown:
    - Aggregate `spend`, `conversions`, `clicks`, `impressions`, `revenue`.
    - Compute group-level `cpa`, `cpc`, `ctr`, `conversion_rate`, and `roas`.
    - If group revenue is entirely null, set group `revenue: null` and group `roas: null`.
    - Compute percentage share of total spend and total conversions.
  - If a dimension is entirely null across all records, omit it from output or return `{"available": false}`.
- **Expected Output:**
  ```json
  {
    "channel": { ... },
    "device": {
      "Desktop": { "spend": 1200.0, "conversions": 50, "cpa": 24.0, "roas": 2.1, "share_of_spend": 45.2 },
      "Mobile": { "spend": 1400.0, "conversions": 40, "cpa": 35.0, "roas": 1.4, "share_of_spend": 54.8 }
    },
    "location": { ... },
    "age_group": { "available": false },
    "customer_segment": { ... }
  }
  ```
- **Edge Cases:** Mixed missing dimensions (records with `location="Delhi"` but `device=None`); groups with zero conversions (CPA null).

---

### Feature 2.4: Structured, Evidence-Based Analytical Insights
- **Business Purpose:** Transform raw metrics into prioritized business recommendations grounded entirely in validated mathematical facts.
- **Required Input:** Output from KPI Engine, Rankings, Trends, and Breakdowns.
- **Processing Logic (Deterministic Heuristic Engine):**
  - **Rule 1 (Waste Detection):** Identify campaigns with spend $> \$100$ and zero conversions $\implies$ generate `WASTE_ALERT` insight with exact dollar amount wasted.
  - **Rule 2 (Channel Outperformance):** Identify channels with ROAS $> 1.5\times$ the aggregate ROAS $\implies$ generate `SCALE_OPPORTUNITY` insight.
  - **Rule 3 (CPA Divergence):** Identify devices or segments with CPA $> 2\times$ average CPA $\implies$ generate `EFFICIENCY_WARNING` insight.
  - **Rule 4 (Data Quality / Untracked Revenue):** If `total_revenue` is `None` $\implies$ generate `TRACKING_RECOMMENDATION` to implement revenue tracking.
- **LLM Role (Analytical Safety):**
  - The LLM does **not** compute numbers, rankings, or percentages.
  - The structured heuristic insight objects are passed to Groq as structured context.
  - The LLM's prompt instructs it to synthesize the findings into executive-ready strategic summaries without altering numerical values or fabricating ungrounded claims.
- **Expected Output:**
  ```json
  [
    {
      "id": "insight-001",
      "type": "SCALE_OPPORTUNITY",
      "severity": "HIGH",
      "title": "Scale Google Ads Desktop Campaigns",
      "finding": "Google Ads delivers an ROAS of 3.2x compared to the portfolio average of 1.82x.",
      "evidence": { "channel": "Google Ads", "roas": 3.2, "portfolio_roas": 1.82 },
      "recommended_action": "Reallocate 15-20% of underperforming Meta budget to Google Ads Search."
    }
  ]
  ```

---

## 11. Proposed Analytics Architecture

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   MARKET ORBIT ANALYTICS ENGINE                                  │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                  │
│  Raw Campaign Records (from PostgreSQL)                                                          │
│          │                                                                                       │
│          ▼                                                                                       │
│  clean_dataset()  (analytics/preprocessing/cleaner.py)                                           │
│          │                                                                                       │
│          ├─────────────────────────┬──────────────────────────┬────────────────────────┐         │
│          ▼                         ▼                          ▼                        ▼         │
│  calculate_kpis()           rank_campaigns()           analyze_trends()        breakdowns()      │
│  (Total / Canonical KPIs)   (Multi-Metric Ranking)     (Time-Series Trends)    (Dimensions)      │
│          │                         │                          │                        │         │
│          └─────────────────────────┼──────────────────────────┴────────────────────────┘         │
│                                    ▼                                                             │
│                      Deterministic Heuristic Engine                                              │
│                      (Rule-Based Insight Generator)                                              │
│                                    │                                                             │
│                                    ▼                                                             │
│                      Structured Mathematical Facts                                               │
│                                    │                                                             │
│                                    ▼                                                             │
│                      Groq LLM Context-Guarded Prompt                                             │
│                      (Executive Synthesis Only - No Math)                                        │
│                                    │                                                             │
│                                    ▼                                                             │
│                      Consolidated AnalyticsOutput                                                │
│                                    │                                                             │
│                                    ▼                                                             │
│                      PostgreSQL analysis_results (JSONB)                                         │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Analytical Safety Guarantees:
1. **Mathematical Isolation:** All calculations executed in Python (pandas/numpy). No arithmetic performed by LLMs.
2. **Deterministic Evidence:** Every insight references specific numerical evidence keys (`spend`, `cpa`, `roas`).
3. **Correlation vs. Causation Guard:** Automated insights will use descriptive framing ("associated with higher ROAS") rather than asserting causal mechanisms.
4. **Dimension Protection:** Zero synthetic imputation for missing dimensions or missing dates.

---

## 12. Proposed API and Response Design

### 1. Updated `AnalysisResultResponse` Schema:
```python
class AnalysisResultResponse(BaseModel):
    dataset_id: str
    kpis: Dict[str, Any]
    rankings: Dict[str, Any]       # Extended: by_roas, by_cpa, by_conversions
    trends: Dict[str, Any]         # Extended: time_series, dimension_breakdowns, channel_breakdown
    ai_recommendations: List[Dict[str, Any]]
```

### 2. Frontend Adaptation Layer (API Client or Hook):
To resolve the camelCase/snake_case mismatch without altering backend conventions, the frontend [`client.js`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/frontend/src/api/client.js) or [`useAnalysis.js`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/frontend/src/hooks/useAnalysis.js) should map backend keys:
- `total_spend` $\to$ `totalSpend`
- `total_revenue` $\to$ `totalRevenue`
- `overall_roas` $\to$ `overallRoas`
- `avg_conversion_rate` $\to$ `avgConversionRate`
- `avg_cpa` $\to$ `avgCpa`
- `rankings.top` $\to$ `topCampaigns`
- `rankings.bottom` $\to$ `bottomCampaigns`
- `ai_recommendations` $\to$ `recommendations`

---

## 13. Proposed Database Changes

**Verdict:** **No database schema migrations are necessary.**
- The existing [`analysis_results`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/db/models/analysis_result.py) table already features `rankings JSONB`, `trends JSONB`, and `ai_recommendations JSONB`.
- PostgreSQL JSONB easily accommodates nested structures (`trends.time_series`, `trends.dimension_breakdowns`).
- Caching behavior in [`AnalysisService`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/services/analysis_service.py) continues to function seamlessly.

---

## 14. Testing Strategy

| Target Area | Test Type | Test Scenarios & Assertions |
| :--- | :--- | :--- |
| **Advanced Ranking** | Unit ([`test_ranking.py`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/tests/test_ranking.py)) | - Ranking by CPA handles zero conversions without crashing (`None`/`inf`).<br>- Missing revenue campaigns excluded from ROAS ranking.<br>- Campaigns with identical scores preserve deterministic ordering. |
| **Time Trends** | Unit ([`test_trends.py`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/tests/test_trends.py)) | - Datasets with no dates return `has_time_series: false`.<br>- Non-contiguous dates preserve accurate chronology.<br>- Daily aggregation accurately sums spend and conversions. |
| **Breakdowns** | Unit ([`test_trends.py`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/tests/test_trends.py)) | - Unpopulated dimensions flagged as unavailable.<br>- Group-level missing revenue preserved as `null`.<br>- Percentage shares sum to $100\%$. |
| **Heuristic Insights** | Unit ([`test_ai.py`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/tests/test_ai.py)) | - High CPA triggers efficiency warning.<br>- Zero conversions with spend $> \$100$ triggers waste alert.<br>- Untracked revenue triggers tracking notice. |
| **API Endpoints** | Integration ([`test_results.py`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/tests/test_results.py)) | - Full response schema validation against Pydantic model.<br>- Cached JSONB returns identical structure on repeat calls. |

---

## 15. Team Coordination Requirements

### 1. Sushanth S (Backend & Database Lead)
- **API Router Enhancements:** Add optional sub-resource endpoints in [`backend/app/api/v1/results.py`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/api/v1/results.py) (`GET /{id}/rankings`, `GET /{id}/trends`, `GET /{id}/recommendations`) if modular frontend fetching is preferred.
- **Service Integration:** Verify that [`AnalysisService`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/services/analysis_service.py) continues to serialize analytics output into JSONB without ORM friction.
- **Database Review:** Confirm agreement that no DDL migrations are needed for Phase 2.

### 2. Apeksha C Rao (Frontend UI Lead)
- **Casing & Adapter Alignment:** Implement response adapter in [`useAnalysis.js`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/frontend/src/hooks/useAnalysis.js) to resolve snake_case to camelCase mapping.
- **Percentage Formatter Fix:** Update [`formatPercentage`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/frontend/src/utils/formatters.js) to prevent double multiplication by 100.
- **Widget Integration:** Update [`PerformanceChart.jsx`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/frontend/src/components/dashboard/PerformanceChart.jsx) and [`TrendCharts.jsx`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/frontend/src/components/dashboard/TrendCharts.jsx) to consume `data?.trends.time_series` and `data?.trends.dimension_breakdowns`.

### 3. Vishal S Naik (Analytics & AI Lead)
- Implement enhanced algorithms in `analytics/performance/ranking.py`.
- Implement time-series and breakdown logic in `analytics/trends/customer_trends.py`.
- Implement deterministic heuristic insights engine and guarded Groq prompt.
- Author unit test suites in `analytics/tests/test_ranking.py`, `test_trends.py`, and `test_ai.py`.

---

## 16. Risks and Edge Cases

1. **Risk:** Sparse or Incomplete Dimensions.  
   *Mitigation:* Preprocessing inspects non-null counts; dimensions with 0 values are omitted gracefully from breakdowns without error.
2. **Risk:** Single-Date Datasets.  
   *Mitigation:* Trend engine sets `has_time_series: false` if distinct date count $< 2$.
3. **Risk:** Untracked Revenue in Demographic Subsets.  
   *Mitigation:* Group-level revenue retains `None` if all records in group are null. Group ROAS evaluates to `None`, never `0.0`.
4. **Risk:** Division by Zero in Segment Metrics.  
   *Mitigation:* Segment CPA and CPC explicitly guard against zero conversions/clicks and return `None` or `0.0`.
5. **Risk:** LLM Hallucination or Arithmetic Inconsistency.  
   *Mitigation:* LLM generates no numerical calculations. All values come from verified heuristic objects.

---

## 17. Recommended Implementation Sequence

```
Step 2.1: Advanced Multi-Metric Campaign Ranking Engine (analytics/performance/ranking.py)
   ↓
Step 2.2: Time-Series & Dimensional Breakdown Engine (analytics/trends/customer_trends.py)
   ↓
Step 2.3: Deterministic Heuristic Insights Engine (analytics/ai/insights.py)
   ↓
Step 2.4: Analytics Test Suite Implementation (test_ranking.py, test_trends.py, test_ai.py)
   ↓
Step 2.5: Backend Integration & Response Model Alignment (AnalysisService & schemas) [Coordination: Sushanth]
   ↓
Step 2.6: Frontend Integration, Adapters & Chart Hookup [Coordination: Apeksha]
```

---

## 18. Files That Would Potentially Be Modified

### Analytics Layer:
- [`analytics/performance/ranking.py`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/performance/ranking.py) (Rewrite/expand ranking logic)
- [`analytics/trends/customer_trends.py`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/trends/customer_trends.py) (Add time trends and dimensional breakdowns)
- [`analytics/ai/groq_client.py`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/ai/groq_client.py) (Integrate guarded Groq API calls)
- [`analytics/ai/prompts.py`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/ai/prompts.py) (Refine prompt templates)
- [`analytics/schemas/result_schema.py`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/schemas/result_schema.py) (Update output schema)
- `analytics/tests/test_ranking.py`, `test_trends.py`, `test_ai.py` (Replace placeholders with full test suites)

### Backend Layer (Sushanth Coordination):
- [`backend/app/services/analysis_service.py`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/services/analysis_service.py) (Map extended ranking and breakdown results)
- [`backend/app/schemas/result.py`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/schemas/result.py) (Refine response models)
- [`backend/app/api/v1/results.py`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/api/v1/results.py) (Optional: add granular sub-resource routes)

### Frontend Layer (Apeksha Coordination):
- [`frontend/src/utils/formatters.js`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/frontend/src/utils/formatters.js) (Fix `formatPercentage` double multiplication)
- [`frontend/src/hooks/useAnalysis.js`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/frontend/src/hooks/useAnalysis.js) (Add camelCase mapping adapter)
- [`frontend/src/components/dashboard/CampaignRanking.jsx`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/frontend/src/components/dashboard/CampaignRanking.jsx) (Update prop keys)
- [`frontend/src/components/dashboard/PerformanceChart.jsx`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/frontend/src/components/dashboard/PerformanceChart.jsx) (Hook up time-series chart)
- [`frontend/src/components/dashboard/TrendCharts.jsx`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/frontend/src/components/dashboard/TrendCharts.jsx) (Hook up dimensional breakdowns)

---

## 19. Items Requiring Human or Team Confirmation

1. **Payload Organization:** Confirm whether `trends` should contain `time_series` and `dimension_breakdowns`, or if a separate top-level `breakdowns` key should be added to `analysis_results`.
2. **Frontend Casing Strategy:** Confirm whether the backend should output snake_case and frontend should use an adapter, or if backend should output both casings.
3. **Groq LLM Activation:** Confirm whether live Groq API key integration should be activated in Phase 2 or if a local deterministic fallback should always be present when `GROQ_API_KEY` is not set.

---

## 20. Final Recommendation

The Phase 1 architecture is robust, clean, and fully capable of supporting Phase 2 requirements without altering core database schemas or breaking existing data contracts. 

Phase 2 work should proceed according to the recommended implementation sequence, beginning with **Step 2.1 (Multi-Metric Campaign Ranking Engine)** and **Step 2.2 (Time-Series & Dimensional Breakdown Engine)** in the analytics module, followed by comprehensive unit test coverage before backend and frontend integration.

---

## DECISIONS REQUIRED BEFORE IMPLEMENTATION

Before code implementation commences, the team must confirm:

1. **Payload Structure Agreement:** Does the team approve nesting time-series trends and dimensional breakdowns under the existing `trends` JSONB key (preserving zero-migration status), or is a new top-level schema key preferred?
2. **Frontend Casing Resolution:** Will Apeksha implement a response normalization adapter in the frontend (`useAnalysis.js`), or should Sushanth/Vishal add camelCase aliases to backend API schemas?
3. **Percentage Formatting Protocol:** Confirmation from Apeksha to update `formatPercentage()` in [`formatters.js`](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/frontend/src/utils/formatters.js) so it does not multiply pre-scaled percentages by 100.
4. **Groq API Fallback Behavior:** Confirmation that when `GROQ_API_KEY` is omitted or quota is exceeded, the system will serve deterministic rule-based insights without raising HTTP 500 errors.
