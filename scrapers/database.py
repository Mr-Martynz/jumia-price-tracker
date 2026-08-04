"""
Database layer for the Jumia Price Tracker.
Handles SQLite schema creation and inserting scraped data.
"""

import sqlite3
import os
from datetime import datetime

# Resolve the path relative to this file's location, not the current working
# directory — this file lives in scrapers/, so the project root is one level up.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DB_DIR, "jumia_prices.db")


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
    Inserts the product if it's new. If it already exists, does nothing
    (keeps the original first_seen_date and name).
    Returns the product's id either way.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM products WHERE product_url = ?", (product_url,))
    existing = cursor.fetchone()

    if existing:
        product_id = existing[0]
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
    Takes the list of product dicts from the scraper and saves them all:
    upserts each product, then records today's price snapshot for each.
    Skips products with no valid price or URL (bad scrape data).
    """
    init_db()
    saved_count = 0

    for product in products:
        if product['product_url'] == 'N/A' or product['price_ngn'] is None:
            continue

        product_id = upsert_product(product['product_url'], product['product_name'])
        insert_price_snapshot(
            product_id,
            product['price_ngn'],
            product['original_price_ngn'],
            product['rating'],
            product['scrape_date']
        )
        saved_count += 1

    print(f"💾 Saved {saved_count} price snapshots to database.")