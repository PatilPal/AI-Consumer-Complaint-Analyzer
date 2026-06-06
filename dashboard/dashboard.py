import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ─── Page Settings ────────────────────────────────────────────
st.set_page_config(
    page_title="AI Consumer Complaint Analyzer",
    layout="wide"
)

# ─── Load Data ────────────────────────────────────────────────
@st.cache_data
def load_data():
    return pd.read_csv("data/processed/cluster_output.csv")

df = load_data()

# ─── Sidebar Filters ──────────────────────────────────────────
st.sidebar.title("Filters")

selected_cluster = st.sidebar.selectbox(
    "DBSCAN Cluster",
    ["All"] + sorted(df["DBSCAN_Cluster"].unique().tolist())
)

selected_risk = st.sidebar.multiselect(
    "Risk Level",
    options=["Critical", "High", "Medium", "Low"],
    default=["Critical", "High", "Medium", "Low"]
)

search = st.sidebar.text_input("Search Complaint")

# ─── Apply Filters ────────────────────────────────────────────
filtered_df = df.copy()

if selected_cluster != "All":
    filtered_df = filtered_df[filtered_df["DBSCAN_Cluster"] == selected_cluster]

if selected_risk:
    filtered_df = filtered_df[filtered_df["Risk Level"].isin(selected_risk)]

if search:
    filtered_df = filtered_df[
        filtered_df["complaint_text"].str.contains(search, case=False, na=False)
    ]

# ─── Title ────────────────────────────────────────────────────
st.title("AI Consumer Complaint Analyzer")
st.markdown("### Complaint Intelligence Dashboard")

# ─── Metrics with delta arrows ────────────────────────────────
total_all      = len(df)
total_filtered = len(filtered_df)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Complaints",
        total_filtered,
        delta=f"{total_filtered - total_all} vs full dataset" if selected_cluster != "All" or search else None
    )

with col2:
    critical_count = len(filtered_df[filtered_df["Risk Level"] == "Critical"])
    total_critical = len(df[df["Risk Level"] == "Critical"])
    st.metric(
        "Critical Risk",
        critical_count,
        delta=f"{critical_count - total_critical}" if critical_count != total_critical else None,
        delta_color="inverse"
    )

with col3:
    st.metric("DBSCAN Clusters", filtered_df["DBSCAN_Cluster"].nunique())

with col4:
    avg_score = round(filtered_df["Risk Score"].mean(), 1) if len(filtered_df) else 0
    st.metric("Avg Risk Score", avg_score)

st.divider()

# ─── Row 1: Scatter + Risk Level Donut ───────────────────────
col_scatter, col_donut = st.columns([2, 1])

with col_scatter:
    fig_scatter = px.scatter(
        filtered_df,
        x="x",
        y="y",
        color=filtered_df["DBSCAN_Cluster"].astype(str),
        hover_data=["complaint_text", "complaint_type", "Risk Score", "KMeans_Cluster"],
        title="DBSCAN Complaint Clusters"
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

with col_donut:
    risk_counts = (
        filtered_df["Risk Level"]
        .value_counts()
        .reindex(["Critical", "High", "Medium", "Low"], fill_value=0)
        .reset_index()
    )
    risk_counts.columns = ["Risk Level", "count"]

    fig_donut = px.pie(
        risk_counts,
        names="Risk Level",
        values="count",
        hole=0.5,
        color="Risk Level",
        color_discrete_map={
            "Critical": "#c0392b",
            "High":     "#e67e22",
            "Medium":   "#f1c40f",
            "Low":      "#27ae60"
        },
        title="Risk Level Distribution"
    )
    fig_donut.update_traces(textposition="inside", textinfo="percent+label")
    st.plotly_chart(fig_donut, use_container_width=True)

# ─── Row 2: Root Cause Bar + Escalation Score Histogram ───────
col_rc, col_hist = st.columns(2)

with col_rc:
    rc_counts = (
        filtered_df["Root Cause"]
        .value_counts()
        .reset_index()
    )
    rc_counts.columns = ["Root Cause", "count"]

    fig_rc = px.bar(
        rc_counts,
        x="count",
        y="Root Cause",
        orientation="h",
        color="count",
        color_continuous_scale="Reds",
        title="Root Cause Frequency"
    )
    fig_rc.update_layout(yaxis={"categoryorder": "total ascending"}, coloraxis_showscale=False)
    st.plotly_chart(fig_rc, use_container_width=True)

with col_hist:
    fig_hist = px.histogram(
        filtered_df,
        x="Risk Score",
        nbins=20,
        color_discrete_sequence=["#e74c3c"],
        title="Escalation Risk Score Distribution"
    )
    fig_hist.update_layout(bargap=0.05)
    st.plotly_chart(fig_hist, use_container_width=True)

# ─── Row 3: Complaint Type Bar + DBSCAN Pie ───────────────────
col_type, col_pie = st.columns(2)

with col_type:
    type_counts = filtered_df["complaint_type"].value_counts().reset_index()
    type_counts.columns = ["complaint_type", "count"]

    fig_bar = px.bar(
        type_counts,
        x="complaint_type",
        y="count",
        color="complaint_type",
        title="Complaint Type Frequency"
    )
    fig_bar.update_layout(showlegend=False)
    st.plotly_chart(fig_bar, use_container_width=True)

with col_pie:
    fig_pie = px.pie(
        filtered_df,
        names="DBSCAN_Cluster",
        title="DBSCAN Cluster Distribution"
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# ─── Data Table ───────────────────────────────────────────────
st.subheader("Complaint Data")
st.dataframe(
    filtered_df[[
        "complaint_text", "complaint_type", "Risk Score",
        "Risk Level", "Root Cause", "DBSCAN_Cluster", "KMeans_Cluster"
    ]],
    use_container_width=True
)
