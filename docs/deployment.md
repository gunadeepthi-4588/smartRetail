# SmartRetail — Cloud Deployment & Production Setup Guide

## 1. Architecture Overview

SmartRetail is designed as a modular 3-tier cloud application:

```
┌─────────────────────────────────────────────────────────┐
│                 React + Vite Frontend                   │
│   (Hosted on Vercel / Netlify / Static Cloud Storage)   │
└───────────────────────────┬─────────────────────────────┘
                            │ HTTPS REST API Requests
                            ▼
┌─────────────────────────────────────────────────────────┐
│                 Flask WSGI Backend                      │
│        (Hosted on Render / Railway / Fly.io)            │
│   - Python 3.10+ / Gunicorn WSGI Server                 │
│   - REST API Endpoints (/api/...)                       │
│   - ML Demand Forecasting Engine (Scikit-Learn)         │
│   - Inventory Intelligence & Explainable Reorders       │
│   - Forecast Accuracy Monitoring                        │
└───────────────────────────┬─────────────────────────────┘
                            │ Parameterized MySQL Connection
                            ▼
┌─────────────────────────────────────────────────────────┐
│                 Managed MySQL Database                  │
│       (Aiven / PlanetScale / Railway / Render DB)       │
│   - 9 Core Relational Tables                            │
│   - Foreign Key Integrity & Atomic ACID Transactions    │
└─────────────────────────────────────────────────────────┘
```

> **Security Guardrail:** The React frontend connects exclusively via the Flask REST API over HTTPS. It **never** connects directly to MySQL.

---

## 2. Cloud Service Recommendations

SmartRetail is optimized for lightweight, low-cost/student-tier managed cloud platforms:

| Tier | Recommended Providers | Role / Specs |
| :--- | :--- | :--- |
| **Frontend** | **Vercel** / **Netlify** / **Cloudflare Pages** | Static single-page React bundle hosting with CDN distribution. |
| **Backend** | **Render** / **Railway** / **Fly.io** | Managed Python application web service running `gunicorn`. |
| **Database** | **Aiven MySQL** / **Railway MySQL** / **Render MySQL** | Managed MySQL 8.0+ instance with SSL and automated backups. |

---

## 3. Environment Variables Reference

### Backend Environment Variables (`backend/.env` or Cloud Dashboard)

| Variable | Required | Example Value | Description |
| :--- | :---: | :--- | :--- |
| `FLASK_ENV` | Yes | `production` | Enables production mode optimizations and disables debug reloading. |
| `FLASK_DEBUG` | Yes | `0` | Disables debug mode and suppresses stack traces on errors. |
| `PORT` | Yes | `5000` (or injected by platform) | Port for the WSGI server to listen on. |
| `SECRET_KEY` | Yes | `f8b29c0a1e3d4...` | Cryptographic key for session/security protection. |
| `DB_HOST` | Yes | `mysql-xxxx.aivencloud.com` | Hostname of the managed cloud MySQL database. |
| `DB_PORT` | Yes | `3306` | Port of the cloud MySQL server. |
| `DB_USER` | Yes | `avnadmin` | MySQL database user. |
| `DB_PASSWORD` | Yes | `YourSecurePassword` | MySQL database user password. |
| `DB_NAME` | Yes | `smart_retail_db` | Name of the SmartRetail database. |
| `CORS_ORIGINS` | Yes | `https://smartretail.vercel.app` | Comma-separated list of authorized frontend origins. |
| `DEFAULT_CURRENCY` | No | `INR` | Store default currency code. |
| `DEFAULT_CURRENCY_SYMBOL` | No | `₹` | Store default currency symbol. |

### Frontend Environment Variables (`frontend/.env` or Cloud Dashboard)

| Variable | Required | Example Value | Description |
| :--- | :---: | :--- | :--- |
| `VITE_API_BASE_URL` | Yes | `https://smartretail-api.onrender.com/api` | Full HTTPS base URL to the deployed Flask backend API. |
| `VITE_APP_NAME` | No | `SmartRetail` | Application display brand name. |
| `VITE_DEFAULT_CURRENCY_SYMBOL`| No | `₹` | Currency symbol for UI formatting. |

---

## 4. Production Database Setup & Migration

Follow this sequential procedure to provision and seed the production database:

1. **Create Managed MySQL Database**:
   Create a new MySQL database instance named `smart_retail_db` on your chosen cloud provider (e.g., Aiven or Railway).
2. **Execute Database Schema**:
   Run `backend/database/schema.sql` against the database to create all 9 tables, indexes, and foreign key constraints:
   ```bash
   mysql -h <DB_HOST> -P <DB_PORT> -u <DB_USER> -p <DB_NAME> < backend/database/schema.sql
   ```
3. **Execute Initial Seed Data (Optional for Demo)**:
   Run `backend/database/seed.sql` to populate sample suppliers, products, inventory records, and historical sales transactions:
   ```bash
   mysql -h <DB_HOST> -P <DB_PORT> -u <DB_USER> -p <DB_NAME> < backend/database/seed.sql
   ```
4. **Automated Setup Alternative**:
   Configure `backend/.env` with your cloud database credentials and run the built-in database setup script:
   ```bash
   python backend/database/init_db.py
   ```

---

## 5. Machine Learning Model Artifact Deployment

- **Model Location**: `backend/ml/saved_models/demand_forecast_model.joblib` (~181 KB)
- **Metadata Location**: `backend/ml/saved_models/model_metadata.json`
- **Dynamic Path Resolution**: `backend/app/services/forecast_service.py` dynamically resolves model paths relative to the Python module root:
  ```python
  base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
  saved_dir = os.path.join(base_dir, "ml", "saved_models")
  model_path = os.path.join(saved_dir, "demand_forecast_model.joblib")
  ```
- **Portability**: Because the pre-trained Random Forest model artifact is committed directly to the repository, the cloud backend loads predictions immediately upon startup without requiring runtime training.

---

## 6. Backend Deployment (e.g. Render / Railway)

1. Connect your Git repository to **Render** or **Railway**.
2. Select **Web Service** with runtime **Python 3**.
3. Configure the build and start commands:
   - **Root Directory**: `backend` (or repository root with path specified)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120`
4. Add all environment variables from Section 3 in the platform dashboard.
5. Deploy and verify the health checks.

---

## 7. Frontend Deployment (e.g. Vercel / Netlify)

1. Connect your Git repository to **Vercel** or **Netlify**.
2. Configure project settings:
   - **Root Directory**: `frontend`
   - **Framework Preset**: `Vite`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
3. Add environment variable:
   - `VITE_API_BASE_URL`: `https://your-deployed-backend.onrender.com/api`
4. Deploy the frontend application.

---

## 8. Verification & Health Checks

After deployment, verify the operational status of all tiers:

1. **Backend Health**:
   ```bash
   curl -i https://your-backend-domain/api/health
   ```
   *Expected: HTTP 200 `{"status": "healthy", "service": "smartretail-backend"}`*

2. **Database Health**:
   ```bash
   curl -i https://your-backend-domain/api/health/db
   ```
   *Expected: HTTP 200 `{"status": "connected", "database_name": "smart_retail_db", "ping": true}`*

3. **Products Endpoint**:
   ```bash
   curl -i https://your-backend-domain/api/products
   ```
   *Expected: HTTP 200 with JSON product array.*

4. **Frontend Navigation**:
   Open your deployed frontend URL in a browser and test all views:
   - `/dashboard`: Financial KPIs and inventory health summaries
   - `/inventory`: Product stock management and explainable recommendation modals
   - `/sales`: Real-time POS checkout with atomic inventory reduction
   - `/analytics`: Revenue, gross profit, and category performance charts
   - `/forecast`: 7-day and 30-day demand prediction generation
   - `/monitoring`: MAE, RMSE, WAPE %, Bias metrics, and actual vs predicted charts
   - `/settings`: Store profile and system diagnostics

---

## 9. Common Deployment Issues & Troubleshooting

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| **CORS Error (`No 'Access-Control-Allow-Origin' header`)** | `CORS_ORIGINS` on backend does not match the deployed frontend URL. | Add your exact frontend URL (including `https://`, without trailing slash) to `CORS_ORIGINS` in the backend environment variables. |
| **Database Connection Refused / Timeout** | Cloud MySQL IP whitelist or incorrect `DB_HOST`/`DB_PORT`. | Ensure the managed database allows connections from your backend IP range (or `0.0.0.0/0` with SSL enabled). |
| **Forecast Generation 500 Error** | Model artifact file missing or invalid permissions. | Ensure `backend/ml/saved_models/demand_forecast_model.joblib` was pushed to Git and exists in the deployment bundle. |
| **SPA 404 Error on Page Refresh** | Static hosting web server does not route subpaths to `index.html`. | Add a rewrite rule in `vercel.json` or `_redirects` (`/* /index.html 200`). |
