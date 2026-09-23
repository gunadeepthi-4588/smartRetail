# SmartRetail — Comprehensive Viva Questions & Answers

A structured, beginner-friendly guide covering all technical, architectural, machine learning, and business logic aspects of the SmartRetail project.

---

## 1. Project Overview

### Q1: What is SmartRetail?
**Answer**: SmartRetail is an end-to-end single-store retail inventory intelligence and demand forecasting system. It combines point-of-sale (POS) tracking, relational database management, machine learning demand forecasting, and deterministic inventory replenishment recommendations.

### Q2: What core problem does it solve?
**Answer**: Small and medium retail store owners traditionally rely on intuition or static spreadsheets to order inventory. This leads to frequent **stockouts** (lost revenue) or **overstocking** (tied-up working capital and perishables spoilage). SmartRetail replaces intuition with data-driven predictive inventory planning.

### Q3: Who is the target user?
**Answer**: Independent single-store retail owners, supermarket managers, and inventory controllers.

### Q4: What is the main business workflow?
**Answer**: 
1. Record customer purchases via POS.
2. Deduct inventory automatically in MySQL.
3. Compute daily sales trends and category analytics.
4. Generate 7-day and 30-day machine learning demand forecasts.
5. Identify stockout/overstock risk.
6. Generate explainable reorder recommendations for the store owner.
7. Monitor forecast error metrics against reconciled sales.

### Q5: What makes this an end-to-end system?
**Answer**: It spans the complete retail data lifecycle: front-of-house customer transactions (POS UI), back-of-house database storage (MySQL ACID transactions), data preprocessing & machine learning (Scikit-Learn pipeline), decision support (inventory reorder engine), and model accuracy tracking (monitoring dashboard).

---

## 2. System Architecture

### Q6: Why did you choose React for the frontend?
**Answer**: React provides a reactive component-based UI with fast virtual DOM updates, clean separation of concerns, easy integration with charting libraries (Chart.js), and a single-page application (SPA) user experience.

### Q7: Why did you choose Python Flask for the backend?
**Answer**: Flask is a lightweight WSGI microframework that allows direct control over REST routing, application factories, database connection lifecycles, and native integration with Python's data science ecosystem (Pandas, NumPy, Scikit-Learn).

### Q8: Why MySQL instead of MongoDB/NoSQL?
**Answer**: Retail operations require strict transactional integrity (ACID guarantees). Relational foreign keys prevent orphan line items, and atomic transactions ensure inventory stock deductions match recorded receipts without partial writes.

### Q9: Why use REST APIs between Frontend and Backend?
**Answer**: REST APIs decouple the presentation layer from backend business logic. The React client communicates entirely via standard HTTP/JSON requests, meaning the frontend never connects directly to the database.

### Q10: Explain the complete data flow.
**Answer**: 
`User Action in React` $\rightarrow$ `HTTP POST/GET via api.js` $\rightarrow$ `Flask Blueprint Route` $\rightarrow$ `Service Layer Logic` $\rightarrow$ `Parameterized PyMySQL Query` $\rightarrow$ `MySQL InnoDB Engine` $\rightarrow$ `JSON Response returned to React`.

---

## 3. Database Design

### Q11: Explain the 9 relational tables in the database.
**Answer**:
1. `stores`: Store name, owner name, currency localization.
2. `users`: Store owner login credentials and password hashes.
3. `suppliers`: Vendor details, contact info, procurement lead times.
4. `products`: Catalog items, SKU, category, cost price, selling price.
5. `inventory`: Stock levels, minimum/maximum thresholds, safety buffer.
6. `sales`: Header transaction records (receipt number, payment method, date).
7. `sale_items`: Line items associated with each receipt.
8. `forecasts`: Stored multi-step future demand predictions.
9. `reorder_recommendations`: Calculated replenishment quantities with status.

### Q12: Why are `products` and `inventory` separate tables?
**Answer**: To maintain normalization and separation of concerns. `products` represents static catalog metadata (SKU, title, category, pricing), whereas `inventory` represents dynamic, frequently changing physical stock attributes (current stock, lead times, safety stock).

### Q13: Why are `sales` and `sale_items` separated?
**Answer**: A single customer receipt (`sales` header) can contain multiple distinct products in varying quantities (`sale_items`). This standard 1-to-many schema supports multi-item checkout.

### Q14: Why does `store_id` exist in the tables?
**Answer**: To ensure data isolation at the store level. All database queries filter by the authenticated user's `store_id`.

### Q15: Why are both `unit_cost` and `unit_price` stored in `sale_items`?
**Answer**: Product catalog prices may fluctuate over time. Storing the exact `unit_cost` and `unit_price` at the moment of transaction guarantees that historical gross profit calculations remain accurate regardless of future price changes.

---

## 4. Machine Learning & Demand Forecasting

### Q16: What is demand forecasting in this project?
**Answer**: Predicting the expected quantity of units that customers will purchase for each product over a future time horizon (7 or 30 days).

### Q17: What is the prediction target ($y$)?
**Answer**: Daily aggregated sales quantity for a specific SKU on date $t$.

### Q18: Why is demand modeled daily rather than hourly or monthly?
**Answer**: Daily granularity captures weekday vs weekend retail cycles while aligning directly with supplier replenishment lead times (typically 2–5 days).

### Q19: Why use a chronological train/test split instead of random k-fold cross-validation?
**Answer**: Time-series data has temporal autocorrelation. Shuffling data randomly would leak future information into the training set (lookahead bias). A chronological split (first 80% train, last 20% test) accurately reflects real-world inference where the model only knows the past.

### Q20: What are lag features?
**Answer**: Historical demand values from past days used as input features ($t-1$, $t-7$, $t-14$, $t-28$). They capture yesterday's momentum, weekly seasonality (sales on previous Mondays), and monthly cycles.

### Q21: What are rolling features?
**Answer**: Moving statistical metrics computed over past windows (7-day, 14-day, 30-day moving averages and standard deviations) to smooth short-term noise and capture demand volatility.

### Q22: How is data leakage strictly avoided?
**Answer**: All lag and rolling calculations are computed using exclusively prior timestamps ($< t$). When evaluating on test data, feature transformations use rolling statistics computed only from the training period.

### Q23: Why implement a baseline model?
**Answer**: To benchmark whether machine learning algorithms provide real statistical lift over simple heuristic baselines (e.g. 7-day Moving Average or Naive yesterday's demand).

### Q24: Which candidate models are implemented?
**Answer**: Baseline Naive, 7-Day Moving Average, Ridge Regression, and Random Forest Regressor. The Random Forest Regressor is chosen for its superior ability to capture non-linear demand spikes.

### Q25: Why not use deep learning (LSTM/Transformers)?
**Answer**: Single-store retail datasets typically have hundreds or thousands of daily records per SKU. Classical gradient-boosted trees and Random Forests deliver equal or better accuracy on tabular time-series of this size with millisecond inference, zero GPU requirements, and no risk of deep network overfitting.

### Q26: What happens when a product has insufficient sales history?
**Answer**: If a product is newly added (< 7 days of sales history), the system automatically falls back to a category-level moving average heuristic until sufficient SKU history accumulates.

---

## 5. Evaluation & Monitoring Metrics

### Q27: What is MAE (Mean Absolute Error)?
**Answer**: The average magnitude of errors in the same units as the demand:
$$\text{MAE} = \frac{1}{N} \sum_{i=1}^{N} |y_i - \hat{y}_i|$$

### Q28: What is RMSE (Root Mean Squared Error)?
**Answer**: Penalizes large outlier errors more heavily than small errors by squaring differences before averaging:
$$\text{RMSE} = \sqrt{\frac{1}{N} \sum_{i=1}^{N} (y_i - \hat{y}_i)^2}$$

### Q29: What is WAPE (Weighted Absolute Percentage Error)?
**Answer**: Standard MAPE fails on retail datasets due to division by zero on days with zero sales. WAPE resolves this by dividing the sum of absolute errors by the sum of actual demand:
$$\text{WAPE} = \frac{\sum |y_i - \hat{y}_i|}{\sum y_i} \times 100\%$$

### Q30: What is Forecast Bias (Tracking Signal)?
**Answer**: Measures systematic directional error:
$$\text{Bias} = \frac{\sum (\hat{y}_i - y_i)}{\sum y_i} \times 100\%$$
- **Positive Bias**: Model systematically over-predicts (leads to overstock).
- **Negative Bias**: Model systematically under-predicts (leads to stockouts).

---

## 6. Inventory Intelligence & Reorder Formulas

### Q31: What is Lead-Time Demand?
**Answer**: The expected sales demand during the supplier's delivery window:
$$\text{Lead-Time Demand} = \text{Forecasted Demand} \times \left(\frac{\text{Supplier Lead Time}}{\text{Forecast Horizon}}\right)$$

### Q32: What is Safety Stock?
**Answer**: Buffer inventory held to protect against unexpected sales surges or delivery delays:
$$\text{Safety Stock} = Z \times \sigma_{\text{daily}} \times \sqrt{\text{Lead Time}}$$
(Or configured store minimum buffer).

### Q33: How is Stockout Risk determined?
**Answer**: When $\text{Current Stock} \le \text{Lead-Time Demand} + \text{Safety Stock}$.

### Q34: What is the Recommended Reorder Quantity formula?
**Answer**:
$$\text{Recommended Quantity} = \max\Big(0,\; \lceil (\text{Forecasted Demand} + \text{Safety Stock}) - \text{Current Stock} - \text{Stock On Order} \rceil\Big)$$

### Q35: Why is `stock_on_order` currently 0 in the MVP?
**Answer**: The MVP manages store-level inventory. Since full automated EDI supplier ordering is not active, pending shipments default to 0 unless manually updated.

### Q36: Why doesn't the system automatically place purchase orders?
**Answer**: In retail management, an AI system should serve as **decision support**, giving the owner the final verification and budget control before financial commitments are made.

---

## 7. Explainability & Deterministic AI

### Q37: What is Explainable AI in SmartRetail?
**Answer**: Providing clear, step-by-step mathematical breakdowns of how every replenishment recommendation was calculated, rather than an opaque black-box number.

### Q38: Why use deterministic mathematical explainability instead of an LLM?
**Answer**: Retail inventory decisions involve financial expenditures. Deterministic calculations are 100% reproducible, verifiable, mathematically sound, and free from generative hallucinations or API costs.

---

## 8. Authentication & Security

### Q39: How are passwords stored?
**Answer**: Passwords are never stored in plaintext. They are hashed using **PBKDF2:SHA256** with unique cryptographic salts using Python's `werkzeug.security`.

### Q40: How are protected routes and APIs handled?
**Answer**: The React frontend uses stateful auth guards that redirect unauthenticated users to `/login`. The Flask backend verifies user identity and isolates queries to the user's `store_id`.

---

## 9. Testing & Quality Assurance

### Q41: How was the project tested?
**Answer**: We executed a suite of **80 automated tests** using Pytest covering API health, CRUD operations, atomic rollbacks, business formulas, ML pipeline data integrity, inventory intelligence, and explainability.

### Q42: How was the frontend build validated?
**Answer**: Executed `npm run build` using Vite, generating a production-optimized bundle in `dist/` with zero build errors or broken imports.

---

## 10. Deployment & Cloud Architecture

### Q43: What is the production deployment architecture?
**Answer**:
- **Frontend**: React + Vite hosted on **Vercel** with SPA URL rewrite routing.
- **Backend**: Flask + Gunicorn WSGI web service on **Render**.
- **Database**: Managed MySQL 8.0+ instance (e.g. **Aiven** / **Railway**).
- **Model**: Pre-trained Random Forest joblib artifact committed in the deployment bundle.

---

## 11. Limitations & Future Scope

### Q44: What are the current limitations of the MVP?
**Answer**:
1. Single-store architecture (no multi-warehouse cross-docking).
2. Human-in-the-loop ordering (recommends quantities without auto-dispatching purchase orders to vendor APIs).
3. Synchronous on-demand inference rather than distributed Celery task queues.

### Q45: What are planned future enhancements?
**Answer**:
1. Multi-branch inventory tracking with inter-store stock transfers.
2. Direct supplier portal integration with automated purchase order generation.
3. Mobile camera barcode scanning at the POS counter.
4. Promotional calendar and local holiday event feature engineering.
