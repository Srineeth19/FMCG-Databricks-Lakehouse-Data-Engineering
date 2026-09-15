# End-to-End Data Engineering Project using Databricks Free Edition | FMCG Domain

An end-to-end data engineering project, built on **Databricks Free Edition**,
simulating a real industry scenario: **a large FMCG retail company (BigMart
Retail) acquires a smaller one (QuickMart)**, and a single Lakehouse must be
built to consolidate both companies' data for unified reporting and
self-service analytics.

> Inspired by / built as a hands-on companion to the codebasics YouTube
> project *"End to End Data Engineering Project using Databricks Free
> Edition | FMCG Domain."* This repo is an original implementation of the
> same brief with synthetic data, written from scratch.

## Tech Stack
- **Python** — synthetic data generation, utility modules
- **SQL** — DDL, gold views, dashboard/Genie queries
- **Amazon S3** — raw data landing zone
- **PySpark / Delta Lake** — bronze → silver → gold **Medallion Architecture**
- **Databricks Workflows** — orchestration
- **Databricks AI/BI Dashboard** — stakeholder reporting
- **Databricks Genie** — natural-language Q&A over the gold layer

## Architecture

See [`docs/architecture.md`](docs/architecture.md) for the full diagram and
rationale. In short:

```
BigMart Retail CSVs  ┐
                      ├─► S3 raw zone ─► Bronze (Delta) ─► Silver (conformed dims + merged fact)
QuickMart CSVs       ┘                                          │
                                                                  ▼
                                          Gold: denormalized_sales ──► Genie Space
                                                     │
                                                     ▼
                                    Gold: aggregate KPI tables ──► AI/BI Dashboard
```

## Repository Structure
```
├── data/                    # Synthetic sample source data (both companies)
├── src/
│   ├── generate_sample_data.py
│   └── utils/               # s3_utils, scd_utils (MERGE helpers), data_quality
├── notebooks/                # Databricks notebooks, numbered in run order
│   ├── 00_setup_catalog_schema.py
│   ├── 01_bronze_ingestion_s3.py
│   ├── 02_silver_dim_customer.py
│   ├── 03_silver_dim_product.py
│   ├── 04_silver_dim_store.py
│   ├── 05_silver_dim_date.py
│   ├── 06_silver_fact_sales_historical.py
│   ├── 07_silver_fact_sales_incremental.py
│   ├── 08_gold_denormalized_sales.py
│   ├── 09_gold_aggregates_for_dashboard.py
│   └── orchestration_job.json
├── sql/                     # Standalone SQL: catalog setup, gold views, Genie notes
├── dashboard/               # Dashboard tile queries
├── docs/                    # Architecture, data model (ERD), setup guide
└── requirements.txt
```

## Data Model
Star schema — `fact_sales` (grain: one row per transaction) joined to
`dim_customer`, `dim_product`, `dim_store`, `dim_date`. Every conformed
table carries a `source_system` column (`BigMart Retail` / `QuickMart`) so
pre/post-acquisition comparisons remain possible after consolidation. Full
ERD in [`docs/data_model.md`](docs/data_model.md).

## Quick Start
```bash
# 1. Generate synthetic FMCG source data for both companies
pip install -r requirements.txt
python src/generate_sample_data.py --out-dir data --seed 42

# 2. Upload data/ to your S3 bucket's raw/ zone
aws s3 cp data/ s3://<your-bucket>/raw/ --recursive

# 3. Clone this repo into Databricks Repos and run the notebooks in order (00 -> 09)
```
Full walkthrough: [`docs/setup_guide.md`](docs/setup_guide.md).

## Pipeline Highlights
- **Bronze**: schema-on-read landing from S3, full lineage columns
  (`_source_system`, `_source_file`, `_ingested_at`).
- **Silver dimensions**: SCD Type 1 upserts via Delta `MERGE INTO`
  (`src/utils/scd_utils.py::upsert_scd1`), deduplicated and conformed
  across both companies' differing source schemas.
- **Silver fact**: separate **historical (full) load** notebook and
  **incremental (watermark + MERGE) load** notebook, so re-running is
  always idempotent.
- **Data quality gates**: null checks, uniqueness checks, referential
  integrity checks, and minimum row-count checks run before every write
  (`src/utils/data_quality.py`) — failing a gate fails the Databricks Job
  task and triggers the configured failure notification.
- **Gold**: one wide `denormalized_sales` table (feeds Genie) plus
  pre-aggregated KPI tables (feeds the dashboard, keeps queries cheap).
- **Orchestration**: `notebooks/orchestration_job.json` — importable
  Databricks Workflow with explicit task dependencies, a daily schedule,
  and failure email notification.
- **Genie**: natural-language analytics over `gold.denormalized_sales` —
  setup notes and sample questions in
  [`sql/genie_sample_questions.md`](sql/genie_sample_questions.md).
- **Dashboard**: query-per-tile reference in
  [`dashboard/dashboard_queries.sql`](dashboard/dashboard_queries.sql).

## License
MIT — see [`LICENSE`](LICENSE). Sample data is entirely synthetic.
