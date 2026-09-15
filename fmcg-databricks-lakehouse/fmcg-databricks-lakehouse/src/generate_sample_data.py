"""
generate_sample_data.py
------------------------
Generates synthetic FMCG source data for TWO companies that are being merged
into a single lakehouse:

  1. big_retail   -> "BigMart Retail"  (the acquiring company - larger, more mature schema)
  2. small_retail -> "QuickMart"       (the acquired company   - smaller, slightly different schema)

The two companies intentionally have different column names / formats to simulate
a realistic acquisition-integration scenario. Silver-layer notebooks are responsible
for conforming these into a single unified schema.

Run:
    python src/generate_sample_data.py --out-dir data --seed 42

Output (CSV, ready to be uploaded to S3 raw/ zone):
    data/big_retail/customers.csv
    data/big_retail/products.csv
    data/big_retail/stores.csv
    data/big_retail/sales_historical.csv
    data/big_retail/sales_incremental.csv

    data/small_retail/customers_small.csv
    data/small_retail/product_master.csv
    data/small_retail/outlets.csv
    data/small_retail/transactions_historical.csv
    data/small_retail/transactions_incremental.csv
"""
import argparse
import csv
import os
import random
from datetime import datetime, timedelta

FMCG_CATEGORIES = {
    "Beverages": ["Cola 500ml", "Orange Juice 1L", "Mineral Water 1L", "Energy Drink 250ml", "Instant Coffee 100g"],
    "Snacks": ["Potato Chips 150g", "Salted Peanuts 200g", "Choco Cookies 300g", "Popcorn 100g", "Namkeen Mix 400g"],
    "Personal Care": ["Shampoo 200ml", "Toothpaste 100g", "Bath Soap 125g", "Hand Sanitizer 100ml", "Body Lotion 200ml"],
    "Home Care": ["Dish Wash Liquid 500ml", "Floor Cleaner 1L", "Laundry Detergent 1kg", "Air Freshener 300ml", "Toilet Cleaner 500ml"],
    "Staples": ["Basmati Rice 5kg", "Refined Oil 1L", "Wheat Flour 5kg", "Sugar 1kg", "Tea Leaves 250g"],
}

CITIES = ["Mumbai", "Delhi", "Bengaluru", "Hyderabad", "Chennai", "Pune", "Kolkata", "Ahmedabad", "Jaipur", "Lucknow"]
STATES = {
    "Mumbai": "Maharashtra", "Pune": "Maharashtra", "Delhi": "Delhi", "Bengaluru": "Karnataka",
    "Hyderabad": "Telangana", "Chennai": "Tamil Nadu", "Kolkata": "West Bengal",
    "Ahmedabad": "Gujarat", "Jaipur": "Rajasthan", "Lucknow": "Uttar Pradesh",
}
FIRST_NAMES = ["Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayaan", "Krishna", "Ishaan",
               "Ananya", "Diya", "Aadhya", "Saanvi", "Myra", "Pari", "Anika", "Navya", "Riya", "Ira"]
LAST_NAMES = ["Sharma", "Verma", "Gupta", "Reddy", "Iyer", "Patel", "Nair", "Singh", "Rao", "Mehta"]


def rand_date(start: datetime, end: datetime) -> datetime:
    delta = end - start
    return start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))


def gen_products(prefix: str, n: int):
    rows = []
    pid = 1
    for category, items in FMCG_CATEGORIES.items():
        for item in items:
            rows.append({
                "product_id": f"{prefix}{pid:04d}",
                "product_name": item,
                "category": category,
                "brand": f"{category.split()[0]}Co",
                "unit_price": round(random.uniform(15, 650), 2),
                "unit_of_measure": "EA",
            })
            pid += 1
    while len(rows) < n:
        category = random.choice(list(FMCG_CATEGORIES.keys()))
        item = random.choice(FMCG_CATEGORIES[category])
        rows.append({
            "product_id": f"{prefix}{pid:04d}",
            "product_name": item,
            "category": category,
            "brand": f"{category.split()[0]}Co",
            "unit_price": round(random.uniform(15, 650), 2),
            "unit_of_measure": "EA",
        })
        pid += 1
    return rows


def gen_customers(prefix: str, n: int):
    rows = []
    for i in range(1, n + 1):
        city = random.choice(CITIES)
        rows.append({
            "customer_id": f"{prefix}{i:05d}",
            "first_name": random.choice(FIRST_NAMES),
            "last_name": random.choice(LAST_NAMES),
            "city": city,
            "state": STATES[city],
            "signup_date": rand_date(datetime(2019, 1, 1), datetime(2024, 12, 31)).strftime("%Y-%m-%d"),
            "loyalty_segment": random.choice(["Bronze", "Silver", "Gold", "Platinum"]),
        })
    return rows


def gen_stores(prefix: str, n: int):
    rows = []
    for i in range(1, n + 1):
        city = random.choice(CITIES)
        rows.append({
            "store_id": f"{prefix}{i:03d}",
            "store_name": f"{prefix}-Store-{city}-{i}",
            "city": city,
            "state": STATES[city],
            "store_type": random.choice(["Supermarket", "Convenience", "Hypermarket"]),
            "opened_date": rand_date(datetime(2015, 1, 1), datetime(2023, 6, 30)).strftime("%Y-%m-%d"),
        })
    return rows


def gen_transactions(prefix: str, customers, products, stores, start, end, n):
    rows = []
    for i in range(1, n + 1):
        cust = random.choice(customers)
        prod = random.choice(products)
        store = random.choice(stores)
        qty = random.randint(1, 10)
        ts = rand_date(start, end)
        rows.append({
            "transaction_id": f"{prefix}TXN{i:07d}",
            "customer_id": cust["customer_id"],
            "product_id": prod["product_id"],
            "store_id": store["store_id"],
            "quantity": qty,
            "unit_price": prod["unit_price"],
            "total_amount": round(qty * float(prod["unit_price"]), 2),
            "transaction_ts": ts.strftime("%Y-%m-%d %H:%M:%S"),
            "payment_mode": random.choice(["Card", "UPI", "Cash", "Wallet"]),
            "last_updated_ts": ts.strftime("%Y-%m-%d %H:%M:%S"),
        })
    return rows


def write_csv(path, rows, fieldnames):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  wrote {len(rows):>6} rows -> {path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="data")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    random.seed(args.seed)

    print("Generating BigMart Retail (big company) source data...")
    big_products = gen_products("BM-P", 40)
    big_customers = gen_customers("BM-C", 4000)
    big_stores = gen_stores("BM-S", 40)
    big_hist = gen_transactions("BM-", big_customers, big_products, big_stores,
                                 datetime(2023, 1, 1), datetime(2024, 12, 31), 60000)
    big_incr = gen_transactions("BM-", big_customers, big_products, big_stores,
                                 datetime(2025, 1, 1), datetime(2025, 1, 7), 2500)

    write_csv(f"{args.out_dir}/big_retail/products.csv", big_products,
              ["product_id", "product_name", "category", "brand", "unit_price", "unit_of_measure"])
    write_csv(f"{args.out_dir}/big_retail/customers.csv", big_customers,
              ["customer_id", "first_name", "last_name", "city", "state", "signup_date", "loyalty_segment"])
    write_csv(f"{args.out_dir}/big_retail/stores.csv", big_stores,
              ["store_id", "store_name", "city", "state", "store_type", "opened_date"])
    write_csv(f"{args.out_dir}/big_retail/sales_historical.csv", big_hist,
              ["transaction_id", "customer_id", "product_id", "store_id", "quantity", "unit_price",
               "total_amount", "transaction_ts", "payment_mode", "last_updated_ts"])
    write_csv(f"{args.out_dir}/big_retail/sales_incremental.csv", big_incr,
              ["transaction_id", "customer_id", "product_id", "store_id", "quantity", "unit_price",
               "total_amount", "transaction_ts", "payment_mode", "last_updated_ts"])

    print("\nGenerating QuickMart (small, acquired company) source data...")
    small_products = gen_products("QM-P", 15)
    small_customers = gen_customers("QM-C", 800)
    small_stores = gen_stores("QM-S", 8)
    small_hist = gen_transactions("QM-", small_customers, small_products, small_stores,
                                   datetime(2023, 1, 1), datetime(2024, 12, 31), 9000)
    small_incr = gen_transactions("QM-", small_customers, small_products, small_stores,
                                   datetime(2025, 1, 1), datetime(2025, 1, 7), 400)

    # Note: deliberately different column names/order to simulate a different source schema
    write_csv(f"{args.out_dir}/small_retail/product_master.csv", small_products,
              ["product_id", "product_name", "category", "brand", "unit_price", "unit_of_measure"])
    write_csv(f"{args.out_dir}/small_retail/customers_small.csv", small_customers,
              ["customer_id", "first_name", "last_name", "city", "state", "signup_date", "loyalty_segment"])
    write_csv(f"{args.out_dir}/small_retail/outlets.csv", small_stores,
              ["store_id", "store_name", "city", "state", "store_type", "opened_date"])
    write_csv(f"{args.out_dir}/small_retail/transactions_historical.csv", small_hist,
              ["transaction_id", "customer_id", "product_id", "store_id", "quantity", "unit_price",
               "total_amount", "transaction_ts", "payment_mode", "last_updated_ts"])
    write_csv(f"{args.out_dir}/small_retail/transactions_incremental.csv", small_incr,
              ["transaction_id", "customer_id", "product_id", "store_id", "quantity", "unit_price",
               "total_amount", "transaction_ts", "payment_mode", "last_updated_ts"])

    print("\nDone. Upload the 'data/' folder to your S3 bucket's raw/ zone, e.g.:")
    print("  s3://<your-bucket>/fmcg-lakehouse/raw/big_retail/")
    print("  s3://<your-bucket>/fmcg-lakehouse/raw/small_retail/")


if __name__ == "__main__":
    main()
