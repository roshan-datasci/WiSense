import pandas as pd


DATA_PATH = "data/wifi_observations.csv"


df = pd.read_csv(DATA_PATH)


print("WiSense Wi-Fi Consistency Check")
print("=" * 35)


# ---------------------------------------------------------
# Network distribution
# ---------------------------------------------------------

print("\nNetwork distribution:")
print(df["network_name"].value_counts().sort_index())


# ---------------------------------------------------------
# Frequency consistency
# ---------------------------------------------------------

print("\nFrequency by network:")

frequency_check = (
    df.groupby("network_name")["frequency_mhz"]
    .agg(["min", "max", "nunique"])
)

print(frequency_check)


# ---------------------------------------------------------
# Signal statistics
# ---------------------------------------------------------

print("\nSignal statistics:")
print(
    df["rssi_dbm"].describe()[
        ["min", "mean", "max"]
    ]
)


# ---------------------------------------------------------
# Speed statistics
# ---------------------------------------------------------

print("\nDownload speed statistics:")
print(
    df["avg_download_mbps"].describe()[
        ["min", "mean", "max"]
    ]
)


# ---------------------------------------------------------
# Connected devices
# ---------------------------------------------------------

print("\nConnected devices:")
print(
    df["connected_devices"].describe()[
        ["min", "mean", "max"]
    ]
)


# ---------------------------------------------------------
# Timestamp range
# ---------------------------------------------------------

timestamps = pd.to_datetime(df["timestamp"])

print("\nTimestamp range:")
print("Start:", timestamps.min())
print("End:  ", timestamps.max())


# ---------------------------------------------------------
# Final result
# ---------------------------------------------------------

print("\nWi-Fi consistency check completed.")