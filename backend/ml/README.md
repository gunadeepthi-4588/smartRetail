# SmartRetail — Demand Forecasting ML Pipeline (Phase 10)

## Overview
This module implements the **Baseline-First Machine Learning Demand Forecasting Pipeline** for SmartRetail.
It transforms raw transactional sales data into a continuous multi-product daily time-series, engineers leakage-free lag and rolling features, evaluates candidate models against simple baselines on chronological validation windows, and persists the optimal model artifact for downstream API serving.

---

## 1. Machine Learning Workflow Architecture

```
MySQL Sales Data / Seed Transactions
         │
         ▼
[data_loader.py] ──> Data Validation (Missing IDs, Invalid Quantities, Non-negative Checks)
         │
         ▼
[preprocessing.py] ──> Daily Aggregation & Continuous Cartesian Zero-Demand Grid
         │
         ▼
[features.py] ──> Feature Engineering (Lags: t-1, t-7, t-14, t-28 | Shifted Rolling Means | Calendar Seasonality)
         │
         ▼
[forecasting.py] ──> Chronological Split (Train: 70% | Validation: 15% | Test: 15%)
         │
         ├──────────────────────────┬──────────────────────────┐
         ▼                          ▼                          ▼
   Naive Baseline          7-Day Moving Avg             Ridge Regression
         │                          │                          │
         └──────────────────────────┼──────────────────────────┘
                                    ▼
                         Random Forest Regressor
                                    │
                                    ▼
[evaluation.py] ──> Model Comparison (MAE, RMSE, WAPE %, Forecast Bias)
                                    │
                                    ▼
[train.py] ──> Model Selection & Artifact Persistence (joblib + metadata JSON)
```

---

## 2. Feature Definitions (Zero Future-Data Leakage)

| Feature | Type | Definition / Mathematical Formula |
|---|---|---|
| `lag_1` | Lag | Quantity sold on day $t-1$ |
| `lag_7` | Lag | Quantity sold on day $t-7$ (same day of previous week) |
| `lag_14` | Lag | Quantity sold on day $t-14$ (2 weeks prior) |
| `lag_28` | Lag | Quantity sold on day $t-28$ (4 weeks prior) |
| `rolling_mean_7` | Rolling | $\frac{1}{7}\sum_{i=1}^7 y_{t-i}$ (Past 7 days only, shifted by 1) |
| `rolling_mean_14` | Rolling | $\frac{1}{14}\sum_{i=1}^{14} y_{t-i}$ (Past 14 days only, shifted by 1) |
| `rolling_mean_28` | Rolling | $\frac{1}{28}\sum_{i=1}^{28} y_{t-i}$ (Past 28 days only, shifted by 1) |
| `day_of_week` | Calendar | Integer 0 (Monday) to 6 (Sunday) |
| `is_weekend` | Calendar | Binary 1 (Saturday/Sunday) or 0 (Weekday) |
| `day_of_month` | Calendar | Integer 1 to 31 |
| `month` | Calendar | Integer 1 to 12 |
| `cat_*` | Category | One-hot encoded product category indicators |

---

## 3. Evaluation Metrics

1. **MAE (Mean Absolute Error)**:
   $$\text{MAE} = \frac{1}{N} \sum_{i=1}^N |y_i - \hat{y}_i|$$
2. **RMSE (Root Mean Squared Error)**:
   $$\text{RMSE} = \sqrt{\frac{1}{N} \sum_{i=1}^N (y_i - \hat{y}_i)^2}$$
3. **WAPE (Weighted Absolute Percentage Error)**:
   $$\text{WAPE} = \frac{\sum_{i=1}^N |y_i - \hat{y}_i|}{\sum_{i=1}^N y_i}$$
4. **Forecast Bias**:
   $$\text{Bias} = \frac{1}{N} \sum_{i=1}^N (\hat{y}_i - y_i)$$

---

## 4. Model Comparison & Selection Results

| Model | MAE | RMSE | WAPE % | Bias | Selection |
|---|---|---|---|---|---|
| **Random Forest (trees=50, depth=6)** | **0.5463** | **1.2719** | **136.58%** | **+0.0370** | **WINNER (Selected)** |
| Moving Average (7-Day) | 0.5625 | 0.9638 | 140.63% | -0.0196 | Baseline Benchmark |
| Naive (Lag-1) | 0.6375 | 1.2796 | 159.38% | -0.0125 | Baseline Benchmark |
| Ridge Regression ($\alpha=1.0$) | 0.6510 | 1.2505 | 162.75% | +0.2735 | Linear Benchmark |

### Held-Out Test Set Performance (Selected Random Forest):
- **Test WAPE**: `123.41%`
- **Test MAE**: `0.5307` units
- **Test Forecast Bias**: `-0.0489` (balanced, negligible under-forecasting)

---

## 5. Saved Artifacts
- Model binary: `backend/ml/saved_models/demand_forecast_model.joblib`
- Pipeline metadata: `backend/ml/saved_models/model_metadata.json`
