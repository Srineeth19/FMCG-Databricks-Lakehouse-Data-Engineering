# Databricks notebook source
# MAGIC %md
# MAGIC # 00 - Setup Catalog & Schemas
# MAGIC Creates the Unity Catalog catalog and the bronze / silver / gold schemas
# MAGIC that back the FMCG lakehouse (Databricks Free Edition ships with Unity
# MAGIC Catalog enabled by default, so no extra setup is required beyond this).

# COMMAND ----------

catalog = "fmcg_lakehouse"

spark.sql(f"CREATE CATALOG IF NOT EXISTS {catalog}")
spark.sql(f"USE CATALOG {catalog}")

for schema in ["bronze", "silver", "gold"]:
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}")

display(spark.sql(f"SHOW SCHEMAS IN {catalog}"))

# COMMAND ----------

# MAGIC %md
# MAGIC ### Volumes for raw file landing (used if you prefer Databricks Volumes over direct S3 reads)

# COMMAND ----------

spark.sql(f"CREATE VOLUME IF NOT EXISTS {catalog}.bronze.raw_files")
print(f"Volume ready at /Volumes/{catalog}/bronze/raw_files")

# COMMAND ----------

# MAGIC %md
# MAGIC Next notebook: **01_bronze_ingestion_s3** — reads the two source companies'
# MAGIC CSVs from S3 and lands them as-is (schema-on-read) into bronze Delta tables.
