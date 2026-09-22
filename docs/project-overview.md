# SmartRetail — Project Overview & Technical Report

## 1. Project Title & Executive Summary
- **Project Title**: **SmartRetail — End-to-End Retail Inventory Intelligence & Demand Forecasting Platform**
- **Domain**: Retail Analytics, Demand Forecasting, Inventory Optimization & Supply Chain Decision-Support
- **Tagline**: *Empowering independent retail store owners with machine-learning demand forecasting, real-time risk intelligence, and transparent, mathematically explainable replenishment decisions.*

---

## 2. Problem Statement
Independent and small-to-medium enterprise (SME) retail shop owners operate under intense margin pressures, volatile customer demand, and supplier lead-time uncertainties. Most store owners rely on manual observation or static spreadsheets to make purchasing and stock management decisions.

This approach creates critical vulnerabilities:
1. **Stockout Risks**: High-demand products run out of stock during supplier lead times, resulting in lost revenue and dissatisfied customers.
2. **Overstock Pitfalls**: Slow-moving products tie up working capital on shelves, risking spoilage, obsolescence, and storage inefficiencies.
3. **Black-Box Skepticism**: Automated ML recommendations often fail in practice when owners do not understand *why* an order quantity was calculated.

---

## 3. Project Objectives
1. **Unified POS & Inventory Management**: Provide real-time sales transaction processing with atomic inventory deduction and rollback protection.
2. **Automated Business Intelligence**: Real-time aggregation of today's vs 30-day revenue, gross profit, sales trends, volume leaders, and slow movers.
3. **Machine Learning Demand Forecasting**: Develop recursive multi-step forecasting models with lag and rolling features, baseline validation, and zero future data leakage.
4. **Inventory Risk Intelligence**: Dynamically evaluate stockout risk against supplier lead-time demand and compute statistical volatility safety stock.
5. **Transparent Explainability**: Deliver human-in-the-loop mathematical justifications for every reorder recommendation.
6. **Continuous Performance Monitoring**: Benchmark historical forecasts against real concluded sales demand using standard metrics (MAE, RMSE, WAPE, Bias).

---

## 4. Target User & Scope Boundaries
- **Target User**: Single retail store owner, inventory manager, or shop cashier.
- **Decision-Support Guarantee**: SmartRetail advises and explains; it **never** places automated purchasing orders without explicit owner confirmation.
- **MVP Boundaries**: Multi-store clustering, supplier purchase order EDI integrations, and deep-learning neural networks are preserved for future roadmap iterations.

---

## 5. Technology Stack

| Layer | Technology | Rationale |
| :--- | :--- | :--- |
| **Frontend UI** | **React 18 + Vite 5** | High-performance single-page application with instant HMR and responsive desktop layout. |
| **Styling** | **Vanilla CSS (Design Tokens)** | Cohesive dark-theme design system with custom CSS variables, glassmorphism, and responsive grids. |
| **Visualizations** | **Chart.js + React-ChartJS-2** | Responsive time-series line, area, and bar charts for sales trends, demand forecasts, and error analysis. |
| **Backend API** | **Flask 3.0+ (Python 3.10+)** | Modular blueprint architecture with thread-safe database connection management and centralized error handling. |
| **WSGI Server** | **Gunicorn** | Production-grade WSGI server handling concurrent request workers in cloud deployment. |
| **Database** | **MySQL 8.0+ / PyMySQL** | Relational schema with strict foreign keys, parameterized SQL (`%s`), and ACID transaction support. |
| **Data & ML** | **Pandas, NumPy, Scikit-Learn** | Data cleaning, daily grid aggregation, feature engineering, and Random Forest multi-step demand regression. |
| **Testing** | **Pytest** | 76 automated unit, integration, and system validation tests (100% pass rate). |

---

## 6. System Architecture & Information Flow

```
Sales Transaction (POS)
       │
       ▼
MySQL (Atomic ACID Commit)
       │
       ▼
Data Cleaning & Aggregation (Daily Product Demand Grid)
       │
       ▼
Time-Series Feature Engineering (Lags: 1, 7, 14, 28 + Rolling Means)
       │
       ▼
Recursive ML Demand Forecasting (7-Day & 30-Day Horizons)
       │
       ▼
Inventory Intelligence (Lead-Time Demand + Dynamic Volatility Safety Stock)
       │
       ▼
Explainable Reorder Engine (Required Stock - Current Stock - Stock on Order)
       │
       ▼
React Dashboard & Historical Accuracy Monitoring (MAE, RMSE, WAPE, Bias)
```

---

## 7. Database Design Summary

The schema consists of 9 normalized tables:
1. `stores`: Store profile and configuration.
2. `users`: System users and store associates.
3. `suppliers`: Supplier directory, contact info, and default lead times.
4. `products`: Product catalog with SKU, category, cost price, and selling price.
5. `inventory`: Stock records with current stock, configured safety stock, min/max levels, and lead-time days.
6. `sales`: Header transactions with receipts, total amounts, and payment methods.
7. `sale_items`: Itemized sale lines capturing quantity, unit price, and historical unit cost.
8. `forecasts`: Stored multi-step demand predictions with future `actual_demand` reconciliation.
9. `reorder_recommendations`: Persisted inventory intelligence recommendation outputs.

---

## 8. Business Formulas & Mathematical Logic

1. **Gross Profit**:
   $$\text{Gross Profit} = \sum (\text{quantity} \times (\text{unit\_price} - \text{unit\_cost}))$$
2. **Reorder Quantity**:
   $$\text{Required Stock} = \text{Forecasted Demand}_{\text{horizon}} + \text{Safety Stock}$$
   $$\text{Recommended Quantity} = \max(0, \text{Required Stock} - \text{Current Stock} - \text{Stock on Order})$$
3. **Stockout Risk**:
   $$\text{Stockout Risk} = \text{Current Stock} < (\text{Lead-Time Demand} + \text{Safety Stock})$$
4. **Dynamic Volatility Safety Stock**:
   $$\text{Safety Stock} = \lceil Z \times \sigma_{\text{daily demand}} \times \sqrt{L_{\text{lead time}}} \rceil \quad (Z = 1.65)$$
5. **Forecast Bias (Sign Convention)**:
   $$\text{Bias} = \frac{1}{N} \sum (\text{predicted} - \text{actual})$$
   *(Positive = slight over-forecasting buffer; Negative = slight under-forecasting risk)*

---

## 9. Limitations & Future Enhancements

### Current MVP Limitations
- Optimized for single-store retail operations.
- Purchase order lifecycle tracking is out of scope (`stock_on_order = 0`).
- Model accuracy relies on historical sales volume; newly added SKUs fall back to statistical safety buffers.

### Future Roadmap
- **Multi-Store Management**: Centralized warehouse inventory balancing across multiple retail branches.
- **Supplier Order Portal**: Automated Purchase Order generation and supplier acknowledgment workflows.
- **Exogenous Variables**: Weather forecasts, local holiday calendars, and promotional discount variables integrated into feature engineering.
