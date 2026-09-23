# SmartRetail — College Project Presentation Slide Outline (12 Slides)

A slide-by-slide structure designed for PowerPoint, Canva, or Google Slides presentations.

---

### Slide 1: Title & Project Overview
- **Title**: SmartRetail — AI-Powered Retail Inventory Intelligence & Demand Forecasting System
- **Subtitle**: A 3-Tier Enterprise Decision Support Platform for Modern Retail
- **Presenter**: Final Year Project Evaluation Team
- **Department**: Computer Science & Engineering / Data Science

---

### Slide 2: Problem Statement
- **Core Challenge**: Retailers struggle with the dilemma of **under-stocking** (lost sales & unhappy customers) vs **over-stocking** (tied-up cash flow & perished inventory).
- **Core Question**: *"How can a store owner know exactly what to reorder, when to reorder, and how much to reorder based on real data?"*

---

### Slide 3: Existing Challenges in Small-to-Mid Retail
- Reliance on subjective intuition and manual paper logbooks.
- Disconnected spreadsheets unable to capture day-of-week seasonality or lead times.
- Zero warning for impending stockouts until shelves are empty.
- Opaque "black-box" forecasting tools that lack shop owner trust.

---

### Slide 4: Proposed System Solution
- An integrated **3-tier web platform** connecting Point-of-Sale (POS), relational database tracking, and machine learning demand forecasting.
- Automated stockout and overstock risk detection.
- Deterministic, explainable replenishment recommendations with transparent mathematical justifications.
- Continuous forecast accuracy monitoring (MAE, RMSE, WAPE, Bias).

---

### Slide 5: Project Objectives
1. Implement atomic, ACID-compliant POS transaction processing.
2. Build an automated data pipeline with zero-demand grid aggregation.
3. Train and deploy a high-accuracy Random Forest time-series forecasting model.
4. Develop an Inventory Intelligence engine factoring in supplier lead times and safety stocks.
5. Provide deterministic "Why?" explainability for every reorder recommendation.
6. Enforce enterprise security: PBKDF2 password hashing, route protection, and store data isolation.

---

### Slide 6: System Architecture
- **3-Tier Architecture Diagram**:
  - **Frontend Tier**: React 18 + Vite Single Page Application.
  - **Backend Tier**: Python Flask REST API with Gunicorn WSGI.
  - **Database Tier**: MySQL 8.0+ with InnoDB storage engine (9 normalized tables).
  - **ML Engine**: Scikit-Learn pipeline with pre-trained joblib artifact.

---

### Slide 7: Technology Stack & Security
- **Frontend**: React 18, Chart.js, Lucide Icons, Vanilla CSS design tokens.
- **Backend**: Python Flask 3.0, Werkzeug Security, Flask-CORS, Gunicorn.
- **Database**: MySQL 8.0+ (ACID transactions, parameterized SQL).
- **Data Science**: Scikit-Learn, Pandas, NumPy, Joblib.
- **Security Guardrails**: Cryptographic PBKDF2:SHA256 password hashing, parameterized SQL, strictly ignored `.env` secrets.

---

### Slide 8: Machine Learning Demand Forecasting
- **Target Variable ($y$)**: Daily aggregated SKU demand.
- **Feature Engineering**:
  - Lag features: $t-1, t-7, t-14, t-28$.
  - Rolling statistics: 7-day, 14-day, 30-day moving averages and standard deviations.
- **Validation**: Chronological 80/20 train-test split preventing forward lookahead bias.
- **Model Choice**: Random Forest Regressor selected for capturing non-linear sales spikes.

---

### Slide 9: Inventory Intelligence & Explainability
- **Stockout Risk Rule**: $\text{Current Stock} \le \text{Lead-Time Demand} + \text{Safety Stock}$.
- **Reorder Formula**:
  $$Q = \max\Big(0,\; \lceil (\text{Forecasted Demand} + \text{Safety Stock}) - \text{Current Stock} - \text{Stock on Order} \rceil\Big)$$
- **Explainable Decision Support**: Interactive "Why?" modal explaining the exact step-by-step arithmetic to the store owner.

---

### Slide 10: Application Workflow & Live Demo Highlights
- Visual sequence of the 8 core application pages:
  - `Login` $\rightarrow$ `Dashboard` $\rightarrow$ `Inventory` $\rightarrow$ `POS Sales` $\rightarrow$ `Analytics` $\rightarrow$ `Demand Forecast` $\rightarrow$ `Inventory Intelligence` $\rightarrow$ `Forecast Monitoring`.
- Demonstration of atomic stock deduction during customer checkout.

---

### Slide 11: Validation, QA & Results
- **Automated Test Suite**: **80 passed out of 80 tests** (100% pass rate in Pytest).
- **Frontend Build**: Verified with Vite production build (`dist/` generated cleanly in 6.7s).
- **Error Tracking**: Live monitoring dashboard tracking MAE, RMSE, WAPE %, and Directional Bias.

---

### Slide 12: Limitations & Future Enhancements
- **Current MVP Scope**: Single-store deployment; human-in-the-loop decision support (recommends replenishment without automatic purchase order dispatch).
- **Future Roadmap**:
  - Multi-store warehouse synchronization.
  - Barcode camera scanning at POS.
  - Automated supplier purchase order email dispatch.
  - External event features (promotions, holidays, local weather).
