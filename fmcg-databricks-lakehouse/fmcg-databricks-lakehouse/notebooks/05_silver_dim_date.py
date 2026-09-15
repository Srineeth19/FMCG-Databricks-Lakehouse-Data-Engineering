# Databricks notebook source
# MAGIC %md
# MAGIC # 05 - Silver: dim_date
# MAGIC Generates a standard calendar date dimension (2022-2026) used to join
# MAGIC against `fact_sales.transaction_date` for time-intelligence in the
# MAGIC gold layer and BI dashboard.

# COMMAND ----------

from pyspark.sql import functions as F

catalog = "fmcg_lakehouse"

df = spark.sql("SELECT explode(sequence(to_date('2022-01-01'), to_date('2026-12-31'), interval 1 day)) as date_key")

dim_date = (df
    .withColumn("year", F.year("date_key"))
    .withColumn("quarter", F.quarter("date_key"))
    .withColumn("month", F.month("date_key"))
    .withColumn("month_name", F.date_format("date_key", "MMMM"))
    .withColumn("week_of_year", F.weekofyear("date_key"))
    .withColumn("day_of_month", F.dayofmonth("date_key"))
    .withColumn("day_name", F.date_format("date_key", "EEEE"))
    .withColumn("is_weekend", F.dayofweek("date_key").isin([1, 7]))
    .withColumn("fiscal_year", F.expr("CASE WHEN month(date_key) >= 4 THEN year(date_key) ELSE year(date_key) - 1 END"))
)

dim_date.write.format("delta").mode("overwrite").saveAsTable(f"{catalog}.silver.dim_date")
spark.sql(f"COMMENT ON TABLE {catalog}.silver.dim_date IS 'Calendar date dimension, fiscal year starts April.'")
display(dim_date.limit(10))
