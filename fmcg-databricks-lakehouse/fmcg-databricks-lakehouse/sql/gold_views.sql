-- gold_views.sql
-- Convenience views on top of the gold tables built by notebooks 08 & 09.
-- Useful for ad-hoc SQL Editor exploration and as the basis for dashboard tiles.

USE CATALOG fmcg_lakehouse;

-- Overall KPI summary (used for the dashboard's top-row scorecards)
CREATE OR REPLACE VIEW gold.v_kpi_summary AS
SELECT
    source_system,
    COUNT(DISTINCT transaction_id) AS total_orders,
    COUNT(DISTINCT customer_id)    AS total_customers,
    SUM(total_amount)              AS total_revenue,
    ROUND(SUM(total_amount) / COUNT(DISTINCT transaction_id), 2) AS avg_order_value
FROM gold.denormalized_sales
GROUP BY source_system;

-- Year-over-year monthly revenue trend
CREATE OR REPLACE VIEW gold.v_revenue_trend AS
SELECT year, month_name, fiscal_year, SUM(revenue) AS revenue, SUM(units_sold) AS units_sold
FROM gold.monthly_revenue_by_category
GROUP BY year, month_name, fiscal_year
ORDER BY year, month_name;

-- Top 10 products by revenue
CREATE OR REPLACE VIEW gold.v_top_products AS
SELECT product_id, product_name, product_category, brand,
       SUM(total_amount) AS revenue, SUM(quantity) AS units_sold
FROM gold.denormalized_sales
GROUP BY product_id, product_name, product_category, brand
ORDER BY revenue DESC
LIMIT 10;

-- Category mix as a % of total revenue
CREATE OR REPLACE VIEW gold.v_category_mix AS
SELECT
    product_category,
    SUM(total_amount) AS revenue,
    ROUND(100.0 * SUM(total_amount) / SUM(SUM(total_amount)) OVER (), 2) AS pct_of_total
FROM gold.denormalized_sales
GROUP BY product_category
ORDER BY revenue DESC;
