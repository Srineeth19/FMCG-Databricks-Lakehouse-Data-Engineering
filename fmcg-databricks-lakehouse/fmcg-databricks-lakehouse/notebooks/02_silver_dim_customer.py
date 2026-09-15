# Databricks notebook source
# MAGIC %md
# MAGIC # 02 - Silver: dim_customer
# MAGIC Conforms `bronze.big_retail_customers` and `bronze.small_retail_customers`
# MAGIC (same business meaning, both already share column names in this demo —
# MAGIC in the real project the small company's raw columns are renamed here)
# MAGIC into one unified, deduplicated, SCD-1 `silver.dim_customer` table with a
# MAGIC surrogate key and a `source_system` lineage column so the acquired
# MAGIC company's customers remain distinguishable downstream.

# COMMAND ----------

import sys
sys.path.append("/Workspace/Repos/fmcg-databricks-lakehouse/src")
from utils.scd_utils import upsert_scd1
from utils.data_quality import assert_no_nulls, assert_unique
from pyspark.sql import functions as F

catalog = "fmcg_lakehouse"

# COMMAND ----------

big = spark.table(f"{catalog}.bronze.big_retail_customers")
small = spark.table(f"{catalog}.bronze.small_retail_customers")

# Standardize + union. In a real acquisition, small company columns often need
# renaming (e.g. `cust_id` -> `customer_id`) — done here explicitly for clarity.
big_std = big.select(
    "customer_id", "first_name", "last_name", "city", "state",
    "signup_date", "loyalty_segment", "_source_system",
)
small_std = small.select(
    "customer_id", "first_name", "last_name", "city", "state",
    "signup_date", "loyalty_segment", "_source_system",
)

unified = big_std.unionByName(small_std).dropDuplicates(["customer_id"])

silver_df = (unified
    .withColumn("full_name", F.concat_ws(" ", "first_name", "last_name"))
    .withColumnRenamed("_source_system", "source_system")
    .withColumn("signup_date", F.to_date("signup_date"))
    .withColumn("updated_at", F.current_timestamp())
    .select("customer_id", "full_name", "first_name", "last_name", "city", "state",
            "signup_date", "loyalty_segment", "source_system", "updated_at")
)

# COMMAND ----------

assert_no_nulls(silver_df, ["customer_id", "full_name"], "silver.dim_customer")
assert_unique(silver_df, ["customer_id"], "silver.dim_customer")

# COMMAND ----------

upsert_scd1(
    spark,
    target_table=f"{catalog}.silver.dim_customer",
    source_df=silver_df,
    business_key="customer_id",
)

# COMMAND ----------

spark.sql(f"""
COMMENT ON TABLE {catalog}.silver.dim_customer IS
'Unified customer dimension combining BigMart Retail and the acquired QuickMart customer base.'
""")
display(spark.table(f"{catalog}.silver.dim_customer").limit(10))
