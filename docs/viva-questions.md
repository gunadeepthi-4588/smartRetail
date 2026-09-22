# SmartRetail — Viva & Technical Defense Questions

This document prepares project presenters for technical viva examinations, design interviews, and code walkthroughs.

---

## 1. Core Architecture & Technology Stack

### Q1: Why did you choose React + Vite for the frontend?
**Answer**: React provides a reactive, component-driven UI ideal for live retail dashboards with dynamic chart updates and modal popups. Vite offers near-instant Hot Module Replacement (HMR) during development and highly optimized Rollup-based tree-shaking for fast production static builds (`<4s`).

### Q2: Why did you choose Flask instead of Django or FastAPI?
**Answer**: Flask provides a lightweight, unopinionated micro-framework that gives complete control over thread-local database connections, custom blueprint modularity, and explicit middleware without unnecessary ORM overhead or complex async abstractions that might complicate relational MySQL transactions.

### Q3: Why did you choose MySQL instead of MongoDB or SQLite?
**Answer**: Retail inventory and sales require strict ACID transactions, foreign key constraints (e.g. cascading item deletion protection), and multi-table relational joins. Document databases lack strict schema enforcement and multi-table relational consistency, while SQLite lacks concurrent multi-threaded write locking necessary for production web servers.

### Q4: Why does React never connect directly to MySQL?
**Answer**: Direct database connections from client-side JavaScript expose database credentials in the browser bundle and create extreme security vulnerabilities (SQL injection, unauthorized modification). Routing requests through a secure Flask REST API enforces input validation, authentication, and parameterized query execution.

---

## 2. Machine Learning & Demand Forecasting

### Q5: What is the target variable of your forecasting model?
**Answer**: The target variable is `daily_demand` (total integer units sold for a specific `product_id` on a given date).

### Q6: Why did you use a chronological (time-aware) split instead of random train/test split?
**Answer**: Time-series data exhibits temporal autocorrelation. A random K-Fold split would cause future data leakage where the model trains on future sales to predict past sales. A chronological split trains strictly on $T_0 \dots T_{\text{train}}$ and evaluates on $T_{\text{train}+1} \dots T_{\text{test}}$.

### Q7: What are lag features and why are they important?
**Answer**: Lag features represent historical demand at specific past intervals ($t-1, t-7, t-14, t-28$). Lag-1 captures yesterday's momentum; Lag-7 and Lag-14 capture day-of-week seasonality (e.g., higher sales on weekends).

### Q8: What are rolling statistics features?
**Answer**: Rolling statistics calculate moving averages and standard deviations over trailing windows (e.g., 7-day, 14-day, 30-day). They smooth out short-term fluctuations and capture medium-term demand trends without looking ahead into future data.

### Q9: How does multi-step recursive forecasting work?
**Answer**: To forecast $N$ days ahead, the model predicts day $T+1$. This predicted value is dynamically fed back into the time-series as the input demand for calculating the lags for day $T+2$, repeating recursively up to $T+N$.

### Q10: Why did you choose Random Forest / Ridge Regression instead of Deep Learning (LSTM/Transformers)?
**Answer**: Tabular retail sales at the single-store level typically have small-to-medium dataset sizes where deep learning models easily overfit, require high computational resources, and act as uninterpretable black boxes. Scikit-learn regressors provide high accuracy, fast inference (<10ms), and full portability in lightweight cloud containers.

---

## 3. Evaluation & Forecast Monitoring Metrics

### Q11: What is MAE (Mean Absolute Error)?
**Answer**: $\text{MAE} = \frac{1}{N} \sum |\text{actual} - \text{predicted}|$. It measures the average absolute error magnitude in demand units, providing an intuitive measurement for store managers.

### Q12: What is RMSE (Root Mean Squared Error)?
**Answer**: $\text{RMSE} = \sqrt{\frac{1}{N} \sum (\text{actual} - \text{predicted})^2}$. Because errors are squared before averaging, RMSE penalizes large forecast blunders more severely than MAE.

### Q13: What is WAPE (Weighted Absolute Percentage Error) and why is it preferred over MAPE?
**Answer**: $\text{WAPE} = \frac{\sum |\text{actual} - \text{predicted}|}{\sum \text{actual}}$. Standard MAPE divides by individual actual sales, leading to division-by-zero on days with zero sales. WAPE normalizes total absolute error across the aggregate sales volume.

### Q14: What is Forecast Bias and what does its sign mean?
**Answer**: $\text{Bias} = \frac{1}{N} \sum (\text{predicted} - \text{actual})$. A positive bias indicates the model tends to over-forecast (acting as a stockout buffer), while a negative bias indicates under-forecasting (risk of lost sales).

---

## 4. Inventory Intelligence & Business Formulas

### Q15: How is Gross Profit calculated and how does it differ from Revenue?
**Answer**:
- $\text{Revenue} = \sum (\text{quantity} \times \text{unit\_price})$
- $\text{Gross Profit} = \sum (\text{quantity} \times (\text{unit\_price} - \text{unit\_cost}))$
Gross profit accounts for the cost of goods sold (COGS), showing actual earnings before fixed store operating expenses.

### Q16: How is Stockout Risk calculated?
**Answer**: $\text{Stockout Risk} = \text{Current Stock} < (\text{Lead-Time Demand} + \text{Safety Stock})$. If current available inventory cannot cover expected customer demand during the supplier's replenishment lead time plus the safety buffer, a stockout risk is flagged.

### Q17: How is Dynamic Volatility Safety Stock calculated?
**Answer**: When no fixed safety stock is configured, the system computes:
$$\text{Safety Stock} = \lceil Z \times \sigma_{\text{daily demand}} \times \sqrt{L_{\text{lead time}}} \rceil$$
Using $Z = 1.65$ (~95% service level) to buffer against daily sales variance.

### Q18: How is Overstock Risk detected?
**Answer**: $\text{Overstock Threshold} = \text{30-Day Sales Total} \times 1.5$. If current stock exceeds 1.5 times the 30-day velocity, the item is flagged as overstocked to avoid tying up working capital.

### Q19: How is the Recommended Reorder Quantity calculated?
**Answer**:
$$\text{Required Stock} = \text{Forecasted Demand} + \text{Safety Stock}$$
$$\text{Recommended Reorder} = \max(0, \text{Required Stock} - \text{Current Stock} - \text{Stock on Order})$$
This guarantees the recommendation is strictly non-negative.

---

## 5. System Design, Security & Operations

### Q20: Why is Explainability crucial in retail AI?
**Answer**: If a model simply outputs "Order 50 units," a shop owner cannot evaluate the financial risk. SmartRetail provides an interactive breakdown showing the exact forecasted demand, safety buffer, current stock, and mathematical formula so the owner can verify the logic.

### Q21: Why does SmartRetail NOT place orders automatically?
**Answer**: SmartRetail is strictly a decision-support system. Automating purchasing introduces financial liability if supply chain conditions, seasonal closures, or cash flow constraints change. The human owner always retains final purchasing authority.

### Q22: How is transaction rollback handled during sales?
**Answer**: In `app/routes/sales.py`, the entire checkout is wrapped in `db.begin()`. If any line item has insufficient stock, the API raises an error, executes `db.rollback()`, and returns HTTP 400. No records are written and zero stock is deducted.

### Q23: How are SQL injection attacks prevented?
**Answer**: 100% of database queries use parameterized SQL tuples (`%s`) handled by the database driver, ensuring user inputs are treated as literal values rather than executable code.

### Q24: What happens if a newly added product has no sales history?
**Answer**: The forecasting pipeline detects insufficient history ($<2$ data points) and falls back safely to baseline moving averages or configured minimum safety stocks without crashing or throwing unhandled exceptions.

### Q25: What are the main limitations and future enhancements?
**Answer**: Current MVP limitations include single-store focus and zero stock-on-order tracking. Future enhancements include multi-store warehouse distribution, automated purchase order EDI generation, and integration of external promotion/weather features.
