# Setup Guide

## 1. Sign up for Databricks Free Edition
Create your workspace, then open the **Workspace** UI.

## 2. Generate (or bring your own) sample data
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python src/generate_sample_data.py --out-dir data --seed 42
```
This creates the `data/big_retail/` and `data/small_retail/` CSVs.

## 3. Create an S3 bucket and upload the raw data
```bash
aws s3 mb s3://fmcg-lakehouse-demo
aws s3 cp data/big_retail/   s3://fmcg-lakehouse-demo/raw/big_retail/   --recursive
aws s3 cp data/small_retail/ s3://fmcg-lakehouse-demo/raw/small_retail/ --recursive
```

## 4. Store AWS credentials as Databricks secrets
```bash
databricks secrets create-scope aws
databricks secrets put-secret aws access_key
databricks secrets put-secret aws secret_key
```

## 5. Clone this repo into Databricks Repos
Workspace → Repos → Add Repo → paste this GitHub URL.

## 6. Run the notebooks in order
1. `00_setup_catalog_schema`
2. `01_bronze_ingestion_s3` (set the `s3_bucket` widget to your bucket name)
3. `02_silver_dim_customer`, `03_silver_dim_product`, `04_silver_dim_store`, `05_silver_dim_date`
4. `06_silver_fact_sales_historical` — run **once** to backfill
5. `07_silver_fact_sales_incremental` — run repeatedly / schedule daily
6. `08_gold_denormalized_sales`
7. `09_gold_aggregates_for_dashboard`

## 7. Set up orchestration
Workflows → Create Job → Import `notebooks/orchestration_job.json` (adjust
notebook paths to match where you cloned the repo).

## 8. Set up Genie
Catalog Explorer → Genie → New Space → add `gold.denormalized_sales` and
the aggregate tables. See `sql/genie_sample_questions.md` for instructions
and example questions to seed the space.

## 9. Build the dashboard
SQL Editor → run each query in `dashboard/dashboard_queries.sql` → save as
a dataset → Dashboards → New Dashboard → add visualizations.
