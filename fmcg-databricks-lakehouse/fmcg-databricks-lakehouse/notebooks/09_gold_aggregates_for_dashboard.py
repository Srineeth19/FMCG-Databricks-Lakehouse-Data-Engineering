# Databricks notebook source
# MAGIC %md
# MAGIC # 09 - Gold: Aggregate tables for the BI Dashboard
# MAGIC Pre-aggregates common KPI cuts so the Databricks AI/BI dashboard queries
# MAGIC stay fast and cheap (SQL Warehouse serverless) instead of scanning the
# MAGIC full denormalized fact table on every view.

# COMMAND ----------

catalog = "fmcg_lakehouse"

# COMMAND ----------

# MAGIC %md ### Monthly revenue by company + category

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE TABLE {catalog}.gold.monthly_revenue_by_category
COMMENT 'Monthly revenue and order volume by source company and product category, for trend charts.'
AS
SELECT
    year, month_name, fiscal_year,
    source_system, product_category,
    SUM(total_amount) AS revenue,
    SUM(quantity) AS units_sold,
    COUNT(DISTINCT transaction_id) AS order_count,
    COUNT(DISTINCT customer_id) AS unique_customers
FROM {catalog}.gold.denormalized_sales
GROUP BY year, month_name, fiscal_year, source_system, product_category
""")

# COMMAND ----------

# MAGIC %md ### Store performance leaderboard

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE TABLE {catalog}.gold.store_performance
COMMENT 'Revenue, orders, and average basket size by store, for the store-performance leaderboard on the dashboard.'
AS
SELECT
    store_id, store_name, store_city, store_state, store_type, source_system,
    SUM(total_amount) AS revenue,
    COUNT(DISTINCT transaction_id) AS order_count,
    ROUND(SUM(total_amount) / COUNT(DISTINCT transaction_id), 2) AS avg_basket_value
FROM {catalog}.gold.denormalized_sales
GROUP BY store_id, store_name, store_city, store_state, store_type, source_system
""")

# COMMAND ----------

# MAGIC %md ### Customer loyalty segment summary

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE TABLE {catalog}.gold.customer_segment_summary
COMMENT 'Revenue and customer counts by loyalty segment and source company.'
AS
SELECT
    loyalty_segment, source_system,
    COUNT(DISTINCT customer_id) AS customers,
    SUM(total_amount) AS revenue,
    ROUND(SUM(total_amount) / COUNT(DISTINCT customer_id), 2) AS revenue_per_customer
FROM {catalog}.gold.denormalized_sales
GROUP BY loyalty_segment, source_system
""")

# COMMAND ----------

for t in ["monthly_revenue_by_category", "store_performance", "customer_segment_summary"]:
    n = spark.table(f"{catalog}.gold.{t}").count()
    print(f"gold.{t}: {n} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC These three tables (plus `gold.denormalized_sales` directly) back the
# MAGIC dashboard tiles defined in `dashboard/dashboard_queries.sql`.
