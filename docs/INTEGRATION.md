# Integration Guide

## Request and data flow

The React frontend calls the FastAPI service under `/api/v1` (by default,
`http://localhost:8000/api/v1`; override with `VITE_API_BASE_URL`). FastAPI
routes delegate to auth, storage, and analysis services. Those services use
SQLAlchemy to persist users, datasets, imported campaigns, and analysis results
in PostgreSQL, configured by `DATABASE_URL`.

For uploads, the frontend builds a `FormData` body with a `file` part and sends
`POST /uploads/`. The request must carry the user's bearer token. The backend
accepts CSV files, validates and imports campaign rows, creates a dataset row,
and responds with `dataset_id`, `filename`, `status` (initially `PENDING`), and
`message`. The dataset ID identifies subsequent dataset and result requests.
The frontend upload helper returns this response; the current upload page does
not retain or route on the returned ID. A client that needs analysis should
retain `dataset_id` and call `GET /results/{dataset_id}`. The service computes
and persists analysis on the first request, then adapts stored analytics for
the same response shape on later requests. `GET /uploads/{dataset_id}/status`
reads the persisted status; the code does not run a background processing job
that advances it.

## Authentication

Login returns an `access_token`. The frontend API client reads the token from
`localStorage` and, when present, sends:

```http
Authorization: Bearer <access_token>
```

The upload helper adds the same header to the multipart request. Protected
uploads, dataset, campaign, and results routes reject missing or invalid
credentials with `401`. Dataset-specific requests also enforce ownership:
unknown IDs return `404`, while another user's dataset returns `403`.

## Dashboard response fields

`GET /results/{dataset_id}` returns `dataset_id`, `kpis`, `performance`,
`topCampaigns`, `bottomCampaigns`, `trends`, and `recommendations`. The frontend
dashboard contract uses camelCase metric and campaign fields. KPI names are
`totalSpend`, `totalRevenue`, `overallRoas`, `avgConversionRate`, and `avgCpa`.
Campaign points use `campaignName`, `spend`, `revenue`, and `roas`; trend points
use `date`, `spend`, `revenue`, and `conversions`. Revenue and dependent ROAS
may be `null` when source revenue is unknown. The separate
`GET /results/{dataset_id}/kpis` returns the KPI object directly, with the same
camelCase fields.

Recommendations are returned in the `recommendations` array. The current
`GroqClient.generate_recommendations` implementation returns two fixed
recommendation objects and does not make a live Groq API request; the backend
stores these with the analysis result.
