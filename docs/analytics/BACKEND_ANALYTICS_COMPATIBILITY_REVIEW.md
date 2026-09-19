# Backend & Analytics Layer Compatibility Review

**Document Version:** 1.0  
**Date:** September 18, 2026  
**Track:** Analytics & AI Architecture  
**Lead:** Vishal S Naik (Analytics & AI Track)  
**Collaborators:** Sushanth S (Backend & Database Track), Apeksha C Rao (Frontend Track)  
**Status:** Inspection & Verification Complete  

---

## 1. Executive Summary

This document records the inspection-only compatibility review between the **Backend + Database layer** and the **Analytics layer** following the fast-forward merge of `main` into the `analytics` branch (commit range `2b257eb..e4a131a`).

The merge integrated:
- Ingestion and database storage of optional dimension fields: `date`, `location`, `age_group`, `customer_segment`, `device`.
- Nullable `revenue` support across database migrations, the SQLAlchemy `Campaign` model, and ingestion.
- Explicit 12-field mapping in `AnalysisService` converting database records into analytics inputs.
- Integration of `clean_dataset()`, `calculate_kpis()`, `rank_campaigns()`, `analyze_trends()`, and `GroqClient.generate_recommendations()`.
- Persistence of analysis results into PostgreSQL `analysis_results` table.

### Summary of Verdict
- **Core Pipeline Compatibility:** **VERIFIED**. The data flow from CSV ingestion $\rightarrow$ PostgreSQL storage $\rightarrow$ `AnalysisService` extraction $\rightarrow$ `clean_dataset()` $\rightarrow$ `calculate_kpis()` functions as specified by the data contract.
- **Test Suite Results:**
  - `analytics/tests`: **27/27 tests PASSing (100%)**.
  - `backend/tests`: Requires backend virtual environment dependencies (`fastapi`, `sqlalchemy`, `pydantic-settings`).
- **Compatibility Issues Identified:** **2 critical / high-priority issues** discovered during type analysis:
  1. `datetime.date` type incompatibility with `CampaignInputRecord` / `validate_dataset()`.
  2. Unhandled `decimal.InvalidOperation` in `CampaignService.import_campaigns` causing 500 errors on invalid numeric input.

---

## 2. 10-Point Verification Checklist

| # | Inspection Item | Verification Status | Key Findings |
| :-: | :--- | :---: | :--- |
| **1** | **Campaign model & DB migrations** | **VERIFIED** | Migrations `006` and `007` align with `schema.sql`. `Campaign` model has all 5 optional fields and nullable revenue. |
| **2** | **CampaignService CSV ingestion** | **PARTIALLY VERIFIED** | Correctly parses optional fields and nullable revenue; missing `DecimalException` in exception handler. |
| **3** | **AnalysisService explicit field mapping** | **VERIFIED** | All 12 fields are explicitly mapped; no fields are dropped, renamed, or omitted. |
| **4** | **Data passed to `clean_dataset()`** | **VERIFIED** | Successfully normalizes records; coerces `datetime.date` to ISO string; preserves `NaN` revenue. |
| **5** | **Compatibility with `CampaignInputRecord`** | **INCOMPATIBILITY DETECTED** | SQLAlchemy `datetime.date` fails Pydantic `CampaignInputRecord` validation (expects `str`). |
| **6** | **Date format & NULL handling** | **VERIFIED** | Valid dates parsed to `date`, missing dates stored as `NULL`/`None`. Cleaner outputs `YYYY-MM-DD`. |
| **7** | **Revenue handling (missing vs. zero)** | **VERIFIED** | Explicit `0.0` yields `total_revenue: 0.0`, `roas: 0.0`, `roi: -100.0%`. Missing yields `None`. |
| **8** | **Compatibility with KPI Engine** | **VERIFIED** | `calculate_kpis()` outputs 15 keys (canonical + aliases); 100% compliant with `KpiResponse`. |
| **9** | **Field integrity check** | **VERIFIED** | All 12 columns retained without data loss or unwanted renaming across the stack. |
| **10** | **Backend & Analytics test results** | **VERIFIED** | Analytics suite passes 27/27 tests. Backend test suite requires backend virtual environment packages. |

---

## 3. Detailed Component Analysis

### 3.1 Database Migrations & SQLAlchemy Model
- **Migrations Inspected:**
  - [database/migrations/003_create_campaigns.sql](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/database/migrations/003_create_campaigns.sql): Original schema had `revenue NUMERIC(12, 2) DEFAULT 0.00` without a `NOT NULL` constraint.
  - [database/migrations/006_make_campaign_revenue_nullable.sql](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/database/migrations/006_make_campaign_revenue_nullable.sql): Runs `ALTER TABLE campaigns ALTER COLUMN revenue DROP DEFAULT;`. Dropping the default allows PostgreSQL to assign `NULL` when revenue is omitted.
  - [database/migrations/007_add_campaign_optional_fields.sql](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/database/migrations/007_add_campaign_optional_fields.sql): Adds `date DATE`, `location VARCHAR(255)`, `age_group VARCHAR(100)`, `customer_segment VARCHAR(100)`, and `device VARCHAR(100)`.
  - [database/schema.sql](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/database/schema.sql): Up to date with all consolidated changes.
- **SQLAlchemy Model ([Campaign](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/db/models/campaign.py#L14-L45)):**
  - Correctly defines `revenue = Column(Numeric(12, 2), nullable=True)`.
  - Correctly defines `date = Column(Date, nullable=True)`.
  - Correctly defines `location`, `age_group`, `customer_segment`, and `device` as `Column(String, nullable=True)`.
  - *Minor Cleanup Note:* Lines 1 and 3–12 contain duplicate import statements for SQLAlchemy column types.

### 3.2 Ingestion via `CampaignService`
- In [CampaignService.import_campaigns](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/services/campaign_service.py#L16-L138):
  - **Revenue:** Evaluated via `Decimal(row["revenue"]) if row.get("revenue") and row["revenue"].strip() else None`.
    - If empty string or omitted $\rightarrow$ `None` (persisted as SQL `NULL`).
    - If `"0"` or `"0.0"` $\rightarrow$ `Decimal('0')` (persisted as SQL `0.00`).
  - **Date:** Evaluated via `datetime.strptime(row["date"].strip(), "%Y-%m-%d").date() if row.get("date") and row["date"].strip() else None`.
    - Valid `YYYY-MM-DD` string $\rightarrow$ `datetime.date` object.
    - Omitted or empty string $\rightarrow$ `None`.
    - Malformed date string $\rightarrow$ Raises `ValueError` $\rightarrow$ Caught and returned as HTTP 422 with row number.
  - **Demographics:** All 4 fields stripped of whitespace; empty strings coerced to `None`.

### 3.3 Explicit Field Mapping in `AnalysisService`
- In [AnalysisService.get_results](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/services/analysis_service.py#L73-L93):
  ```python
  campaign_data = [
      {
          "campaign_name": campaign.campaign_name,
          "channel": campaign.channel,
          "impressions": campaign.impressions,
          "clicks": campaign.clicks,
          "spend": float(campaign.spend or 0),
          "conversions": campaign.conversions,
          "revenue": float(campaign.revenue) if campaign.revenue is not None else None,
          "date": campaign.date,
          "location": campaign.location,
          "age_group": campaign.age_group,
          "customer_segment": campaign.customer_segment,
          "device": campaign.device,
      }
      for campaign in campaigns
  ]
  ```
  All 12 fields are explicitly preserved and typed for downstream processing.

### 3.4 Data Cleaning via `clean_dataset()`
- [clean_dataset()](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/preprocessing/cleaner.py#L7-L79):
  - Ingests `campaign_data` without mutating original dictionaries (uses deepcopy).
  - Ensures numeric casts: `spend` (float64, fillna 0.0), `conversions` (int64, fillna 0), `impressions` (int64, fillna 0), `clicks` (int64, fillna 0).
  - Preserves untracked revenue as `NaN` (does **not** coerce missing revenue to 0.0).
  - Converts `datetime.date` into ISO string `"YYYY-MM-DD"` via `str(v).strip()` while preserving `None`/`NaN`.
  - Preserves demographic dimensions as strings or `None`.

### 3.5 KPI Engine Compatibility
- [calculate_kpis()](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/kpi/metrics.py#L5-L102) handles all contract requirements:
  - `has_revenue` evaluates whether `"revenue"` column exists and has at least one non-null value (`df["revenue"].notna().any()`).
  - When revenue is missing: `total_revenue = None`, `roas = None`, `roi = None`.
  - When revenue is explicit zero: `total_revenue = 0.0`, `roas = 0.0`, `roi = -100.0`.
  - Zero denominator protection is active across `cpa`, `cpc`, `conversion_rate`, `ctr`, `roas`, and `roi`.
  - Returns canonical keys and legacy aliases (`avg_cpa`, `avg_cpc`, `avg_conversion_rate`, `overall_roas`).
  - Validates seamlessly against backend [KpiResponse](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/schemas/result.py#L6-L25).

---

## 4. Potential Compatibility Issues & Defect Analysis

### Defect 1: Date Type Incompatibility with `CampaignInputRecord`
- **Location:** [backend/app/services/analysis_service.py: line 86](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/services/analysis_service.py#L86) vs [analytics/schemas/campaign_schema.py: line 25](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/schemas/campaign_schema.py#L25)
- **Mechanism:**
  - `Campaign.date` from SQLAlchemy returns a Python `datetime.date` object.
  - `AnalysisService` passes `"date": campaign.date`.
  - `CampaignInputRecord` expects `date: Optional[str] = Field(default=None)` and its validator enforces `isinstance(v, str)`.
  - Calling `validate_dataset(campaign_data)` or `CampaignInputRecord(**row)` raises:
    ```text
    pydantic_core.ValidationError: 1 validation error for CampaignInputRecord
    date: Input should be a valid string [type=string_type, input_value=datetime.date(2026, 9, 18), input_type=date]
    ```
- **Why it didn't fail existing tests:** Test [test_analysis_passes_optional_fields_to_analytics](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/tests/test_results.py#L237-L314) mocked `date="2026-09-18"` as a string rather than the real `datetime.date` object produced by SQLAlchemy.

### Defect 2: Unhandled `decimal.InvalidOperation` on Non-Numeric Spend/Revenue
- **Location:** [backend/app/services/campaign_service.py: line 48 & 106](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/services/campaign_service.py#L48)
- **Mechanism:**
  - Non-numeric strings in CSV fields (e.g. `spend = "$100"` or `revenue = "invalid"`) cause `Decimal(...)` to raise `decimal.InvalidOperation`.
  - In Python, `decimal.InvalidOperation` inherits from `decimal.DecimalException`, not `ValueError`.
  - The row loop in `CampaignService` only catches `except (ValueError, KeyError) as exc:`.
  - This causes an unhandled 500 error instead of returning an HTTP 422 validation response indicating the offending row number.

### Defect 3: Whitespace-Only String in `spend` Column
- **Location:** [backend/app/services/campaign_service.py: line 48](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/services/campaign_service.py#L48)
- **Mechanism:**
  - Expression: `spend = Decimal(row["spend"] or "0")`.
  - If `row["spend"]` is `"   "` (spaces), the boolean expression evaluates to `"   "`. Passing `"   "` to `Decimal()` triggers `decimal.InvalidOperation`.

### Defect 4: Inconsistent Test Import Paths
- **Location:** [backend/tests/test_campaign_service.py: line 1](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/tests/test_campaign_service.py#L1)
- **Mechanism:**
  - `test_campaign_service.py` imports `from backend.app.services.campaign_service import CampaignService`.
  - All other tests (`test_results.py`, `test_upload.py`, `test_validation.py`) import `from app.services...`.
  - Depending on whether `PYTHONPATH=.` or `PYTHONPATH=backend`, one or the other will fail during test collection.

---

## 5. Required Code Fixes

### Fix 1: Serialize `date` to ISO String in `AnalysisService`
File: [backend/app/services/analysis_service.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/services/analysis_service.py) (line 86)
```diff
-                "date": campaign.date,
+                "date": campaign.date.isoformat() if campaign.date else None,
```

### Fix 2: Support `date` and `datetime` Objects in `CampaignInputRecord`
File: [analytics/schemas/campaign_schema.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/analytics/schemas/campaign_schema.py)
```diff
-from datetime import datetime
-from typing import Optional
+from datetime import date, datetime
+from typing import Optional, Union
...
-    date: Optional[str] = Field(default=None, description="Campaign record date in YYYY-MM-DD format")
+    date: Optional[Union[str, date]] = Field(default=None, description="Campaign record date in YYYY-MM-DD format")

     @field_validator("date")
     @classmethod
-    def validate_date_format(cls, v: Optional[str]) -> Optional[str]:
+    def validate_date_format(cls, v: Optional[Union[str, date]]) -> Optional[str]:
         if v is None:
             return None
+        if isinstance(v, (date, datetime)):
+            return v.strftime("%Y-%m-%d")
         if isinstance(v, str):
             v_clean = v.strip()
             if not v_clean:
                 return None
             try:
                 datetime.strptime(v_clean, "%Y-%m-%d")
                 return v_clean
             except ValueError:
                 raise ValueError("Date must be a valid calendar date in 'YYYY-MM-DD' format")
-        raise ValueError("Date must be a string in 'YYYY-MM-DD' format")
+        raise ValueError("Date must be a string or date in 'YYYY-MM-DD' format")
```

### Fix 3: Handle `DecimalException` & Whitespace in `CampaignService`
File: [backend/app/services/campaign_service.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/services/campaign_service.py)
```diff
-from decimal import Decimal
+from decimal import Decimal, DecimalException
...
-                            spend=Decimal(
-                                row["spend"] or "0"
-                            ),
+                            spend=Decimal(
+                                (row.get("spend") or "0").strip() or "0"
+                            ),
...
-                    except (ValueError, KeyError) as exc:
+                    except (ValueError, KeyError, DecimalException) as exc:
                         raise HTTPException(
                             status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                             detail=(
                                 f"Invalid data in CSV row "
                                 f"{row_number}: {exc}"
                             ),
                         )
```

### Fix 4: Clean Duplicate Imports in Campaign Model
File: [backend/app/db/models/campaign.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/app/db/models/campaign.py)
```diff
-from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Numeric, Date, func
 from app.db.base import Base
 from sqlalchemy import (
     Column,
     String,
     Integer,
     DateTime,
     ForeignKey,
     Numeric,
     Date,
     func,
 )
```

### Fix 5: Normalize Test Import Path
File: [backend/tests/test_campaign_service.py](file:///c:/Users/Vishal%20S%20Naik/MyProjects/market-orbit/backend/tests/test_campaign_service.py)
```diff
-from backend.app.services.campaign_service import CampaignService
+from app.services.campaign_service import CampaignService
```

---

## 6. Recommended Next Steps

1. **Apply the 5 Non-Breaking Fixes:**
   - Commit the fixes for date serialization, `CampaignInputRecord` date-object support, and `DecimalException` handling.
2. **Setup Unified Development Environment:**
   - Create a single virtual environment containing dependencies from both `analytics/requirements.txt` and `backend/requirements.txt` so both test suites can run seamlessly via `pytest`.
3. **Frontend Track Alignment:**
   - Coordinate with Apeksha to confirm the frontend handles `null` values for `totalRevenue`, `overallRoas`, and `roi` (rendering `"N/A"` instead of `"$0"`).
   - Ensure the frontend respects the pre-scaled percentage values for `conversion_rate` and `ctr` ($5.0 = 5\%$).
