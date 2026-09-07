"""
Second-pass cleanup: merges product rows that are the same product but with
slightly different scraped text — e.g. word order swapped between scrapes
("1.77 inch Big Button" vs "Big Button 1.77 inch"). The first cleanup script
only matched exact-identical names, which missed these.

How it matches: normalizes each name by lowercasing, stripping punctuation,
splitting into words, and sorting those words alphabetically. Two names
with the same words in a different order produce the same "key" and get
merged. Names with genuinely different words (e.g. different color/model
variants) still produce different keys and are correctly left separate.
"""
import sqlite3
import os
import re
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "jumia_prices.db")


def normalize_key(name):
    cleaned = re.sub(r'[^a-z0-9\s]', ' ', name.lower())
    words = cleaned.split()
    return ' '.join(sorted(words))


conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("SELECT id, product_name, first_seen_date FROM products")
all_products = cursor.fetchall()

groups = defaultdict(list)
for product_id, name, first_seen in all_products:
    key = normalize_key(name)
    groups[key].append((product_id, name, first_seen))

merged_count = 0
group_count = 0

for key, rows in groups.items():
    if len(rows) < 2:
        continue

    group_count += 1
    # Keep the one with the earliest first_seen_date
    rows.sort(key=lambda r: r[2])
    keep_id, keep_name, _ = rows[0]
    duplicates = rows[1:]

    for dup_id, dup_name, _ in duplicates:
        cursor.execute(
            "UPDATE price_history SET product_id = ? WHERE product_id = ?",
            (keep_id, dup_id)
        )
        cursor.execute("DELETE FROM products WHERE id = ?", (dup_id,))

    print(f"Merged {len(duplicates)} variant(s) into: {keep_name[:60]}")
    merged_count += len(duplicates)

conn.commit()
conn.close()

print(f"\n✅ Done. {group_count} groups had duplicates. Merged {merged_count} rows total.")