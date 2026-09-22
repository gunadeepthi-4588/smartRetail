# SmartRetail — REST API Reference Documentation

This document provides a comprehensive reference for all REST API endpoints exposed by the Flask backend application factory (`/api/*`).

---

## 1. System & Health Endpoints

### `GET /api/health`
- **Description**: Returns general backend operational status and service metadata.
- **Parameters**: None
- **Response `200 OK`**:
```json
{
  "status": "healthy",
  "service": "smartretail-backend",
  "version": "1.0.0"
}
```

### `GET /api/health/db`
- **Description**: Executes lightweight ping against MySQL database and verifies table integrity without leaking connection credentials.
- **Parameters**: None
- **Response `200 OK`**:
```json
{
  "status": "connected",
  "database_name": "smart_retail_db",
  "tables_found": 9,
  "ping": true
}
```

---

## 2. Product Catalog Management

### `GET /api/products`
- **Description**: Retrieves list of products with inventory metrics and supplier details.
- **Query Parameters**:
  - `category` *(optional string)*: Filter by category (e.g. `Beverages`, `Snacks`, `Dairy`).
  - `search` *(optional string)*: Search by SKU or product name.
  - `supplier_id` *(optional int)*: Filter by supplier ID.
- **Response `200 OK`**:
```json
{
  "status": "success",
  "count": 1,
  "data": [
    {
      "product_id": 1,
      "sku": "SKU-BEV-001",
      "name": "Masala Chai Tea Bags 250g",
      "category": "Beverages",
      "cost_price": 90.0,
      "selling_price": 135.0,
      "current_stock": 25,
      "safety_stock": 10,
      "min_stock_level": 15,
      "max_stock_level": 100,
      "lead_time_days": 2,
      "supplier_name": "Heritage Beverages Ltd"
    }
  ]
}
```

### `GET /api/products/<product_id>`
- **Description**: Retrieves detailed information for a single product.
- **Response `200 OK`** or `404 Not Found`.

### `POST /api/products`
- **Description**: Creates a new product and initializes an inventory record with default safety stock and lead times.
- **Request Body**:
```json
{
  "store_id": 1,
  "supplier_id": 1,
  "sku": "SKU-SNK-005",
  "name": "Roasted Cashews 200g",
  "category": "Snacks",
  "cost_price": 180.0,
  "selling_price": 260.0,
  "current_stock": 30,
  "min_stock_level": 10,
  "max_stock_level": 100,
  "safety_stock": 8,
  "lead_time_days": 3
}
```
- **Response `201 Created`**

### `PUT /api/products/<product_id>`
- **Description**: Updates product master details (name, category, prices, supplier).

### `DELETE /api/products/<product_id>`
- **Description**: Safely deletes product if no sales history references it; rejects deletion if historical transactions exist.

---

## 3. Inventory Operations

### `GET /api/inventory`
- **Description**: Retrieves stock status and replenishment thresholds across the catalog.
- **Query Parameters**:
  - `status` *(optional)*: `HEALTHY`, `LOW_STOCK`, `OUT_OF_STOCK`, `OVERSTOCK`, `All`.
  - `category` *(optional)*: Filter by category.
  - `search` *(optional)*: Filter by name or SKU.
- **Response `200 OK`**:
```json
{
  "status": "success",
  "count": 1,
  "data": [
    {
      "product_id": 1,
      "sku": "SKU-BEV-001",
      "name": "Masala Chai Tea Bags 250g",
      "category": "Beverages",
      "current_stock": 12,
      "safety_stock": 10,
      "min_stock_level": 15,
      "max_stock_level": 100,
      "stock_status": "LOW_STOCK"
    }
  ]
}
```

### `PUT /api/inventory/<product_id>`
- **Description**: Adjusts physical stock count or updates replenishment configuration (`min_stock_level`, `max_stock_level`, `safety_stock`, `lead_time_days`).

---

## 4. Sales & POS Transactions

### `GET /api/sales`
- **Description**: Retrieves historical transaction records with receipt numbers and item totals.
- **Query Parameters**:
  - `limit` *(optional int, default 50)*
  - `payment_method` *(optional string: `Cash`, `Card`, `UPI`)*

### `GET /api/sales/<sale_id>`
- **Description**: Retrieves full itemized receipt for a transaction.

### `POST /api/sales`
- **Description**: Atomic sales transaction creation and inventory deduction. If any item has insufficient stock, the entire transaction rolls back.
- **Request Body**:
```json
{
  "store_id": 1,
  "payment_method": "UPI",
  "items": [
    {
      "product_id": 1,
      "quantity": 2,
      "unit_price": 135.0
    },
    {
      "product_id": 6,
      "quantity": 3,
      "unit_price": 35.0
    }
  ]
}
```
- **Response `201 Created`**:
```json
{
  "status": "success",
  "message": "Sale created and inventory updated successfully.",
  "data": {
    "sale_id": 42,
    "receipt_number": "REC-20260922-042",
    "total_amount": 375.0,
    "items_count": 2,
    "payment_method": "UPI"
  }
}
```

---

## 5. Analytics & Business Intelligence

### `GET /api/analytics/dashboard`
- **Description**: Aggregates today's and 30-day KPIs: Revenue, Gross Profit, Total Units Sold, Transactions, Out-of-Stock count, and Low-Stock alerts.
- **Response `200 OK`**:
```json
{
  "status": "success",
  "data": {
    "financial_kpis": {
      "today_revenue": 1620.0,
      "today_transactions": 2,
      "revenue_30d": 37685.0,
      "gross_profit_30d": 11493.0,
      "units_sold_30d": 247,
      "transactions_30d": 30,
      "gross_margin_pct_30d": 30.5
    },
    "inventory_kpis": {
      "total_products": 20,
      "out_of_stock_count": 1,
      "low_stock_count": 3,
      "overstock_count": 2,
      "healthy_stock_count": 14
    }
  }
}
```

### `GET /api/analytics/sales-trend?days=30`
- **Description**: Returns daily sales, revenue, and gross profit time-series for Chart.js area/line charts.

### `GET /api/analytics/top-products?days=30&limit=5`
- **Description**: Returns top products ranked separately by volume (units sold), revenue, and gross profit.

### `GET /api/analytics/slow-movers?days_threshold=14`
- **Description**: Identifies products with low daily velocity and excess stock capital tied up.

### `GET /api/analytics/category-performance?days=30`
- **Description**: Aggregates revenue, profit, and units sold grouped by retail category.

---

## 6. Machine Learning Demand Forecasting

### `POST /api/forecast`
- **Description**: Generates multi-step recursive demand predictions for a specified product and horizon.
- **Request Body**:
```json
{
  "product_id": 1,
  "horizon_days": 7
}
```
- **Response `201 Created`**:
```json
{
  "status": "success",
  "data": {
    "product": {
      "product_id": 1,
      "sku": "SKU-BEV-001",
      "name": "Masala Chai Tea Bags 250g",
      "category": "Beverages"
    },
    "forecast_run_date": "2026-09-22",
    "horizon_days": 7,
    "model_name": "Random Forest (trees=50, depth=6)",
    "total_projected_demand": 21.5,
    "avg_daily_projected_demand": 3.07,
    "predictions": [
      {
        "target_date": "2026-09-23",
        "predicted_demand": 3.2,
        "day_of_week": "Wednesday"
      }
    ]
  }
}
```

### `GET /api/forecast/<product_id>?horizon_days=7`
- **Description**: Fetches latest stored forecast alongside the last 14 days of historical sales.

---

## 7. Inventory Intelligence & Explainable Recommendations

### `GET /api/inventory/intelligence`
- **Description**: Runs risk assessment across all products: stockout risk, overstock risk, lead-time demand, safety stock, and recommended reorders.
- **Query Parameters**:
  - `days` *(optional int, default 7)*: Planning horizon.

### `GET /api/recommendations`
- **Description**: Returns prioritized purchasing recommendations with full mathematical explanations for the store owner.
- **Query Parameters**:
  - `days` *(optional int, default 7)*
  - `status` *(optional: `REORDER`, `NO_REORDER`)*
- **Response `200 OK`**:
```json
{
  "status": "success",
  "count": 1,
  "data": [
    {
      "product_id": 1,
      "sku": "SKU-BEV-001",
      "name": "Masala Chai Tea Bags 250g",
      "current_stock": 12,
      "recommended_quantity": 20,
      "recommendation_status": "REORDER",
      "stockout_risk": true,
      "overstock_risk": false,
      "explanation": {
        "reorder": {
          "recommended": true,
          "recommended_quantity": 20,
          "required_stock": 32,
          "forecasted_demand": 24,
          "safety_stock": 8,
          "current_stock": 12,
          "stock_on_order": 0,
          "formula": "Required Stock (Forecasted Demand + Safety Stock) - Current Stock - Stock on Order",
          "calculation_string": "(24 + 8) - 12 - 0 = 20.00 -> 20 units",
          "reason": "Expected demand (24 units over 7 days) plus safety stock (8 units) is higher than current available stock (12 units)."
        },
        "stockout_risk": {
          "risk_detected": true,
          "lead_time_days": 2,
          "lead_time_demand": 10,
          "safety_stock": 8,
          "lead_time_required_stock": 18,
          "stockout_gap": 6,
          "reason": "Stockout risk is detected because current stock (12 units) is below expected demand during supplier lead time (10 units over 2 days) plus safety stock (8 units)."
        },
        "decision_protocol": {
          "human_in_the_loop": true,
          "statement": "SmartRetail is a decision-support platform. The store owner always makes the final purchasing decision. No automated orders are placed."
        }
      }
    }
  ]
}
```

---

## 8. Forecast Monitoring & Model Performance

### `GET /api/monitoring/forecast`
- **Description**: Returns item-level comparison between predicted demand and actual sales for target dates that have passed.
- **Query Parameters**:
  - `product_id` *(optional int)*
  - `days` *(optional int: 7, 30, 90)*
  - `model_name` *(optional string)*
- **Response `200 OK`**:
```json
{
  "status": "success",
  "product_id": 1,
  "days": 30,
  "model_name": "Random Forest (trees=50, depth=6)",
  "sample_count": 30,
  "data": [
    {
      "date": "2026-09-01",
      "predicted_demand": 10.0,
      "actual_demand": 12.0,
      "error": 2.0,
      "absolute_error": 2.0,
      "percentage_error": 16.67,
      "model_name": "Random Forest (trees=50, depth=6)"
    }
  ]
}
```

### `GET /api/monitoring/summary`
- **Description**: Computes aggregate performance metrics ($\text{MAE}$, $\text{RMSE}$, $\text{WAPE}$, $\text{Bias}$), sample observations, model metadata, and neutral deterministic interpretations.
- **Response `200 OK`**:
```json
{
  "status": "success",
  "product_id": 1,
  "period_days": 30,
  "metrics": {
    "mae": 1.45,
    "rmse": 1.82,
    "wape": 0.11,
    "wape_pct": 11.0,
    "bias": 0.25
  },
  "sample_count": 30,
  "model_name": "Random Forest (trees=50, depth=6)",
  "interpretation": "Forecasts are, on average, higher than actual demand during the selected period.",
  "data_freshness": {
    "last_forecast_date": "2026-09-20",
    "last_actual_date": "2026-09-20",
    "insufficient_data": false
  }
}
```

### `POST /api/monitoring/reconcile`
- **Description**: Safely triggers synchronization of concluded sales data into the `forecasts.actual_demand` column.
