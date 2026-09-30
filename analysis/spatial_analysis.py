from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# WISENSE — SPATIAL WIFI ANALYSIS
# PHASE 8
# ============================================================

ROOT_DIR = Path(__file__).resolve().parents[1]

DATA_PATH = ROOT_DIR / "data" / "wifi_clustered.csv"


# ============================================================
# LOAD DATA
# ============================================================

if not DATA_PATH.exists():
    raise FileNotFoundError(
        f"Dataset not found: {DATA_PATH}"
    )


df = pd.read_csv(DATA_PATH)


REQUIRED_COLUMNS = [
    "observation_id",
    "network_name",
    "rssi_dbm",
    "avg_download_mbps",
    "connected_devices",
    "frequency_mhz",
    "latitude",
    "longitude",
    "cluster",
]


missing_columns = [
    column
    for column in REQUIRED_COLUMNS
    if column not in df.columns
]


if missing_columns:
    raise ValueError(
        "Missing required columns: "
        + ", ".join(missing_columns)
    )


# ============================================================
# HELPERS
# ============================================================

def section(title: str):

    print()
    print("=" * 64)
    print(title)
    print("=" * 64)


# ============================================================
# HEADER
# ============================================================

section(
    "WISENSE — SPATIAL WIFI ANALYSIS"
)


print(
    f"Observations : {len(df)}"
)

print(
    f"Networks     : {df['network_name'].nunique()}"
)

print(
    f"Latitude     : "
    f"{df['latitude'].min():.6f} "
    f"to "
    f"{df['latitude'].max():.6f}"
)

print(
    f"Longitude    : "
    f"{df['longitude'].min():.6f} "
    f"to "
    f"{df['longitude'].max():.6f}"
)


# ============================================================
# 1. NETWORK LOCATION SUMMARY
# ============================================================

section(
    "[1] NETWORK LOCATION SUMMARY"
)


network_locations = (
    df.groupby("network_name")
    .agg(
        observations=(
            "network_name",
            "size",
        ),

        latitude=(
            "latitude",
            "mean",
        ),

        longitude=(
            "longitude",
            "mean",
        ),

        avg_rssi=(
            "rssi_dbm",
            "mean",
        ),

        avg_speed=(
            "avg_download_mbps",
            "mean",
        ),

        avg_devices=(
            "connected_devices",
            "mean",
        ),

        frequency=(
            "frequency_mhz",
            "first",
        ),

        dominant_cluster=(
            "cluster",
            lambda values: values.mode().iloc[0],
        ),
    )
    .reset_index()
)


print(
    network_locations.round(4).to_string(
        index=False
    )
)


# ============================================================
# 2. SPATIAL EXTENT
# ============================================================

section(
    "[2] SPATIAL EXTENT"
)


latitude_range = (
    df["latitude"].max()
    - df["latitude"].min()
)


longitude_range = (
    df["longitude"].max()
    - df["longitude"].min()
)


print(
    f"Latitude range  : "
    f"{latitude_range:.6f} degrees"
)

print(
    f"Longitude range : "
    f"{longitude_range:.6f} degrees"
)


# Approximate conversion.
# One degree of latitude is approximately 111 km.
# Longitude conversion depends on latitude.

mean_latitude = (
    df["latitude"].mean()
)


latitude_km = (
    latitude_range * 111.0
)


longitude_km = (
    longitude_range
    * 111.0
    * np.cos(
        np.radians(mean_latitude)
    )
)


print(
    f"Approx. north-south extent : "
    f"{latitude_km:.3f} km"
)

print(
    f"Approx. east-west extent   : "
    f"{longitude_km:.3f} km"
)


# ============================================================
# 3. NETWORK SPATIAL CENTERS
# ============================================================

section(
    "[3] NETWORK SPATIAL CENTERS"
)


for _, row in network_locations.iterrows():

    print(
        f"{row['network_name']}: "
        f"lat={row['latitude']:.6f}, "
        f"lon={row['longitude']:.6f}"
    )


# ============================================================
# 4. SPATIAL PERFORMANCE
# ============================================================

section(
    "[4] SPATIAL PERFORMANCE"
)


spatial_performance = (
    df.groupby("network_name")
    .agg(
        avg_speed=(
            "avg_download_mbps",
            "mean",
        ),

        avg_rssi=(
            "rssi_dbm",
            "mean",
        ),

        avg_devices=(
            "connected_devices",
            "mean",
        ),

        latitude=(
            "latitude",
            "mean",
        ),

        longitude=(
            "longitude",
            "mean",
        ),
    )
    .reset_index()
)


print(
    spatial_performance.round(2).to_string(
        index=False
    )
)


# ============================================================
# 5. CLUSTER LOCATION SUMMARY
# ============================================================

section(
    "[5] CLUSTER LOCATION SUMMARY"
)


cluster_locations = (
    df.groupby("cluster")
    .agg(
        observations=(
            "cluster",
            "size",
        ),

        latitude=(
            "latitude",
            "mean",
        ),

        longitude=(
            "longitude",
            "mean",
        ),

        avg_rssi=(
            "rssi_dbm",
            "mean",
        ),

        avg_speed=(
            "avg_download_mbps",
            "mean",
        ),

        avg_devices=(
            "connected_devices",
            "mean",
        ),
    )
    .reset_index()
)


print(
    cluster_locations.round(2).to_string(
        index=False
    )
)


# ============================================================
# 6. SPATIAL DATA QUALITY
# ============================================================

section(
    "[6] SPATIAL DATA QUALITY"
)


print(
    f"Missing latitude  : "
    f"{df['latitude'].isna().sum()}"
)

print(
    f"Missing longitude : "
    f"{df['longitude'].isna().sum()}"
)

print(
    f"Unique coordinates: "
    f"{df[['latitude', 'longitude']].drop_duplicates().shape[0]}"
)


# ============================================================
# 7. MAP-READY DATA
# ============================================================

section(
    "[7] MAP-READY DATA"
)


map_columns = [
    "observation_id",
    "network_name",
    "latitude",
    "longitude",
    "rssi_dbm",
    "avg_download_mbps",
    "connected_devices",
    "frequency_mhz",
    "cluster",
]


map_data = (
    df[map_columns]
    .copy()
)


print(
    f"Map points available: "
    f"{len(map_data)}"
)


print()

print(
    map_data.head(10).round(4).to_string(
        index=False
    )
)


# ============================================================
# 8. COMPLETE
# ============================================================

section(
    "SPATIAL ANALYSIS COMPLETE"
)