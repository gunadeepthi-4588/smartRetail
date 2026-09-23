# SmartRetail — 5–7 Minute College Demonstration Script

This script provides a structured, professional live demonstration sequence for faculty, evaluators, and viva panels.

---

### STEP 1 — Login (0:00 – 0:45)
- **Action**: 
  - Open `http://localhost:5173/login`.
  - Click **Fill Demo Email** (populates `owner@smartretail.com`).
  - Enter the demo password and click **Sign In**.
- **Explanation**: 
  - *"SmartRetail enforces secure authentication using industry-standard PBKDF2:SHA256 password hashing stored in MySQL. Notice that unauthenticated access is guarded, and upon successful authentication, the app loads the store owner context for Metro Mart Superstore."*

---

### STEP 2 — Dashboard (0:45 – 1:30)
- **Action**: 
  - Walk through the main KPI summary cards (Total Revenue, Gross Profit, Total Orders, Active Low Stock Items).
  - Show the Quick Stock Alert widget.
- **Explanation**: 
  - *"The dashboard aggregates live business KPIs directly from relational sales and inventory tables in MySQL. It gives the shop owner an immediate overview of sales velocity, financial health, and urgent inventory risks."*

---

### STEP 3 — Inventory Management (1:30 – 2:15)
- **Action**: 
  - Navigate to `/inventory`.
  - Filter by category (e.g., *Dairy*, *Beverages*, *Staples*) and stock status (*Optimal*, *Low Stock*, *Overstock*).
- **Explanation**: 
  - *"The inventory module tracks catalog items, unit costs, selling prices, minimum stock thresholds, safety stocks, and supplier lead times. Every SKU has clear visibility into its current stock health."*

---

### STEP 4 — Point-of-Sale (POS) & Sales Transaction (2:15 – 3:00)
- **Action**: 
  - Navigate to `/sales`.
  - Select a product (e.g., *Farm Fresh Whole Milk 1L*), enter quantity (e.g., *2*), and click **Complete Sale**.
  - Show the generated receipt confirmation.
  - Return to `/inventory` to show that the stock decreased immediately by 2 units.
- **Explanation**: 
  - *"When a sale occurs, the Flask backend executes an atomic ACID transaction that inserts the sale header, line items, and deducts inventory in MySQL simultaneously. If stock is insufficient, the transaction safely rolls back."*

---

### STEP 5 — Business Analytics (3:00 – 3:45)
- **Action**: 
  - Navigate to `/analytics`.
  - Point out the 30-day Sales Trend chart, Top Best Sellers, Revenue Leaders, Gross Profit Leaders, Category Share, and 30-Day Slow Movers.
- **Explanation**: 
  - *"Our analytics engine calculates revenue ($Q \times P$), gross margin ($\text{Revenue} - \text{Cost}$), and flags slow-moving products with zero sales in the last 30 days to help reduce dead inventory capital."*

---

### STEP 6 — Machine Learning Demand Forecasting (3:45 – 4:30)
- **Action**: 
  - Navigate to `/forecast`.
  - Select a product (e.g., *Farm Fresh Whole Milk 1L*) and view the 7-day predicted demand trajectory.
- **Explanation**: 
  - *"SmartRetail uses a pre-trained Random Forest model trained on chronological lag features ($t-1, t-7, t-14, t-28$) and rolling statistical averages. It performs multi-step recursive forecasting without requiring slow re-training during normal browsing."*

---

### STEP 7 — Inventory Intelligence (4:30 – 5:15)
- **Action**: 
  - Highlight the Stockout Risk tag, Lead-Time Demand, Safety Stock buffer, and Recommended Order Quantity.
- **Explanation**: 
  - *"Raw predictions alone aren't enough for shop owners. The Inventory Intelligence module combines the forecast with supplier lead time (e.g. 3 days) and daily demand volatility ($\sigma$) to compute exact buffer stock and reorder requirements."*

---

### STEP 8 — Transparent Explainability ("Why?" Modal) (5:15 – 5:50)
- **Action**: 
  - Click the **Why? (Explain)** button next to a reorder recommendation.
  - Walk through the step-by-step mathematical breakdown modal.
- **Explanation**: 
  - *"Rather than an uninterpretable black box, we provide deterministic mathematical explainability: $\text{Recommended Quantity} = \max(0, \text{Required Stock} - \text{Current Stock})$. We emphasize that SmartRetail is an intelligent decision-support system that recommends replenishment but never automatically places supplier orders."*

---

### STEP 9 — Forecast Monitoring & Accuracy Tracking (5:50 – 6:30)
- **Action**: 
  - Navigate to `/monitoring`.
  - Show the Actual vs Predicted demand chart and summary error metrics (MAE, RMSE, WAPE %, and Forecast Bias).
- **Explanation**: 
  - *"To ensure trust and prevent model drift, our monitoring service compares past predictions against actual sales reconciled from MySQL, calculating Mean Absolute Error and tracking whether the model tends to over-forecast or under-forecast."*

---

### STEP 10 — Logout & Route Protection (6:30 – 7:00)
- **Action**: 
  - Click **Logout** in the header.
  - Attempt to manually navigate back to `/dashboard` in the address bar.
  - Demonstrate that the user is immediately redirected to `/login`.
- **Explanation**: 
  - *"All frontend pages and backend REST APIs require authentication, ensuring store privacy and security. This completes our end-to-end SmartRetail demonstration."*
