# Market Orbit: Complete Codebase Audit & Progress Report

**Generated Date:** September 17, 2026  
**Active Branch:** `analytics` (Branched from `main` @ `c20e84c`)  
**Repository:** `market-orbit`  
**Lead Analytics / AI Engineer:** Vishal S Naik  

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Git Commit History & Progress Trajectory](#2-git-commit-history--progress-trajectory)
3. [Complete Annotated File Structure](#3-complete-annotated-file-structure)
4. [Subsystem-by-Subsystem Technical Audit](#4-subsystem-by-subsystem-technical-audit)
   - [4.1 Backend (`backend/`)](#41-backend-backend)
   - [4.2 Database & Migrations (`database/`)](#42-database--migrations-database)
   - [4.3 Analytics & AI Engine (`analytics/`)](#43-analytics--ai-engine-analytics)
   - [4.4 Frontend UI (`frontend/`)](#44-frontend-ui-frontend)
   - [4.5 System Documentation (`docs/`)](#45-system-documentation-docs)
   - [4.6 DevOps & Infrastructure](#46-devops--infrastructure)
5. [Cross-Cutting Integration & Gap Analysis](#5-cross-cutting-integration--gap-analysis)
6. [Roadmap & Immediate Action Plan for `analytics` Branch](#6-roadmap--immediate-action-plan-for-analytics-branch)

---

## 1. Executive Summary

**Market Orbit (AI Marketing Performance Analyzer)** is an intelligent marketing analytics platform designed to ingest campaign data (CSV/Excel), compute marketing performance KPIs, identify performance trends, generate AI-driven strategic recommendations via Groq, and display the findings in an interactive dashboard.

### High-Level Status Snapshot

| Layer / Track | Assigned Owner | Implementation Completeness | Status & Highlights |
| :--- | :--- | :---: | :--- |
| **Backend & APIs** | Sushanth S | **85%** | PR #1 merged. Complete JWT auth, CSV file storage, validation, campaign rows ingestion into PostgreSQL, and dataset querying. Results API is currently returning stub/mock data. |
| **Database & Schema** | Sushanth S | **100%** | 5 core relational tables, 5 migration scripts, seed sample data, and SQLAlchemy ORM models configured. |
| **Analytics & AI** | Vishal S Naik | **35%** | Base calculation functions (cleaning, metrics, ranking, channel trends) exist. Groq AI client is currently a stub returning static data; unit tests are empty `assert True` placeholders. |
| **Frontend UI** | Apeksha C Rao | **40%** | React + Vite app scaffolded with Dropzone, KPI Cards, and API client. Router, real charting libraries, and dynamic dataset selection are not yet hooked up. |
| **DevOps / Infra** | Shared | **50%** | `docker-compose.yml` configures Postgres, Backend, and Frontend services. `backend/Dockerfile` and `frontend/Dockerfile` are missing. |

---

## 2. Git Commit History & Progress Trajectory

The project history shows linear architectural progression followed by a substantial backend PR merge:

```
*   c20e84c (HEAD -> analytics, origin/main, origin/HEAD, main) Merge pull request #1 from apekshacrao/backend
|\  
| * d77ff05 feat(upload): add dataset campaigns endpoint
| * 964dbe2 feat(upload): add user dataset listing
| * d3fb334 feat(upload): implement dataset status endpoint
| * 93e5a7d feat(upload): import csv rows into campaigns
| * b34dcfb feat(upload): store and validate uploaded csv files
| * 4a0495b feat(upload): persist uploaded datasets
| * 82ad888 feat(auth): enforce dataset ownership
| * e6c3678 feat(auth): implement JWT authentication
| * 282e3de feat(auth): persist registered users in database
| * 81ab674 feat(db): inject database session into results API
| * da401b7 feat(db): verify database connection on startup
| * 431b21d feat(config): configure backend database environment
| * 1605467 feat(db): align ORM models with PostgreSQL schema
|/  
* 00d485d initial project architecture
* 21e6fdb Update README with project details and features
* fc56bb4 Initial commit
```

**Key Milestone Delivered in PR #1:**
- Transitioned backend from placeholder stubs to a working database-backed authentication and CSV dataset ingestion service.

---

## 3. Complete Annotated File Structure

```
market-orbit/
├── .env.example                               # Environment template for root orchestration
├── .gitignore                                 # Git ignore rules
├── AUDIT_REPORT.md                            # Comprehensive codebase audit (this document)
├── README.md                                  # Complete product overview & specification
├── docker-compose.yml                         # Multi-container orchestration (DB, Backend, Frontend)
│
├── docs/                                      # System Specifications & Contracts
│   ├── API_CONTRACT.md                        # REST API endpoint schemas & status codes
│   ├── ARCHITECTURE.md                        # Data flow & component topology
│   ├── DATA_DICTIONARY.md                     # Campaign CSV column definitions & types
│   └── INTEGRATION.md                         # Inter-module communication protocols
│
├── database/                                  # Database DDL, Migrations & Seeds
│   ├── README.md                              # Database setup documentation
│   ├── schema.sql                             # Master DDL (all 5 tables)
│   ├── migrations/
│   │   ├── 001_create_users.sql               # Users table migration
│   │   ├── 002_create_datasets.sql            # Datasets table migration
│   │   ├── 003_create_campaigns.sql           # Campaign records table migration
│   │   ├── 004_create_analysis_results.sql    # JSONB analysis results migration
│   │   └── 005_create_application_logs.sql    # Logs migration
│   └── seed/
│       ├── sample_campaign_data.csv           # Reference multi-channel campaign dataset
│       └── seed.sql                           # Seed execution SQL
│
├── backend/                                   # FastAPI Core Backend
│   ├── .env.example                           # Backend environment variables template
│   ├── .gitignore                             # Backend gitignore
│   ├── README.md                              # Backend installation & execution guide
│   ├── requirements.txt                       # Python dependencies (FastAPI, SQLAlchemy, psycopg2, etc.)
│   ├── app/
│   │   ├── main.py                            # FastAPI app instance, CORS middleware, startup probe
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── auth.py                    # /api/v1/auth router (register, login, me)
│   │   │       ├── uploads.py                 # /api/v1/uploads router (upload, status, campaigns)
│   │   │       └── results.py                 # /api/v1/results router (dataset analysis & KPIs)
│   │   ├── core/
│   │   │   ├── config.py                      # Pydantic BaseSettings config
│   │   │   ├── exceptions.py                  # Custom domain exceptions
│   │   │   └── security.py                    # bcrypt password hashing & JWT encode/decode
│   │   ├── db/
│   │   │   ├── base.py                        # SQLAlchemy Base class
│   │   │   ├── session.py                     # Database engine, SessionLocal, startup check
│   │   │   └── models/
│   │   │       ├── user.py                    # User ORM model
│   │   │       ├── dataset.py                 # Dataset ORM model
│   │   │       ├── campaign.py                # Campaign ORM model
│   │   │       ├── analysis_result.py         # AnalysisResult ORM model (JSONB)
│   │   │       └── application_log.py         # ApplicationLog ORM model
│   │   ├── dependencies/
│   │   │   └── auth.py                        # Depends(get_current_user) & Depends(get_db)
│   │   ├── schemas/
│   │   │   ├── auth.py                        # UserRegister, UserLogin, Token schemas
│   │   │   ├── upload.py                      # Upload responses & Dataset schemas
│   │   │   └── result.py                      # AnalysisResultResponse & KpiResponse schemas
│   │   └── services/
│   │       ├── auth_service.py                # Authentication business logic
│   │       ├── campaign_service.py            # CSV row parser & batch campaign table loader
│   │       ├── storage_service.py             # File saving, validation & dataset queries
│   │       ├── validation_service.py          # CSV header validation logic
│   │       └── analysis_service.py            # [STUB] Returns hardcoded mock KPI numbers
│   └── tests/                                 # Pytest backend test suite
│       ├── test_auth.py                       # Auth unit tests
│       ├── test_campaign_service.py           # Campaign CSV parsing & row count tests
│       ├── test_results.py                    # Results route tests
│       ├── test_upload.py                     # Comprehensive upload & validation tests
│       └── test_validation.py                 # Header validation tests
│
├── analytics/                                 # Data Processing & AI Engine (Vishal S Naik)
│   ├── README.md                              # Analytics module readme
│   ├── requirements.txt                       # pandas, numpy, scipy, groq, pydantic, pytest
│   ├── ai/
│   │   ├── groq_client.py                     # [STUB] Groq API client structure (returns mock data)
│   │   └── prompts.py                         # Marketing prompt template for Groq
│   ├── kpi/
│   │   └── metrics.py                         # ROAS, CPA, CPC, CTR, Conversion Rate calculation
│   ├── performance/
│   │   └── ranking.py                         # Top-N & Bottom-N campaign ranking by ROAS
│   ├── preprocessing/
│   │   ├── cleaner.py                         # Header strip/lowercase & null value fill
│   │   ├── normalizer.py                      # Data type casting via pd.to_numeric
│   │   └── validators.py                      # DataFrame column validation
│   ├── schemas/
│   │   └── result_schema.py                   # Pydantic AnalyticsOutput model
│   ├── trends/
│   │   └── customer_trends.py                 # Group-by channel aggregation
│   └── tests/                                 # [STUBS] Placeholder unit tests (assert True)
│       ├── test_ai.py
│       ├── test_metrics.py
│       ├── test_preprocessing.py
│       ├── test_ranking.py
│       └── test_trends.py
│
└── frontend/                                  # React (Vite) Application (Apeksha C Rao)
    ├── .env.example                           # Frontend VITE_API_BASE_URL
    ├── .gitignore                             # Frontend gitignore
    ├── index.html                             # HTML shell
    ├── package.json                           # Dependencies (React 18, Vite 5)
    ├── README.md                              # Frontend setup documentation
    └── src/
        ├── App.jsx                            # App layout wrapper (Navbar + Dashboard)
        ├── main.jsx                           # DOM mounting
        ├── index.css                          # CSS design system & layout styling
        ├── api/
        │   ├── client.js                      # Fetch wrapper with Bearer token header
        │   ├── authApi.js                     # Login & Register endpoints
        │   ├── uploadApi.js                   # Dataset upload & listing endpoints
        │   └── resultsApi.js                  # Analysis & KPI endpoints
        ├── components/
        │   ├── common/
        │   │   ├── ErrorMessage.jsx           # Error alert box
        │   │   ├── Loader.jsx                 # Spinner
        │   │   ├── Navbar.jsx                 # Header bar with user state & logout
        │   │   └── ProtectedRoute.jsx         # Auth guard wrapper
        │   ├── dashboard/
        │   │   ├── AiRecommendations.jsx      # Recommendations card list
        │   │   ├── CampaignRanking.jsx        # Top / bottom campaign tables
        │   │   ├── KpiCards.jsx               # Spend, Revenue, ROAS stat cards
        │   │   ├── PerformanceChart.jsx       # [PLACEHOLDER] Chart visualization placeholder
        │   │   └── TrendCharts.jsx            # [PLACEHOLDER] Trend visualization placeholder
        │   └── upload/
        │       ├── FileDropzone.jsx           # Drag-and-drop file uploader
        │       ├── UploadProgress.jsx         # Progress bar
        │       └── ValidationErrors.jsx       # CSV error display
        ├── hooks/
        │   ├── useAuth.js                     # Token & current user state hook
        │   └── useAnalysis.js                 # Dataset analysis fetcher hook
        ├── pages/
        │   ├── Dashboard.jsx                  # Dashboard overview page
        │   ├── Login.jsx                      # User login form
        │   ├── Register.jsx                   # Registration form
        │   └── Upload.jsx                     # File upload page
        ├── types/
        │   └── analysis.js                    # JSDoc type contracts
        └── utils/
            ├── constants.js                   # Application constants
            ├── formatters.js                  # Currency, ROAS, and percentage formatters
            └── validation.js                  # Form validation helpers
```

---

## 4. Subsystem-by-Subsystem Technical Audit

### 4.1 Backend (`backend/`)
- **Status:** **Feature-Rich & Tested**
- **Authentication**:
  - Uses `passlib[bcrypt]` for secure password hashing and `python-jose` for JWT generation and verification.
  - Endpoints: `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `GET /api/v1/auth/me`.
  - Ownership validation: Ensures users can only access datasets and campaigns they own.
- **Upload & Dataset Ingestion**:
  - Validates CSV file extension and mandatory columns (`campaign_name`, `channel`, `spend`, `revenue`).
  - Saves file under `backend/uploads/{uuid}.csv`.
  - Creates a `Dataset` row (`status="PENDING"`).
  - Uses `CampaignService.import_campaigns` to parse rows and bulk insert into PostgreSQL `campaigns` table.
  - Endpoints: `POST /api/v1/uploads/`, `GET /api/v1/uploads/`, `GET /api/v1/uploads/{dataset_id}/status`, `GET /api/v1/uploads/{dataset_id}/campaigns`.
- **Results API & Gaps**:
  - `AnalysisService` in `backend/app/services/analysis_service.py` currently returns hardcoded dummy values:
    ```python
    "kpis": {"total_spend": 10000, "total_revenue": 35000, "overall_roas": 3.5}
    ```
  - It does not yet query campaign records from the database, convert them to a DataFrame, or invoke the `analytics/` pipeline.
  - It does not persist calculated outputs into the `analysis_results` table.

### 4.2 Database & Migrations (`database/`)
- **Status:** **Complete & Aligned**
- Master schema (`schema.sql`) and migrations (`001` through `005`) define:
  1. `users`: UUID PK, unique email, hashed_password, full_name, is_active, timestamps.
  2. `datasets`: UUID PK, FK to `users(id)` ON DELETE CASCADE, filename, file_path, status, row_count.
  3. `campaigns`: UUID PK, FK to `datasets(id)` ON DELETE CASCADE, impressions, clicks, spend, conversions, revenue.
  4. `analysis_results`: UUID PK, FK to `datasets(id)` ON DELETE CASCADE, JSONB fields (`kpis`, `rankings`, `trends`, `ai_recommendations`).
  5. `application_logs`: UUID PK, level, message, context, timestamp.
- Seed data (`seed/sample_campaign_data.csv`) is provided for testing.

### 4.3 Analytics & AI Engine (`analytics/`)
- **Status:** **Foundation Laid; Needs Implementation & Real Testing**
- **Implemented Functions**:
  - `clean_dataset(df)`: Column normalization and filling nulls with zero.
  - `normalize_metrics(df)`: Explicit conversion of metrics (`impressions`, `clicks`, `spend`, `conversions`, `revenue`) to numeric.
  - `validate_dataset(df)`: Checks presence of required columns.
  - `calculate_kpis(df)`: Calculates total spend, total revenue, ROAS, CTR, CPC, CPA, conversion rate.
  - `rank_campaigns(df, top_n)`: Groups by campaign, computes ROAS, returns top and bottom campaigns.
  - `analyze_trends(df)`: Groups metrics by channel.
- **Unfinished / Mock Components**:
  - `GroqClient.generate_recommendations`: Currently returns static mock dicts without calling `groq.Groq` or evaluating the prompt template.
  - All tests in `analytics/tests/` (`test_ai.py`, `test_metrics.py`, `test_preprocessing.py`, `test_ranking.py`, `test_trends.py`) contain `assert True` placeholder stubs.
  - No orchestrator function currently exists to run the end-to-end data pipeline from a single entry point.

### 4.4 Frontend UI (`frontend/`)
- **Status:** **Scaffolding Complete; Routing & Chart Visualizations Pending**
- **Implemented**:
  - Clean CSS layout and responsive baseline in `index.css`.
  - Authentication forms (`LoginForm.jsx`, `RegisterForm.jsx`).
  - Drag-and-drop CSV upload dropzone with validation error alerts.
  - Dashboard component layout with KPI metric cards, campaign ranking table, and recommendation cards.
  - Centralized API client (`api/client.js`) handling token storage in `localStorage` and request headers.
- **Pending / Incomplete**:
  - `App.jsx` renders `<Dashboard />` unconditionally without client-side routing (`react-router-dom`).
  - `Dashboard.jsx` calls `useAnalysis()` without passing a `datasetId`.
  - Chart components (`PerformanceChart.jsx`, `TrendCharts.jsx`) display placeholder `<div>` blocks; no charting library (such as Chart.js, Recharts, or ApexCharts) is installed in `package.json`.

### 4.5 System Documentation (`docs/`)
- **Status:** **Clear & Well-Defined**
- `API_CONTRACT.md`: Specifies request/response models for Auth, Uploads, and Results.
- `ARCHITECTURE.md`: Displays component interaction flow.
- `DATA_DICTIONARY.md`: Specifies required vs optional columns and types.
- `INTEGRATION.md`: Outlines inter-service communication standards.

### 4.6 DevOps & Infrastructure
- `docker-compose.yml` configures:
  - `db`: PostgreSQL 15 on port `5432:5432` with volume mount and auto-init using `schema.sql`.
  - `backend`: Exposes port `8000:8000`.
  - `frontend`: Exposes port `3000:3000`.
- **Finding:** Neither `backend/Dockerfile` nor `frontend/Dockerfile` currently exists. Running `docker-compose up` will fail until these Dockerfiles are created.

---

## 5. Cross-Cutting Integration & Gap Analysis

```
[ Frontend: React Dashboard ]
            │ (1) Sends CSV
            ▼
[ Backend: FastAPI /uploads/ ] ──── (2) Stores ────► [ PostgreSQL (campaigns) ]
            │
            │ ⚠️ GAP 1: Backend results API does NOT call Analytics Engine
            ▼
[ Analytics Engine (Pandas + Groq) ]
    ├── Data Cleaning & Validation  (Ready)
    ├── KPI & Ranking Calculations  (Ready)
    ├── Channel Trends              (Ready)
    └── ⚠️ GAP 2: Groq AI Client    (Returns mock data; needs live API key & client call)
            │
            │ ⚠️ GAP 3: Analysis results not saved to PostgreSQL `analysis_results`
            ▼
[ Backend: FastAPI /results/{id} ]  (Currently returns static hardcoded JSON)
            │
            │ ⚠️ GAP 4: Frontend calls useAnalysis() without dataset_id; charts are placeholders
            ▼
[ Frontend Dashboard Displays ]
```

---

## 6. Roadmap & Immediate Action Plan for `analytics` Branch

As lead for the **Analytics & AI track (Vishal S Naik)**, here is the prioritized implementation checklist for this branch:

### Step 1: Real Groq AI Client Implementation
- In `analytics/ai/groq_client.py`:
  - Initialize the official `Groq(api_key=...)` client.
  - Construct prompt using `analytics/ai/prompts.py`.
  - Invoke `client.chat.completions.create` with a model like `llama-3.3-70b-versatile` or `mixtral-8x7b-32768`.
  - Add robust error handling (fallback to rule-based recommendations if `GROQ_API_KEY` is missing or the API call fails).
  - Enforce structured JSON output matching `AnalyticsOutput`.

### Step 2: Unified Analytics Pipeline Orchestrator
- Create a primary entry function (e.g. `analytics/pipeline.py` or `analytics/__init__.py:run_analysis`):
  ```python
  def run_marketing_analysis(df: pd.DataFrame, groq_api_key: str = None) -> dict:
      # 1. clean_dataset
      # 2. normalize_metrics
      # 3. calculate_kpis
      # 4. rank_campaigns
      # 5. analyze_trends
      # 6. groq_client.generate_recommendations
      # Return combined dictionary matching AnalysisResult model
  ```

### Step 3: Backend Bridge Integration
- In `backend/app/services/analysis_service.py`:
  - Fetch campaign rows from the database for `dataset_id`.
  - Convert rows into a Pandas DataFrame.
  - Execute `run_marketing_analysis(df)`.
  - Persist the calculated metrics into the `analysis_results` table in PostgreSQL.
  - Return the real calculated metrics in `GET /api/v1/results/{dataset_id}`.

### Step 4: Comprehensive Unit Tests
- Replace placeholder stubs in `analytics/tests/`:
  - `test_metrics.py`: Test zero divisions, zero clicks, high ROAS calculations.
  - `test_preprocessing.py`: Verify messy headers, nulls, and negative values.
  - `test_ranking.py`: Verify tie-breaks, single campaign, and empty inputs.
  - `test_trends.py`: Verify multi-channel aggregation.
  - `test_ai.py`: Test prompt generation and mock Groq API responses.

---
*Report generated and validated against local branch `analytics`.*
