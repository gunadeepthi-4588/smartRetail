# SmartRetail — Real Retail Dataset Integration Guide

## 1. Dataset Overview

| Metadata Field | Value |
| :--- | :--- |
| **Dataset Name** | **FreshRetailNet-50K** |
| **Official Source** | [Hugging Face: Dingdong-Inc/FreshRetailNet-50K](https://huggingface.co/datasets/Dingdong-Inc/FreshRetailNet-50K) |
| **Research Citation** | *FreshRetailNet-50K: A Stockout-Annotated Censored Demand Dataset for Latent Demand Recovery and Forecasting in Fresh Retail* ([arXiv:2505.16319](https://arxiv.org/abs/2505.16319)) |
| **License** | Creative Commons Attribution 4.0 International (**CC BY 4.0**) |
| **Release Year** | **2025** |
| **Original Domain** | Large-scale fresh retail e-commerce & frontline fulfillment centers |

FreshRetailNet-50K is an open benchmark dataset comprising 50,000 store-product 90-day time series from 898 frontline fulfillment stores across 18 tier-1 cities, with explicit hourly stockout event annotations and contextual covariates.

---

## 2. Store & Product Selection

### 2.1 Selected Store
- **Store ID**: `Store 18` (Tier-1 Urban Frontline Fulfillment Superstore)
- **Selection Rationale**: Continuous chronological records spanning the full 90-day train series plus 7-day evaluation series (97 consecutive calendar days total), featuring high product diversity and high observation completeness.

### 2.2 Selected Product Portfolio
A balanced portfolio of **20 real retail products** across **8 core commercial categories** was selected to represent realistic retail dynamics (high-velocity staples, perishables, beverages, snacks, and seasonal fruits):

| Product ID | SKU | Product Name | Category | Supplier | Cost (₹) | Price (₹) | Safety Stock | Lead Time | Stockout % |
| :---: | :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **1** | `SKU-VEG-117` | Organic Baby Spinach 250g | Fresh Produce | Heritage Greens | 45.00 | 65.00 | 25 | 2 days | 45.4% |
| **2** | `SKU-VEG-070` | Fresh Broccoli Florets 500g | Fresh Produce | Heritage Greens | 50.00 | 75.00 | 20 | 2 days | 69.1% |
| **3** | `SKU-VEG-215` | Hydroponic Butter Lettuce 300g | Fresh Produce | Heritage Greens | 40.00 | 60.00 | 15 | 2 days | 67.0% |
| **4** | `SKU-VEG-019` | Tricolor Bell Peppers 400g | Fresh Produce | Heritage Greens | 60.00 | 90.00 | 15 | 2 days | 58.8% |
| **5** | `SKU-VEG-118` | Organic Cherry Tomatoes 250g | Fresh Produce | Heritage Greens | 35.00 | 55.00 | 15 | 2 days | 49.5% |
| **6** | `SKU-DRY-292` | Farm Fresh Pasteurized Milk 1L | Dairy & Eggs | Heritage Greens | 55.00 | 75.00 | 20 | 2 days | 48.5% |
| **7** | `SKU-FRT-300` | Premium Red Gala Apples 1kg | Fruits | Golden Harvest | 140.00 | 200.00 | 30 | 3 days | 55.7% |
| **8** | `SKU-FRT-104` | Fresh Cavendish Bananas 1kg | Fruits | Golden Harvest | 35.00 | 50.00 | 20 | 3 days | 58.8% |
| **9** | `SKU-FRT-486` | Seedless Sweet Mandarins 750g | Fruits | Golden Harvest | 90.00 | 130.00 | 15 | 3 days | 40.2% |
| **10** | `SKU-FRT-122` | Imported Green Kiwi 4-Pack | Fruits | Golden Harvest | 110.00 | 160.00 | 15 | 3 days | 54.6% |
| **11** | `SKU-PRT-691` | Fresh Chicken Breast Fillet 500g | Meat & Poultry | Golden Harvest | 160.00 | 230.00 | 25 | 2 days | 57.7% |
| **12** | `SKU-PRT-666` | Tender Chicken Thighs 500g | Meat & Poultry | Golden Harvest | 140.00 | 200.00 | 15 | 2 days | 41.2% |
| **13** | `SKU-SEA-783` | Atlantic Salmon Portions 300g | Seafood | Golden Harvest | 350.00 | 480.00 | 12 | 3 days | 35.1% |
| **14** | `SKU-BAK-413` | Artisan Sourdough Loaf 450g | Bakery | Sunrise Group | 70.00 | 110.00 | 20 | 2 days | 54.6% |
| **15** | `SKU-SNK-481` | Roasted Salted Almonds 200g | Snacks | Sunrise Group | 180.00 | 260.00 | 15 | 4 days | 59.8% |
| **16** | `SKU-BEV-580` | Pure Cold-Pressed Orange Juice 1L | Beverages | Sunrise Group | 85.00 | 130.00 | 20 | 2 days | 70.1% |
| **17** | `SKU-STP-004` | Organic Jasmine White Rice 2kg | Staples | PureCare Staples | 190.00 | 270.00 | 15 | 4 days | 37.1% |
| **18** | `SKU-BEV-600` | Natural Sparkling Water 750ml | Beverages | Sunrise Group | 40.00 | 65.00 | 15 | 3 days | 70.1% |
| **19** | `SKU-BEV-596` | Artisanal Green Tea Leaves 150g | Beverages | Sunrise Group | 120.00 | 180.00 | 15 | 3 days | 61.9% |
| **20** | `SKU-PNT-549` | Extra Virgin Olive Oil 500ml | Pantry | PureCare Staples | 280.00 | 390.00 | 12 | 4 days | 30.9% |

---

## 3. Dataset Volume & Temporal Span

- **Date Range**: `2024-03-28` to `2024-07-02` (97 consecutive calendar days)
- **Total Product-Day Observations**: `1,940` (20 products × 97 days)
- **Total Sales Transactions**: `97` daily POS transaction batches
- **Total Line Item Records (`sale_items`)**: `1,910`
- **Total Historical Units Sold**: `7,037 units`
- **Total Stockout-Adjusted Unconstrained Demand**: `9,775 units`
- **Stockout-Affected Observations**: `1,034 days` (53.3% across the portfolio)

---

## 4. Preprocessing & Import Pipeline

### 4.1 Automated Import Script
Located at [`backend/database/import_freshretail.py`](file:///c:/Users/sreec/OneDrive/Documents/Desktop/smartRetail/backend/database/import_freshretail.py):
1. **Remote Ingestion**: Fetches `train.parquet` (106 MB) and `eval.parquet` (8.4 MB) directly from Hugging Face into `backend/data_raw/` (gitignored).
2. **Filtering**: Extracts Store 18 and the 20 chosen product time-series.
3. **Relational Transformation**: Constructs compliant SQL seed scripts preserving store owner (User 1), 4 suppliers, 20 products, inventory master, and 97 daily transactions.
4. **Idempotent Seeding**: Applies clean seeding to MySQL / SQLite fallback without duplicate insertion risks.

### 4.2 Handling Stockout Censoring (Unconstrained Latent Demand Recovery)
In retail sales data, when an item stocks out midday, recorded sales drop to zero or plateau, not because customer demand disappeared, but because supply was exhausted. **Treating stockout-censored sales as true demand causes systemic under-forecasting and chronic stockouts.**

FreshRetailNet-50K provides `stock_hour6_22_cnt` (hours of stockout during 6:00–22:00 operating hours, $H_{\text{total}} = 16$).
We implement a two-tier unconstrained demand reconstruction:
1. **Partial Stockout ($1 \le H_{\text{stockout}} < 16$)**:
   $$\text{Demand}_{\text{unconstrained}} = \text{Demand}_{\text{observed}} \times \frac{16}{16 - H_{\text{stockout}}}$$
2. **Full-Day Stockout ($H_{\text{stockout}} = 16$, observed sales = 0)**:
   $$\text{Demand}_{\text{unconstrained}} = \text{Rolling 7-Day Uncensored Mean}(\text{Product})$$

---

## 5. Feature Engineering (Strictly Preventing Data Leakage)

All features are computed chronologically per product without using future lookahead:
- **Calendar & Seasonal Features**:
  - `day_of_week` (0–6)
  - `day_of_month` (1–31)
  - `week_of_year` (1–52)
  - `month` (1–12)
  - `is_weekend` (0 or 1)
- **Lag Features**:
  - `lag_1`, `lag_7`, `lag_14`, `lag_28` (computed via `groupby('product_id').shift(k)`)
- **Rolling Mean Features**:
  - `rolling_mean_7`, `rolling_mean_14`, `rolling_mean_28` (computed via `shift(1).rolling(w).mean()`, ensuring today's demand is never part of its own rolling predictor)
- **Categorical Features**:
  - One-hot category encodings (`cat_Fresh Produce`, `cat_Fruits`, `cat_Dairy & Eggs`, etc.)

---

## 6. Train / Validation / Test Chronological Partition

Data is partitioned strictly by date boundaries across all 20 products:

| Split Partition | Calendar Period | Days | Observations | Ratio |
| :--- | :---: | :---: | :---: | :---: |
| **Training Set** | `2024-03-28` to `2024-06-02` | 67 days | 1,340 rows | 70.0% |
| **Validation Set** | `2024-06-03` to `2024-06-17` | 15 days | 300 rows | 15.0% |
| **Held-Out Test Set** | `2024-06-18` to `2024-07-02` | 15 days | 300 rows | 15.0% |

---

## 7. Model Evaluation & Benchmark Results

### 7.1 Validation Leaderboard (15-Day Chronological Horizon)

| Model Name | MAE | RMSE | WAPE (%) | Forecast Bias | Selection Verdict |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Moving Average (7-Day)** | **1.2010** | **1.6273** | **26.55%** | **-0.1267** | **Selected Model (Lowest WAPE & MAE)** |
| **Ridge Regression ($\alpha=1.0$)** | 1.3590 | 1.7792 | 30.05% | +0.2039 | Best ML Linear Model |
| **Naive Baseline (Lag-1)** | 1.3633 | 2.0108 | 30.14% | -0.0100 | High variance baseline |
| **Gradient Boosting ($T=50, D=4$)** | 1.5527 | 2.1345 | 34.33% | +0.4770 | Tree ensemble |
| **Random Forest ($T=50, D=6$)** | 1.5859 | 2.0958 | 35.06% | +0.4425 | Tree ensemble |

### 7.2 Held-Out Test Set Performance (Final Validation)
- **Test Period**: `2024-06-18` to `2024-07-02` (300 observations)
- **Test WAPE**: `35.52%`
- **Test MAE**: `2.2295 units`
- **Test Bias**: `-0.3086 units`

---

## 8. Dataset Integration Workflow

```mermaid
graph LR
    A["FreshRetailNet-50K (Hugging Face)"] --> B["Store 18 (20 Products Filter)"]
    B --> C["Stockout Censoring Correction"]
    C --> D["seed.sql & Relational DB Seeding"]
    D --> E["Feature Engineering (Lags, Rolling, Calendar)"]
    E --> F["Chronological Train/Val/Test Split"]
    F --> G["Model Benchmark (MAE/RMSE/WAPE/Bias)"]
    G --> H["Persisted Model Artifact (.joblib)"]
    H --> I["Recursive Multi-Step Forecast (7/30 Days)"]
    I --> J["Inventory Intelligence & Reorder Calculation"]
    J --> K["Explainable Decision Engine (UI Display)"]
```

---

## 9. Limitations & Boundary Conditions

1. **Normalized Volumetric Units**: FreshRetailNet-50K scales volumetric sales by global coefficients. SmartRetail rounds these into discrete integer units.
2. **Catalog Pricing**: FreshRetailNet provides physical transaction volume and discounts, but does not provide purchase invoice costs in INR. Realistic unit purchase costs and selling prices have been mapped to preserve margin calculations (25–35% gross profit margin).
3. **Single Store Boundary**: In accordance with the SmartRetail single-owner architecture, Store 18 was isolated as the primary fulfillment store.
