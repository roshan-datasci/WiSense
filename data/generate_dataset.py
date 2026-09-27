import numpy as np
import pandas as pd


RANDOM_SEED = 42
N_OBSERVATIONS = 1000

rng = np.random.default_rng(RANDOM_SEED)


# ---------------------------------------------------------
# Network definitions
# ---------------------------------------------------------

networks = {
    "Network_A": {
        "frequency_mhz": 5180,
        "latitude": 9.9252,
        "longitude": 78.1198,
    },
    "Network_B": {
        "frequency_mhz": 2437,
        "latitude": 9.9258,
        "longitude": 78.1204,
    },
    "Network_C": {
        "frequency_mhz": 5200,
        "latitude": 9.9247,
        "longitude": 78.1192,
    },
    "Network_D": {
        "frequency_mhz": 2462,
        "latitude": 9.9261,
        "longitude": 78.1208,
    },
}


network_names = rng.choice(
    list(networks.keys()),
    size=N_OBSERVATIONS,
    p=[0.267, 0.236, 0.238, 0.259],
)


# ---------------------------------------------------------
# Basic network information
# ---------------------------------------------------------

frequency_mhz = np.array(
    [networks[name]["frequency_mhz"] for name in network_names]
)

base_latitude = np.array(
    [networks[name]["latitude"] for name in network_names]
)

base_longitude = np.array(
    [networks[name]["longitude"] for name in network_names]
)


# ---------------------------------------------------------
# Network conditions
# ---------------------------------------------------------

distance_to_ap_m = np.clip(
    rng.gamma(shape=2.2, scale=7.0, size=N_OBSERVATIONS) + 3,
    3,
    50,
)


connected_devices = np.clip(
    rng.poisson(lam=5, size=N_OBSERVATIONS) + 1,
    1,
    15,
)


peak_usage_hours = rng.uniform(
    8,
    23,
    size=N_OBSERVATIONS,
)


# Signal strength becomes weaker with distance.
rssi_dbm = (
    -40
    - 0.65 * distance_to_ap_m
    - 0.9 * connected_devices
    + rng.normal(0, 4, N_OBSERVATIONS)
)

rssi_dbm = np.clip(
    rssi_dbm,
    -90,
    -35,
)


# Signal variability.
signal_std_dbm = (
    1.5
    + 0.18 * connected_devices
    + 0.025 * distance_to_ap_m
    + rng.normal(0, 0.8, N_OBSERVATIONS)
)

signal_std_dbm = np.clip(
    signal_std_dbm,
    0.5,
    8.0,
)


# ---------------------------------------------------------
# Download speed
# ---------------------------------------------------------

# Speed is influenced by:
# - stronger signal
# - shorter distance
# - fewer connected devices
# - lower peak usage

avg_download_mbps = (
    105
    + 0.95 * (rssi_dbm + 50)
    - 0.75 * distance_to_ap_m
    - 2.7 * connected_devices
    - 2.0 * np.maximum(peak_usage_hours - 17, 0)
    + rng.normal(0, 8, N_OBSERVATIONS)
)

avg_download_mbps = np.clip(
    avg_download_mbps,
    5,
    150,
)


# ---------------------------------------------------------
# Geographic variation
# ---------------------------------------------------------

latitude = base_latitude + rng.normal(
    0,
    0.0008,
    N_OBSERVATIONS,
)

longitude = base_longitude + rng.normal(
    0,
    0.0008,
    N_OBSERVATIONS,
)


# ---------------------------------------------------------
# Timestamp
# ---------------------------------------------------------

timestamps = pd.date_range(
    start="2025-01-01 08:00:00",
    periods=N_OBSERVATIONS,
    freq="5min",
)


# ---------------------------------------------------------
# Build dataframe
# ---------------------------------------------------------

df = pd.DataFrame(
    {
        "observation_id": np.arange(1, N_OBSERVATIONS + 1),
        "network_name": network_names,
        "rssi_dbm": np.round(rssi_dbm, 2),
        "signal_std_dbm": np.round(signal_std_dbm, 2),
        "distance_to_ap_m": np.round(distance_to_ap_m, 2),
        "connected_devices": connected_devices,
        "avg_download_mbps": np.round(avg_download_mbps, 2),
        "peak_usage_hours": np.round(peak_usage_hours, 2),
        "frequency_mhz": frequency_mhz,
        "latitude": np.round(latitude, 6),
        "longitude": np.round(longitude, 6),
        "timestamp": timestamps,
    }
)


# ---------------------------------------------------------
# Save
# ---------------------------------------------------------

output_path = "data/wifi_observations.csv"

df.to_csv(
    output_path,
    index=False,
)

print(f"Dataset created: {output_path}")
print(f"Rows: {len(df)}")
print(f"Columns: {len(df.columns)}")
print()
print(df.head())