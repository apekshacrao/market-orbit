# API Contract

The routes below are mounted under `/api/v1`. Response status codes are the
current FastAPI defaults unless noted. Examples use illustrative values; IDs,
computed metrics, and recommendation content are runtime data, not fixed
guarantees.

## Authentication

All request bodies are JSON. `email` must be a valid email address; registration
`name` is optional and may be `null`.

### `POST /auth/register`

Request: `email: string`, `password: string`, and optional `name: string | null`.
Returns `200 OK` with a `UserResponse`:

```json
{
  "id": "illustrative-user-id",
  "email": "asha@example.com",
  "name": "Asha Rao",
  "is_active": true
}
```

An already registered email returns `409 Conflict` with `{"detail":"Email already registered"}`.

### `POST /auth/login`

Request: `email: string`, `password: string`. Returns `200 OK`:

```json
{
  "access_token": "illustrative-jwt",
  "token_type": "bearer",
  "user": {
    "id": "illustrative-user-id",
    "name": "Asha Rao",
    "email": "asha@example.com"
  }
}
```

Unknown email or incorrect password returns `401 Unauthorized` with
`{"detail":"Invalid email or password"}`.

### `GET /auth/me`

Requires `Authorization: Bearer <access_token>`. Returns `200 OK` with the
registration user shape (`id`, `email`, nullable `name`, `is_active`). Invalid,
missing, or inactive-user credentials return `401 Unauthorized`.

### Bearer authentication

Uploads, dataset, campaign, and results routes require the bearer token issued
by login. Send it as `Authorization: Bearer <access_token>`. Missing or invalid
credentials return `401 Unauthorized` (invalid credentials include
`WWW-Authenticate: Bearer`). Dataset-specific routes return `404 Not Found`
(`{"detail":"Dataset not found"}`) for an unknown ID and `403 Forbidden`
(`{"detail":"You do not have access to this dataset"}`) when the dataset
belongs to another user.

## Uploads and datasets

### `POST /uploads/`

Requires authentication. Send one `file` part as `multipart/form-data`; only a
`.csv` filename is accepted. A successful upload validates/imports the CSV and
returns `200 OK`:

```json
{
  "dataset_id": "illustrative-dataset-id",
  "filename": "campaigns.csv",
  "status": "PENDING",
  "message": "File uploaded successfully"
}
```

An unsupported extension returns `400 Bad Request`. A CSV failing format
validation returns `422 Unprocessable Entity` with `detail` containing
`message: "Invalid CSV file"` and an `errors` list.

### `GET /uploads/`

Requires authentication. Returns `200 OK` with the current user's datasets,
newest first. Each item has `id: string`, `filename: string`, `status: string`,
and `row_count: integer`; an empty list is valid.

### `GET /uploads/{dataset_id}/status`

Requires authentication. Returns `200 OK`, for example
`{"dataset_id":"illustrative-dataset-id","status":"PENDING"}`. The status
is the stored dataset status; the code does not constrain it to a fixed enum.

### `GET /uploads/{dataset_id}/campaigns`

Requires authentication. Returns `200 OK` with the dataset's campaigns in
creation order. Each campaign has `id`, `campaign_name`, `channel`,
`impressions`, `clicks`, `spend`, and `conversions`; `revenue` is nullable and
`date`, `location`, `age_group`, `customer_segment`, and `device` are optional
nullable fields. Numeric fields are numbers (integer counts, floating spend
and revenue); `date`, when present, is an ISO date string.

CSV rows may omit revenue; in that case revenue is stored as unknown (`null`),
not as zero. An explicitly supplied zero remains zero. Analysis aggregate
revenue fields can therefore be `null` when any included source revenue is
unknown.

## Results

### `GET /results/{dataset_id}`

Requires authentication and dataset access. Returns `200 OK` with the aggregate
dashboard contract:

```json
{
  "dataset_id": "illustrative-dataset-id",
  "kpis": {
    "totalSpend": 1000.0,
    "totalRevenue": 2500.0,
    "overallRoas": 2.5,
    "avgConversionRate": 4.0,
    "avgCpa": 25.0
  },
  "performance": [
    {"campaignName": "Campaign A", "spend": 1000.0, "revenue": 2500.0, "roas": 2.5}
  ],
  "topCampaigns": [
    {"campaignName": "Campaign A", "spend": 1000.0, "revenue": 2500.0, "roas": 2.5}
  ],
  "bottomCampaigns": [
    {"campaignName": "Campaign B", "spend": 200.0, "revenue": null, "roas": null}
  ],
  "trends": [
    {"date": "2026-09-18", "spend": 1000.0, "revenue": 2500.0, "conversions": 40}
  ],
  "recommendations": []
}
```

The example values and array contents are illustrative. The schema requires
`dataset_id: string`; KPI fields `totalSpend: number`, `totalRevenue: number | null`,
`overallRoas: number | null`, `avgConversionRate: number | null`, and
`avgCpa: number | null`; and arrays `performance`, `topCampaigns`,
`bottomCampaigns`, `trends`, and `recommendations`. Each performance/ranking
point has `campaignName: string`, `spend: number`, `revenue: number | null`,
and `roas: number | null`. Each trend point has `date: string`, `spend: number`,
`revenue: number | null`, and `conversions: integer`. Recommendation entries
are objects (`Dict[str, Any]`); their keys are not constrained by this response
schema. Performance is grouped by campaign name. Trends include valid dated
campaign rows grouped by date and sorted ascending. Unknown revenue propagates
to a campaign/date aggregate as `null`; ROAS is `null` if revenue is unknown
(and for performance if spend is not positive).

### `GET /results/{dataset_id}/kpis`

This separate endpoint returns `200 OK` with the `KpiResponse` object directly,
not nested under `kpis`:

```json
{
  "totalSpend": 1000.0,
  "totalRevenue": 2500.0,
  "overallRoas": 2.5,
  "avgConversionRate": 4.0,
  "avgCpa": 25.0
}
```

The five fields use the same camelCase names and number/null types as the
aggregate endpoint's `kpis`. In particular, this route does not expose
snake_case keys such as `total_spend`.
