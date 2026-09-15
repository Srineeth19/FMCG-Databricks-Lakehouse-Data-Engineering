"""
scd_utils.py
------------
Reusable Slowly Changing Dimension (SCD Type 1) and fact MERGE helpers used
across the silver-layer dimension and fact notebooks.

These wrap Delta Lake's MERGE INTO so each notebook only needs to supply:
  - the target table name
  - the source (staged/deduplicated) DataFrame
  - the business (natural) key column(s)
"""
from delta.tables import DeltaTable
from pyspark.sql import DataFrame, SparkSession


def upsert_scd1(spark: SparkSession, target_table: str, source_df: DataFrame,
                 business_key: str, exclude_from_update=None):
    """
    Performs an SCD Type 1 upsert (insert new, overwrite changed) into a Delta table.
    If the target table does not exist yet, it is created from source_df.

    exclude_from_update: columns that should NOT be overwritten on match
                          (e.g. surrogate_key, created_ts)
    """
    exclude_from_update = exclude_from_update or []

    if not spark.catalog.tableExists(target_table):
        (source_df.write.format("delta").mode("overwrite").saveAsTable(target_table))
        print(f"Created {target_table} with {source_df.count()} rows (initial load).")
        return

    delta_target = DeltaTable.forName(spark, target_table)
    update_cols = {c: f"source.{c}" for c in source_df.columns if c not in exclude_from_update}
    insert_cols = {c: f"source.{c}" for c in source_df.columns}

    (delta_target.alias("target")
        .merge(source_df.alias("source"), f"target.{business_key} = source.{business_key}")
        .whenMatchedUpdate(set=update_cols)
        .whenNotMatchedInsert(values=insert_cols)
        .execute())
    print(f"Merged {source_df.count()} source rows into {target_table}.")


def upsert_fact(spark: SparkSession, target_table: str, source_df: DataFrame,
                 grain_key: str, watermark_col: str = "last_updated_ts"):
    """
    Incremental fact-table MERGE keyed on the transaction grain (e.g. transaction_id).
    Only overwrites a matched row when the incoming record is newer than what's stored,
    which safely supports re-running the incremental notebook (idempotency).
    """
    if not spark.catalog.tableExists(target_table):
        (source_df.write.format("delta").mode("overwrite").saveAsTable(target_table))
        print(f"Created {target_table} with {source_df.count()} rows (historical load).")
        return

    delta_target = DeltaTable.forName(spark, target_table)
    update_cols = {c: f"source.{c}" for c in source_df.columns}

    (delta_target.alias("target")
        .merge(source_df.alias("source"), f"target.{grain_key} = source.{grain_key}")
        .whenMatchedUpdate(
            condition=f"source.{watermark_col} > target.{watermark_col}",
            set=update_cols)
        .whenNotMatchedInsert(values=update_cols)
        .execute())
    print(f"Incrementally merged {source_df.count()} source rows into {target_table}.")


def get_last_watermark(spark: SparkSession, table: str, watermark_col: str = "last_updated_ts"):
    """Returns the max watermark timestamp currently stored, or None if the table is empty/missing."""
    if not spark.catalog.tableExists(table):
        return None
    result = spark.table(table).selectExpr(f"max({watermark_col}) as wm").collect()
    return result[0]["wm"] if result else None
