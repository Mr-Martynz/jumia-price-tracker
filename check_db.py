import sqlite3

conn = sqlite3.connect('data/jumia_prices.db')
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print("Tables found:", tables)
conn.close()