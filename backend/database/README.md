# SmartRetail — Database Documentation

This directory contains the relational database definition, constraints, and realistic retail seed data for the SmartRetail single-store platform.

## 1. Relational Schema Architecture (`schema.sql`)

```
+-------------------+       +-------------------+       +-----------------------+
|      stores       |       |     products      |       |      inventory        |
+-------------------+       +-------------------+       +-----------------------+
| store_id (PK)     |<-----\| product_id (PK)   |<-----\| inventory_id (PK)     |
| name              |      || store_id (FK)     |      || product_id (FK, UQ)   |
| owner_name        |      || supplier_id (FK)  |      || current_stock         |
| currency          |      || sku (UNIQUE)      |      || min_stock_level       |
| currency_symbol   |      || name              |      || max_stock_level       |
| created_at        |      || category          |      || safety_stock          |
+-------------------+      || cost_price        |      || lead_time_days        |
                           || selling_price     |      || last_updated          |
                           || created_at        |      +-----------------------+
                           |+-------------------+
                           |         |
                           |         | (1:N)
                           |         v
+-------------------+      | +-------------------+       +-----------------------+
|      sales        |      | |    sale_items     |       |       forecasts       |
+-------------------+      | +-------------------+       +-----------------------+
| sale_id (PK)      |<-----|-| sale_item_id (PK) |       | forecast_id (PK)      |
| store_id (FK)     |      | | sale_id (FK)      |       | product_id (FK)       |
| receipt_number(UQ)|      | | product_id (FK)   |       | forecast_date         |
| total_amount      |      | | quantity          |       | target_date           |
| payment_method    |      | | unit_price        |       | predicted_demand      |
| sale_date         |      | | unit_cost         |       | actual_demand (NULL)  |
+-------------------+      | +-------------------+       | model_name            |
                           |                             | horizon_days          |
                           |                             +-----------------------+
                           v
               +-----------------------------+
               |   reorder_recommendations   |
               +-----------------------------+
               | recommendation_id (PK)      |
               | product_id (FK)             |
               | calculation_date            |
               | predicted_demand            |
               | current_stock               |
               | safety_stock                |
               | lead_time_demand            |
               | recommended_quantity        |
               | status (Pending/Reviewed)   |
               | created_at                  |
               +-----------------------------+
```

## 2. Table Summary

| Table | Primary Key | Foreign Keys | Key Constraints / Indexes |
| :--- | :--- | :--- | :--- |
| `stores` | `store_id` | - | Currency default 'INR', symbol '₹' |
| `users` | `user_id` | `store_id -> stores` | `username` (UQ), `email` (UQ) |
| `suppliers` | `supplier_id` | `store_id -> stores` | Lead times per supplier |
| `products` | `product_id` | `store_id -> stores`, `supplier_id -> suppliers` | `sku` (UQ), INDEX(`category`) |
| `inventory` | `inventory_id` | `product_id -> products` | `product_id` (UQ), INDEX(`current_stock`) |
| `sales` | `sale_id` | `store_id -> stores` | `receipt_number` (UQ), INDEX(`sale_date`) |
| `sale_items` | `sale_item_id` | `sale_id -> sales`, `product_id -> products` | INDEX(`product_id`), INDEX(`sale_id`) |
| `forecasts` | `forecast_id` | `product_id -> products` | `actual_demand` NULLABLE |
| `reorder_recommendations` | `recommendation_id` | `product_id -> products` | Step-by-step reorder calculation |

## 3. How to Initialize and Verify

### Method 1: Using Python Runner (Recommended)
Ensure your `.env` contains your MySQL password:
```bash
cd backend
python database/init_db.py
```

### Method 2: Using MySQL CLI Directly
```bash
mysql -u root -p < database/schema.sql
mysql -u root -p < database/seed.sql
```
