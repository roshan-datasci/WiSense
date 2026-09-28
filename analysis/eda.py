from pathlib import Path

import pandas as pd


DATA_PATH = Path("data/wifi_observations.csv")


def load_data() -> pd.DataFrame:
    """Load the WiSense Wi-Fi observation dataset."""
    df = pd.read_csv(DATA_PATH)

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    return df


def main() -> None:
    df = load_data()

    print("=" * 60)
    print("WISENSE — EXPLORATORY DATA ANALYSIS")
    print("=" * 60)

    # -----------------------------------------------------
    # Dataset overview
    # -----------------------------------------------------

    print("\n[1] DATASET OVERVIEW")
    print("-" * 40)

    print(f"Observations : {len(df)}")
    print(f"Features     : {len(df.columns)}")
    print(f"Time start   : {df['timestamp'].min()}")
    print(f"Time end     : {df['timestamp'].max()}")

    # -----------------------------------------------------
    # Network distribution
    # -----------------------------------------------------

    print("\n[2] NETWORK DISTRIBUTION")
    print("-" * 40)

    network_counts = (
        df["network_name"]
        .value_counts()
        .sort_index()
    )

    print(network_counts)

    # -----------------------------------------------------
    # Signal analysis
    # -----------------------------------------------------

    print("\n[3] SIGNAL ANALYSIS")
    print("-" * 40)

    signal_summary = df["rssi_dbm"].describe()

    print(signal_summary)

    # -----------------------------------------------------
    # Download speed analysis
    # -----------------------------------------------------

    print("\n[4] DOWNLOAD SPEED ANALYSIS")
    print("-" * 40)

    speed_summary = df["avg_download_mbps"].describe()

    print(speed_summary)

    # -----------------------------------------------------
    # Connected devices
    # -----------------------------------------------------

    print("\n[5] CONNECTED DEVICES")
    print("-" * 40)

    device_summary = df["connected_devices"].describe()

    print(device_summary)

    # -----------------------------------------------------
    # Network-level summary
    # -----------------------------------------------------

    print("\n[6] NETWORK-LEVEL SUMMARY")
    print("-" * 40)

    network_summary = (
        df.groupby("network_name")
        .agg(
            observations=("observation_id", "count"),
            avg_signal_dbm=("rssi_dbm", "mean"),
            avg_speed_mbps=("avg_download_mbps", "mean"),
            avg_devices=("connected_devices", "mean"),
            avg_distance_m=("distance_to_ap_m", "mean"),
        )
        .round(2)
    )

    print(network_summary)

    # -----------------------------------------------------
    # Correlation analysis
    # -----------------------------------------------------

    print("\n[7] CORRELATION WITH DOWNLOAD SPEED")
    print("-" * 40)

    numeric_columns = [
        "rssi_dbm",
        "signal_std_dbm",
        "distance_to_ap_m",
        "connected_devices",
        "avg_download_mbps",
        "peak_usage_hours",
        "frequency_mhz",
    ]

    speed_correlations = (
        df[numeric_columns]
        .corr()["avg_download_mbps"]
        .sort_values(ascending=False)
    )

    print(speed_correlations.round(3))

    # -----------------------------------------------------
    # Overall correlation matrix
    # -----------------------------------------------------

    print("\n[8] CORRELATION MATRIX")
    print("-" * 40)

    correlation_matrix = (
        df[numeric_columns]
        .corr()
        .round(3)
    )

    print(correlation_matrix)

    # -----------------------------------------------------
    # Frequency / band distribution
    # -----------------------------------------------------

    print("\n[9] FREQUENCY DISTRIBUTION")
    print("-" * 40)

    frequency_counts = (
        df["frequency_mhz"]
        .value_counts()
        .sort_index()
    )

    print(frequency_counts)

    # -----------------------------------------------------
    # Peak usage analysis
    # -----------------------------------------------------

    print("\n[10] PEAK USAGE")
    print("-" * 40)

    print(
        df["peak_usage_hours"]
        .describe()
        .round(2)
    )

    print("\n" + "=" * 60)
    print("EDA COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()