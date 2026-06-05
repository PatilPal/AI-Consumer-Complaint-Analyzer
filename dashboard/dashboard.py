import streamlit as st
import pandas as pd
import plotly.express as px

# Page Settings
st.set_page_config(
    page_title="AI Consumer Complaint Analyzer",
    layout="wide"
)

# Load Data
df = pd.read_csv("data/processed/cluster_output.csv")

# Sidebar
st.sidebar.title("Filters")

selected_cluster = st.sidebar.selectbox(
    "DBSCAN Cluster",
    ["All"] + list(df["DBSCAN_Cluster"].unique())
)

search = st.sidebar.text_input(
    "Search Complaint"
)

# Apply Filters
if selected_cluster != "All":
    filtered_df = df[
        df["DBSCAN_Cluster"] == selected_cluster
    ]
else:
    filtered_df = df

if search:
    filtered_df = filtered_df[
        filtered_df["complaint_text"]
        .str.contains(search, case=False, na=False)
    ]

# Title
st.title("AI Consumer Complaint Analyzer")
st.markdown("### Complaint Clustering Dashboard")

# Metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Complaints", len(filtered_df))

with col2:
    st.metric("Critical Risk", len(filtered_df[filtered_df['Risk Level'] == 'Critical']))

with col3:
    st.metric("DBSCAN Clusters", filtered_df["DBSCAN_Cluster"].nunique())

with col4:
    st.metric("KMeans Clusters", filtered_df["KMeans_Cluster"].nunique())

# Scatter Plot
fig = px.scatter(
    filtered_df,
    x="x",
    y="y",
    color=filtered_df["DBSCAN_Cluster"].astype(str),
    hover_data=[
        "complaint_text",
        "complaint_type",
        "Risk Score",
        "KMeans_Cluster"
    ],
    title="DBSCAN Complaint Clusters"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# Data Table
st.subheader("Complaint Data")

st.dataframe(
    filtered_df,
    use_container_width=True
)

# Pie Chart
st.subheader("DBSCAN Cluster Distribution")

pie_fig = px.pie(
    filtered_df,
    names="DBSCAN_Cluster",
    title="DBSCAN Cluster Distribution"
)

st.plotly_chart(
    pie_fig,
    use_container_width=True
)

# Bar Chart
st.subheader("Complaint Types")

bar_fig = px.bar(
    filtered_df["complaint_type"]
    .value_counts()
    .reset_index(),
    x="complaint_type",
    y="count",
    title="Complaint Type Frequency"
)

st.plotly_chart(
    bar_fig,
    use_container_width=True
)

# Show Sample Records
st.subheader("Sample Complaints")

st.dataframe(
    filtered_df[
        [
            "complaint_text",
            "complaint_type",
            "Risk Score",
            "DBSCAN_Cluster",
            "KMeans_Cluster"
        ]
    ],
    use_container_width=True
)