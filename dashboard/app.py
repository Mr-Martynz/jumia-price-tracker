import streamlit as st
import pandas as pd
import plotly.graph_objects as go
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

# A little breathing room between sections/columns — default Streamlit
# spacing is tight, this loosens it slightly without a full custom theme.
st.markdown("""
    <style>
        .block-container { padding-top: 2rem; padding-bottom: 3rem; }
        div[data-testid="stMetric"] { padding: 0.5rem 0; }
        div[data-testid="column"] { padding: 0 0.75rem; }
    </style>
""", unsafe_allow_html=True)


def load_current_prices():
    """One row per product with its most recent price."""
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
    """Full price history for one product, oldest first."""
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
    st.markdown(f"**{label}**")
    for _, row in df.iterrows():
        name = row["product_name"]
        short_name = name[:55] + "..." if len(name) > 55 else name
        st.write(f"₦{row['price_ngn']:,.0f} — {short_name}")


def get_trend(pct_change):
    """
    Converts a raw % change into a plain-English trend label.
    Anything within +/-1% is treated as 'Stable' rather than Rising/Falling —
    tiny fluctuations aren't a meaningful trend, and calling a 0.3% wobble
    'Rising' would overstate what the data actually shows.
    """
    if pct_change > 1:
        return "📈 Rising", "#e74c3c"
    elif pct_change < -1:
        return "📉 Falling", "#2ecc71"
    else:
        return "➡️ Stable", "#95a5a6"


def get_buy_framing(pct_change):
    """
    Plain-English buy/wait framing based on price direction since first seen.
    Deliberately conservative — this describes what already happened
    (price went up or down), not a prediction of what will happen next.
    We don't have enough history yet to forecast, so we don't claim to.
    """
    if pct_change <= -3:
        return f"⬇️ Down {abs(pct_change):.1f}% since first tracked — good time to consider buying"
    elif pct_change >= 3:
        return f"⬆️ Up {pct_change:.1f}% since first tracked — may be worth waiting"
    else:
        return "Price has stayed roughly steady since first tracked"


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

        trend_label, trend_color = get_trend(pct_change)
        buy_framing = get_buy_framing(pct_change)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current Price", f"₦{current_price:,.0f}", delta=f"{pct_change:+.1f}%")
        with col2:
            st.markdown(f"**Price Trend**")
            st.markdown(f"<span style='color:{trend_color}; font-size:1.4rem'>{trend_label}</span>", unsafe_allow_html=True)
        with col3:
            st.markdown("**Buy Signal**")
            st.write(buy_framing)

        st.divider()
        st.subheader("Price History")

        # Interactive Plotly chart — replaces the earlier static Matplotlib
        # version. Lets viewers hover for exact values and zoom into a
        # specific date range, which a flat image can't offer.
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=history_df["scrape_date"],
            y=history_df["price_ngn"],
            mode="lines+markers",
            line=dict(color="#f68b1e", width=2),
            marker=dict(size=8),
            name="Price"
        ))

        low_idx = history_df["price_ngn"].idxmin()
        high_idx = history_df["price_ngn"].idxmax()
        fig.add_annotation(
            x=history_df.loc[low_idx, "scrape_date"], y=history_df.loc[low_idx, "price_ngn"],
            text=f"Lowest ₦{lowest_price:,.0f}", showarrow=True, arrowhead=2,
            font=dict(color="#2ecc71"), ay=40
        )
        fig.add_annotation(
            x=history_df.loc[high_idx, "scrape_date"], y=history_df.loc[high_idx, "price_ngn"],
            text=f"Highest ₦{highest_price:,.0f}", showarrow=True, arrowhead=2,
            font=dict(color="#e74c3c"), ay=-40
        )

        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Price (₦)",
            hovermode="x unified",
            margin=dict(t=20, b=20)
        )

        st.plotly_chart(fig, use_container_width=True)

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