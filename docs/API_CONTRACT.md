# API Contract Specification

## Authentication Endpoints

### `POST /api/v1/auth/register`
- Request: `{ "email": "string", "password": "string", "name": "string" }`
- Response: `201 Created` -> `{ "id": "string", "email": "string", "name": "string", "is_active": true }`

### `POST /api/v1/auth/login`
- Request: `{ "email": "string", "password": "string" }`
- Response: `200 OK` -> `{ "access_token": "string", "token_type": "bearer" }`

### `GET /api/v1/auth/me`
- Headers: `Authorization: Bearer <token>`
- Response: `200 OK` -> `{ "id": "string", "email": "string", "name": "string", "is_active": true }`

## Uploads Endpoints

### `POST /api/v1/uploads/`
- Request: `multipart/form-data` with `file`
- Response: `202 Accepted` -> `{ "dataset_id": "string", "filename": "string", "status": "PENDING", "message": "File uploaded" }`

### `GET /api/v1/uploads/{dataset_id}/status`
- Response: `200 OK` -> `{ "dataset_id": "string", "status": "PENDING|PROCESSING|COMPLETED|FAILED" }`

## Results Endpoints

### `GET /api/v1/results/{dataset_id}`
- Response: `200 OK` -> Full analysis results (KPIs, rankings, trends, recommendations)

### `GET /api/v1/results/{dataset_id}/kpis`
- Response: `200 OK` -> `{ "total_spend": 0.0, "total_revenue": 0.0, "overall_roas": 0.0, ... }`
