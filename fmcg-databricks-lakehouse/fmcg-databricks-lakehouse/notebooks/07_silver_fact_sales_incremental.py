# Databricks notebook source
# MAGIC %md
# MAGIC # 07 - Silver: fact_sales (Incremental Load)
# MAGIC Designed to run on a **daily schedule** (see `notebooks/orchestration_job.json`).
# MAGIC Reads only new/changed transactions since the last watermark, using a
# MAGIC MERGE so the job is idempotent and safe to re-run or backfill.

# COMMAND ----------

import sys
sys.path.append("/Workspace/Repos/fmcg-databricks-lakehouse/src")
from utils.scd_utils import upsert_fact, get_last_watermark
from utils.data_quality import assert_no_nulls, assert_referential_integrity
from pyspark.sql import functions as F

catalog = "fmcg_lakehouse"
target_table = f"{catalog}.silver.fact_sales"

# COMMAND ----------

# Watermark-based incremental read: only pull rows newer than what's already in silver.
last_wm = get_last_watermark(spark, target_table, "last_updated_ts")
print(f"Last watermark in {target_table}: {last_wm}")

big = spark.table(f"{catalog}.bronze.big_retail_sales_incremental")
small = spark.table(f"{catalog}.bronze.small_retail_sales_incremental")

cols = ["transaction_id", "customer_id", "product_id", "store_id", "quantity", "unit_price",
        "total_amount", "transaction_ts", "payment_mode", "last_updated_ts", "_source_system"]

incoming = (big.select(*cols).unionByName(small.select(*cols))
    .withColumnRenamed("_source_system", "source_system")
    .withColumn("transaction_ts", F.to_timestamp("transaction_ts"))
    .withColumn("last_updated_ts", F.to_timestamp("last_updated_ts"))
    .withColumn("transaction_date", F.to_date("transaction_ts"))
)

if last_wm is not None:
    incoming = incoming.filter(F.col("last_updated_ts") > F.lit(last_wm))

new_row_count = incoming.count()
print(f"New/changed rows to merge: {new_row_count}")

# COMMAND ----------

if new_row_count > 0:
    assert_no_nulls(incoming, ["transaction_id", "customer_id", "product_id", "store_id"], "silver.fact_sales (incremental)")
    dim_customer = spark.table(f"{catalog}.silver.dim_customer")
    dim_product = spark.table(f"{catalog}.silver.dim_product")
    dim_store = spark.table(f"{catalog}.silver.dim_store")
    assert_referential_integrity(incoming, dim_customer, "customer_id", "customer_id", "silver.fact_sales (incremental)")
    assert_referential_integrity(incoming, dim_product, "product_id", "product_id", "silver.fact_sales (incremental)")
    assert_referential_integrity(incoming, dim_store, "store_id", "store_id", "silver.fact_sales (incremental)")

    upsert_fact(spark, target_table, incoming, grain_key="transaction_id", watermark_col="last_updated_ts")
else:
    print("No new rows — skipping merge.")

# COMMAND ----------

display(spark.sql(f"""
    SELECT source_system, count(*) as txn_count, max(last_updated_ts) as latest
    FROM {target_table}
    GROUP BY source_system
"""))
