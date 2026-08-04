import sqlite3

conn = sqlite3.connect('data/jumia_prices.db')

total_products = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
print(f"Total tracked products: {total_products}\n")

rows = conn.execute("""
    SELECT p.product_name, COUNT(h.id) as snapshot_count,
           MIN(h.price_ngn) as lowest, MAX(h.price_ngn) as highest
    FROM products p
    JOIN price_history h ON p.id = h.product_id
    GROUP BY p.id
    ORDER BY snapshot_count DESC
""").fetchall()

print(f"{'Snapshots':<10} {'Lowest':<12} {'Highest':<12} Product Name")
print("-" * 80)
for name, count, lowest, highest in rows:
    short_name = name[:45] + "..." if len(name) > 45 else name
    print(f"{count:<10} ₦{lowest:<11,.0f} ₦{highest:<11,.0f} {short_name}")

conn.close()