# Genie Space Setup — FMCG Sales

Genie is configured in the Databricks UI (Catalog Explorer → *Genie* →
*New Space*), not via code. This file documents how the space used in this
project was set up, so it's reproducible.

## Tables added to the space
- `fmcg_lakehouse.gold.denormalized_sales` (primary)
- `fmcg_lakehouse.gold.monthly_revenue_by_category`
- `fmcg_lakehouse.gold.store_performance`
- `fmcg_lakehouse.gold.customer_segment_summary`

## General instructions given to the Genie space
```
This space answers questions about FMCG retail sales after BigMart Retail
(the acquirer) acquired QuickMart (the acquired company). "source_system"
distinguishes the two: 'BigMart Retail' vs 'QuickMart'. Revenue figures are
in INR. Fiscal year starts April 1. When a question mentions "the acquired
company" or "the smaller company", interpret that as QuickMart.
```

## Sample business questions this space can answer
- "What is our total revenue by product category this fiscal year?"
- "Compare average order value between BigMart Retail and QuickMart."
- "Which are the top 5 stores by revenue in Mumbai?"
- "How many Gold and Platinum loyalty customers do we have per city?"
- "Show monthly revenue trend for Beverages vs Snacks in 2024."
- "What percentage of total revenue comes from QuickMart stores?"
- "Which product category has the highest average basket value?"

## Example curated SQL pairs (improves Genie accuracy)
Add these under "Example SQL queries" in the Genie space UI:

```sql
-- "total revenue by source company"
SELECT source_system, SUM(total_amount) AS revenue
FROM fmcg_lakehouse.gold.denormalized_sales
GROUP BY source_system;

-- "top 5 stores by revenue"
SELECT store_name, revenue
FROM fmcg_lakehouse.gold.store_performance
ORDER BY revenue DESC
LIMIT 5;
```
