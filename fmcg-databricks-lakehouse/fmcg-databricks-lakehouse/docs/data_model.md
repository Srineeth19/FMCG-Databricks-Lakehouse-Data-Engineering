# Data Model

Star schema, grain of `fact_sales` = one row per sales transaction line.

```mermaid
erDiagram
    FACT_SALES }o--|| DIM_CUSTOMER : customer_id
    FACT_SALES }o--|| DIM_PRODUCT  : product_id
    FACT_SALES }o--|| DIM_STORE    : store_id
    FACT_SALES }o--|| DIM_DATE     : transaction_date

    FACT_SALES {
        string transaction_id PK
        string customer_id FK
        string product_id FK
        string store_id FK
        date transaction_date FK
        int quantity
        decimal unit_price
        decimal total_amount
        string payment_mode
        string source_system
        timestamp last_updated_ts
    }
    DIM_CUSTOMER {
        string customer_id PK
        string full_name
        string city
        string state
        date signup_date
        string loyalty_segment
        string source_system
    }
    DIM_PRODUCT {
        string product_id PK
        string product_name
        string category
        string brand
        decimal unit_price
        string source_system
    }
    DIM_STORE {
        string store_id PK
        string store_name
        string city
        string state
        string store_type
        string source_system
    }
    DIM_DATE {
        date date_key PK
        int year
        int quarter
        int month
        string month_name
        boolean is_weekend
        int fiscal_year
    }
```

## Why `source_system` is on every table
Since this is an acquisition-integration project, every conformed table
carries a `source_system` column (`BigMart Retail` vs `QuickMart`). This
lets analysts and Genie answer both "consolidated" questions (whole
company) and "pre/post-merger comparison" questions without needing
separate schemas per company.

## Medallion layers
| Layer  | Contents | Format |
|--------|----------|--------|
| Bronze | Raw as-landed CSV -> Delta, one table per source file per company | Delta, append/overwrite |
| Silver | Conformed, deduplicated, SCD-1 dimensions + merged fact table | Delta, MERGE |
| Gold   | `denormalized_sales` (Genie) + pre-aggregated KPI tables (dashboard) | Delta, CTAS |
