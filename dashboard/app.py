import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
import sys
import os

# dashboard/app.py needs to reach scrapers/database.py, which is a sibling
# folder, not a subfolder — add the project root to sys.path so the import
# below can find it.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from scrapers.database import DB_PATH

st.set_page_config(
    page_title="Jumia Price Tracker",
    page_icon="🛒",
    layout="wide"
)


def load_current_prices():
    """
    Returns one row per product with its most recent price — this is what
    powers the top-5 cheapest/most-expensive overview. Uses a subquery to
    grab only the latest scrape_date per product, not every historical row.
    """
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""
        SELECT p.id, p.product_name, h.price_ngn, h.scrape_date
        FROM products p
        JOIN price_history h ON p.id = h.product_id
        WHERE h.scrape_date = (
            SELECT MAX(scrape_date) FROM price_history WHERE product_id = p.id
        )
    """, conn)
    conn.close()
    return df


def load_price_history(product_id):
    """Returns the full price history for one product, oldest first."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT scrape_date, price_ngn FROM price_history WHERE product_id = ? ORDER BY scrape_date",
        conn,
        params=(product_id,)
    )
    conn.close()
    df["scrape_date"] = pd.to_datetime(df["scrape_date"])
    return df


def render_product_list(df, label):
    """Renders a simple ranked list of products with their prices."""
    st.markdown(f"**{label}**")
    for _, row in df.iterrows():
        name = row["product_name"]
        short_name = name[:55] + "..." if len(name) > 55 else name
        st.write(f"₦{row['price_ngn']:,.0f} — {short_name}")


# ---- SIDEBAR: QUICK STATS ----
with st.sidebar:
    st.header("📈 Quick Stats")

# ---- HEADER ----
st.title("🛒 Jumia Price Tracker")
st.caption("Track how product prices change over time")

current_prices_df = load_current_prices()

if current_prices_df.empty:
    st.error("No products tracked yet. Run the scraper first to collect some data.")
    st.stop()

with st.sidebar:
    st.metric("Total Products Tracked", len(current_prices_df))
    st.metric("Average Price", f"₦{current_prices_df['price_ngn'].mean():,.0f}")
    last_updated = current_prices_df["scrape_date"].max()
    st.caption(f"Last updated: {last_updated}")

st.divider()

# ---- SEARCH & DRILL INTO A SPECIFIC PRODUCT ----
st.subheader("🔍 Search for a Product")

search_term = st.text_input("Type part of a product name:", "")

if search_term:
    filtered_df = current_prices_df[
        current_prices_df["product_name"].str.contains(search_term, case=False, na=False)
    ]
else:
    filtered_df = current_prices_df

if filtered_df.empty:
    st.warning("No products match that search. Browse the overview below instead.")
else:
    selected_name = st.selectbox(
        f"Choose a product to view ({len(filtered_df)} match{'es' if len(filtered_df) != 1 else ''}):",
        filtered_df["product_name"].sort_values()
    )
    selected_id = int(filtered_df.loc[filtered_df["product_name"] == selected_name, "id"].iloc[0])

    history_df = load_price_history(selected_id)

    if len(history_df) < 2:
        st.info("📊 Only 1 price point recorded so far for this product — check back after the next scrape to see a trend.")
        st.metric("Current Price", f"₦{history_df['price_ngn'].iloc[-1]:,.0f}")
    else:
        current_price = history_df["price_ngn"].iloc[-1]
        lowest_price = history_df["price_ngn"].min()
        highest_price = history_df["price_ngn"].max()
        first_price = history_df["price_ngn"].iloc[0]
        pct_change = ((current_price - first_price) / first_price) * 100

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Current Price", f"₦{current_price:,.0f}")
        with col2:
            st.metric("Lowest Recorded", f"₦{lowest_price:,.0f}")
        with col3:
            st.metric("Highest Recorded", f"₦{highest_price:,.0f}")
        with col4:
            st.metric("Change Since First Seen", f"{pct_change:+.1f}%", delta=f"{pct_change:+.1f}%")

        st.subheader("Price History")

        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(history_df["scrape_date"], history_df["price_ngn"],
                color="#f68b1e", linewidth=2, marker="o", markersize=6)

        # Annotate the lowest and highest points so the chart tells the
        # story at a glance, without needing to cross-reference the metrics above.
        low_idx = history_df["price_ngn"].idxmin()
        high_idx = history_df["price_ngn"].idxmax()
        low_point = history_df.loc[low_idx]
        high_point = history_df.loc[high_idx]

        ax.annotate(f"Lowest\n₦{low_point['price_ngn']:,.0f}",
                    xy=(low_point["scrape_date"], low_point["price_ngn"]),
                    xytext=(0, -25), textcoords="offset points",
                    ha="center", fontsize=9, color="#2ecc71",
                    arrowprops=dict(arrowstyle="->", color="#2ecc71"))

        ax.annotate(f"Highest\n₦{high_point['price_ngn']:,.0f}",
                    xy=(high_point["scrape_date"], high_point["price_ngn"]),
                    xytext=(0, 20), textcoords="offset points",
                    ha="center", fontsize=9, color="#e74c3c",
                    arrowprops=dict(arrowstyle="->", color="#e74c3c"))

        ax.set_ylabel("Price (₦)")
        ax.set_xlabel("Date")
        plt.xticks(rotation=30)
        plt.tight_layout()
        st.pyplot(fig)

st.divider()

# ---- OVERVIEW: TOP 5 CHEAPEST / MOST EXPENSIVE ----
st.subheader("📊 Browse: Top 5 Cheapest & Most Expensive")

col1, col2 = st.columns(2)

with col1:
    cheapest = current_prices_df.nsmallest(5, "price_ngn")
    render_product_list(cheapest, "💸 Top 5 Cheapest")

with col2:
    priciest = current_prices_df.nlargest(5, "price_ngn")
    render_product_list(priciest, "👑 Top 5 Most Expensive")

st.divider()
st.caption(f"Tracking {len(current_prices_df)} products total.")