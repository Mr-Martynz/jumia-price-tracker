"""
Database layer for the Jumia Price Tracker.
Handles SQLite schema creation and inserting scraped data.
"""

import sqlite3
import os
import re
from datetime import datetime
from urllib.parse import urlparse, urlunparse

# Resolve the path relative to this file's location, not the current working
# directory — this file lives in scrapers/, so the project root is one level up.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DB_DIR, "jumia_prices.db")


def normalize_url(url):
    """
    Strips query parameters and fragments from a URL, keeping only the
    scheme/domain/path. Jumia product links sometimes carry tracking
    parameters that change between scrapes even for the same product page —
    without this, the same product could get stored as multiple different
    rows just because its tracking params differed run to run.
    """
    parsed = urlparse(url)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))


def normalize_name_key(name):
    """
    Lowercase, strip punctuation, sort words alphabetically — so a product
    whose scraped title text varies slightly between scrapes (word order,
    punctuation) still matches to the same underlying product, instead of
    creating a new duplicate row every time Jumia's text differs slightly.
    """
    cleaned = re.sub(r'[^a-z0-9\s]', ' ', name.lower())
    words = cleaned.split()
    return ' '.join(sorted(words))


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    """Creates the products and price_history tables if they don't exist yet."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_url TEXT UNIQUE NOT NULL,
            product_name TEXT NOT NULL,
            first_seen_date TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            price_ngn REAL,
            original_price_ngn REAL,
            rating TEXT,
            scrape_date TEXT NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Database ready.")


def upsert_product(product_url, product_name):
    """
    Inserts the product if it's new. Matches on URL first (fast, exact);
    if no URL match, falls back to checking if any existing product has
    the same normalized name — catches the same product appearing with
    a slightly different URL or reworded title on a later scrape.
    Returns the product's id either way.
    """
    product_url = normalize_url(product_url)
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM products WHERE product_url = ?", (product_url,))
    existing = cursor.fetchone()

    if existing:
        product_id = existing[0]
    else:
        # No exact URL match — check if this is the same product under a
        # different URL/title variant before creating a new row.
        name_key = normalize_name_key(product_name)
        cursor.execute("SELECT id, product_name FROM products")
        name_match_id = None
        for row_id, row_name in cursor.fetchall():
            if normalize_name_key(row_name) == name_key:
                name_match_id = row_id
                break

        if name_match_id:
            product_id = name_match_id
        else:
            today = datetime.now().strftime("%Y-%m-%d")
            cursor.execute(
                "INSERT INTO products (product_url, product_name, first_seen_date) VALUES (?, ?, ?)",
                (product_url, product_name, today)
            )
            product_id = cursor.lastrowid

    conn.commit()
    conn.close()
    return product_id


def insert_price_snapshot(product_id, price_ngn, original_price_ngn, rating, scrape_date):
    """Adds one price data point for a product on a given date."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """INSERT INTO price_history
           (product_id, price_ngn, original_price_ngn, rating, scrape_date)
           VALUES (?, ?, ?, ?, ?)""",
        (product_id, price_ngn, original_price_ngn, rating, scrape_date)
    )

    conn.commit()
    conn.close()


def save_scraped_products(products):
    """
    Takes the list of product dicts from JumiaAutoScraper.scrape_page() and
    saves them all: upserts each product, then records a price snapshot for
    each. Skips products with no URL or no price (incomplete scrape data).

    Expects each product dict to have: name, price, url, original_price,
    rating, scrape_date — matching JumiaAutoScraper's output fields.
    """
    init_db()
    saved_count = 0

    for product in products:
        if not product.get('url') or product.get('price') is None:
            continue

        product_id = upsert_product(product['url'], product['name'])
        insert_price_snapshot(
            product_id,
            product['price'],
            product.get('original_price'),
            product.get('rating'),
            product['scrape_date']
        )
        saved_count += 1

    print(f"💾 Saved {saved_count} price snapshots to database.")