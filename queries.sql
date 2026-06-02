-- SQL Queries for Pharma Sales Analytics
-- This file contains the exact queries used by the Streamlit dashboard
-- and can be used for learning, debugging, or running analytics manually.

-- ==============================================================================
-- 1. KPI CARD QUERIES
-- ==============================================================================

-- KPI: Total Revenue
SELECT SUM(total_revenue) AS total_revenue 
FROM pharma_sales;

-- KPI: Total Units Sold
SELECT SUM(quantity) AS total_units_sold 
FROM pharma_sales;

-- KPI: Top Performing Drug (Highest Revenue)
SELECT drug_name, SUM(total_revenue) AS revenue
FROM pharma_sales
GROUP BY drug_name
ORDER BY revenue DESC
LIMIT 1;

-- KPI: Top Region (Highest Units Sold)
SELECT region, SUM(quantity) AS units_sold
FROM pharma_sales
GROUP BY region
ORDER BY units_sold DESC
LIMIT 1;


-- ==============================================================================
-- 2. DASHBOARD VISUALIZATION QUERIES (WITH FILTER PLACEHOLDERS)
-- ==============================================================================

-- Monthly Sales Trend (Revenue & Quantity over time)
-- Displays how sales fluctuate month-by-month
SELECT 
    DATE_TRUNC('month', sale_date) AS sale_month,
    SUM(total_revenue) AS monthly_revenue,
    SUM(quantity) AS monthly_units
FROM pharma_sales
-- Example filters that the dashboard injects:
-- WHERE sale_date BETWEEN '2024-06-03' AND '2026-06-03'
--   AND region IN ('North', 'South')
--   AND category IN ('Analgesics', 'Antibiotics')
GROUP BY sale_month
ORDER BY sale_month ASC;


-- Product Performance (Drug sales rank)
-- Helps managers identify top-revenue generators and high-volume items
SELECT 
    drug_name,
    category,
    SUM(quantity) AS total_units,
    SUM(total_revenue) AS total_revenue,
    ROUND(AVG(unit_price), 2) AS average_unit_price
FROM pharma_sales
GROUP BY drug_name, category
ORDER BY total_revenue DESC;


-- Region-wise Performance (Market share split)
-- Shows geography-based revenue and volume contribution
SELECT 
    region,
    SUM(quantity) AS total_units,
    SUM(total_revenue) AS total_revenue,
    ROUND((SUM(total_revenue) * 100.0 / (SELECT SUM(total_revenue) FROM pharma_sales)), 2) AS revenue_percentage
FROM pharma_sales
GROUP BY region
ORDER BY total_revenue DESC;


-- Customer Type Performance (Hospital vs Clinic vs Pharmacy)
-- Identifies the largest purchaser demographics by volume and order size
SELECT 
    customer_type,
    COUNT(sale_id) AS total_transactions,
    SUM(quantity) AS total_units,
    SUM(total_revenue) AS total_revenue,
    ROUND(AVG(quantity), 2) AS average_order_size
FROM pharma_sales
GROUP BY customer_type
ORDER BY total_revenue DESC;


-- Payment Method Breakdown (Cash vs Credit vs Insurance)
-- Reflects transaction convenience and insurance integration
SELECT 
    payment_method,
    COUNT(sale_id) AS transaction_count,
    SUM(total_revenue) AS total_revenue,
    ROUND((COUNT(sale_id) * 100.0 / (SELECT COUNT(*) FROM pharma_sales)), 2) AS transaction_percentage
FROM pharma_sales
GROUP BY payment_method
ORDER BY total_revenue DESC;


-- ==============================================================================
-- 3. EXTRA ANALYTICAL/INSIGHT QUERIES (BONUS STUDY MATERIAL)
-- ==============================================================================

-- Seasonality Analysis: Identifying flu-season sales spikes (Winter vs Summer)
-- Filters for Analgesics and Respiratory drugs to see seasonal differences
SELECT 
    EXTRACT(MONTH FROM sale_date) AS sale_month_num,
    TO_CHAR(sale_date, 'Month') AS sale_month_name,
    SUM(CASE WHEN category IN ('Respiratory', 'Analgesics') THEN quantity ELSE 0 END) AS seasonal_drug_units,
    SUM(CASE WHEN category IN ('Respiratory', 'Analgesics') THEN total_revenue ELSE 0 END) AS seasonal_drug_revenue,
    SUM(quantity) AS total_all_units
FROM pharma_sales
GROUP BY sale_month_num, sale_month_name
ORDER BY sale_month_num;


-- Top Transactions (Wholesale audit query)
-- Finds the largest individual orders (likely hospitals/clinics) for logistics planning
SELECT 
    sale_id,
    sale_date,
    drug_name,
    category,
    customer_type,
    quantity,
    total_revenue,
    region
FROM pharma_sales
ORDER BY total_revenue DESC
LIMIT 10;
