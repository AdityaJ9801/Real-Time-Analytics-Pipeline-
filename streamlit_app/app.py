import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ---------------------------------------------------------
# Streamlit Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="E-Commerce Analytics Dashboard",
    layout="wide",
    page_icon="📊"
)

st.title("📊 E-Commerce Analytics Dashboard")
st.markdown("Gain **real-time, data-driven insights** into your e-commerce platform's performance.")


# ---------------------------------------------------------
# API Configuration
# ---------------------------------------------------------
API_BASE_URL = "http://dashboard:5000"

@st.cache_data(ttl=15, show_spinner=False)
def fetch_api_data(endpoint: str):
    """Fetch data from the backend API."""
    try:
        response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Failed to fetch data from `{endpoint}` — {e}")
        return None


# ---------------------------------------------------------
# Section: API Connection Status
# ---------------------------------------------------------
st.divider()
st.subheader("🔌 API Connection Status")

try:
    response = requests.get(API_BASE_URL, timeout=5)
    if response.status_code == 200:
        st.success("✅ Successfully connected to the Dashboard API.")
    else:
        st.error(f"⚠️ API connection failed — Status code: {response.status_code}")
except requests.exceptions.RequestException as e:
    st.error(f"❌ API connection failed: {e}")


# ---------------------------------------------------------
# Section: Overall Statistics & KPIs
# ---------------------------------------------------------
st.divider()
st.header("📈 Platform Overview")

with st.spinner("Fetching overall statistics..."):
    stats_data = fetch_api_data("/stats")

if stats_data:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Events", f"{stats_data.get('total_events', 0):,}")
    col2.metric("Unique Users", f"{stats_data.get('unique_users', 0):,}")
    col3.metric("Unique Products", f"{stats_data.get('unique_products', 0):,}")
    col4.metric("Conversion Rate", f"{stats_data.get('conversion_rate', 0)*100:.2f}%")

    # Device & location distribution
    st.subheader("🌍 Audience Breakdown")
    cols = st.columns(2)

    if 'device_distribution' in stats_data:
        with cols[0]:
            df_device = pd.DataFrame(list(stats_data['device_distribution'].items()), columns=['Device', 'Count'])
            fig = go.Figure(go.Pie(labels=df_device['Device'], values=df_device['Count'], hole=0.3))
            fig.update_layout(title="Device Distribution")
            st.plotly_chart(fig, use_container_width=True)

    if 'top_locations' in stats_data:
        with cols[1]:
            df_loc = pd.DataFrame(list(stats_data['top_locations'].items()), columns=['Location', 'Count'])
            fig = go.Figure(go.Bar(x=df_loc['Location'], y=df_loc['Count'], text=df_loc['Count'], textposition="auto"))
            fig.update_layout(title="Top 5 Locations", xaxis_title="Location", yaxis_title="Events")
            st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("⚠️ Unable to load platform statistics.")

st.divider()
st.header("👤 Top Active Users")

top_users = fetch_api_data("/top-users")

if top_users and "top_users" in top_users:
    df_top_users = pd.DataFrame(top_users["top_users"])
    fig = go.Figure(go.Bar(
        x=df_top_users["user_id"],
        y=df_top_users["events"],
        text=df_top_users["events"],
        textposition="auto"
    ))
    fig.update_layout(title="Most Active Users", xaxis_title="User ID", yaxis_title="Events")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No user activity data found.")





# ---------------------------------------------------------
# Section: Top Products
# ---------------------------------------------------------
st.divider()
st.header("🏆 Product Performance")

cols = st.columns(2)

with cols[0]:
    st.subheader("Top Viewed Products")
    top_viewed_data = fetch_api_data("/top-products")
    if top_viewed_data and "top_viewed_products" in top_viewed_data:
        df_views = pd.DataFrame(top_viewed_data["top_viewed_products"])
        fig = go.Figure(go.Bar(
            x=df_views["product_id"], y=df_views["views"],
            text=df_views["avg_session_time"], texttemplate="🕒 %{text}s avg",
            textposition="auto"
        ))
        fig.update_layout(title="Most Viewed Products", xaxis_title="Product ID", yaxis_title="Views")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No viewed product data available.")

with cols[1]:
    st.subheader("Top Purchased Products")
    top_purchased_data = fetch_api_data("/top-purchases")
    if top_purchased_data and "top_purchased_products" in top_purchased_data:
        df_purchases = pd.DataFrame(top_purchased_data["top_purchased_products"])
        fig = go.Figure(go.Bar(
            x=df_purchases["product_id"], y=df_purchases["purchases"],
            text=df_purchases["total_revenue"], texttemplate="💰 ₹%{text}",
            textposition="auto", marker_color="#00CC96"
        ))
        fig.update_layout(title="Most Purchased Products", xaxis_title="Product ID", yaxis_title="Purchases")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No purchased product data available.")



# ---------------------------------------------------------
# Section: User Insights
# ---------------------------------------------------------
st.divider()
st.header("👥 User Insights")

user_data = fetch_api_data("/user-insights")
if user_data:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Users", user_data.get("total_users", 0))
    col2.metric("Active Users", user_data.get("active_users", 0))
    col3.metric("New Users", user_data.get("new_users", 0))
    col4.metric("Avg Actions/User", user_data.get("avg_actions_per_user", 0))
else:
    st.warning("⚠️ User insight data not available.")


# ---------------------------------------------------------
# Section: Raw Data Tables
# ---------------------------------------------------------
st.divider()
st.header("📄 Raw Data (Preview)")

if top_viewed_data and "top_viewed_products" in top_viewed_data:
    with st.expander("Top Viewed Products Data"):
        st.dataframe(pd.DataFrame(top_viewed_data["top_viewed_products"]), use_container_width=True)

if top_purchased_data and "top_purchased_products" in top_purchased_data:
    with st.expander("Top Purchased Products Data"):
        st.dataframe(pd.DataFrame(top_purchased_data["top_purchased_products"]), use_container_width=True)



# ---------------------------------------------------------
# Refresh Button
# ---------------------------------------------------------
st.divider()
if st.button("🔄 Refresh Dashboard"):
    st.cache_data.clear()
    st.rerun()
