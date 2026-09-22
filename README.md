# SmartRetail — Retail Inventory Intelligence & Demand Forecasting Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0%2B-black.svg)](https://flask.palletsprojects.com/)
[![React](https://img.shields.io/badge/React-18-61dafb.svg)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-5.0-646cff.svg)](https://vitejs.dev/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1.svg)](https://www.mysql.com/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.4%2B-F7931E.svg)](https://scikit-learn.org/)
[![Tests](https://img.shields.io/badge/Tests-76%20Passed-brightgreen.svg)]()
[![License](https://img.shields.io/badge/License-MIT-green.svg)]()

> **SmartRetail** is an end-to-end retail inventory intelligence and demand forecasting platform designed to help independent retail store owners understand sales velocity, forecast customer demand using machine learning, identify stockout/overstock risks, and make transparent, mathematically explainable reorder decisions.
>
> *Important Note: SmartRetail is a **decision-support platform** and does not automatically place purchasing orders.*

---

## 📌 Problem Statement

Retail shop owners are constantly forced to answer critical inventory and financial questions:
- *Which products sell the most, and which drive true gross profit?*
- *Which products are slow-moving and tying up essential working capital?*
- *Which products are on the verge of running out of stock before supplier replenishment?*
- *Which items are overstocked and risk spoilage or obsolescence?*
- *How many units should be reordered right now to satisfy upcoming demand?*

Traditional spreadsheet or manual estimation methods fail to capture non-linear demand trends, supplier lead-time buffers, and day-of-week seasonality. SmartRetail bridges this gap by unifying transactional POS sales, real-time analytics, machine-learning demand forecasting, and transparent reorder explainability into a single, intuitive dashboard.

---

## 💡 Solution Architecture

```
Point of Sale (Sales)
        │
        ▼
MySQL Relational Storage (ACID Transactions)
        │
        ▼
Data Cleaning & Daily Demand Aggregation
        │
        ▼
Time-Series Feature Engineering (Lags: 1, 7, 14, 28 + Rolling Statistics)
        │
        ▼
Recursive ML Demand Forecasting (7-Day & 30-Day Horizons)
        │
        ▼
Inventory Intelligence & Risk Detection (Stockout & Overstock)
        │
        ▼
Explainable Reorder Engine (Required Stock - Current Stock - Stock on Order)
        │
        ▼
React Dashboard & Historical Accuracy Monitoring (MAE, RMSE, WAPE, Bias)
```

---

## 🚀 Key Features

### 1. Point of Sale & Sales Transactions
- Record multi-item retail sales transactions with Cash, Card, and UPI payment methods.
- Atomic inventory deduction: if any line item exceeds available stock, the entire transaction rolls back cleanly with zero stock leakage.

### 2. Product & Inventory Management
- Real-time stock level monitoring across categories.
- Stock health statuses: `HEALTHY`, `LOW_STOCK`, `OUT_OF_STOCK`, `OVERSTOCK`.
- Configurable replenishment parameters: `safety_stock`, `lead_time_days`, `min_stock_level`, `max_stock_level`.

### 3. Retail Analytics & Business Intelligence
- Real-time financial KPIs: Today's Revenue, 30-Day Revenue, Gross Profit, and Profit Margins.
- Distinct rankings for Volume Leaders (units sold), Revenue Leaders, and Gross Profit Leaders.
- 30-day interactive sales trend area charts and slow-moving SKU detection.

### 4. Machine Learning Demand Forecasting
- Recursive multi-step regression using Random Forest with baseline benchmarking.
- Time-aware chronological validation with zero future data leakage.
- Time-series features: Lag-1, Lag-7, Lag-14, Lag-28, 7D/14D/30D rolling means and standard deviations, day-of-week, and weekend indicators.

### 5. Inventory Intelligence & Risk Detection
- **Stockout Risk**: Triggered when $\text{Current Stock} < \text{Lead-Time Demand} + \text{Safety Stock}$.
- **Dynamic Volatility Safety Stock**: Statistical estimation based on historical demand volatility ($\sigma$) and lead time ($L$):
  $$\text{Safety Stock} = \lceil Z \times \sigma_{\text{daily demand}} \times \sqrt{L} \rceil \quad (Z = 1.65)$$
- **Overstock Risk**: Flags when $\text{Current Stock} > \text{30-Day Velocity} \times 1.5$.

### 6. Transparent Explainability Engine
- Every recommendation is accompanied by a mathematical breakdown:
  $$\text{Required Stock} = \text{Forecasted Demand} + \text{Safety Stock}$$
  $$\text{Recommended Quantity} = \max(0, \text{Required Stock} - \text{Current Stock} - \text{Stock on Order})$$
- Interactive **"Why?" / View Details** modal explaining the exact formula and reason string to the store owner.
- Guaranteed **Human-in-the-Loop** decision protocol.

### 7. Forecast Monitoring & Drift Tracking
- Historical accuracy verification comparing predicted demand against actual sales once dates conclude.
- Industry-standard metrics: **MAE**, **RMSE**, **WAPE %**, and **Forecast Bias** (+/- direction).

---

## 🛠️ Technology Stack

| Layer | Technology | Details |
| :--- | :--- | :--- |
| **Frontend UI** | **React 18** | Single Page Application with component-driven architecture |
| **Build Tool** | **Vite 5** | High-speed bundler with Hot Module Replacement (HMR) |
| **Styling** | **Vanilla CSS** | Tailored dark-theme design tokens, CSS variables, and responsive grid |
| **Visualizations** | **Chart.js** | Interactive time-series line, area, and bar charts |
| **Backend API** | **Flask 3.0+** | Modular Blueprint REST API with thread-safe database connections |
| **WSGI Server** | **Gunicorn** | Production WSGI application server |
| **Database** | **MySQL 8.0+** | 9 normalized tables with foreign keys and ACID transactions |
| **Data & ML** | **Scikit-Learn, Pandas, NumPy** | Feature engineering, temporal split, and Random Forest regressor |
| **Testing** | **Pytest** | 76 automated unit, integration, and system validation tests |

---

## 🗄️ Database Architecture

The schema consists of 9 core relational tables:
1. `stores`: Retail store profile and operational configuration.
2. `users`: Store operators and cashier accounts.
3. `suppliers`: Supplier directory, contact info, and lead times.
4. `products`: Catalog items with SKU, category, cost price, and selling price.
5. `inventory`: Stock records with safety stock, min/max thresholds, and lead times.
6. `sales`: Transaction headers with receipts and payment methods.
7. `sale_items`: Itemized lines storing quantity, unit price, and historical unit cost.
8. `forecasts`: Stored multi-step predictions with future `actual_demand` reconciliation.
9. `reorder_recommendations`: Persisted inventory intelligence recommendation outputs.

---

## 📐 Core Business Formulas

1. **Best Sellers (Volume)**: $\text{Total Units Sold} = \sum \text{quantity}$
2. **Revenue**: $\text{Revenue} = \sum (\text{quantity} \times \text{unit\_price})$
3. **Gross Profit**: $\text{Gross Profit} = \sum (\text{quantity} \times (\text{unit\_price} - \text{unit\_cost}))$
4. **Stockout Risk**: $\text{Current Stock} < \text{Lead-Time Demand} + \text{Safety Stock}$
5. **Overstock Threshold**: $\text{Current Stock} > \text{Average 30-Day Demand} \times 1.5$
6. **Required Stock**: $\text{Required Stock} = \text{Forecasted Demand}_{\text{horizon}} + \text{Safety Stock}$
7. **Recommended Reorder**: $\text{Recommended Reorder} = \max(0, \text{Required Stock} - \text{Current Stock} - \text{Stock on Order})$
   *(Note: $\text{Stock on Order} = 0$ in the MVP as purchase order tracking is out of scope).*
8. **Forecast Bias**: $\text{Bias} = \frac{1}{N} \sum (\text{predicted} - \text{actual})$ *(Positive = over-forecast buffer, Negative = under-forecast risk)*

---

## 📦 Installation & Local Setup

### Prerequisites
- **Python**: 3.10 or higher
- **Node.js**: 18.x or higher
- **MySQL**: 8.0 or higher
- **Git**

### Step 1: Clone Repository
```bash
git clone https://github.com/yourusername/smartRetail.git
cd smartRetail
```

### Step 2: Database Initialization
```bash
# Login to MySQL and apply schema and seed data
mysql -u root -p < backend/database/schema.sql
mysql -u root -p smart_retail_db < backend/database/seed.sql
```
*Alternatively, run the automated setup script:*
```bash
python backend/database/init_db.py
```

### Step 3: Backend Setup (Flask)
```bash
cd backend
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
# source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Edit .env with your MySQL credentials (DB_HOST, DB_USER, DB_PASSWORD, DB_NAME)

python run.py
# Backend runs at http://localhost:5000
```

### Step 4: Frontend Setup (React)
```bash
cd ../frontend
npm install
cp .env.example .env
npm run dev
# Frontend runs at http://localhost:5173
```

---

## 🧪 Testing & Validation

Execute the full backend test suite:
```bash
cd backend
pytest -v
```
*Results: **76 passed out of 76 tests (100% pass rate in 5.05s)**.*

Verify frontend production build:
```bash
cd frontend
npm run build
```

---

## ☁️ Cloud Deployment Architecture

- **Frontend**: [Vercel](https://vercel.com) / [Netlify](https://netlify.com) (Static Vite SPA)
- **Backend**: [Render](https://render.com) / [Railway](https://railway.app) / [Fly.io](https://fly.io) (`gunicorn wsgi:app`)
- **Database**: [Aiven MySQL](https://aiven.io) / [Railway MySQL](https://railway.app)

Refer to [docs/deployment.md](docs/deployment.md) for step-by-step production deployment instructions.

---

## 📚 Complete Documentation Index

- [Project Overview & Report](docs/project-overview.md)
- [System Architecture & Design](docs/architecture.md)
- [REST API Reference](docs/api.md)
- [Testing & Quality Assurance Report](docs/testing.md)
- [Cloud Deployment Guide](docs/deployment.md)
- [Presentation Demo Script](docs/demo-script.md)
- [Viva Defense & Interview Q&A](docs/viva-questions.md)
- [Final Phase Completion Checklist](docs/final-status.md)

---

## ⚠️ Known Limitations & Boundaries
- **Single-Store Focus**: Configured for a single retail storefront operator.
- **Decision-Support Guardrail**: Reorder recommendations advise the owner; no automated purchasing orders are placed.
- **Stock-on-Order**: Configured as zero in this MVP (purchase order tracking is out of scope).
- **Historical Data Dependency**: Forecast reliability depends on historical transaction volume; new products use statistical safety stock fallbacks.

---

## 🔮 Future Enhancements
- **Multi-Store Warehouse Balancing**: Inter-branch inventory transfers and multi-location analytics.
- **Supplier Purchase Order Portal**: Automated PDF PO generation and supplier email dispatch.
- **Exogenous Variables**: Weather forecasts, local events, and promotional calendar integration.

---

## 📄 License
This project is open source and available under the [MIT License](LICENSE).
