# Databricks notebook source
# MAGIC %md
# MAGIC # 01 - Bronze Ingestion from Amazon S3
# MAGIC Lands raw CSVs from both source companies (BigMart Retail + QuickMart)
# MAGIC into bronze Delta tables **as-is** — no cleaning, no renaming. This
# MAGIC preserves a full-fidelity copy of the source for auditability/replay.

# COMMAND ----------

# MAGIC %pip install -q boto3

# COMMAND ----------

import sys
sys.path.append("/Workspace/Repos/fmcg-databricks-lakehouse/src")   # adjust to your repo path
from utils.s3_utils import configure_s3_access, get_s3_path

dbutils.widgets.text("s3_bucket", "fmcg-lakehouse-demo")
bucket = dbutils.widgets.get("s3_bucket")

# COMMAND ----------

# Credentials pulled from a Databricks secret scope (create with the Databricks CLI:
#   databricks secrets create-scope aws
#   databricks secrets put-secret aws access_key
#   databricks secrets put-secret aws secret_key
access_key = dbutils.secrets.get(scope="aws", key="access_key")
secret_key = dbutils.secrets.get(scope="aws", key="secret_key")
configure_s3_access(spark, access_key, secret_key, region="ap-south-1")

# COMMAND ----------

catalog = "fmcg_lakehouse"

BIG_FILES = {
    "customers": "customers.csv",
    "products": "products.csv",
    "stores": "stores.csv",
    "sales_historical": "sales_historical.csv",
    "sales_incremental": "sales_incremental.csv",
}
SMALL_FILES = {
    "customers": "customers_small.csv",
    "products": "product_master.csv",
    "stores": "outlets.csv",
    "sales_historical": "transactions_historical.csv",
    "sales_incremental": "transactions_incremental.csv",
}

# COMMAND ----------


def land_to_bronze(company_folder: str, source_files: dict, source_system: str):
    from pyspark.sql import functions as F
    for entity, filename in source_files.items():
        path = get_s3_path(company_folder, filename, bucket=bucket)
        df = (spark.read.option("header", "true").option("inferSchema", "true").csv(path)
              .withColumn("_source_system", F.lit(source_system))
              .withColumn("_source_file", F.lit(filename))
              .withColumn("_ingested_at", F.current_timestamp()))
        target = f"{catalog}.bronze.{company_folder}_{entity}"
        df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(target)
        print(f"Bronze loaded: {target} ({df.count()} rows)")


# COMMAND ----------

land_to_bronze("big_retail", BIG_FILES, source_system="BigMart Retail")

# COMMAND ----------

land_to_bronze("small_retail", SMALL_FILES, source_system="QuickMart")

# COMMAND ----------

display(spark.sql(f"SHOW TABLES IN {catalog}.bronze"))

# COMMAND ----------

# MAGIC %md
# MAGIC Next: **02-04 silver dimension notebooks** conform the two schemas
# MAGIC (different column names/order) into a single unified `dim_customer`,
# MAGIC `dim_product`, `dim_store`.
