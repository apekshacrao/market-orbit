# Phase 1: Data Contract & Analytics Foundation
## Step 1.1 — Review Data Dictionary

**Document Version:** 1.0  
**Date:** September 17, 2026  
**Track Owner:** Vishal S Naik (Analytics & AI)  
**Status:** Completed (Read-Only Inspection & Documentation)  

---

## 1. Task Completion Status

- **Status:** **COMPLETED**
- **Mode:** Strictly Read-Only Inspection and Documentation.
- **Scope:** Detailed audit of [docs/DATA_DICTIONARY.md](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/docs/DATA_DICTIONARY.md), [docs/API_CONTRACT.md](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/docs/API_CONTRACT.md), [docs/ARCHITECTURE.md](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/docs/ARCHITECTURE.md), [database/schema.sql](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/database/schema.sql), backend ORM models, backend upload services, and analytics modules.
- **Rule Adherence:** No application code, database schemas, API contracts, or frontend components were modified. No missing fields or requirements were invented. All unknown attributes are explicitly documented as **UNKNOWN** or **REQUIRES CONFIRMATION**.

---

## 2. Existing Data Dictionary Status

- **File Location:** [docs/DATA_DICTIONARY.md](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/docs/DATA_DICTIONARY.md)
- **File Length:** 15 lines (723 bytes)
- **Current Completeness:** **Partial / Minimalist**
- **Coverage:** Outlines 8 campaign fields for CSV uploads.
- **Identified Gaps:**
  - Omits customer demographic attributes (`age_group`, `location`, `customer_segment`, `device`).
  - Omits `leads` (required in PDF specification for CPL and Conversion Rate).
  - Lacks definitions for derived KPI outputs and the analytics output JSON structure.
  - Lacks concrete validation rules (handling of negative numbers, date formats, allowable channel names).

---

## 3. Complete Documented Field Inventory

Inventory of the 8 fields defined in [docs/DATA_DICTIONARY.md](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/docs/DATA_DICTIONARY.md):

| Field Name | Documented Type | Required Status | Documented Description | Example Value | Intended Purpose & Usage |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `campaign_name` | String | **Required** | Name / identifier of campaign | `"Summer Sale 2026"` | **Storage & Analytics**: Primary entity identifier, ranking key, and AI prompt context. |
| `channel` | String | **Required** | Marketing channel / platform | `"Google Ads"`, `"Meta Ads"` | **Storage & Analytics**: Primary group-by key for channel breakdown and trend analysis. |
| `spend` | Float | **Required** | Total ad spend in USD | `1200.00` | **Storage & Analytics**: Core denominator/numerator for ROAS, CPA, CPC, and ROI. |
| `revenue` | Float | **Required** | Total attributed revenue in USD | `4500.00` | **Storage & Analytics**: Primary numerator for ROAS and ROI calculations. |
| `impressions` | Integer | **Optional** | Total ad impressions served | `50000` | **Storage & Analytics**: Denominator for Click-Through Rate (CTR). |
| `clicks` | Integer | **Optional** | Total link clicks recorded | `2500` | **Storage & Analytics**: Numerator for CTR; denominator for CPC and Conversion Rate. |
| `conversions` | Integer | **Optional** | Total converted actions | `180` | **Storage & Analytics**: Numerator for Conversion Rate; denominator for CPA. |
| `date` | Date | **Optional** | Campaign record date | `"2026-06-01"` | **Documented / Seed Only**: Intended for temporal trend analysis, but currently dropped during backend database ingestion. |

---

## 4. Required vs. Optional Field Comparison Across Sources

| Field Name | Project PDF / README | `DATA_DICTIONARY.md` | Backend Validator (`validation_service.py`) | Analytics Validator (`validators.py`) | Database Schema (`campaigns` table) | Alignment Assessment |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `campaign_name` | Mandatory | Required | Required | Required | `NOT NULL` | **Aligned** |
| `channel` | Mandatory | Required | Required | Required | `NOT NULL` | **Aligned** |
| `spend` | Mandatory | Required | Required | Required | `DEFAULT 0.00` | **Aligned** |
| `revenue` | "When available" | Required | Required | Required | `DEFAULT 0.00` | **Conflict**: Mandatory in code & dictionary, but conditional in PDF. |
| `impressions` | Optional | Optional | Optional (Not checked) | Optional | `DEFAULT 0` | **Aligned** |
| `clicks` | Optional | Optional | Optional (Not checked) | Optional | `DEFAULT 0` | **Aligned** |
| `conversions` | Optional | Optional | Optional (Not checked) | Optional | `DEFAULT 0` | **Aligned** |
| `date` | "When available" | Optional | Ignored | Ignored | **MISSING FROM DDL** | **Conflict**: Present in seed CSV, but omitted from database table. |
| `leads` | Mandatory for CPL | **NOT DOCUMENTED** | **NOT CHECKED** | **NOT CHECKED** | **MISSING FROM DDL** | **Critical Gap**: In PDF, but completely absent across repo. |
| `location` | "When available" | **NOT DOCUMENTED** | **NOT CHECKED** | **NOT CHECKED** | **MISSING FROM DDL** | **Gap**: In PDF, absent from repo. |
| `age_group` | "When available" | **NOT DOCUMENTED** | **NOT CHECKED** | **NOT CHECKED** | **MISSING FROM DDL** | **Gap**: In PDF, absent from repo. |
| `customer_segment`| "When available" | **NOT DOCUMENTED** | **NOT CHECKED** | **NOT CHECKED** | **MISSING FROM DDL** | **Gap**: In PDF, absent from repo. |
| `device` | Conceptual Trend | **NOT DOCUMENTED** | **NOT CHECKED** | **NOT CHECKED** | **MISSING FROM DDL** | **Gap**: Absent from repo. |

---

## 5. KPI Data Requirements Table

| KPI Name | Required Input Fields | Mandatory vs. Optional | Formula (Source Documented) | Zero-Denominator Handling | Missing-Data Handling | Discrepancies & Conflicts |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Total Spend** | `spend` | Mandatory | `sum(spend)` | N/A | Default to `0.0` | None. |
| **Total Revenue** | `revenue` | Mandatory in Dict; Optional in PDF | `sum(revenue)` | N/A | Default to `0.0` | None. |
| **Cost Per Lead (CPL)** | `spend`, `leads` | `spend`: Mandatory<br>`leads`: **UNKNOWN** | `Total Campaign Cost / Number of Leads` *(Documented in README/PDF)* | Return `0.0` or `null` if `leads <= 0` | Cannot calculate if `leads` is missing | **CRITICAL GAP**: `leads` column does not exist. Code calculates `avg_cpa = spend / conversions` instead. |
| **Conversion Rate** | PDF: `conversions`, `leads`<br>Code: `conversions`, `clicks` | `conversions`: Optional<br>`leads`: Unknown<br>`clicks`: Optional | **PDF formula:** `(Conversions / Leads) * 100`<br>**Code formula:** `total_conversions / total_clicks` | Guarded: return `0.0` if denominator is `0` | Defaults to `0` if denominator missing | **DIRECT CONFLICT**: PDF uses Leads; codebase uses Clicks. |
| **Click-Through Rate (CTR)** | `clicks`, `impressions` | Both Optional | `(Clicks / Impressions) * 100` *(README/PDF)*<br>`total_clicks / total_impressions` *(Code)* | Guarded in code: `if total_impressions > 0 else 0.0` | Defaults to `0` if fields are missing | Aligned in logic; format (decimal vs. percentage string) requires frontend alignment. |
| **Lead Rate** | `leads`, `clicks` or `impressions` | **UNKNOWN** | **NOT DOCUMENTED** in any project source | **REQUIRES CONFIRMATION** | **REQUIRES CONFIRMATION** | Formula not present in repo. |
| **Return on Investment (ROI)** | `revenue`, `spend` | Both Mandatory in Dict | `((Revenue - Cost) / Cost) * 100` *(Documented in README/PDF)* | Guard required: return `0.0` if `spend <= 0` | Default to `0.0` if missing | Documented in PDF, but **omitted from `analytics/kpi/metrics.py`**. |
| **Return on Ad Spend (ROAS)** | `revenue`, `spend` | Both Mandatory in Dict | `total_revenue / total_spend` *(Documented in README/code)* | Guarded in code: `if total_spend > 0 else 0.0` | Default to `0.0` if missing | Aligned. |

---

## 6. Trend Analysis Data Requirements

| Dimension / Trend Attribute | In Data Dictionary? | In Database Schema? | In Current Code? | Analytics Viability Assessment |
| :--- | :--- | :--- | :--- | :--- |
| **Channel (`channel`)** | **Yes** (String, Required) | **Yes** (`VARCHAR(100)`) | **Yes** (`customer_trends.py`) | **Ready**: Channel breakdown aggregates spend, revenue, conversions. |
| **Date / Time (`date`)** | **Yes** (Date, Optional) | **No** (Omitted from table) | **No** (Dropped on upload) | **BLOCKED**: Date is ignored by `CampaignService`. Temporal trends cannot be computed from DB. |
| **Location** | **No** | **No** | **No** | **UNAVAILABLE / REQUIRES CONFIRMATION**: In PDF, but no schema representation. |
| **Age Group** | **No** | **No** | **No** | **UNAVAILABLE / REQUIRES CONFIRMATION**: In PDF, but no schema representation. |
| **Customer Segment** | **No** | **No** | **No** | **UNAVAILABLE / REQUIRES CONFIRMATION**: In PDF, but no schema representation. |
| **Device** | **No** | **No** | **No** | **UNAVAILABLE / REQUIRES CONFIRMATION**: No schema or code representation. |

---

## 7. Explicit Data Quality Rules

### 7.1 Rules Explicitly Documented
1. **Header Requirement:** Uploaded CSV must contain `campaign_name`, `channel`, `spend`, `revenue` ([docs/DATA_DICTIONARY.md](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/docs/DATA_DICTIONARY.md)).
2. **File Type:** Only `.csv` format accepted ([docs/API_CONTRACT.md](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/docs/API_CONTRACT.md)).

### 7.2 Rules Implemented in Code but Not Documented
1. **Header Normalization:** Columns are lowercased, stripped, and spaces converted to underscores ([cleaner.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/preprocessing/cleaner.py)).
2. **String Trimming:** `campaign_name` and `channel` are stripped of whitespace ([campaign_service.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/services/campaign_service.py)).
3. **Null Handling:** Missing numeric values default to `0` or `0.0` ([cleaner.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/preprocessing/cleaner.py), [campaign_service.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/services/campaign_service.py)).
4. **Header Rejection:** Missing required headers trigger `HTTP 422` ([validation_service.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/services/validation_service.py)).
5. **Row Casting Errors:** Non-numeric strings in numeric columns trigger `HTTP 422` citing the exact CSV row number ([campaign_service.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/services/campaign_service.py)).
6. **Zero Rows:** Empty CSV files trigger `HTTP 422` ([campaign_service.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/services/campaign_service.py)).

### 7.3 Rules Requiring Team Confirmation
1. **Negative Numeric Values:** Neither code nor docs reject negative spend/revenue/impressions. Should negative values be rejected via `HTTP 422` or clamped to `0.0`?
2. **Duplicate Records:** No handling exists for multiple entries of the same campaign name and channel. Should duplicates be aggregated or rejected?
3. **Date Format Standard:** Date formats are not strictly validated against ISO 8601 (`YYYY-MM-DD`).
4. **Extra CSV Columns:** If an uploaded CSV includes extra columns (e.g., `location`, `age_group`), backend currently discards them silently.

---

## 8. Documentation vs. Existing Code Comparison

| Aspect | Documentation (`docs/`) | Implementation in Code | Analytics Impact |
| :--- | :--- | :--- | :--- |
| **`revenue` Field** | Documented as **Required**. | Enforced as required by `ValidationService`. | Upload fails if `revenue` is missing. |
| **`date` Field** | Documented in `DATA_DICTIONARY.md` and seed CSV. | Dropped during backend ingestion in `CampaignService`. | **Critical**: Temporal/time-series trend analysis is blocked. |
| **`leads` Field** | Documented in `README.md` for CPL and Conversion Rate. | Missing across data dictionary, backend, DB, and analytics. | **Critical**: CPL cannot be calculated as specified in PDF. |
| **Conversion Rate** | PDF states `(Conversions / Leads) * 100`. | `metrics.py` calculates `conversions / clicks`. | **Conflict**: Must decide between Click Conversion Rate vs. Lead Conversion Rate. |
| **ROI Calculation** | Documented in `README.md`. | Omitted from `analytics/kpi/metrics.py`. | Analytics must add ROI formula to `metrics.py`. |

---

## 9. Backend Data Availability Findings

1. **Available in PostgreSQL `campaigns` Table:**
   - `campaign_name` (`VARCHAR(255)`)
   - `channel` (`VARCHAR(100)`)
   - `impressions` (`INTEGER DEFAULT 0`)
   - `clicks` (`INTEGER DEFAULT 0`)
   - `spend` (`NUMERIC(12, 2) DEFAULT 0.00`)
   - `conversions` (`INTEGER DEFAULT 0`)
   - `revenue` (`NUMERIC(12, 2) DEFAULT 0.00`)
2. **Missing from PostgreSQL `campaigns` Table:**
   - `date` (Omitted from table DDL).
   - `leads` (Missing).
   - `location`, `age_group`, `customer_segment`, `device` (Missing).
3. **Upload Processing Behavior:**
   - [backend/app/services/campaign_service.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/services/campaign_service.py) parses only the 7 columns listed above. Any additional columns in the uploaded CSV are silently dropped.

---

## 10. Information Required from Sushanth (Backend & Database Lead)

Questions to align on before finalizing the Analytics Data Contract:

1. **Campaign Date Field Persistence:**  
   *"Can you add a `date` (DATE) column to the `campaigns` table and include it in `CampaignService.import_campaigns`? It is present in our sample CSV and data dictionary, and Analytics needs it for time-series trend analysis."*
2. **Clarification on `leads` vs. `conversions`:**  
   *"The project PDF specifies CPL based on `leads`, but our database and validation only support `conversions`. Will customer files include `leads`, or should Analytics standardize on `conversions` (CPA) and remove `leads` from the contract?"*
3. **Customer Trend Dimensions:**  
   *"The PDF mentions trend analysis by `location`, `age group`, and `customer segment` 'when available'. Will these be supported as optional columns (or via a JSONB `metadata` column in `campaigns`), or should Analytics strictly limit trend analysis to `channel` for Phase 1?"*
4. **Revenue Optionality:**  
   *"The PDF notes revenue is used 'when available', but backend `ValidationService` rejects uploads missing `revenue`. Should files without revenue be supported (for CTR/CPC/CPA analysis), or is revenue strictly required for all datasets?"*
5. **Data Handoff Interface:**  
   *"When `AnalysisService` triggers the Analytics engine, will it pass a Pandas DataFrame created from `campaigns` table rows, or should Analytics provide a helper function that takes SQLAlchemy `Campaign` model instances?"*

---

## 11. Documentation Gaps and Conflicts

1. **Conversion Rate Definition Conflict:** PDF specifies `(Conversions / Leads) * 100`, while `metrics.py` implements `conversions / clicks`.
2. **Missing `leads` Column:** Required by PDF formulas, but omitted from `DATA_DICTIONARY.md`, DB schema, and code.
3. **Omission of `date` Column in Database:** Documented in `DATA_DICTIONARY.md` and seed CSV, but missing from PostgreSQL `campaigns` table.
4. **Missing Customer Attribute Specs:** No schema or formatting standards exist for demographic fields (`location`, `age_group`, `segment`).
5. **Output Format Ambiguity:** Specifications do not clarify whether rates (CTR, Conversion Rate, ROI) should be returned as decimals (`0.05`) or percentage values (`5.0`).

---

## 12. Recommended Next Step

**Phase 1 — Step 1.2: Resolve Data Contract & Align with Sushanth**
- Review the 5 alignment questions in Section 10 with Sushanth.
- Update [docs/DATA_DICTIONARY.md](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/docs/DATA_DICTIONARY.md) with agreed changes.
- Proceed to Phase 1 — Step 1.3: Update analytics schemas and preprocessing to conform to the approved data contract.
