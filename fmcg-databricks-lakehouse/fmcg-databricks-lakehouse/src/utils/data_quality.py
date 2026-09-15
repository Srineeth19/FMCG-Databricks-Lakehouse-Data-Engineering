"""
data_quality.py
----------------
Lightweight data-quality checks run at the end of each silver/gold notebook.
Raises an exception (failing the Databricks Job task) if a hard rule is violated,
which is what drives the "failure" branch in the orchestration Workflow.
"""
from pyspark.sql import DataFrame
from pyspark.sql import functions as F


class DataQualityError(Exception):
    pass


def assert_no_nulls(df: DataFrame, columns: list, table_name: str):
    for col in columns:
        null_count = df.filter(F.col(col).isNull()).count()
        if null_count > 0:
            raise DataQualityError(f"[{table_name}] Found {null_count} NULLs in required column '{col}'.")
    print(f"[{table_name}] PASS - no nulls in {columns}")


def assert_unique(df: DataFrame, key_columns: list, table_name: str):
    total = df.count()
    distinct = df.select(*key_columns).distinct().count()
    if total != distinct:
        raise DataQualityError(
            f"[{table_name}] Duplicate keys found on {key_columns}: {total} rows vs {distinct} distinct keys.")
    print(f"[{table_name}] PASS - {key_columns} unique across {total} rows")


def assert_referential_integrity(fact_df: DataFrame, dim_df: DataFrame, fact_key: str,
                                  dim_key: str, table_name: str):
    orphan_count = (fact_df.select(fact_key).distinct()
                    .join(dim_df.select(dim_key), fact_df[fact_key] == dim_df[dim_key], "left_anti")
                    .count())
    if orphan_count > 0:
        raise DataQualityError(
            f"[{table_name}] {orphan_count} rows in fact reference missing '{fact_key}' in dimension.")
    print(f"[{table_name}] PASS - referential integrity OK on {fact_key}")


def assert_row_count_min(df: DataFrame, min_rows: int, table_name: str):
    n = df.count()
    if n < min_rows:
        raise DataQualityError(f"[{table_name}] Row count {n} is below expected minimum {min_rows}.")
    print(f"[{table_name}] PASS - row count {n} >= {min_rows}")
