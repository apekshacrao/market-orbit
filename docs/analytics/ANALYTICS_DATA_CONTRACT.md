# Finalized Analytics Data Contract: Phase 1 — Step 1.2

**Document Version:** 1.0  
**Date:** September 17, 2026  
**Track:** Analytics & AI Architecture  
**Lead:** Vishal S Naik (Analytics & AI Track)  
**Collaborator:** Sushanth S (Backend & Database Track)  
**Status:** Verification & Contract Design Finalized  

---

## SECTION 1 — CONFIRMED DECISIONS

The following architectural and data decisions have been established and confirmed by Sushanth:

1. **Date Field Support:** The `date` field will be supported in the PostgreSQL database schema and the CSV upload ingestion pipeline.
2. **Leads and CPA Alignment:** For the scope of this platform, **`conversions` will be treated as `leads`**. Conversions will serve as the primary denominator for Cost Per Acquisition (CPA / CPL) calculations.
3. **Optional Demographic Fields:** The fields `location`, `age_group`, `customer_segment`, and `device` are defined as **strictly optional**. They must be ingested and analyzed only when present in uploaded datasets.
4. **Optional Revenue:** The `revenue` field is **strictly optional**. Datasets lacking revenue data must be accepted, validated, stored, and analyzed without failure.
5. **Analytics Input Interface:** The backend will hand off validated campaign records to the Analytics Engine in a structured format (JSON / dictionary records) containing all available fields.
6. **Field Requirements Hierarchy:**
   - **Mandatory:** Core campaign identification (`campaign_name`, `channel`) and core performance metrics (`spend`, `conversions`).
   - **Optional:** `date`, `revenue`, `impressions`, `clicks`, `location`, `age_group`, `customer_segment`, and `device`.

---

## SECTION 2 — CURRENT IMPLEMENTATION STATUS

*Verification based on direct inspection of active source code, schemas, and tests:*

| Field Name | Confirmed Status | Present in Code? | Validation Status | Database Support | JSON / API Support | Issues & Technical Gaps Found |
| :--- | :--- | :---: | :--- | :--- | :--- | :--- |
| `campaign_name` | **Mandatory** | **Yes** | Required in [validation_service.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/services/validation_service.py#L7) | `VARCHAR(255) NOT NULL` in [schema.sql](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/database/schema.sql#L25) | Present in [schemas/upload.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/schemas/upload.py#L32) | Fully aligned. |
| `channel` | **Mandatory** | **Yes** | Required in [validation_service.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/services/validation_service.py#L8) | `VARCHAR(100) NOT NULL` in [schema.sql](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/database/schema.sql#L26) | Present in [schemas/upload.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/schemas/upload.py#L33) | Fully aligned. |
| `spend` | **Mandatory** | **Yes** | Required in [validation_service.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/services/validation_service.py#L9) | `NUMERIC(12, 2) DEFAULT 0.00` in [schema.sql](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/database/schema.sql#L29) | Present in [schemas/upload.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/schemas/upload.py#L36) | Fully aligned. |
| `conversions` | **Mandatory** | **Partial** | **Optional** in current validation; defaults to `0` | `INTEGER DEFAULT 0` in [schema.sql](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/database/schema.sql#L30) | Present in [schemas/upload.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/schemas/upload.py#L37) | **Mismatch:** Confirmed as mandatory core metric, but backend currently treats it as optional. |
| `impressions` | **Optional** | **Yes** | Optional; defaults to `0` | `INTEGER DEFAULT 0` in [schema.sql](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/database/schema.sql#L27) | Present in [schemas/upload.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/schemas/upload.py#L34) | Fully aligned. |
| `clicks` | **Optional** | **Yes** | Optional; defaults to `0` | `INTEGER DEFAULT 0` in [schema.sql](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/database/schema.sql#L28) | Present in [schemas/upload.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/schemas/upload.py#L35) | Fully aligned. |
| `revenue` | **Optional** | **Yes** | **Enforced as Mandatory** in [validation_service.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/services/validation_service.py#L10) | `NUMERIC(12, 2) DEFAULT 0.00` | Present in [schemas/upload.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/schemas/upload.py#L38) | **CRITICAL CONFLICT:** Backend validator and `test_validation.py` explicitly reject CSVs without revenue with HTTP 422. DB defaults to `0.00`, conflating zero revenue with untracked revenue. |
| `date` | **Optional** | **No** | Ignored by validator | **MISSING** from `campaigns` table | Absent from [schemas/upload.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/schemas/upload.py) | **CRITICAL GAP:** Exists in seed CSV and `DATA_DICTIONARY.md`, but dropped during ingestion by [campaign_service.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/services/campaign_service.py#L30-L53). |
| `location` | **Optional** | **No** | Ignored / Discarded | **MISSING** from database | Absent from schemas | **NOT IMPLEMENTED:** Dropped if present in CSV. |
| `age_group` | **Optional** | **No** | Ignored / Discarded | **MISSING** from database | Absent from schemas | **NOT IMPLEMENTED:** Dropped if present in CSV. |
| `customer_segment` | **Optional** | **No** | Ignored / Discarded | **MISSING** from database | Absent from schemas | **NOT IMPLEMENTED:** Dropped if present in CSV. |
| `device` | **Optional** | **No** | Ignored / Discarded | **MISSING** from database | Absent from schemas | **NOT IMPLEMENTED:** Dropped if present in CSV. |

---

## SECTION 3 — PROPOSED ANALYTICS INPUT CONTRACT

This contract defines the schema of the payload transferred from the backend database/service to the Analytics Engine for processing.

### Payload Schema: `CampaignRecord` (List of Items)

| Field Name | JSON / Python Type | Requirement | Nullable? | Description | Analytics Usage |
| :--- | :--- | :--- | :---: | :--- | :--- |
| `campaign_name` | `string` | **Mandatory** | No | Name or unique label of the campaign | Primary entity key for aggregation, ranking, and Groq prompt context. |
| `channel` | `string` | **Mandatory** | No | Marketing channel (e.g., `"Google Ads"`, `"Meta"`) | Primary dimension for channel breakdown, CPA by channel, and trends. |
| `spend` | `float` / `Decimal` | **Mandatory** | No | Total campaign expenditure in USD ($ \ge 0.0 $) | Core numerator for CPA, CPC; denominator for ROAS and ROI. |
| `conversions` | `integer` | **Mandatory** | No | Total conversion events ($ \ge 0 $) | **Treated as Leads**. Primary denominator for CPA; numerator for conversion rate. |
| `impressions` | `integer` | **Optional** | Yes | Total ad impressions served ($ \ge 0 $) | Denominator for Click-Through Rate (CTR). Defaults to `0` if absent. |
| `clicks` | `integer` | **Optional** | Yes | Total link clicks recorded ($ \ge 0 $) | Numerator for CTR; denominator for CPC and Click Conversion Rate. Defaults to `0`. |
| `revenue` | `float` / `Decimal` | **Optional** | **Yes** | Total attributed revenue in USD ($ \ge 0.0 $) | Required for ROAS and ROI. **Must be `null` if untracked** (never fabricated `0.0`). |
| `date` | `string` (ISO-8601) | **Optional** | **Yes** | Campaign execution date (`"YYYY-MM-DD"`) | Enables daily/weekly time-series trend analysis. `null` if untracked. |
| `location` | `string` | **Optional** | **Yes** | Geographic region, state, or country | Dimension for geographic performance breakdown. `null` if untracked. |
| `age_group` | `string` | **Optional** | **Yes** | Target age bracket (e.g., `"25-34"`) | Dimension for demographic efficiency breakdown. `null` if untracked. |
| `customer_segment` | `string` | **Optional** | **Yes** | Cohort/segment (e.g., `"High Intent"`) | Dimension for audience efficiency analysis. `null` if untracked. |
| `device` | `string` | **Optional** | **Yes** | Device type (e.g., `"Mobile"`, `"Desktop"`) | Dimension for device efficiency analysis. `null` if untracked. |

### Derived Metrics (Produced by Analytics, NOT Input)
- `cpa` (Cost per Acquisition / Conversion)
- `conversion_rate` (Clicks-to-Conversions)
- `ctr` (Impressions-to-Clicks)
- `cpc` (Cost per Click)
- `roas` (Attributed Revenue / Spend — *only if revenue present*)
- `roi` ((Revenue - Spend) / Spend — *only if revenue present*)

---

## SECTION 4 — PROPOSED JSON EXAMPLE

### 4.1 Example: Full Dataset with Optional Demographics & Revenue
```json
[
  {
    "campaign_name": "Summer Apparel Sale 2026",
    "channel": "Google Ads",
    "spend": 1250.00,
    "conversions": 85,
    "impressions": 45000,
    "clicks": 2100,
    "revenue": 4800.00,
    "date": "2026-06-01",
    "location": "North America",
    "age_group": "25-34",
    "customer_segment": "Returning Customers",
    "device": "Mobile"
  },
  {
    "campaign_name": "Brand Awareness Blast",
    "channel": "Meta Ads",
    "spend": 800.00,
    "conversions": 25,
    "impressions": 85000,
    "clicks": 1400,
    "revenue": 1200.00,
    "date": "2026-06-01",
    "location": "Europe",
    "age_group": "18-24",
    "customer_segment": "Top of Funnel",
    "device": "Mobile"
  }
]
```

### 4.2 Example: Dataset Without Revenue and Without Demographics
*Demonstrating a lead generation dataset where revenue is omitted:*
```json
[
  {
    "campaign_name": "B2B SaaS Trial Push",
    "channel": "LinkedIn Ads",
    "spend": 2400.00,
    "conversions": 48,
    "impressions": 18000,
    "clicks": 520,
    "revenue": null,
    "date": "2026-06-02",
    "location": null,
    "age_group": null,
    "customer_segment": null,
    "device": null
  },
  {
    "campaign_name": "Webinar Signups",
    "channel": "Google Ads",
    "spend": 950.00,
    "conversions": 62,
    "impressions": 12000,
    "clicks": 410,
    "revenue": null,
    "date": "2026-06-03",
    "location": null,
    "age_group": null,
    "customer_segment": null,
    "device": null
  }
]
```

---

## SECTION 5 — KPI IMPLICATIONS

The confirmed decisions directly shape the analytics calculations:

1. **CPA (Cost Per Acquisition):**
   - **Formula:** $\text{CPA} = \frac{\text{Total Spend}}{\text{Total Conversions}}$
   - Since conversions represent leads, CPA is functionally equivalent to Cost Per Lead (CPL).
   - **Zero Denominator Rule:** If $\text{conversions} = 0$, $\text{CPA}$ must return `0.0` (or `null`), never throw division by zero.
2. **Conversion Rate:**
   - **Formula:** $\text{Conversion Rate} = \frac{\text{Total Conversions}}{\text{Total Clicks}}$
   - *Rationale:* Since conversions are leads, comparing conversions to leads would yield 100%. Therefore, conversion rate strictly measures Click-to-Conversion efficiency.
   - **Zero Denominator Rule:** If $\text{clicks} = 0$, return `0.0`.
3. **Revenue-Based Metrics (ROAS and ROI):**
   - If `revenue` is `null` across the dataset:
     - `total_revenue`: Returns `null` (not `0.00`).
     - `overall_roas`: Returns `null` (not `0.0x`).
     - `roi`: Returns `null` (not `-100.0%`).
   - If `revenue` is present:
     - $\text{ROAS} = \frac{\text{Total Revenue}}{\text{Total Spend}}$
     - $\text{ROI} = \frac{\text{Total Revenue} - \text{Total Spend}}{\text{Total Spend}} \times 100$
4. **Campaign Ranking Fallback:**
   - When revenue is available: Rank campaigns primarily by **ROAS**.
   - When revenue is `null`: Automatically fallback to ranking by **CPA efficiency** (lowest CPA among top campaigns) and **total conversions volume**.
5. **Customer Trends Segmentation:**
   - **Channel:** Always aggregated (mandatory).
   - **Demographics:** Grouped only when a dimension (`location`, `age_group`, `customer_segment`, `device`) contains non-null values. If all records for a dimension are `null`, the dimension is omitted from the output JSON.
6. **Date-Based Trends:**
   - If `date` contains valid ISO strings: Produce daily/weekly trend lines for spend and conversions.
   - If `date` is `null`: Time-series section is flagged as `{"available": false}`.

---

## SECTION 6 — CONFLICTS AND RISKS

1. **Backend Validation Crash Risk:**
   - `backend/app/services/validation_service.py` currently defines `REQUIRED_COLUMNS = {"campaign_name", "channel", "spend", "revenue"}`.
   - Any upload without revenue is rejected immediately with `HTTP 422`.
2. **Database Value Conflation:**
   - `database/schema.sql` defines `spend NUMERIC(12, 2) DEFAULT 0.00` and `revenue NUMERIC(12, 2) DEFAULT 0.00`.
   - Storing untracked revenue as `0.00` in SQL makes it impossible for Analytics to distinguish between a campaign that earned $0 and a campaign where revenue was not tracked.
3. **Analytics Preprocessing Fabricating Values:**
   - [cleaner.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/preprocessing/cleaner.py#L7-L13) currently contains:
     ```python
     cleaned = cleaned.fillna({"revenue": 0.0, ...})
     ```
   - This converts `null` revenue to `0.0`, resulting in a fabricated `0.0x` ROAS and a false `-100%` ROI.
4. **Data Truncation on Ingestion:**
   - [campaign_service.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/services/campaign_service.py#L30-L53) only parses 7 columns.
   - Even if the user uploads `date`, `location`, `age_group`, `customer_segment`, or `device`, the backend currently **silently discards** them during insertion.
5. **Frontend/Backend Schema Case Mismatch:**
   - Backend [KpiResponse](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/schemas/result.py#L4-L9) uses snake_case (`total_spend`, `overall_roas`, `avg_cpa`).
   - Frontend [analysis.js](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/frontend/src/types/analysis.js#L2-L8) and [KpiCards.jsx](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/frontend/src/components/dashboard/KpiCards.jsx#L5-L9) expect camelCase (`totalSpend`, `overallRoas`, `avgCpa`).

---

## SECTION 7 — REQUIRED CONFIRMATIONS FROM SUSHANTH

The following 4 technical implementation decisions require Sushanth's final confirmation:

1. **Storage Mechanism for Demographic Dimensions:**  
   *Will `location`, `age_group`, `customer_segment`, and `device` be added as 4 distinct nullable columns on the `campaigns` table, or stored in a single JSONB column (e.g., `attributes JSONB` or `metadata JSONB`) on `campaigns`?*
2. **Nullable Revenue in Database:**  
   *Can the `campaigns.revenue` column be altered to allow `NULL` (removing the default `0.00` constraint for omitted fields) so Analytics can cleanly differentiate between $0 revenue and untracked revenue?*
3. **Date Column Schema Type:**  
   *Will the new `date` column in `campaigns` be a PostgreSQL `DATE` type or `TIMESTAMP WITH TIME ZONE`, and should the backend require ISO-8601 `YYYY-MM-DD` strings during CSV parsing?*
4. **Backend-to-Analytics Invocation Pattern:**  
   *Will `AnalysisService` invoke the Analytics Engine via a direct Python function passing a list of dictionaries/JSON (`run_analysis(campaign_records: list[dict])`), or will it pass a pre-built Pandas DataFrame?*

---

## SECTION 8 — RECOMMENDED NEXT STEP

Without modifying any existing files, proceed to:

**Phase 1 — Step 1.3: Update Analytics Schemas & Preprocessing Architecture**
1. Draft the formal Pydantic model for the Analytics Input (`CampaignInputRecord`) and Output (`AnalyticsOutput`) supporting nullable revenue, optional date, and optional demographics.
2. Refactor [cleaner.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/preprocessing/cleaner.py) and [validators.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/preprocessing/validators.py) to:
   - Accept missing revenue without validation error.
   - Preserve `None` / `null` for revenue instead of zero-filling.
   - Preserve optional date and demographic attributes when provided.
3. Update [metrics.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/kpi/metrics.py) to calculate ROAS and ROI conditionally only when revenue is non-null.
