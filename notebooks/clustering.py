import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.cluster import DBSCAN, KMeans

# Load complaint data
complaints_df = pd.read_csv("cleaned_complaints (1).csv")

# Load embeddings
embeddings_df = pd.read_csv("complaint_embeddings.csv")

# Convert embeddings to numpy array
X = embeddings_df.values

# PCA (384 -> 2 dimensions)
pca = PCA(n_components=2, random_state=42)
reduced = pca.fit_transform(X)

# DBSCAN Clustering
dbscan = DBSCAN(
    eps=1.5,
    min_samples=5
)

dbscan_clusters = dbscan.fit_predict(reduced)

# K-Means Clustering
kmeans = KMeans(
    n_clusters=5,
    random_state=42,
    n_init=10
)

kmeans_clusters = kmeans.fit_predict(reduced)

# Create final dataframe
final_df = complaints_df.copy()

final_df["x"] = reduced[:, 0]
final_df["y"] = reduced[:, 1]

final_df["DBSCAN_Cluster"] = dbscan_clusters
final_df["KMeans_Cluster"] = kmeans_clusters

# Risk Score
final_df["Risk Score"] = (
    final_df["anger_score"] * 50
    + final_df["days_pending"] * 2
    + final_df["repeat_count"] * 5
).astype(int)

# Save output
final_df.to_csv(
    "cluster_output.csv",
    index=False
)

print("\nCluster Output Created Successfully\n")
print(final_df.head())
print("\nShape:", final_df.shape)
