-- PostgreSQL Database Schema for Pharma Sales Analytics
-- Drop table if it already exists (useful for clean reinstalls)
DROP TABLE IF EXISTS pharma_sales;

-- Create the primary table for storing transaction records
CREATE TABLE pharma_sales (
    sale_id SERIAL PRIMARY KEY,
    sale_date TIMESTAMP NOT NULL,
    drug_name VARCHAR(100) NOT NULL,
    category VARCHAR(100) NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(10, 2) NOT NULL CHECK (unit_price >= 0.0),
    total_revenue NUMERIC(12, 2) NOT NULL CHECK (total_revenue >= 0.0),
    region VARCHAR(50) NOT NULL,
    customer_type VARCHAR(50) NOT NULL,
    payment_method VARCHAR(50) NOT NULL
);

-- Comments explaining the column usage (excellent standard practice)
COMMENT ON COLUMN pharma_sales.sale_id IS 'Unique identifier for each transaction (Primary Key)';
COMMENT ON COLUMN pharma_sales.sale_date IS 'Timestamp of when the transaction occurred';
COMMENT ON COLUMN pharma_sales.drug_name IS 'Name of the pharmaceutical product sold';
COMMENT ON COLUMN pharma_sales.category IS 'Therapeutic or drug classification category';
COMMENT ON COLUMN pharma_sales.quantity IS 'Number of units sold in this transaction';
COMMENT ON COLUMN pharma_sales.unit_price IS 'Price per unit, adjusted dynamically for inflation & margins';
COMMENT ON COLUMN pharma_sales.total_revenue IS 'Calculated total revenue (quantity * unit_price)';
COMMENT ON COLUMN pharma_sales.region IS 'Geographic region of the sale (North, South, East, West)';
COMMENT ON COLUMN pharma_sales.customer_type IS 'Purchaser category (Pharmacy, Hospital, Clinic)';
COMMENT ON COLUMN pharma_sales.payment_method IS 'Method of payment (Cash, Credit Card, Insurance)';

-- Create indexes for performance optimization
-- 1. Index on sale_date because the dashboard filters by date ranges and aggregates monthly
CREATE INDEX idx_pharma_sales_date ON pharma_sales(sale_date);

-- 2. Index on region because the dashboard filters by region
CREATE INDEX idx_pharma_sales_region ON pharma_sales(region);

-- 3. Index on category because dashboard filters by drug category
CREATE INDEX idx_pharma_sales_category ON pharma_sales(category);

-- 4. Index on drug_name to optimize group-by operations for product performance analysis
CREATE INDEX idx_pharma_sales_drug ON pharma_sales(drug_name);
