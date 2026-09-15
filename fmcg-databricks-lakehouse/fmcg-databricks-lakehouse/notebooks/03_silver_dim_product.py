# Databricks notebook source
# MAGIC %md
# MAGIC # 03 - Silver: dim_product
# MAGIC Conforms `bronze.big_retail_products` (product catalog) and
# MAGIC `bronze.small_retail_products` (QuickMart's `product_master`) into one
# MAGIC unified FMCG product dimension, standardizing category/brand casing and
# MAGIC deduplicating on `product_id`.

# COMMAND ----------

import sys
sys.path.append("/Workspace/Repos/fmcg-databricks-lakehouse/src")
from utils.scd_utils import upsert_scd1
from utils.data_quality import assert_no_nulls, assert_unique
from pyspark.sql import functions as F

catalog = "fmcg_lakehouse"

# COMMAND ----------

big = spark.table(f"{catalog}.bronze.big_retail_products")
small = spark.table(f"{catalog}.bronze.small_retail_products")

cols = ["product_id", "product_name", "category", "brand", "unit_price", "unit_of_measure", "_source_system"]
unified = big.select(*cols).unionByName(small.select(*cols)).dropDuplicates(["product_id"])

silver_df = (unified
    .withColumn("category", F.initcap("category"))
    .withColumn("brand", F.initcap("brand"))
    .withColumnRenamed("_source_system", "source_system")
    .withColumn("unit_price", F.round("unit_price", 2))
    .withColumn("updated_at", F.current_timestamp())
)

# COMMAND ----------

assert_no_nulls(silver_df, ["product_id", "product_name", "category"], "silver.dim_product")
assert_unique(silver_df, ["product_id"], "silver.dim_product")

# COMMAND ----------

upsert_scd1(spark, f"{catalog}.silver.dim_product", silver_df, business_key="product_id")

spark.sql(f"""
COMMENT ON TABLE {catalog}.silver.dim_product IS
'Unified FMCG product catalog across BigMart Retail and QuickMart, standardized on category/brand naming.'
""")
display(spark.table(f"{catalog}.silver.dim_product").limit(10))
