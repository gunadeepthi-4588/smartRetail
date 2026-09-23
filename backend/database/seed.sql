-- ==============================================================================
-- SmartRetail Realistic Seed Data
-- 1 Store | 1 Owner | 4 Suppliers | 20 Products | 40+ Sales Transactions
-- Designed for Analytics, Risk Detection & Demand Forecasting Validation
-- ==============================================================================

USE smart_retail_db;

-- Clear any existing data in reverse order of foreign keys
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE reorder_recommendations;
TRUNCATE TABLE forecasts;
TRUNCATE TABLE sale_items;
TRUNCATE TABLE sales;
TRUNCATE TABLE inventory;
TRUNCATE TABLE products;
TRUNCATE TABLE suppliers;
TRUNCATE TABLE users;
TRUNCATE TABLE stores;
SET FOREIGN_KEY_CHECKS = 1;

-- ------------------------------------------------------------------------------
-- 1. STORE
-- ------------------------------------------------------------------------------
INSERT INTO stores (store_id, name, owner_name, currency, currency_symbol, created_at)
VALUES (1, 'Metro Mart Superstore', 'Rajesh Kumar', 'INR', '₹', '2026-01-01 08:00:00');

-- ------------------------------------------------------------------------------
-- 2. USERS (Store Owner)
-- ------------------------------------------------------------------------------
-- Demo account: owner@smartretail.com | Secure PBKDF2:SHA256 password hash
INSERT INTO users (user_id, store_id, username, password_hash, email, created_at)
VALUES (1, 1, 'rajesh_owner', 'pbkdf2:sha256:1000000$BdZ61SZ126aQxfRY$4158b14a266270a1bf746a363d50687a3e5ae7d924d4c958eaf9eece8c0e766c', 'owner@smartretail.com', '2026-01-01 08:30:00');

-- ------------------------------------------------------------------------------
-- 3. SUPPLIERS (With varying lead times)
-- ------------------------------------------------------------------------------
INSERT INTO suppliers (supplier_id, store_id, name, contact_name, email, phone, lead_time_days, created_at) VALUES
(1, 1, 'Heritage Dairy & Beverages Ltd.', 'Sunil Sharma', 'orders@heritagedairy.com', '+91 98765 43210', 2, '2026-01-02 09:00:00'),
(2, 1, 'Golden Harvest Foods & Grains', 'Pooja Verma', 'supply@goldenharvest.in', '+91 98765 43211', 4, '2026-01-02 09:15:00'),
(3, 1, 'Sunrise Snacks & Confectionery', 'Amit Patel', 'sales@sunrisesnacks.com', '+91 98765 43212', 3, '2026-01-02 09:30:00'),
(4, 1, 'PureCare Personal & Home Essentials', 'Neha Gupta', 'distrib@purecare.com', '+91 98765 43213', 5, '2026-01-02 09:45:00');

-- ------------------------------------------------------------------------------
-- 4. PRODUCTS (20 Items across 5 Categories)
-- ------------------------------------------------------------------------------
INSERT INTO products (product_id, store_id, supplier_id, sku, name, category, cost_price, selling_price, created_at) VALUES
-- Beverages
(1, 1, 1, 'SKU-BEV-001', 'Masala Chai Tea Bags 250g', 'Beverages', 90.00, 135.00, '2026-01-05 10:00:00'),
(2, 1, 1, 'SKU-BEV-002', 'Arabica Filter Coffee 500g', 'Beverages', 220.00, 330.00, '2026-01-05 10:05:00'),
(3, 1, 1, 'SKU-BEV-003', 'Alphonso Mango Nectar 1L', 'Beverages', 65.00, 95.00, '2026-01-05 10:10:00'),
(4, 1, 1, 'SKU-BEV-004', 'Sparkling Lime Soda 750ml', 'Beverages', 30.00, 45.00, '2026-01-05 10:15:00'),

-- Snacks
(5, 1, 3, 'SKU-SNK-001', 'Roasted Salted Cashews 200g', 'Snacks', 180.00, 260.00, '2026-01-05 10:20:00'),
(6, 1, 3, 'SKU-SNK-002', 'Classic Salted Potato Crisps 100g', 'Snacks', 20.00, 35.00, '2026-01-05 10:25:00'),
(7, 1, 3, 'SKU-SNK-003', 'Multigrain Digestive Biscuits 400g', 'Snacks', 45.00, 70.00, '2026-01-05 10:30:00'),
(8, 1, 3, 'SKU-SNK-004', 'Spicy Corn Nachos 150g', 'Snacks', 38.00, 60.00, '2026-01-05 10:35:00'),

-- Staples
(9, 1, 2, 'SKU-STP-001', 'Premium Basmati Rice 5kg', 'Staples', 420.00, 560.00, '2026-01-05 10:40:00'),
(10, 1, 2, 'SKU-STP-002', 'Whole Wheat Atta 10kg', 'Staples', 340.00, 450.00, '2026-01-05 10:45:00'),
(11, 1, 2, 'SKU-STP-003', 'Cold Pressed Mustard Oil 1L', 'Staples', 140.00, 195.00, '2026-01-05 10:50:00'),
(12, 1, 2, 'SKU-STP-004', 'Organic Toor Dal 1kg', 'Staples', 110.00, 155.00, '2026-01-05 10:55:00'),

-- Personal Care
(13, 1, 4, 'SKU-PC-001', 'Herbal Neem Handwash 500ml', 'Personal Care', 85.00, 130.00, '2026-01-05 11:00:00'),
(14, 1, 4, 'SKU-PC-002', 'Coconut Nourishing Shampoo 350ml', 'Personal Care', 150.00, 230.00, '2026-01-05 11:05:00'),
(15, 1, 4, 'SKU-PC-003', 'Sandalwood Soap Pack of 3', 'Personal Care', 95.00, 145.00, '2026-01-05 11:10:00'),
(16, 1, 4, 'SKU-PC-004', 'Mint Cooling Toothpaste 150g', 'Personal Care', 55.00, 85.00, '2026-01-05 11:15:00'),

-- Household
(17, 1, 4, 'SKU-HH-001', 'Citrus Floor Cleaner 1L', 'Household', 80.00, 125.00, '2026-01-05 11:20:00'),
(18, 1, 4, 'SKU-HH-002', 'Concentrated Dishwash Gel 750ml', 'Household', 90.00, 140.00, '2026-01-05 11:25:00'),
(19, 1, 4, 'SKU-HH-003', 'Biodegradable Garbage Bags 30s', 'Household', 70.00, 110.00, '2026-01-05 11:30:00'),
(20, 1, 4, 'SKU-HH-004', 'Microfiber Cleaning Cloth 3-Pack', 'Household', 60.00, 100.00, '2026-01-05 11:35:00');

-- ------------------------------------------------------------------------------
-- 5. INVENTORY (Varying stock levels to showcase low stock, healthy, and overstock)
-- ------------------------------------------------------------------------------
INSERT INTO inventory (inventory_id, product_id, current_stock, min_stock_level, max_stock_level, safety_stock, lead_time_days, last_updated) VALUES
-- Low Stock Risks (< Safety Stock)
(1, 1, 12, 30, 150, 25, 2, '2026-09-20 18:00:00'),  -- Masala Chai: Low Stock!
(2, 6, 8, 35, 200, 30, 3, '2026-09-20 18:00:00'),   -- Potato Crisps: Critically Low!
(3, 9, 7, 20, 100, 15, 4, '2026-09-20 18:00:00'),   -- Basmati Rice: Low Stock!

-- Healthy Stock Levels
(4, 2, 45, 15, 80, 15, 2, '2026-09-20 18:00:00'),   -- Arabica Coffee: Healthy
(5, 3, 60, 20, 120, 20, 2, '2026-09-20 18:00:00'),  -- Mango Nectar: Healthy
(6, 4, 85, 25, 150, 25, 2, '2026-09-20 18:00:00'),  -- Lime Soda: Healthy
(7, 5, 35, 15, 70, 15, 3, '2026-09-20 18:00:00'),   -- Cashews: Healthy
(8, 7, 50, 20, 100, 20, 3, '2026-09-20 18:00:00'),  -- Biscuits: Healthy
(9, 8, 40, 15, 90, 15, 3, '2026-09-20 18:00:00'),   -- Nachos: Healthy
(10, 10, 28, 15, 80, 15, 4, '2026-09-20 18:00:00'), -- Wheat Atta: Healthy
(11, 11, 38, 15, 80, 15, 4, '2026-09-20 18:00:00'), -- Mustard Oil: Healthy
(12, 12, 42, 20, 100, 20, 4, '2026-09-20 18:00:00'),-- Toor Dal: Healthy
(13, 13, 32, 15, 75, 15, 5, '2026-09-20 18:00:00'), -- Handwash: Healthy
(14, 15, 55, 20, 100, 20, 5, '2026-09-20 18:00:00'),-- Soap: Healthy
(15, 16, 48, 15, 90, 15, 5, '2026-09-20 18:00:00'), -- Toothpaste: Healthy
(16, 17, 30, 15, 70, 15, 5, '2026-09-20 18:00:00'), -- Floor Cleaner: Healthy
(17, 18, 35, 15, 80, 15, 5, '2026-09-20 18:00:00'), -- Dishwash: Healthy
(18, 19, 40, 15, 80, 15, 5, '2026-09-20 18:00:00'), -- Garbage Bags: Healthy

-- Overstocked / Slow-Moving Candidates (Stock >> 30-Day Demand)
(19, 14, 110, 15, 60, 15, 5, '2026-09-20 18:00:00'), -- Shampoo: Overstocked!
(20, 20, 165, 10, 50, 10, 5, '2026-09-20 18:00:00'); -- Microfiber Cloth: Heavily Overstocked!

-- ------------------------------------------------------------------------------
-- 6. SALES & SALE_ITEMS (Historical Sales over 30 Days)
-- ------------------------------------------------------------------------------

-- Transaction 1 (2026-08-22)
INSERT INTO sales (sale_id, store_id, receipt_number, total_amount, payment_method, sale_date) VALUES
(1, 1, 'REC-20260822-001', 1345.00, 'UPI', '2026-08-22 10:15:00');
INSERT INTO sale_items (sale_item_id, sale_id, product_id, quantity, unit_price, unit_cost) VALUES
(1, 1, 1, 3, 135.00, 90.00),
(2, 1, 6, 5, 35.00, 20.00),
(3, 1, 9, 1, 560.00, 420.00),
(4, 1, 3, 2, 95.00, 65.00),
(5, 1, 7, 3, 70.00, 45.00);

-- Transaction 2 (2026-08-23)
INSERT INTO sales (sale_id, store_id, receipt_number, total_amount, payment_method, sale_date) VALUES
(2, 1, 'REC-20260823-002', 880.00, 'Cash', '2026-08-23 11:30:00');
INSERT INTO sale_items (sale_item_id, sale_id, product_id, quantity, unit_price, unit_cost) VALUES
(6, 2, 2, 2, 330.00, 220.00),
(7, 2, 5, 1, 260.00, 180.00);

-- Transaction 3 (2026-08-24)
INSERT INTO sales (sale_id, store_id, receipt_number, total_amount, payment_method, sale_date) VALUES
(3, 1, 'REC-20260824-003', 1195.00, 'Card', '2026-08-24 14:20:00');
INSERT INTO sale_items (sale_item_id, sale_id, product_id, quantity, unit_price, unit_cost) VALUES
(8, 3, 10, 2, 450.00, 340.00),
(9, 3, 11, 1, 195.00, 140.00),
(10, 3, 12, 1, 155.00, 110.00);

-- Transaction 4 (2026-08-25)
INSERT INTO sales (sale_id, store_id, receipt_number, total_amount, payment_method, sale_date) VALUES
(4, 1, 'REC-20260825-004', 590.00, 'UPI', '2026-08-25 16:45:00');
INSERT INTO sale_items (sale_item_id, sale_id, product_id, quantity, unit_price, unit_cost) VALUES
(11, 4, 6, 8, 35.00, 20.00),
(12, 4, 1, 2, 135.00, 90.00),
(13, 4, 4, 1, 45.00, 30.00);

-- Transaction 5 (2026-08-26)
INSERT INTO sales (sale_id, store_id, receipt_number, total_amount, payment_method, sale_date) VALUES
(5, 1, 'REC-20260826-005', 980.00, 'Cash', '2026-08-26 18:10:00');
INSERT INTO sale_items (sale_item_id, sale_id, product_id, quantity, unit_price, unit_cost) VALUES
(14, 5, 5, 2, 260.00, 180.00),
(15, 5, 8, 4, 60.00, 38.00),
(16, 5, 13, 2, 130.00, 85.00);

-- Transaction 6 (2026-08-27)
INSERT INTO sales (sale_id, store_id, receipt_number, total_amount, payment_method, sale_date) VALUES
(6, 1, 'REC-20260827-006', 1515.00, 'Card', '2026-08-27 12:00:00');
INSERT INTO sale_items (sale_item_id, sale_id, product_id, quantity, unit_price, unit_cost) VALUES
(17, 6, 9, 2, 560.00, 420.00),
(18, 6, 10, 1, 450.00, 340.00),
(19, 6, 16, 1, 85.00, 55.00);

-- Transaction 7 (2026-08-28)
INSERT INTO sales (sale_id, store_id, receipt_number, total_amount, payment_method, sale_date) VALUES
(7, 1, 'REC-20260828-007', 710.00, 'UPI', '2026-08-28 17:30:00');
INSERT INTO sale_items (sale_item_id, sale_id, product_id, quantity, unit_price, unit_cost) VALUES
(20, 7, 1, 4, 135.00, 90.00),
(21, 7, 7, 2, 70.00, 45.00),
(22, 7, 15, 1, 145.00, 95.00);

-- Transaction 8 (2026-08-29)
INSERT INTO sales (sale_id, store_id, receipt_number, total_amount, payment_method, sale_date) VALUES
(8, 1, 'REC-20260829-008', 925.00, 'Cash', '2026-08-29 19:15:00');
INSERT INTO sale_items (sale_item_id, sale_id, product_id, quantity, unit_price, unit_cost) VALUES
(23, 8, 2, 1, 330.00, 220.00),
(24, 8, 6, 10, 35.00, 20.00),
(25, 8, 17, 1, 125.00, 80.00),
(26, 8, 18, 1, 140.00, 90.00);

-- Transaction 9 (2026-08-30)
INSERT INTO sales (sale_id, store_id, receipt_number, total_amount, payment_method, sale_date) VALUES
(9, 1, 'REC-20260830-009', 1475.00, 'UPI', '2026-08-30 11:00:00');
INSERT INTO sale_items (sale_item_id, sale_id, product_id, quantity, unit_price, unit_cost) VALUES
(27, 9, 9, 1, 560.00, 420.00),
(28, 9, 5, 3, 260.00, 180.00),
(29, 9, 4, 3, 45.00, 30.00);

-- Transaction 10 (2026-08-31)
INSERT INTO sales (sale_id, store_id, receipt_number, total_amount, payment_method, sale_date) VALUES
(10, 1, 'REC-20260831-010', 820.00, 'Card', '2026-08-31 15:40:00');
INSERT INTO sale_items (sale_item_id, sale_id, product_id, quantity, unit_price, unit_cost) VALUES
(30, 10, 1, 3, 135.00, 90.00),
(31, 10, 6, 6, 35.00, 20.00),
(32, 10, 8, 3, 60.00, 38.00);

-- Transactions 11 to 25 (September Daily Sales)
INSERT INTO sales (sale_id, store_id, receipt_number, total_amount, payment_method, sale_date) VALUES
(11, 1, 'REC-20260901-011', 1230.00, 'UPI', '2026-09-01 10:30:00'),
(12, 1, 'REC-20260902-012', 655.00, 'Cash', '2026-09-02 12:15:00'),
(13, 1, 'REC-20260903-013', 1780.00, 'Card', '2026-09-03 14:00:00'),
(14, 1, 'REC-20260904-014', 940.00, 'UPI', '2026-09-04 16:30:00'),
(15, 1, 'REC-20260905-015', 1390.00, 'Cash', '2026-09-05 18:45:00'),
(16, 1, 'REC-20260906-016', 2140.00, 'UPI', '2026-09-06 11:20:00'),
(17, 1, 'REC-20260907-017', 795.00, 'Card', '2026-09-07 13:10:00'),
(18, 1, 'REC-20260908-018', 1120.00, 'UPI', '2026-09-08 15:50:00'),
(19, 1, 'REC-20260909-019', 860.00, 'Cash', '2026-09-09 17:00:00'),
(20, 1, 'REC-20260910-020', 1650.00, 'UPI', '2026-09-10 19:30:00'),
(21, 1, 'REC-20260911-021', 995.00, 'Card', '2026-09-11 11:15:00'),
(22, 1, 'REC-20260912-022', 1870.00, 'UPI', '2026-09-12 14:40:00'),
(23, 1, 'REC-20260913-023', 1420.00, 'Cash', '2026-09-13 16:25:00'),
(24, 1, 'REC-20260914-024', 680.00, 'Card', '2026-09-14 18:00:00'),
(25, 1, 'REC-20260915-025', 1560.00, 'UPI', '2026-09-15 19:45:00'),
(26, 1, 'REC-20260916-026', 1045.00, 'Cash', '2026-09-16 10:50:00'),
(27, 1, 'REC-20260917-027', 1290.00, 'UPI', '2026-09-17 13:20:00'),
(28, 1, 'REC-20260918-028', 1980.00, 'Card', '2026-09-18 15:10:00'),
(29, 1, 'REC-20260919-029', 1435.00, 'UPI', '2026-09-19 17:35:00'),
(30, 1, 'REC-20260920-030', 1620.00, 'Cash', '2026-09-20 19:00:00');

INSERT INTO sale_items (sale_item_id, sale_id, product_id, quantity, unit_price, unit_cost) VALUES
-- Sale 11
(33, 11, 2, 2, 330.00, 220.00),
(34, 11, 9, 1, 560.00, 420.00),
(35, 11, 19, 1, 110.00, 70.00),
-- Sale 12
(36, 12, 1, 2, 135.00, 90.00),
(37, 12, 6, 7, 35.00, 20.00),
(38, 12, 7, 2, 70.00, 45.00),
-- Sale 13
(39, 13, 9, 2, 560.00, 420.00),
(40, 13, 10, 1, 450.00, 340.00),
(41, 13, 13, 1, 130.00, 85.00),
(42, 13, 16, 1, 85.00, 55.00),
-- Sale 14
(43, 14, 5, 2, 260.00, 180.00),
(44, 14, 8, 4, 60.00, 38.00),
(45, 14, 3, 2, 95.00, 65.00),
-- Sale 15
(46, 15, 1, 4, 135.00, 90.00),
(47, 15, 6, 10, 35.00, 20.00),
(48, 15, 11, 2, 195.00, 140.00),
(49, 15, 18, 1, 140.00, 90.00),
-- Sale 16 (High Volume Day)
(50, 16, 9, 2, 560.00, 420.00),
(51, 16, 10, 1, 450.00, 340.00),
(52, 16, 5, 1, 260.00, 180.00),
(53, 16, 2, 1, 330.00, 220.00),
-- Sale 17
(54, 17, 12, 3, 155.00, 110.00),
(55, 17, 1, 2, 135.00, 90.00),
(56, 17, 4, 2, 45.00, 30.00),
-- Sale 18
(57, 18, 9, 1, 560.00, 420.00),
(58, 18, 6, 8, 35.00, 20.00),
(59, 18, 7, 4, 70.00, 45.00),
-- Sale 19
(60, 19, 2, 1, 330.00, 220.00),
(61, 19, 5, 1, 260.00, 180.00),
(62, 19, 15, 1, 145.00, 95.00),
(63, 19, 17, 1, 125.00, 80.00),
-- Sale 20
(64, 20, 9, 2, 560.00, 420.00),
(65, 20, 10, 1, 450.00, 340.00),
(66, 20, 6, 2, 35.00, 20.00),
-- Sale 21
(67, 21, 1, 3, 135.00, 90.00),
(68, 21, 8, 5, 60.00, 38.00),
(69, 21, 13, 2, 130.00, 85.00),
-- Sale 22
(70, 22, 9, 2, 560.00, 420.00),
(71, 22, 2, 1, 330.00, 220.00),
(72, 22, 11, 1, 195.00, 140.00),
(73, 22, 18, 1, 140.00, 90.00),
(74, 22, 16, 1, 85.00, 55.00),
-- Sale 23
(75, 23, 10, 2, 450.00, 340.00),
(76, 23, 5, 2, 260.00, 180.00),
-- Sale 24
(77, 24, 1, 2, 135.00, 90.00),
(78, 24, 6, 6, 35.00, 20.00),
(79, 24, 7, 2, 70.00, 45.00),
(80, 24, 4, 1, 45.00, 30.00),
-- Sale 25
(81, 25, 9, 1, 560.00, 420.00),
(82, 25, 2, 1, 330.00, 220.00),
(83, 25, 5, 1, 260.00, 180.00),
(84, 25, 6, 6, 35.00, 20.00),
(85, 25, 19, 2, 110.00, 70.00),
-- Sale 26
(86, 26, 1, 3, 135.00, 90.00),
(87, 26, 12, 2, 155.00, 110.00),
(88, 26, 8, 3, 60.00, 38.00),
(89, 26, 15, 1, 145.00, 95.00),
-- Sale 27
(90, 27, 10, 1, 450.00, 340.00),
(91, 27, 9, 1, 560.00, 420.00),
(92, 27, 7, 4, 70.00, 45.00),
-- Sale 28
(93, 28, 2, 2, 330.00, 220.00),
(94, 28, 5, 2, 260.00, 180.00),
(95, 28, 9, 1, 560.00, 420.00),
(96, 28, 14, 1, 230.00, 150.00), -- Single sale for Shampoo across month!
-- Sale 29
(97, 29, 1, 3, 135.00, 90.00),
(98, 29, 6, 9, 35.00, 20.00),
(99, 29, 11, 2, 195.00, 140.00),
(100, 29, 18, 1, 140.00, 90.00),
(101, 29, 16, 2, 85.00, 55.00),
-- Sale 30
(102, 30, 9, 1, 560.00, 420.00),
(103, 30, 10, 1, 450.00, 340.00),
(104, 30, 2, 1, 330.00, 220.00),
(105, 30, 5, 1, 260.00, 180.00),
(106, 30, 20, 1, 100.00, 60.00); -- Single sale for Microfiber cloth!
