-- dashboard_queries.sql
-- Query for each tile in the "FMCG Lakehouse — Post-Acquisition Sales" AI/BI Dashboard.
-- Build the dashboard in Databricks: SQL Editor -> save each query as a dataset ->
-- Dashboards -> New Dashboard -> add each dataset as a visualization.

USE CATALOG fmcg_lakehouse;

-- TILE 1: Scorecards (total revenue, total orders, avg order value, total customers)
SELECT
    SUM(total_amount) AS total_revenue,
    COUNT(DISTINCT transaction_id) AS total_orders,
    ROUND(SUM(total_amount) / COUNT(DISTINCT transaction_id), 2) AS avg_order_value,
    COUNT(DISTINCT customer_id) AS total_customers
FROM gold.denormalized_sales;

-- TILE 2: Revenue trend by month (line chart, series = source_system)
SELECT year, month_name, source_system, SUM(revenue) AS revenue
FROM gold.monthly_revenue_by_category
GROUP BY year, month_name, source_system
ORDER BY year, month_name;

-- TILE 3: Revenue by category (bar/pie chart)
SELECT product_category, SUM(total_amount) AS revenue
FROM gold.denormalized_sales
GROUP BY product_category
ORDER BY revenue DESC;

-- TILE 4: BigMart Retail vs QuickMart contribution (donut chart)
SELECT source_system, SUM(total_amount) AS revenue
FROM gold.denormalized_sales
GROUP BY source_system;

-- TILE 5: Top 10 stores leaderboard (table)
SELECT store_name, store_city, store_type, source_system, revenue, order_count, avg_basket_value
FROM gold.store_performance
ORDER BY revenue DESC
LIMIT 10;

-- TILE 6: Revenue by city (map / bar chart)
SELECT store_city, SUM(total_amount) AS revenue
FROM gold.denormalized_sales
GROUP BY store_city
ORDER BY revenue DESC;

-- TILE 7: Loyalty segment breakdown (stacked bar)
SELECT loyalty_segment, source_system, revenue, customers
FROM gold.customer_segment_summary
ORDER BY loyalty_segment;

-- TILE 8: Payment mode mix (pie chart)
SELECT payment_mode, COUNT(*) AS txn_count, SUM(total_amount) AS revenue
FROM gold.denormalized_sales
GROUP BY payment_mode;

-- TILE 9: Weekday vs weekend sales pattern
SELECT is_weekend, ROUND(AVG(total_amount), 2) AS avg_txn_value, COUNT(*) AS txn_count
FROM gold.denormalized_sales
GROUP BY is_weekend;
