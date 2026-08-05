"""
One-time cleanup: merges duplicate product rows that were created before the
URL-normalization fix. Products with the exact same name got split into
multiple rows because their URLs differed only by tracking query params.

This finds products sharing the same product_name, keeps the OLDEST one
(earliest first_seen_date), moves all price_history rows from the
duplicates onto the kept product, then deletes the now-empty duplicate rows.
"""
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "jumia_prices.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Find product names that have more than one row
cursor.execute("""
    SELECT product_name, COUNT(*) as cnt
    FROM products
    GROUP BY product_name
    HAVING cnt > 1
""")
duplicate_names = cursor.fetchall()

print(f"Found {len(duplicate_names)} product names with duplicate rows.\n")

merged_count = 0
for name, count in duplicate_names:
    cursor.execute(
        "SELECT id FROM products WHERE product_name = ? ORDER BY first_seen_date ASC",
        (name,)
    )
    ids = [row[0] for row in cursor.fetchall()]
    keep_id = ids[0]
    duplicate_ids = ids[1:]

    for dup_id in duplicate_ids:
        cursor.execute(
            "UPDATE price_history SET product_id = ? WHERE product_id = ?",
            (keep_id, dup_id)
        )
        cursor.execute("DELETE FROM products WHERE id = ?", (dup_id,))

    print(f"Merged {len(duplicate_ids)} duplicate(s) of: {name[:60]}")
    merged_count += len(duplicate_ids)

conn.commit()
conn.close()

print(f"\n✅ Done. Merged {merged_count} duplicate rows total.")