# Sample Data

This folder ships a **small trimmed sample** of the synthetic FMCG data
(so the repo stays lightweight) — dimension files are complete, and the
transaction/fact CSVs are sampled down to ~100-200 rows.

To regenerate the **full** dataset (60k+ historical transactions for
BigMart Retail, 9k for QuickMart) before uploading to S3:

```bash
python src/generate_sample_data.py --out-dir data --seed 42
```

| Folder | Company | Files |
|---|---|---|
| `big_retail/` | BigMart Retail (acquirer) | `customers.csv`, `products.csv`, `stores.csv`, `sales_historical.csv`, `sales_incremental.csv` |
| `small_retail/` | QuickMart (acquired) | `customers_small.csv`, `product_master.csv`, `outlets.csv`, `transactions_historical.csv`, `transactions_incremental.csv` |

Note the deliberately different file/column naming between the two
companies — this simulates the real-world schema mismatch you'd hit
integrating an acquired company's data, and is resolved in the silver
notebooks (`02`-`04`).
