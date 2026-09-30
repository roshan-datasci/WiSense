from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# WISENSE — ADVANCED WIFI ANALYTICS
# PHASE 7
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
    "signal_std_dbm",
    "distance_to_ap_m",
    "connected_devices",
    "avg_download_mbps",
    "peak_usage_hours",
    "frequency_mhz",
    "latitude",
    "longitude",
    "timestamp",
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
# TIMESTAMP
# ============================================================

df["timestamp"] = pd.to_datetime(
    df["timestamp"],
    errors="coerce",
)


if df["timestamp"].isna().any():
    raise ValueError(
        "Invalid timestamps detected."
    )


df = (
    df.sort_values("timestamp")
    .reset_index(drop=True)
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
    "WISENSE — ADVANCED WIFI ANALYTICS"
)

print(
    f"Observations : {len(df)}"
)

print(
    f"Networks     : {df['network_name'].nunique()}"
)

print(
    f"Time start   : {df['timestamp'].min()}"
)

print(
    f"Time end     : {df['timestamp'].max()}"
)


# ============================================================
# 1. OVERALL PERFORMANCE
# ============================================================

section(
    "[1] OVERALL PERFORMANCE"
)


print(
    f"Average speed      : "
    f"{df['avg_download_mbps'].mean():.2f} Mbps"
)

print(
    f"Median speed       : "
    f"{df['avg_download_mbps'].median():.2f} Mbps"
)

print(
    f"Speed std          : "
    f"{df['avg_download_mbps'].std():.2f} Mbps"
)

print(
    f"Minimum speed      : "
    f"{df['avg_download_mbps'].min():.2f} Mbps"
)

print(
    f"Maximum speed      : "
    f"{df['avg_download_mbps'].max():.2f} Mbps"
)

print(
    f"Average RSSI       : "
    f"{df['rssi_dbm'].mean():.2f} dBm"
)

print(
    f"Average devices    : "
    f"{df['connected_devices'].mean():.2f}"
)

print(
    f"Average distance   : "
    f"{df['distance_to_ap_m'].mean():.2f} m"
)


# ============================================================
# 2. NETWORK PERFORMANCE
# ============================================================

section(
    "[2] NETWORK PERFORMANCE"
)


network_performance = (
    df.groupby("network_name")
    .agg(
        observations=(
            "network_name",
            "size",
        ),
        avg_speed=(
            "avg_download_mbps",
            "mean",
        ),
        median_speed=(
            "avg_download_mbps",
            "median",
        ),
        speed_std=(
            "avg_download_mbps",
            "std",
        ),
        avg_rssi=(
            "rssi_dbm",
            "mean",
        ),
        avg_signal_std=(
            "signal_std_dbm",
            "mean",
        ),
        avg_devices=(
            "connected_devices",
            "mean",
        ),
        avg_distance=(
            "distance_to_ap_m",
            "mean",
        ),
    )
    .reset_index()
)


print(
    network_performance.round(2).to_string(
        index=False
    )
)


# ============================================================
# 3. CORRELATION ANALYSIS
# ============================================================

section(
    "[3] PERFORMANCE CORRELATIONS"
)


correlation_columns = [
    "rssi_dbm",
    "signal_std_dbm",
    "distance_to_ap_m",
    "connected_devices",
    "peak_usage_hours",
    "frequency_mhz",
    "avg_download_mbps",
]


correlation_matrix = (
    df[correlation_columns]
    .corr()
)


speed_correlations = (
    correlation_matrix["avg_download_mbps"]
    .drop("avg_download_mbps")
    .sort_values(
        ascending=False
    )
)


print(
    "Correlation with download speed:"
)

print()

print(
    speed_correlations.round(3).to_string()
)


# ============================================================
# 4. SIGNAL ANALYSIS
# ============================================================

section(
    "[4] SIGNAL ANALYSIS"
)


signal_bins = pd.cut(
    df["rssi_dbm"],
    bins=[
        -100,
        -70,
        -60,
        -50,
        -40,
        0,
    ],
    labels=[
        "Very Weak",
        "Weak",
        "Good",
        "Strong",
        "Very Strong",
    ],
)


signal_performance = (
    df.assign(
        signal_category=signal_bins
    )
    .groupby(
        "signal_category",
        observed=False,
    )
    .agg(
        observations=(
            "avg_download_mbps",
            "size",
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
    signal_performance.round(2).to_string(
        index=False
    )
)


# ============================================================
# 5. DISTANCE ANALYSIS
# ============================================================

section(
    "[5] DISTANCE ANALYSIS"
)


distance_bins = pd.cut(
    df["distance_to_ap_m"],
    bins=[
        0,
        10,
        20,
        30,
        40,
        50,
        np.inf,
    ],
    labels=[
        "0-10 m",
        "10-20 m",
        "20-30 m",
        "30-40 m",
        "40-50 m",
        "50+ m",
    ],
)


distance_performance = (
    df.assign(
        distance_category=distance_bins
    )
    .groupby(
        "distance_category",
        observed=False,
    )
    .agg(
        observations=(
            "avg_download_mbps",
            "size",
        ),
        avg_speed=(
            "avg_download_mbps",
            "mean",
        ),
        avg_rssi=(
            "rssi_dbm",
            "mean",
        ),
    )
    .reset_index()
)


print(
    distance_performance.round(2).to_string(
        index=False
    )
)


# ============================================================
# 6. DEVICE CONGESTION
# ============================================================

section(
    "[6] DEVICE CONGESTION ANALYSIS"
)


device_bins = pd.cut(
    df["connected_devices"],
    bins=[
        0,
        3,
        6,
        9,
        12,
        15,
        np.inf,
    ],
    labels=[
        "1-3",
        "4-6",
        "7-9",
        "10-12",
        "13-15",
        "16+",
    ],
)


congestion_performance = (
    df.assign(
        device_category=device_bins
    )
    .groupby(
        "device_category",
        observed=False,
    )
    .agg(
        observations=(
            "avg_download_mbps",
            "size",
        ),
        avg_speed=(
            "avg_download_mbps",
            "mean",
        ),
        avg_rssi=(
            "rssi_dbm",
            "mean",
        ),
    )
    .reset_index()
)


print(
    congestion_performance.round(2).to_string(
        index=False
    )
)


# ============================================================
# 7. HOURLY PERFORMANCE
# ============================================================

section(
    "[7] HOURLY PERFORMANCE"
)


df["hour"] = (
    df["timestamp"]
    .dt.hour
)


hourly_performance = (
    df.groupby("hour")
    .agg(
        observations=(
            "avg_download_mbps",
            "size",
        ),
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
    )
    .reset_index()
)


print(
    hourly_performance.round(2).to_string(
        index=False
    )
)


# ============================================================
# 8. PEAK PERIOD ANALYSIS
# ============================================================

section(
    "[8] PEAK PERIOD ANALYSIS"
)


peak_threshold = (
    df["peak_usage_hours"]
    .median()
)


df["peak_period"] = np.where(
    df["peak_usage_hours"]
    >= peak_threshold,
    "High Usage Period",
    "Lower Usage Period",
)


peak_performance = (
    df.groupby("peak_period")
    .agg(
        observations=(
            "avg_download_mbps",
            "size",
        ),
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
    )
    .reset_index()
)


print(
    f"Peak threshold : "
    f"{peak_threshold:.2f}"
)

print()

print(
    peak_performance.round(2).to_string(
        index=False
    )
)


# ============================================================
# 9. ROLLING PERFORMANCE
# ============================================================

section(
    "[9] ROLLING PERFORMANCE"
)


ROLLING_WINDOW = 12


df["rolling_speed"] = (
    df["avg_download_mbps"]
    .rolling(
        window=ROLLING_WINDOW,
        min_periods=1,
    )
    .mean()
)


df["rolling_rssi"] = (
    df["rssi_dbm"]
    .rolling(
        window=ROLLING_WINDOW,
        min_periods=1,
    )
    .mean()
)


df["rolling_devices"] = (
    df["connected_devices"]
    .rolling(
        window=ROLLING_WINDOW,
        min_periods=1,
    )
    .mean()
)


print(
    f"Rolling window : "
    f"{ROLLING_WINDOW} observations"
)

print()

print(
    f"Latest rolling speed : "
    f"{df['rolling_speed'].iloc[-1]:.2f} Mbps"
)

print(
    f"Latest rolling RSSI  : "
    f"{df['rolling_rssi'].iloc[-1]:.2f} dBm"
)

print(
    f"Latest rolling devices : "
    f"{df['rolling_devices'].iloc[-1]:.2f}"
)


# ============================================================
# 10. PERFORMANCE EXTREMES
# ============================================================

section(
    "[10] PERFORMANCE EXTREMES"
)


best_observation = df.loc[
    df["avg_download_mbps"].idxmax()
]


worst_observation = df.loc[
    df["avg_download_mbps"].idxmin()
]


print(
    "Highest observed speed:"
)

print(
    f"Network : "
    f"{best_observation['network_name']}"
)

print(
    f"Speed   : "
    f"{best_observation['avg_download_mbps']:.2f} Mbps"
)

print(
    f"RSSI    : "
    f"{best_observation['rssi_dbm']:.2f} dBm"
)

print()

print(
    "Lowest observed speed:"
)

print(
    f"Network : "
    f"{worst_observation['network_name']}"
)

print(
    f"Speed   : "
    f"{worst_observation['avg_download_mbps']:.2f} Mbps"
)

print(
    f"RSSI    : "
    f"{worst_observation['rssi_dbm']:.2f} dBm"
)


# ============================================================
# 11. DATA QUALITY
# ============================================================

section(
    "[11] ANALYTICS DATA QUALITY"
)


print(
    f"Missing values   : "
    f"{df.isna().sum().sum()}"
)

print(
    f"Duplicate rows   : "
    f"{df.duplicated().sum()}"
)

print(
    f"Unique timestamps: "
    f"{df['timestamp'].nunique()}"
)

print(
    f"Unique networks  : "
    f"{df['network_name'].nunique()}"
)


# ============================================================
# COMPLETE
# ============================================================

section(
    "ADVANCED ANALYTICS COMPLETE"
)