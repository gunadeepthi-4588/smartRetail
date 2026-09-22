# SmartRetail — Retail Inventory Intelligence & Demand Forecasting Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0%2B-black.svg)](https://flask.palletsprojects.com/)
[![React](https://img.shields.io/badge/React-18-61dafb.svg)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-5.0-646cff.svg)](https://vitejs.dev/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1.svg)](https://www.mysql.com/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.4%2B-F7931E.svg)](https://scikit-learn.org/)
[![Tests](https://img.shields.io/badge/Tests-76%20Passed-brightgreen.svg)]()

> A full-stack decision-support platform for retail store owners that combines real-time POS sales management, inventory tracking, ML demand forecasting, stockout/overstock risk detection, and transparent, mathematically explainable reorder recommendations.

---

## 🏛️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                 React + Vite Frontend                   │
│   - Desktop-first responsive dashboard                  │
│   - Chart.js interactive time-series visualizations     │
│   - Centralized API service with proxy/cloud switching  │
│   - Explainable Reorder Recommendation Modal            │
└───────────────────────────┬─────────────────────────────┘
                            │ HTTPS REST API
                            ▼
┌─────────────────────────────────────────────────────────┐
│                 Flask WSGI Backend                      │
│   - Thread-safe MySQL connection pool & teardown        │
│   - ACID transactions for multi-item POS sales          │
│   - Financial & inventory analytics engine              │
│   - ML recursive multi-step forecasting pipeline        │
│   - Inventory intelligence & reorder recommendation     │
│   - Historical accuracy monitoring (MAE, RMSE, WAPE)    │
└───────────────────────────┬─────────────────────────────┘
                            │ Parameterized SQL (%s)
                            ▼
┌─────────────────────────────────────────────────────────┐
│                 MySQL Relational Database               │
│   - 9 normalized tables with foreign keys and indexes   │
│   - stores, users, suppliers, products, inventory,      │
│     sales, sale_items, forecasts, reorder_recommendations│
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Key Features

1. **Product Catalog & Real-Time Inventory Management**:
   - Track current stock, configured safety stock, min/max thresholds, and supplier lead times.
   - Status indicators (`HEALTHY`, `LOW_STOCK`, `OUT_OF_STOCK`, `OVERSTOCK`).

2. **Point of Sale (POS) & Sales Transactions**:
   - Multi-item checkout with atomic inventory reduction.
   - Automatic transaction rollback if any item exceeds available stock.

3. **Analytics & Business Intelligence**:
   - Live revenue, gross profit, units sold, and average order value tracking.
   - 30-day sales trends, top revenue/volume leaders, and slow-moving SKU detection.

4. **Machine Learning Demand Forecasting**:
   - Baseline-first temporal split (no future data leakage).
   - Time-series feature engineering: lag features (1, 7, 14, 28) and rolling statistics (7D, 14D, 30D).
   - Recursive multi-step forecasting for 7-day and 30-day planning horizons.

5. **Inventory Intelligence & Reorder Engine**:
   - Stockout risk detection based on supplier lead-time demand + safety stock buffer.
   - Dynamic volatility safety stock fallback: $\text{Safety Stock} = \lceil Z \times \sigma_{\text{daily}} \times \sqrt{L} \rceil$.
   - Overstock risk detection based on 30-day velocity thresholds.

6. **Transparent Explainability Layer**:
   - Full mathematical justification for every recommendation:
     $$\text{Recommended Reorder} = \max(0, \text{Forecasted Demand} + \text{Safety Stock} - \text{Current Stock} - \text{Stock on Order})$$
   - Guaranteed **Human-in-the-Loop** decision protocol: No automated purchasing.

7. **Forecast Monitoring & Performance Tracking**:
   - Historical evaluation comparing predicted demand against actual sales.
   - Standard metrics: MAE, RMSE, WAPE %, and Forecast Bias.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.10+, Flask 3.0+, Gunicorn, PyMySQL, Cryptography
- **Data Science & ML**: Scikit-learn, Pandas, NumPy, Joblib
- **Frontend**: React 18, Vite 5, Vanilla CSS Design System, Chart.js, Lucide Icons
- **Database**: MySQL 8.0+
- **Testing**: Pytest (76 passing tests)

---

## 📦 Local Development Quickstart

### Prerequisites
- Python 3.10+
- Node.js 18+
- MySQL 8.0+

### 1. Database Setup
```bash
# Login to MySQL and run initialization
mysql -u root -p < backend/database/schema.sql
mysql -u root -p smart_retail_db < backend/database/seed.sql
```
*Or use the automated script:*
```bash
python backend/database/init_db.py
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
# source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Edit .env with your MySQL credentials

python run.py
# Backend runs at http://localhost:5000
```

### 3. Frontend Setup
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
# Frontend runs at http://localhost:5173
```

---

## 🧪 Testing & Quality Assurance

Run the complete backend test suite:
```bash
cd backend
pytest -v
```
*Results: **76 passed out of 76 tests**.*

Run frontend production build verification:
```bash
cd frontend
npm run build
```

---

## ☁️ Cloud Deployment Architecture

SmartRetail is cloud-ready and deployable on standard hosting platforms:

- **Frontend**: [Vercel](https://vercel.com) / [Netlify](https://netlify.com) (Static Vite SPA)
- **Backend**: [Render](https://render.com) / [Railway](https://railway.app) / [Fly.io](https://fly.io) (`gunicorn wsgi:app`)
- **Database**: [Aiven MySQL](https://aiven.io) / [Railway MySQL](https://railway.app)

See [docs/deployment.md](docs/deployment.md) for detailed, step-by-step deployment instructions and environment configuration.

---

## 🔒 Security & Best Practices

- **Zero Hardcoded Secrets**: Credentials are strictly loaded from environment variables.
- **SQL Injection Prevention**: 100% parameterized queries (`%s`) across all database operations.
- **Atomic Operations**: Database transactions rollback automatically on errors.
- **Controlled Error Sanitization**: Generic, descriptive JSON error messages with zero traceback or credential leaks.

---

## 📄 License
This project is licensed under the MIT License.
