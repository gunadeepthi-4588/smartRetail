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
                            │ Parameterized MySQL Connection (with SSL)
                            ▼
┌─────────────────────────────────────────────────────────┐
│                 Managed MySQL Database                  │
│       (Aiven / TiDB / PlanetScale / Railway / Render)   │
│   - 9 Core Relational Tables                            │
│   - Real FreshRetailNet-50K Product & Sales History     │
│   - Foreign Key Integrity & Atomic ACID Transactions    │
└─────────────────────────────────────────────────────────┘
```

> **Security Guardrail:** The React frontend connects exclusively via the Flask REST API over HTTPS. It **never** connects directly to MySQL.

---

## 2. Cloud Service Recommendations

SmartRetail is optimized for lightweight, low-cost/student-tier managed cloud platforms:

| Tier | Recommended Providers | Role / Specs |
| :--- | :--- | :--- |
| **Frontend** | **Vercel** / **Netlify** / **Cloudflare Pages** | Static single-page React bundle hosting with global CDN. |
| **Backend** | **Render** / **Railway** / **Fly.io** | Managed Python application web service running `gunicorn`. |
| **Database** | **Aiven MySQL** / **TiDB Cloud** / **Railway MySQL** / **Render DB** | Managed MySQL 8.0+ instance with TLS/SSL encryption and automated backups. |

---

## 3. Environment Variables Reference

### Backend Environment Variables (`backend/.env` or Cloud Provider Dashboard)

| Variable | Required | Example Placeholder Value | Description |
| :--- | :---: | :--- | :--- |
| `FLASK_ENV` | Yes | `production` | Enables production mode optimizations and disables debug reloading. |
| `FLASK_DEBUG` | Yes | `0` | Disables debug mode and suppresses stack traces on errors. |
| `PORT` | Yes | `5000` (or injected by platform) | Port for the WSGI server to listen on. |
| `SECRET_KEY` | Yes | `your-cryptographic-secret-key-here` | Cryptographic key for session/security protection. |
| `DB_HOST` | Yes | `your-managed-mysql-host.example.com` | Hostname of the managed cloud MySQL database. |
| `DB_PORT` | Yes | `3306` (or provider port e.g. `24536`) | Port of the cloud MySQL server. |
| `DB_USER` | Yes | `your_db_username` | MySQL database user. |
| `DB_PASSWORD` | Yes | `your_db_password` | MySQL database user password. |
| `DB_NAME` | Yes | `smart_retail_db` (or `defaultdb`) | Name of the database provisioned on the cloud instance. |
| `DB_SSL_MODE` | Conditional | `REQUIRED` | SSL connection mode (required by Aiven, TiDB, AWS RDS). |
| `DB_SSL_CA` | Optional | `/path/to/ca.pem` | Path to custom SSL Certificate Authority bundle if required. |
| `CORS_ORIGINS` | Yes | `https://your-app.vercel.app,http://localhost:5173` | Comma-separated list of authorized frontend origins. |
| `DEFAULT_CURRENCY` | No | `INR` | Store default currency code. |
| `DEFAULT_CURRENCY_SYMBOL` | No | `₹` | Store default currency symbol. |
| `DEFAULT_SAFETY_STOCK_DAYS` | No | `7` | Default safety stock duration in days. |
| `DEFAULT_LEAD_TIME_DAYS` | No | `3` | Default supplier replenishment lead time. |

### Frontend Environment Variables (`frontend/.env` or Vercel Dashboard)

| Variable | Required | Example Placeholder Value | Description |
| :--- | :---: | :--- | :--- |
| `VITE_API_BASE_URL` | Yes | `https://your-backend-service.onrender.com/api` | Full HTTPS base URL to the deployed Flask backend API. |
| `VITE_APP_NAME` | No | `SmartRetail` | Application display brand name. |
| `VITE_DEFAULT_CURRENCY` | No | `INR` | Currency code for UI display. |
| `VITE_DEFAULT_CURRENCY_SYMBOL`| No | `₹` | Currency symbol for UI formatting. |

---

## 4. Fresh Cloud MySQL Database Setup & Initialization

Follow this step-by-step procedure to provision and seed a fresh managed cloud MySQL database:

### Step 1: Provision the Managed MySQL Instance
1. Create a MySQL 8.0+ instance on your chosen cloud provider (**Aiven**, **TiDB Cloud**, **Railway**, or **Render**).
2. Note your connection credentials from the cloud dashboard:
   - **Host** (`DB_HOST`)
   - **Port** (`DB_PORT`)
   - **User** (`DB_USER`)
   - **Password** (`DB_PASSWORD`)
   - **Database Name** (`DB_NAME`, e.g. `smart_retail_db` or `defaultdb`)
   - **SSL Requirements** (e.g. `DB_SSL_MODE=REQUIRED`)
3. Ensure the cloud provider's IP allowlist permits connections from your deployment IP or `0.0.0.0/0` (secured with strong password and TLS).

### Step 2: Set Environment Variables
In your local `backend/.env` (for initial provisioning) or directly in your cloud hosting dashboard:
```env
DB_HOST=your-managed-mysql-host.example.com
DB_PORT=3306
DB_USER=your_db_username
DB_PASSWORD=your_db_password
DB_NAME=smart_retail_db
DB_SSL_MODE=REQUIRED
```

### Step 3: Run the Database Initialization Script
Execute the single unified initialization and verification script:
```bash
python backend/database/init_db.py
```

#### What `init_db.py` Executes Automatically:
1. **Verifies Connectivity**: Establishes secure TLS/SSL connection to `DB_HOST:DB_PORT`.
2. **Applies Schema DDL (`schema.sql`)**: Creates the 9 core relational tables in proper dependency order:
   - `stores`
   - `users` (Store owner credentials)
   - `suppliers` (4 suppliers with lead times)
   - `products` (20 real products mapped from FreshRetailNet-50K)
   - `inventory` (Stock master, min/max/safety levels)
   - `sales` (97 daily POS receipts)
   - `sale_items` (1,910 real transaction items)
   - `forecasts` (Prediction records table)
   - `reorder_recommendations` (Explainable reorder recommendations table)
3. **Applies Seed Data (`seed.sql`)**: Populates the real FreshRetailNet-50K dataset (Store 18, 20 products across 8 categories, 97 consecutive days of sales).
4. **Runs Verification Checks**:
   - Table row counts
   - Product-Inventory joins
   - Financial totals (₹1,069,725.00 revenue, ₹328,630.00 gross profit, 30.72% margin)
   - Low-stock risk detection
   - Orphan records / referential integrity (0 orphan records)

### Step 4: (Optional) Re-ingesting Raw FreshRetailNet-50K Dataset
If you ever want to re-download or regenerate the dataset from scratch from Hugging Face:
```bash
python backend/database/import_freshretail.py
```
> **Note**: Raw dataset parquet files are stored in `data_raw/` and are strictly gitignored (`.gitignore`). They are **not** committed to Git or required for cloud deployment because `seed.sql` and model artifacts are pre-built and committed.

---

## 5. Machine Learning Model Artifacts

- **Model Artifact**: `backend/ml/saved_models/demand_forecast_model.joblib`
- **Model Metadata**: `backend/ml/saved_models/model_metadata.json`
- **Stockout Annotations**: `backend/ml/saved_models/stockout_annotations.json`
- **Portability**: The pre-trained time-series model artifact is committed to the repository. The cloud backend loads predictions immediately upon startup without requiring runtime training.
- **Retraining Pipeline**: If needed, run `python -m ml.train` from `backend/` to re-evaluate models on the latest dataset.

---

## 6. Backend Web Service Deployment (e.g. Render)

1. Connect your Git repository to **Render** (or **Railway** / **Fly.io**).
2. Create a new **Web Service** with runtime **Python 3**.
3. Configure settings:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120`
4. Add all environment variables from Section 3 in the Render dashboard.
5. Deploy and verify the health checks.

---

## 7. Frontend Deployment (e.g. Vercel)

1. Connect your Git repository to **Vercel** (or **Netlify**).
2. Configure project settings:
   - **Root Directory**: `frontend`
   - **Framework Preset**: `Vite`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
3. Add environment variable:
   - `VITE_API_BASE_URL`: `https://your-deployed-backend.onrender.com/api`
4. Deploy the frontend application.

---

## 8. Post-Deployment Verification & Health Checks

Verify operational status across all tiers using `curl`:

1. **Backend Service Health**:
   ```bash
   curl -i https://your-backend-domain/api/health
   ```
   *Expected: HTTP 200 `{"status": "online", "service": "smartretail-backend"}`*

2. **Database Connectivity Health**:
   ```bash
   curl -i https://your-backend-domain/api/health/db
   ```
   *Expected: HTTP 200 `{"status": "connected", "engine": "mysql", "ping": true}`*

3. **Products Catalog**:
   ```bash
   curl -i https://your-backend-domain/api/products
   ```
   *Expected: HTTP 200 with 20 real FreshRetailNet products.*

4. **Inventory Intelligence & Reorders**:
   ```bash
   curl -i https://your-backend-domain/api/inventory/intelligence?days=7
   ```
   *Expected: HTTP 200 with stockout risk, overstock risk, and explainable reorder recommendations.*

---

## 9. Common Deployment Issues & Troubleshooting

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| **`Access denied for user ... to database`** | Cloud provider restricted user permissions to a specific database name. | Set `DB_NAME` in `.env` to the exact database name assigned by your cloud provider (e.g. `defaultdb` or `smart_retail_db`). `init_db.py` automatically adapts. |
| **`SSL connection error / SSL required`** | Cloud MySQL requires TLS encryption. | Set `DB_SSL_MODE=REQUIRED` in backend environment variables. |
| **CORS Error (`No 'Access-Control-Allow-Origin'`)** | Backend `CORS_ORIGINS` does not match frontend domain. | Add your deployed frontend URL (e.g. `https://your-app.vercel.app`) to `CORS_ORIGINS` in backend environment variables. |
| **SPA 404 on Refresh** | Static hosting does not route subpaths to `index.html`. | Add a rewrite rule in `frontend/vercel.json` (`{ "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }] }`). |
