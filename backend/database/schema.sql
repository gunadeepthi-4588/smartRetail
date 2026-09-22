-- ==============================================================================
-- SmartRetail Database Schema
-- Architecture: Single-Store, Single-Owner Retail Inventory & Demand Forecasting
-- Database Engine: MySQL 8.0+ / InnoDB
-- ==============================================================================

CREATE DATABASE IF NOT EXISTS smart_retail_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE smart_retail_db;

-- ------------------------------------------------------------------------------
-- 1. STORES
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS stores (
    store_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    owner_name VARCHAR(100) NOT NULL,
    currency VARCHAR(10) NOT NULL DEFAULT 'INR',
    currency_symbol VARCHAR(5) NOT NULL DEFAULT '₹',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ------------------------------------------------------------------------------
-- 2. USERS (Store Owner Login)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    store_id INT NOT NULL,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_users_store FOREIGN KEY (store_id) REFERENCES stores(store_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ------------------------------------------------------------------------------
-- 3. SUPPLIERS
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id INT AUTO_INCREMENT PRIMARY KEY,
    store_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    contact_name VARCHAR(100) NULL,
    email VARCHAR(100) NULL,
    phone VARCHAR(20) NULL,
    lead_time_days INT NOT NULL DEFAULT 3,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_suppliers_store FOREIGN KEY (store_id) REFERENCES stores(store_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ------------------------------------------------------------------------------
-- 4. PRODUCTS
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS products (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    store_id INT NOT NULL,
    supplier_id INT NULL,
    sku VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(150) NOT NULL,
    category VARCHAR(50) NOT NULL,
    cost_price DECIMAL(10, 2) NOT NULL,
    selling_price DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_products_store FOREIGN KEY (store_id) REFERENCES stores(store_id) ON DELETE CASCADE,
    CONSTRAINT fk_products_supplier FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id) ON DELETE SET NULL,
    INDEX idx_products_category (category),
    INDEX idx_products_store (store_id)
) ENGINE=InnoDB;

-- ------------------------------------------------------------------------------
-- 5. INVENTORY
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS inventory (
    inventory_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL UNIQUE,
    current_stock INT NOT NULL DEFAULT 0,
    min_stock_level INT NOT NULL DEFAULT 10,
    max_stock_level INT NOT NULL DEFAULT 200,
    safety_stock INT NOT NULL DEFAULT 20,
    lead_time_days INT NOT NULL DEFAULT 3,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_inventory_product FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
    INDEX idx_inventory_stock (current_stock)
) ENGINE=InnoDB;

-- ------------------------------------------------------------------------------
-- 6. SALES
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sales (
    sale_id INT AUTO_INCREMENT PRIMARY KEY,
    store_id INT NOT NULL,
    receipt_number VARCHAR(50) NOT NULL UNIQUE,
    total_amount DECIMAL(10, 2) NOT NULL,
    payment_method VARCHAR(30) NOT NULL DEFAULT 'Cash', -- 'Cash', 'Card', 'UPI'
    sale_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_sales_store FOREIGN KEY (store_id) REFERENCES stores(store_id) ON DELETE CASCADE,
    INDEX idx_sales_date (sale_date),
    INDEX idx_sales_store (store_id)
) ENGINE=InnoDB;

-- ------------------------------------------------------------------------------
-- 7. SALE_ITEMS
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sale_items (
    sale_item_id INT AUTO_INCREMENT PRIMARY KEY,
    sale_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    unit_cost DECIMAL(10, 2) NOT NULL,
    CONSTRAINT fk_sale_items_sale FOREIGN KEY (sale_id) REFERENCES sales(sale_id) ON DELETE CASCADE,
    CONSTRAINT fk_sale_items_product FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE RESTRICT,
    INDEX idx_sale_items_product (product_id),
    INDEX idx_sale_items_sale (sale_id)
) ENGINE=InnoDB;

-- ------------------------------------------------------------------------------
-- 8. FORECASTS (Populated in ML Phases)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS forecasts (
    forecast_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    forecast_date DATE NOT NULL,
    target_date DATE NOT NULL,
    predicted_demand DECIMAL(10, 2) NOT NULL,
    actual_demand DECIMAL(10, 2) NULL DEFAULT NULL,
    model_name VARCHAR(50) NOT NULL,
    horizon_days INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_forecasts_product FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
    INDEX idx_forecasts_product_target (product_id, target_date)
) ENGINE=InnoDB;

-- ------------------------------------------------------------------------------
-- 9. REORDER_RECOMMENDATIONS (Populated in Inventory Intelligence Phase)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reorder_recommendations (
    recommendation_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    calculation_date DATE NOT NULL,
    predicted_demand DECIMAL(10, 2) NOT NULL,
    current_stock INT NOT NULL,
    safety_stock INT NOT NULL,
    lead_time_demand DECIMAL(10, 2) NOT NULL,
    recommended_quantity INT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Pending', -- 'Pending', 'Reviewed', 'Dismissed'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_reorder_product FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
    INDEX idx_reorder_product (product_id)
) ENGINE=InnoDB;
