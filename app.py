import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

DATA = Path(__file__).parent / "data"

st.set_page_config(
    page_title="Every Bottle Back — Customer Growth Dashboard",
    page_icon="♻️",
    layout="wide",
)

# ---------------------------------------------------------------
# Data loading (cached)
# ---------------------------------------------------------------
@st.cache_data
def load_data():
    monthly = pd.read_csv(DATA / "monthly_growth.csv")
    segments = pd.read_csv(DATA / "segment_breakdown.csv")
    seg_growth = pd.read_csv(DATA / "segment_growth.csv")
    regions = pd.read_csv(DATA / "region_breakdown.csv")
    channels = pd.read_csv(DATA / "channel_breakdown.csv")
    historical = pd.read_csv(DATA / "historical_context.csv")
    return monthly, segments, seg_growth, regions, channels, historical

monthly, segments, seg_growth, regions, channels, historical = load_data()

# ---------------------------------------------------------------
# Header
# ---------------------------------------------------------------
st.title("Every Bottle Back — customer growth dashboard")
st.caption(
    "Reliable tracking window: July 2025 – May 2026 (current collection system). "
    "See the historical context panel below for the full 2022–2025 growth story."
)

# ---------------------------------------------------------------
# KPI row
# ---------------------------------------------------------------
latest = monthly.iloc[-1]
prev = monthly.iloc[-2]
growth_rate = (latest["active_customers"] - prev["active_customers"]) / prev["active_customers"] * 100

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total customers tracked", f"{int(monthly['cumulative_customers'].iloc[-1]):,}")
k2.metric("New customers (latest month)", f"{int(latest['new_customers']):,}")
k3.metric("Active customers (latest month)", f"{int(latest['active_customers']):,}", f"{growth_rate:+.1f}%")
k4.metric("Bottles/materials collected (latest month)", f"{latest['total_kg_collected']:,.0f} kg")

st.divider()

# ---------------------------------------------------------------
# Growth trend
# ---------------------------------------------------------------
st.subheader("Customer growth trend")
tab1, tab2 = st.tabs(["Cumulative growth", "New customers per month"])

with tab1:
    fig = px.line(monthly, x="month", y="cumulative_customers", markers=True,
                   labels={"month": "Month", "cumulative_customers": "Cumulative customers"})
    fig.update_layout(height=400, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    fig = px.bar(monthly, x="month", y="new_customers",
                 labels={"month": "Month", "new_customers": "New customers"})
    fig.update_layout(height=400, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ---------------------------------------------------------------
# Segments
# ---------------------------------------------------------------
st.subheader("Who are the customers?")
c1, c2 = st.columns([1, 1.4])

with c1:
    fig = px.pie(segments, names="category", values="count", hole=0.45)
    fig.update_layout(height=380, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

with c2:
    top_segments = segments.nlargest(5, "count")["category"].tolist()
    sg = seg_growth[seg_growth["category"].isin(top_segments)]
    fig = px.area(sg, x="join_month", y="new_customers", color="category",
                   labels={"join_month": "Month", "new_customers": "New customers"})
    fig.update_layout(height=380, margin=dict(l=10, r=10, t=10, b=10), legend_title=None)
    st.plotly_chart(fig, use_container_width=True)

st.caption(
    "Segments are matched from the customer master list (98.5% match rate against active "
    "customers in this window)."
)

st.divider()

# ---------------------------------------------------------------
# Geography & acquisition channel
# ---------------------------------------------------------------
st.subheader("Where customers come from")
c3, c4 = st.columns(2)

with c3:
    top_regions = regions.nlargest(10, "count")
    fig = px.bar(top_regions, x="count", y="region", orientation="h",
                 labels={"count": "Customers", "region": ""})
    fig.update_layout(height=380, margin=dict(l=10, r=10, t=10, b=10), yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig, use_container_width=True)

with c4:
    fig = px.bar(channels.nlargest(10, "count"), x="channel", y="count",
                 labels={"channel": "", "count": "Customers"})
    fig.update_layout(height=380, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

st.caption(
    "Region and acquisition-channel data comes from the contact/CRM sheets, which only "
    "overlap with ~27% of active customers in this window — treat these as directional, "
    "not complete."
)

st.divider()

# ---------------------------------------------------------------
# Growth vs volume
# ---------------------------------------------------------------
st.subheader("Does customer growth track collection volume?")
fig = go.Figure()
fig.add_trace(go.Bar(x=monthly["month"], y=monthly["active_customers"], name="Active customers", yaxis="y1"))
fig.add_trace(go.Scatter(x=monthly["month"], y=monthly["total_kg_collected"], name="Kg collected",
                          yaxis="y2", mode="lines+markers"))
fig.update_layout(
    height=400,
    margin=dict(l=10, r=10, t=10, b=10),
    yaxis=dict(title="Active customers"),
    yaxis2=dict(title="Kg collected", overlaying="y", side="right"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ---------------------------------------------------------------
# Historical context (separate era, clearly labeled)
# ---------------------------------------------------------------
with st.expander("Historical context: 2022–2025 growth (previous tracking system)", expanded=False):
    st.markdown(
        "Every Bottle Back used a different manual tracking system (the *Simple Count* log) "
        "from April 2022 to June 2025, before switching to the current collection/accounting "
        "system in July 2025. The two systems track customers differently and are **not "
        "directly comparable** — this chart is shown for long-term narrative context only, "
        "not as part of the main KPI set above."
    )
    fig = px.line(historical, x="month", y="cumulative_customers", markers=False,
                  labels={"month": "Month", "cumulative_customers": "Cumulative customers (legacy system)"})
    fig.update_layout(height=350, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"Legacy system reached {int(historical['cumulative_customers'].iloc[-1]):,} cumulative customers by June 2025.")

st.divider()
st.caption(
    "Built with Streamlit, Pandas, and Plotly | Every Bottle Back internship project 2026"
)
