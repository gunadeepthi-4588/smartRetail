# SmartRetail — End-to-End Technical Data Flow

This document details the step-by-step data, security, and algorithmic flow across the entire SmartRetail application.

---

## 1. Complete Architecture Flow Diagram

```mermaid
flowchart TD
    A[Store Owner / Cashier] -->|1. Interactive Web Action| B[React Frontend SPA]
    B -->|2. HTTPS REST Request with JSON Payload| C[Flask REST API Server]
    C -->|3. PBKDF2 Password / Session Validation| D{Authenticated?}
    
    D -->|No| E[Return HTTP 401 / Redirect to Login]
    D -->|Yes| F[PyMySQL Connection Pool]
    
    F -->|4. Parameterized SQL Queries & ACID Transactions| G[(MySQL 8.0 Database)]
    G -->|5. Historical Sales & Inventory Stock Levels| H[Data Ingestion Service]
    
    H -->|6. Zero-Demand Grid & Daily Aggregation| I[Pandas / NumPy Feature Pipeline]
    I -->|7. Lag Features: t-1, t-7, t-14, t-28 & Rolling Means| J[Pre-trained Scikit-Learn Model]
    
    J -->|8. Multi-Step Recursive Future Demand Predictions| K[Forecast Storage in forecasts Table]
    K -->|9. Combine Forecast + Supplier Lead Time + Volatility| L[Inventory Intelligence Engine]
    
    L -->|10. Compute Risk Levels & Order Quantity: Q = max 0, Req - Curr| M[Reorder Recommendation Engine]
    M -->|11. Generate Step-by-Step Arithmetic Breakdown| N[Deterministic Explainability Layer]
    
    N -->|12. Return Consolidated JSON Response| C
    C -->|13. HTTP 200 OK with Data Payloads| B
    B -->|14. Render Interactive Dashboard, Charts & 'Why?' Modal| A
```

---

## 2. Detailed Technical Execution Steps

| Step | Layer | Component / File | Description |
| :--- | :--- | :--- | :--- |
| **1** | **User Interface** | `frontend/src/pages/` | Store owner interacts with Login, POS, Dashboard, Inventory, or Forecast views. |
| **2** | **API Client** | `frontend/src/services/api.js` | Dispatches structured `fetch` calls to backend endpoint routes (`/api/*`). |
| **3** | **Auth Guard** | `backend/app/routes/auth.py` | Validates credentials via `werkzeug.security.check_password_hash` and establishes session context. |
| **4** | **Database Layer** | `backend/app/db.py` | Executes parameterized SQL statements with thread-safe connection pooling and rollback protection. |
| **5** | **Storage Engine** | `MySQL 8.0 / InnoDB` | Stores records across 9 relational tables with foreign key referential integrity. |
| **6** | **ML Ingestion** | `backend/ml/data_loader.py` | Queries historical sales, infills zero-sales days, and produces daily time series. |
| **7** | **Feature Engine** | `backend/ml/features.py` | Generates 15 lag and rolling statistical features with zero forward data leakage. |
| **8** | **Model Inference**| `backend/app/services/forecast_service.py` | Runs pre-trained Random Forest model (`demand_forecast_model.joblib`) for 7 or 30 future days. |
| **9** | **Forecast Store** | `forecasts` table | Persists predictions with `actual_demand = NULL` for future reconciliation. |
| **10**| **Risk & Intelligence**| `backend/app/services/inventory_intelligence_service.py` | Computes lead-time demand, safety stock, and identifies stockout/overstock conditions. |
| **11**| **Reorder Math** | `reorder_recommendations` | Calculates recommended purchase quantity $Q = \max(0, \text{Required} - \text{Current})$. |
| **12**| **Explainability**| `inventory_intelligence_service.py` | Constructs deterministic human-readable mathematical breakdown. |
| **13**| **REST Response** | Flask Blueprints | Serializes response payload into JSON with appropriate HTTP status codes. |
| **14**| **Visual Render** | React + Chart.js | Dynamically updates KPIs, interactive charts, data tables, and explainability modals. |
