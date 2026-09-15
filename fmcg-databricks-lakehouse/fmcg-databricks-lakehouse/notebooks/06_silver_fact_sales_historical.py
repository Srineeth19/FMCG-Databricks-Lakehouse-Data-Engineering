# Databricks notebook source
# MAGIC %md
# MAGIC # 06 - Silver: fact_sales (Historical / Full Load)
# MAGIC One-time full load that consolidates the historical transaction files
# MAGIC from **both** companies into a single `silver.fact_sales` table at
# MAGIC transaction grain, conformed against the unified dimensions built in
# MAGIC notebooks 02-05. Run this ONCE to backfill; subsequent runs use
# MAGIC notebook 07 (incremental).

# COMMAND ----------

import sys
sys.path.append("/Workspace/Repos/fmcg-databricks-lakehouse/src")
from utils.data_quality import assert_no_nulls, assert_unique, assert_referential_integrity, assert_row_count_min
from pyspark.sql import functions as F

catalog = "fmcg_lakehouse"

# COMMAND ----------

big = spark.table(f"{catalog}.bronze.big_retail_sales_historical")
small = spark.table(f"{catalog}.bronze.small_retail_sales_historical")

cols = ["transaction_id", "customer_id", "product_id", "store_id", "quantity", "unit_price",
        "total_amount", "transaction_ts", "payment_mode", "last_updated_ts", "_source_system"]

fact_raw = big.select(*cols).unionByName(small.select(*cols))

fact_df = (fact_raw
    .withColumnRenamed("_source_system", "source_system")
    .withColumn("transaction_ts", F.to_timestamp("transaction_ts"))
    .withColumn("last_updated_ts", F.to_timestamp("last_updated_ts"))
    .withColumn("transaction_date", F.to_date("transaction_ts"))
    .dropDuplicates(["transaction_id"])
)

# COMMAND ----------

# Data quality gates before writing the historical fact table
assert_no_nulls(fact_df, ["transaction_id", "customer_id", "product_id", "store_id"], "silver.fact_sales")
assert_unique(fact_df, ["transaction_id"], "silver.fact_sales")
assert_row_count_min(fact_df, 50000, "silver.fact_sales")

dim_customer = spark.table(f"{catalog}.silver.dim_customer")
dim_product = spark.table(f"{catalog}.silver.dim_product")
dim_store = spark.table(f"{catalog}.silver.dim_store")
assert_referential_integrity(fact_df, dim_customer, "customer_id", "customer_id", "silver.fact_sales")
assert_referential_integrity(fact_df, dim_product, "product_id", "product_id", "silver.fact_sales")
assert_referential_integrity(fact_df, dim_store, "store_id", "store_id", "silver.fact_sales")

# COMMAND ----------

(fact_df.write.format("delta")
    .mode("overwrite")
    .partitionBy("transaction_date")
    .saveAsTable(f"{catalog}.silver.fact_sales"))

spark.sql(f"""
COMMENT ON TABLE {catalog}.silver.fact_sales IS
'Consolidated sales transaction fact at grain=transaction_id, combining BigMart Retail and QuickMart. Partitioned by transaction_date.'
""")

print(f"Historical fact load complete: {fact_df.count()} rows")
display(spark.table(f"{catalog}.silver.fact_sales").limit(10))
