# System Architecture

```
[ Frontend (React + Vite) ]
          │
     HTTP / REST
          ▼
[ Backend API (FastAPI) ] ─── [ PostgreSQL Database ]
          │
          ▼
[ Analytics Engine ]
    ├── Preprocessing & Validation
    ├── KPI & Metrics Engine
    ├── Performance Ranking
    ├── Trend Analyzer
    └── Groq AI Insights Engine
```
