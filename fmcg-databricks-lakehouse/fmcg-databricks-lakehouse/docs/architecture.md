# Architecture

## Business context
BigMart Retail (a large FMCG retail chain) has acquired QuickMart (a smaller
regional chain). Leadership needs one consolidated view of sales,
customers, products, and stores across both businesses — for finance
reporting, category management, and store-performance comparisons — within
90 days of deal close.

## Tech architecture

```mermaid
flowchart LR
    subgraph Sources
        A1[BigMart Retail<br/>CSV exports]
        A2[QuickMart<br/>CSV exports]
    end

    A1 --> S3[(Amazon S3<br/>raw landing zone)]
    A2 --> S3

    S3 --> B[Bronze Delta Tables<br/>schema-on-read, 1:1 with source files]

    B --> SD1[Silver dim_customer]
    B --> SD2[Silver dim_product]
    B --> SD3[Silver dim_store]
    B --> SD4[Silver dim_date]
    SD1 & SD2 & SD3 & SD4 --> SF[Silver fact_sales<br/>historical load + incremental MERGE]

    SF --> G1[Gold denormalized_sales]
    G1 --> G2[Gold aggregate tables<br/>monthly revenue, store perf, segments]

    G1 --> GENIE[Genie Space<br/>natural-language Q&A]
    G2 --> DASH[AI/BI Dashboard]

    ORCH[Databricks Workflows<br/>daily schedule] -.orchestrates.-> B
    ORCH -.-> SD1
    ORCH -.-> SF
    ORCH -.-> G1
```

## Why Databricks Free Edition works for this
- Unity Catalog (catalog/schema/table governance) is included.
- Delta Lake MERGE gives idempotent, re-runnable incremental loads.
- Serverless SQL Warehouses power the dashboard without managing clusters.
- Genie Spaces ship out of the box — no extra BI licensing needed for
  stakeholder self-service.
- Databricks Workflows (Jobs) provide free orchestration with task
  dependencies, retries, and failure alerting.

## Two learning paths
1. **Beginner path**: run each notebook manually, in order (00 → 09),
   inspecting each table as you go.
2. **Advanced path**: import `notebooks/orchestration_job.json` as a
   Databricks Workflow and let it run end-to-end on a schedule; focus on
   the MERGE/incremental logic in `src/utils/scd_utils.py` and the data
   quality gates in `src/utils/data_quality.py`.
