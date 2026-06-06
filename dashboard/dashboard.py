import requests
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

@st.cache_data(ttl=5)
def load_data():
    try:
        response = requests.get("http://127.0.0.1:8000/complaints")
        data = response.json()
        if isinstance(data, list) and len(data) > 0:
            return pd.DataFrame(data)
        else:
            return pd.read_csv(r"C:\Projects\AI-Consumer-Complaint-Analyzer\data\processed\cluster_output.csv")
    except:
        return pd.read_csv(r"C:\Projects\AI-Consumer-Complaint-Analyzer\data\processed\cluster_output.csv")

df = load_data()

# ─── Sidebar Filters ──────────────────────────────────────────


st.sidebar.title("Filters")

selected_cluster = st.sidebar.selectbox(
    "DBSCAN Cluster",
    ["All"] + sorted(df["complaint_type"].unique().tolist())
)

selected_risk = st.sidebar.multiselect(
    "risk_level",
    options=["Critical", "High", "Medium", "Low"],
    default=["Critical", "High", "Medium", "Low"]
)

search = st.sidebar.text_input("Search Complaint")

# ─── Apply Filters ────────────────────────────────────────────
filtered_df = df.copy()

if selected_cluster != "All":
    filtered_df = filtered_df[filtered_df["complaint_type"] == selected_cluster]

if selected_risk:
    filtered_df = filtered_df[filtered_df["risk_level"].isin(selected_risk)]

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
    critical_count = len(filtered_df[filtered_df["risk_level"] == "Critical"])
    total_critical = len(df[df["risk_level"] == "Critical"])
    st.metric(
        "Critical Risk",
        critical_count,
        delta=f"{critical_count - total_critical}" if critical_count != total_critical else None,
        delta_color="inverse"
    )

with col3:
    st.metric("Complaint Types", filtered_df["complaint_type"].nunique())

with col4:
    avg_score = round(filtered_df["risk_score"].mean(), 1) if len(filtered_df) else 0
    st.metric("Avg Risk Score", avg_score)

st.divider()

# ─── Row 1: Scatter + Risk Level Donut ───────────────────────
col_scatter, col_donut = st.columns([2, 1])

with col_scatter:
    type_counts = filtered_df["complaint_type"].value_counts().reset_index()
    type_counts.columns = ["complaint_type", "count"]
    fig_scatter = px.bar(
        type_counts,
        x="complaint_type",
        y="count",
        color="complaint_type",
        title="Complaints by Type"
    )
    fig_scatter.update_layout(showlegend=False)
    st.plotly_chart(fig_scatter, use_container_width=True)
with col_donut:
    risk_counts = (
        filtered_df["risk_level"]
        .value_counts()
        .reindex(["Critical", "High", "Medium", "Low"], fill_value=0)
        .reset_index()
    )
    risk_counts.columns = ["risk_level", "count"]

    fig_donut = px.pie(
        risk_counts,
        names="risk_level",
        values="count",
        hole=0.5,
        color="risk_level",
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
        filtered_df["root_cause"]
        .value_counts()
        .reset_index()
    )
    rc_counts.columns = ["root_cause", "count"]

    fig_rc = px.bar(
        rc_counts,
        x="count",
        y="root_cause",
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
        x="risk_score",
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
        names="complaint_type",
        title="DBSCAN Cluster Distribution"
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# ─── Data Table ───────────────────────────────────────────────
st.subheader("Complaint Data")
st.dataframe(
    filtered_df[[
        "complaint_text", "complaint_type", "risk_score",
        "risk_level", "root_cause", "timestamp"
    ]],
    use_container_width=True
)
