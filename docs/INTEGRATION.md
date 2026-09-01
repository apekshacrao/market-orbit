# Integration Guide

## Component Communication

1. **Frontend to Backend**:
   - HTTP/REST communication via Vite React client (`frontend/src/api/client.js`) targeting `/api/v1`.
   - JWT tokens passed in `Authorization: Bearer <token>` header.

2. **Backend to Analytics**:
   - Modular Python service invocation calling `analytics.preprocessing`, `analytics.kpi`, and `analytics.ai.groq_client`.

3. **Backend to Database**:
   - SQLAlchemy ORM interfacing with PostgreSQL schema defined in `database/schema.sql`.
