# Databricks notebook source
# MAGIC %md
# MAGIC # 04 - Silver: dim_store
# MAGIC Conforms `bronze.big_retail_stores` and `bronze.small_retail_stores`
# MAGIC (QuickMart's `outlets`) into one unified store/outlet dimension.

# COMMAND ----------

import sys
sys.path.append("/Workspace/Repos/fmcg-databricks-lakehouse/src")
from utils.scd_utils import upsert_scd1
from utils.data_quality import assert_no_nulls, assert_unique
from pyspark.sql import functions as F

catalog = "fmcg_lakehouse"

# COMMAND ----------

big = spark.table(f"{catalog}.bronze.big_retail_stores")
small = spark.table(f"{catalog}.bronze.small_retail_stores")

cols = ["store_id", "store_name", "city", "state", "store_type", "opened_date", "_source_system"]
unified = big.select(*cols).unionByName(small.select(*cols)).dropDuplicates(["store_id"])

silver_df = (unified
    .withColumnRenamed("_source_system", "source_system")
    .withColumn("opened_date", F.to_date("opened_date"))
    .withColumn("updated_at", F.current_timestamp())
)

# COMMAND ----------

assert_no_nulls(silver_df, ["store_id", "store_name", "city"], "silver.dim_store")
assert_unique(silver_df, ["store_id"], "silver.dim_store")

# COMMAND ----------

upsert_scd1(spark, f"{catalog}.silver.dim_store", silver_df, business_key="store_id")

spark.sql(f"""
COMMENT ON TABLE {catalog}.silver.dim_store IS
'Unified store/outlet dimension across BigMart Retail stores and the acquired QuickMart outlets.'
""")
display(spark.table(f"{catalog}.silver.dim_store").limit(10))
