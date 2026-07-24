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
# Style — rounded cards, soft background, accent palette
# ---------------------------------------------------------------
ACCENT = "#0F6E56"     # teal
ACCENT2 = "#534AB7"    # purple
ACCENT3 = "#D85A30"    # coral
PALETTE = [ACCENT, ACCENT2, ACCENT3, "#EF9F27", "#378ADD", "#D4537E"]

st.markdown("""
<style>
[data-testid="stMetric"] {
    background: white;
    border-radius: 14px;
    padding: 16px 18px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    border: 1px solid rgba(0,0,0,0.05);
}
[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 14px;
}
div[data-testid="stExpander"] {
    border-radius: 14px;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------
# Data loading (cached)
# ---------------------------------------------------------------
@st.cache_data
def load_data():
    tx = pd.read_csv(DATA / "enriched_transactions.csv", parse_dates=["date"])
    historical = pd.read_csv(DATA / "historical_context.csv")
    return tx, historical

tx, historical = load_data()

# ---------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------
st.sidebar.header("Filters")

months = sorted(tx["month"].unique())
month_range = st.sidebar.select_slider(
    "Month range",
    options=months,
    value=(months[0], months[-1]),
)

material_options = sorted(tx["material_group"].unique())
materials = st.sidebar.multiselect("Material type", material_options, default=material_options)

category_options = sorted(tx["category"].unique())
categories = st.sidebar.multiselect("Customer segment", category_options, default=category_options)

region_options = sorted(tx["region"].dropna().unique())
regions = st.sidebar.multiselect("Region (partial data)", region_options, default=region_options)

st.sidebar.caption(
    "Region filter only affects the ~27% of customers with a matched contact record; "
    "other charts are unaffected by it."
)

mask = (
    (tx["month"] >= month_range[0]) & (tx["month"] <= month_range[1])
    & (tx["material_group"].isin(materials))
    & (tx["category"].isin(categories))
)
f = tx[mask].copy()

region_mask = mask & (tx["region"].isin(regions) | tx["region"].isna())
f_region = tx[region_mask].copy()

# ---------------------------------------------------------------
# Header
# ---------------------------------------------------------------
st.title("Every Bottle Back — customer growth dashboard")
st.caption(
    f"Showing {month_range[0]} to {month_range[1]} · reliable tracking window "
    "(current collection system, July 2025 onward). Use the sidebar to filter."
)

if f.empty:
    st.warning("No data matches the current filters. Try widening your selection.")
    st.stop()

# ---------------------------------------------------------------
# KPI row
# ---------------------------------------------------------------
monthly = f.groupby("month").agg(
    active_customers=("name_key", "nunique"),
    total_kg=("total_quantity", "sum"),
).reset_index()
new_per_month = f.drop_duplicates("name_key").groupby("join_month").size()
monthly["new_customers"] = monthly["month"].map(new_per_month).fillna(0)
monthly = monthly.sort_values("month")
monthly["cumulative_customers"] = monthly["new_customers"].cumsum()

latest = monthly.iloc[-1]
prev = monthly.iloc[-2] if len(monthly) > 1 else monthly.iloc[-1]
growth_rate = (
    (latest["active_customers"] - prev["active_customers"]) / prev["active_customers"] * 100
    if prev["active_customers"] else 0
)

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Customers in view", f"{f['name_key'].nunique():,}")
k2.metric("New this month", f"{int(latest['new_customers']):,}")
k3.metric("Active this month", f"{int(latest['active_customers']):,}", f"{growth_rate:+.1f}%")
k4.metric("Kg collected (filtered)", f"{f['total_quantity'].sum():,.0f} kg")
k5.metric("Materials selected", f"{len(materials)}/{len(material_options)}")

st.divider()

# ---------------------------------------------------------------
# Growth trend + goal ring
# ---------------------------------------------------------------
c1, c2 = st.columns([2, 1])

with c1:
    st.subheader("Growth trend")
    tab1, tab2 = st.tabs(["Cumulative growth", "New customers per month"])
    with tab1:
        fig = px.area(monthly, x="month", y="cumulative_customers", markers=True,
                       color_discrete_sequence=[ACCENT])
        fig.update_layout(height=340, margin=dict(l=10, r=10, t=10, b=10),
                           yaxis_title="Cumulative customers", xaxis_title=None)
        st.plotly_chart(fig, use_container_width=True)
    with tab2:
        fig = px.bar(monthly, x="month", y="new_customers", color_discrete_sequence=[ACCENT2])
        fig.update_layout(height=340, margin=dict(l=10, r=10, t=10, b=10),
                           yaxis_title="New customers", xaxis_title=None)
        st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("Progress to 6,000")
    target = 6000
    total_customers = int(tx["name_key"].nunique())  # unfiltered, whole-system total
    pct = min(total_customers / target * 100, 100)
    fig = go.Figure(go.Pie(
        values=[pct, 100 - pct], hole=0.72, sort=False, direction="clockwise",
        marker=dict(colors=[ACCENT, "#EEEEEE"]), textinfo="none",
    ))
    fig.update_layout(
        showlegend=False, height=280, margin=dict(l=10, r=10, t=10, b=10),
        annotations=[dict(text=f"<b>{pct:.0f}%</b><br>{total_customers:,}", x=0.5, y=0.5,
                           font_size=22, showarrow=False)],
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Whole-system customer count vs. a 6,000-customer milestone (unfiltered).")

st.divider()

# ---------------------------------------------------------------
# Segments + Materials
# ---------------------------------------------------------------
st.subheader("Who's recycling, and what")
c3, c4 = st.columns(2)

with c3:
    seg_counts = f.drop_duplicates("name_key")["category"].value_counts().reset_index()
    seg_counts.columns = ["category", "count"]
    fig = px.pie(seg_counts, names="category", values="count", hole=0.45,
                 color_discrete_sequence=PALETTE)
    fig.update_layout(height=360, margin=dict(l=10, r=10, t=30, b=10), title="Customer segments")
    st.plotly_chart(fig, use_container_width=True)

with c4:
    mat_counts = f.groupby("material_group")["total_quantity"].sum().reset_index()
    mat_counts = mat_counts.sort_values("total_quantity", ascending=True)
    fig = px.bar(mat_counts, x="total_quantity", y="material_group", orientation="h",
                 color="material_group", color_discrete_sequence=PALETTE)
    fig.update_layout(height=360, margin=dict(l=10, r=10, t=30, b=10),
                       title="Volume by material type", xaxis_title="Kg", yaxis_title=None,
                       showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ---------------------------------------------------------------
# Segment growth over time
# ---------------------------------------------------------------
st.subheader("Segment growth over time")
top_cats = f.drop_duplicates("name_key")["category"].value_counts().nlargest(5).index.tolist()
seg_growth = (
    f[f["category"].isin(top_cats)]
    .drop_duplicates("name_key")
    .groupby(["join_month", "category"]).size().reset_index(name="new_customers")
)
fig = px.area(seg_growth, x="join_month", y="new_customers", color="category",
              color_discrete_sequence=PALETTE)
fig.update_layout(height=340, margin=dict(l=10, r=10, t=10, b=10), legend_title=None,
                   xaxis_title=None, yaxis_title="New customers")
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ---------------------------------------------------------------
# Geography & acquisition channel (uses region-filtered subset)
# ---------------------------------------------------------------
st.subheader("Where customers come from")
c5, c6 = st.columns(2)

with c5:
    region_counts = f_region.drop_duplicates("name_key")["region"].dropna().value_counts().nlargest(10).reset_index()
    region_counts.columns = ["region", "count"]
    fig = px.bar(region_counts, x="count", y="region", orientation="h",
                 color_discrete_sequence=[ACCENT3])
    fig.update_layout(height=360, margin=dict(l=10, r=10, t=10, b=10),
                       yaxis=dict(autorange="reversed"), xaxis_title="Customers", yaxis_title=None)
    st.plotly_chart(fig, use_container_width=True)

with c6:
    channel_counts = f_region.drop_duplicates("name_key")["acquisition_channel"].dropna().value_counts().nlargest(10).reset_index()
    channel_counts.columns = ["channel", "count"]
    fig = px.bar(channel_counts, x="channel", y="count", color_discrete_sequence=[ACCENT2])
    fig.update_layout(height=360, margin=dict(l=10, r=10, t=10, b=10), xaxis_title=None, yaxis_title="Customers")
    st.plotly_chart(fig, use_container_width=True)

st.caption(
    "Region and acquisition-channel data covers ~27% of customers (matched contact records) "
    "— treat as directional, not complete."
)

st.divider()

# ---------------------------------------------------------------
# Growth vs volume
# ---------------------------------------------------------------
st.subheader("Customer growth vs. collection volume")
fig = go.Figure()
fig.add_trace(go.Bar(x=monthly["month"], y=monthly["active_customers"], name="Active customers",
                      marker_color=ACCENT, yaxis="y1"))
fig.add_trace(go.Scatter(x=monthly["month"], y=monthly["total_kg"], name="Kg collected",
                          line=dict(color=ACCENT3, width=3), yaxis="y2", mode="lines+markers"))
fig.update_layout(
    height=380, margin=dict(l=10, r=10, t=10, b=10),
    yaxis=dict(title="Active customers"),
    yaxis2=dict(title="Kg collected", overlaying="y", side="right"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ---------------------------------------------------------------
# Historical context (separate era, always full — not affected by filters)
# ---------------------------------------------------------------
with st.expander("Historical context: 2022–2025 growth (previous tracking system)", expanded=False):
    st.markdown(
        "Every Bottle Back used a different manual tracking system (the *Simple Count* log) "
        "from April 2022 to June 2025, before switching to the current collection/accounting "
        "system in July 2025. The two systems track customers differently and are **not "
        "directly comparable** — this chart is not affected by the sidebar filters."
    )
    fig = px.line(historical, x="month", y="cumulative_customers",
                  color_discrete_sequence=[ACCENT2])
    fig.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10),
                       yaxis_title="Cumulative customers (legacy system)", xaxis_title=None)
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"Legacy system reached {int(historical['cumulative_customers'].iloc[-1]):,} cumulative customers by June 2025.")

st.divider()
st.caption("Built with Streamlit, Pandas, and Plotly | Every Bottle Back internship project 2026")
