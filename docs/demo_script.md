# SmartRetail — 5–7 Minute College Demonstration Script

This script provides a concise, professional step-by-step walkthrough for project evaluation, viva, or live demonstration.

---

### Step 1: Login (0:00 – 0:45)
- **Action**: Open `/login`. Click **Fill Demo Email** (fills `owner@smartretail.com`). Type store password and submit.
- **Talking Point**: *"SmartRetail uses secure PBKDF2 password hashing and stores credentials safely in MySQL. Notice the automatic redirect to our authenticated store management dashboard."*

---

### Step 2: Dashboard & Store KPIs (0:45 – 1:30)
- **Action**: Show top KPI cards (Total Revenue, Gross Profit, Total Orders, Low Stock Alerts).
- **Talking Point**: *"The dashboard displays live aggregated business health metrics calculated in real-time from our relational database, with immediate visibility into store inventory status."*

---

### Step 3: Inventory Management (1:30 – 2:15)
- **Action**: Navigate to `/inventory`. Filter by category (e.g., Dairy, Staples) and stock status.
- **Talking Point**: *"Here, store owners monitor stock levels, safety thresholds, and lead times across all catalog items."*

---

### Step 4: Live Point-of-Sale (POS) Transaction (2:15 – 3:00)
- **Action**: Navigate to `/sales`. Select a product, enter quantity, and click **Complete Sale**.
- **Talking Point**: *"When a sale occurs, the Flask backend executes an atomic transaction that registers the receipt, line items, and immediately decrements inventory stock in MySQL with ACID integrity."*

---

### Step 5: Real-Time Analytics (3:00 – 3:45)
- **Action**: Navigate to `/analytics`. Point out the Sales Trend chart, Top Revenue Products, and Category Breakdown.
- **Talking Point**: *"All sales immediately reflect in our financial analytics. We compute revenue, gross profit, and automatically flag slow-moving items with zero sales in the last 30 days."*

---

### Step 6: Machine Learning Demand Forecasting (3:45 – 4:30)
- **Action**: Navigate to `/forecast`. Select a product (e.g., Farm Fresh Whole Milk) and view the 7-day predicted demand trajectory.
- **Talking Point**: *"SmartRetail uses a pre-trained Random Forest model trained on chronological lag and rolling features. It generates multi-step daily forecasts without requiring heavy runtime re-training."*

---

### Step 7 & 8: Inventory Risk & Reorder Recommendations (4:30 – 5:15)
- **Action**: On `/inventory` or `/forecast`, view the Stockout / Overstock risk tags and recommended reorder quantities.
- **Talking Point**: *"The system dynamically computes lead-time demand and safety stock buffers to pinpoint stockout risk and calculate exact reorder quantities."*

---

### Step 9: Transparent "Why?" Explainability (5:15 – 5:50)
- **Action**: Click the **Why? (Explain)** button next to a reorder recommendation to open the calculation breakdown modal.
- **Talking Point**: *"Rather than a black-box recommendation, we provide clear mathematical explainability showing forecasted demand, lead-time requirements, and safety stock gaps."*

---

### Step 10: Forecast Accuracy Monitoring (5:50 – 6:30)
- **Action**: Navigate to `/monitoring`. Show the Actual vs Predicted demand chart and summary error metrics (MAE, RMSE, WAPE %, Forecast Bias).
- **Talking Point**: *"To ensure trustworthy AI, our monitoring module tracks model performance against actual sales, detecting demand drift and over/under-forecasting bias."*

---

### Step 11: Secure Logout (6:30 – 7:00)
- **Action**: Click **Logout** in the header. Attempt to open `/dashboard` directly and demonstrate that access is protected and redirects back to `/login`.
- **Talking Point**: *"All protected views and APIs require active session authorization, preventing unauthorized access."*
