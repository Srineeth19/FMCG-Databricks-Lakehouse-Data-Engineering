"""
s3_utils.py
-----------
Helper functions for connecting Databricks Free Edition to an Amazon S3 bucket
and reading the FMCG raw landing zone into Spark DataFrames.

Databricks Free Edition does not support Unity Catalog external locations /
instance profiles the way a paid workspace does, so the simplest, most
portable approach is:

  1. Store AWS credentials as Databricks secrets (recommended), OR
  2. Set them as Spark conf / environment variables for the cluster session.

Usage (inside a notebook):

    from src.utils.s3_utils import get_s3_path, read_csv_from_s3

    df = read_csv_from_s3(spark, get_s3_path("big_retail", "customers.csv"))
"""

S3_BUCKET = "fmcg-lakehouse-demo"          # <-- change to your bucket name
S3_RAW_PREFIX = "raw"                      # raw landing zone prefix


def configure_s3_access(spark, access_key: str, secret_key: str, region: str = "ap-south-1"):
    """
    Configures the Spark session to read/write S3 using access keys.
    In production, prefer Databricks secret scopes instead of hardcoding keys:

        access_key = dbutils.secrets.get(scope="aws", key="access_key")
        secret_key = dbutils.secrets.get(scope="aws", key="secret_key")
    """
    hadoop_conf = spark._jsc.hadoopConfiguration()
    hadoop_conf.set("fs.s3a.access.key", access_key)
    hadoop_conf.set("fs.s3a.secret.key", secret_key)
    hadoop_conf.set("fs.s3a.endpoint", f"s3.{region}.amazonaws.com")
    hadoop_conf.set("fs.s3a.aws.credentials.provider",
                     "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider")
    return spark


def get_s3_path(company_folder: str, file_name: str, bucket: str = S3_BUCKET,
                 prefix: str = S3_RAW_PREFIX) -> str:
    """Builds a fully-qualified s3a:// path for a raw source file."""
    return f"s3a://{bucket}/{prefix}/{company_folder}/{file_name}"


def read_csv_from_s3(spark, path: str, schema=None):
    reader = spark.read.option("header", "true").option("inferSchema", schema is None)
    if schema is not None:
        reader = reader.schema(schema)
    return reader.csv(path)
