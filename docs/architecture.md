# SmartRetail — System Architecture & Component Design

## 1. High-Level Architecture

SmartRetail implements a decoupled, modern 3-tier web architecture:

```mermaid
graph TD
    Client["Client Browser (React 18 + Vite SPA)"]
    API["Flask REST API Server (Python 3.10+ / Gunicorn)"]
    DB[("MySQL Database Server")]
    ML["Scikit-Learn ML Forecasting Pipeline"]
    Intel["Inventory Intelligence & Reorder Engine"]

    Client -->|HTTPS REST JSON| API
    API -->|Thread-Safe Parameterized SQL| DB
    API -->|Features & Time-Series| ML
    ML -->|Multi-Step Predictions| API
    API -->|Forecasts + Historical Demand| Intel
    Intel -->|Explainable Recommendations| Client
```

---

## 2. Frontend Architecture (React SPA)

The frontend is structured into modular layers:

- **Routing & State**: Single-page navigation managing `/login`, `/dashboard`, `/inventory`, `/sales`, `/analytics`, `/forecast`, `/monitoring`, and `/settings`.
- **UI Components**:
  - `components/layout/`: `AppLayout`, `Sidebar`, `Header`
  - `components/common/`: `KpiCard`, `Badge`, `Modal`
  - `pages/`: Dedicated business views
- **API Client Service (`src/services/api.js`)**:
  - Centralized abstraction utilizing `fetchApi`
  - Switches automatically between local `/api` proxy and cloud HTTPS base URL (`VITE_API_BASE_URL`)
  - Intercepts and parses backend error responses without crashing the UI

---

## 3. Backend Architecture (Flask REST API)

The backend follows the Application Factory pattern:

```
backend/
├── app/
│   ├── routes/                # REST API Blueprints
│   │   ├── health.py          # /api/health, /api/health/db
│   │   ├── products.py        # /api/products CRUD
│   │   ├── inventory.py       # /api/inventory management
│   │   ├── sales.py           # /api/sales atomic POS
│   │   ├── analytics.py       # /api/analytics KPIs & trends
│   │   ├── forecast.py        # /api/forecast generation & retrieval
│   │   ├── recommendations.py # /api/recommendations & intelligence
│   │   └── monitoring.py      # /api/monitoring accuracy tracking
│   ├── services/              # Business Logic & Algorithms
│   │   ├── forecast_service.py
│   │   ├── inventory_intelligence_service.py
│   │   └── monitoring_service.py
│   ├── db.py                  # PyMySQL connection pool & teardown
│   └── __init__.py            # Flask app factory with CORS & error handlers
├── ml/                        # Machine Learning Pipeline
│   ├── data_loader.py         # Daily sales aggregation
│   ├── features.py            # Lag and rolling feature engineering
│   ├── models.py              # Candidate regressors
│   ├── train.py               # Temporal validation & artifact generation
│   └── saved_models/          # Pre-trained .joblib artifacts
├── database/                  # Schema, Seed & Init Scripts
└── wsgi.py                    # Gunicorn production entry point
```

---

## 4. Machine Learning & Forecasting Workflow

```mermaid
flowchart TD
    A[Raw Sales Records in MySQL] --> B[Daily Product Demand Aggregation]
    B --> C[Zero-Demand Grid Imputation]
    C --> D[Feature Engineering: Lags 1, 7, 14, 28 + Rolling Means]
    D --> E[Chronological Train / Validation Split]
    E --> F[Baseline Model: Naive / Moving Average]
    E --> G[ML Candidates: Ridge, Random Forest]
    G --> H[Model Evaluation on Validation Set]
    H --> I[Save Selected Model Artifact: demand_forecast_model.joblib]
    I --> J[Recursive Multi-Step Inference for T+1..T+Horizon]
    J --> K[Persist Predictions into forecasts Table]
```

---

## 5. Inventory Intelligence & Explainability Engine

```mermaid
flowchart TD
    FC[Stored ML Forecast] --> RE[Reorder Engine]
    INV[Current Inventory Stock] --> RE
    HIST[Historical Daily Sales] --> SS[Safety Stock Calculation]
    
    SS -->|Configured or Volatility Fallback| RE
    RE -->|Required = Forecast + Safety Stock| REQ[Required Stock]
    REQ -->|Reorder = max 0, Required - Current| REC[Recommended Quantity]
    REC --> EXP[Deterministic Mathematical Breakdown]
    EXP --> UI[Interactive Why? Modal on Frontend]
```

---

## 6. Database Relationship Architecture

```mermaid
erDiagram
    STORES ||--o{ USERS : employs
    STORES ||--o{ PRODUCTS : catalogs
    SUPPLIERS ||--o{ PRODUCTS : supplies
    PRODUCTS ||--|| INVENTORY : tracks
    STORES ||--o{ SALES : processes
    SALES ||--|{ SALE_ITEMS : contains
    PRODUCTS ||--o{ SALE_ITEMS : references
    PRODUCTS ||--o{ FORECASTS : predicts
    PRODUCTS ||--o{ REORDER_RECOMMENDATIONS : generates
```
