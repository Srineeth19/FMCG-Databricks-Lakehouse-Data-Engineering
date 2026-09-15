# Databricks notebook source
# MAGIC %md
# MAGIC # 08 - Gold: denormalized_sales (Genie-ready)
# MAGIC Joins `fact_sales` with all unified dimensions into a single wide,
# MAGIC business-friendly table. This is the table registered with a **Genie
# MAGIC Space** so stakeholders can ask natural-language questions
# MAGIC ("What were Q4 sales by category for QuickMart stores in Mumbai?")
# MAGIC without needing to know the star schema or write SQL.
# MAGIC
# MAGIC Column **comments** below matter a lot for Genie — they're the primary
# MAGIC signal Genie uses to map business terms to columns.

# COMMAND ----------

catalog = "fmcg_lakehouse"

spark.sql(f"""
CREATE OR REPLACE TABLE {catalog}.gold.denormalized_sales
COMMENT 'One row per sales transaction with all dimension attributes flattened in. Primary table for the Genie space and BI dashboard.'
AS
SELECT
    f.transaction_id,
    f.transaction_ts,
    f.transaction_date,
    d.year, d.quarter, d.month_name, d.day_name, d.is_weekend, d.fiscal_year,

    c.customer_id, c.full_name AS customer_name, c.city AS customer_city,
    c.state AS customer_state, c.loyalty_segment,

    p.product_id, p.product_name, p.category AS product_category,
    p.brand AS product_brand, p.unit_of_measure,

    s.store_id, s.store_name, s.city AS store_city, s.state AS store_state,
    s.store_type,

    f.quantity,
    f.unit_price,
    f.total_amount,
    f.payment_mode,
    f.source_system   -- 'BigMart Retail' or 'QuickMart' — lets Genie answer
                       -- "compare sales between the two companies" style questions
FROM {catalog}.silver.fact_sales f
JOIN {catalog}.silver.dim_customer c ON f.customer_id = c.customer_id
JOIN {catalog}.silver.dim_product  p ON f.product_id  = p.product_id
JOIN {catalog}.silver.dim_store    s ON f.store_id    = s.store_id
JOIN {catalog}.silver.dim_date     d ON f.transaction_date = d.date_key
""")

# COMMAND ----------

# MAGIC %md ### Add column comments (improves Genie's natural-language understanding)

# COMMAND ----------

column_comments = {
    "transaction_id": "Unique identifier for a single sales transaction (line item).",
    "transaction_date": "Calendar date the transaction occurred.",
    "fiscal_year": "Fiscal year, starting April 1.",
    "customer_name": "Full name of the purchasing customer.",
    "loyalty_segment": "Customer loyalty tier: Bronze, Silver, Gold, or Platinum.",
    "product_category": "FMCG product category, e.g. Beverages, Snacks, Personal Care, Home Care, Staples.",
    "store_type": "Format of the retail location: Supermarket, Convenience, or Hypermarket.",
    "total_amount": "Total revenue for this transaction line (quantity * unit_price), in INR.",
    "source_system": "Which acquired company the transaction originated from: 'BigMart Retail' (acquirer) or 'QuickMart' (acquired).",
}
for col, comment in column_comments.items():
    spark.sql(f"ALTER TABLE {catalog}.gold.denormalized_sales ALTER COLUMN {col} COMMENT '{comment}'")

print("Column comments applied.")
display(spark.table(f"{catalog}.gold.denormalized_sales").limit(10))

# COMMAND ----------

# MAGIC %md
# MAGIC ### Next step (done in the Databricks UI, not code)
# MAGIC 1. Go to **Genie** in the left sidebar → **New Space**.
# MAGIC 2. Add table `fmcg_lakehouse.gold.denormalized_sales`.
# MAGIC 3. Add a few sample instructions/example questions (see `sql/genie_sample_questions.md`).
# MAGIC 4. Publish the space and share it with business stakeholders.
