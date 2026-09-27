from pathlib import Path

import pandas as pd


DATA_PATH = Path("data/wifi_observations.csv")


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
]


def validate_dataset(path: Path) -> bool:
    print("WiSense Dataset Validation")
    print("=" * 30)

    if not path.exists():
        print(f"FAIL: Dataset not found: {path}")
        return False

    df = pd.read_csv(path)

    errors = []

    # -----------------------------------------------------
    # Structure
    # -----------------------------------------------------

    if list(df.columns) != REQUIRED_COLUMNS:
        errors.append("Column structure does not match the expected schema.")

    if len(df) != 1000:
        errors.append(f"Expected 1000 rows, found {len(df)}.")

    # -----------------------------------------------------
    # Missing values
    # -----------------------------------------------------

    missing_total = int(df.isna().sum().sum())

    if missing_total > 0:
        errors.append(f"Dataset contains {missing_total} missing values.")

    # -----------------------------------------------------
    # Duplicate records
    # -----------------------------------------------------

    duplicate_rows = int(df.duplicated().sum())

    if duplicate_rows > 0:
        errors.append(f"Dataset contains {duplicate_rows} duplicate rows.")

    duplicate_ids = int(df["observation_id"].duplicated().sum())

    if duplicate_ids > 0:
        errors.append(
            f"Dataset contains {duplicate_ids} duplicate observation IDs."
        )

    # -----------------------------------------------------
    # Observation IDs
    # -----------------------------------------------------

    expected_ids = set(range(1, len(df) + 1))
    actual_ids = set(df["observation_id"])

    if actual_ids != expected_ids:
        errors.append("Observation IDs are not a complete sequence from 1 to N.")

    # -----------------------------------------------------
    # Network names
    # -----------------------------------------------------

    valid_networks = {
        "Network_A",
        "Network_B",
        "Network_C",
        "Network_D",
    }

    invalid_networks = set(df["network_name"]) - valid_networks

    if invalid_networks:
        errors.append(
            f"Unexpected network names found: {sorted(invalid_networks)}"
        )

    # -----------------------------------------------------
    # Numeric ranges
    # -----------------------------------------------------

    range_checks = {
        "rssi_dbm": (-100, -20),
        "signal_std_dbm": (0, 20),
        "distance_to_ap_m": (0, 100),
        "connected_devices": (1, 100),
        "avg_download_mbps": (0, 1000),
        "peak_usage_hours": (0, 24),
        "frequency_mhz": (2000, 7000),
        "latitude": (-90, 90),
        "longitude": (-180, 180),
    }

    for column, (minimum, maximum) in range_checks.items():
        invalid = df[
            (df[column] < minimum) |
            (df[column] > maximum)
        ]

        if not invalid.empty:
            errors.append(
                f"{column}: {len(invalid)} values outside "
                f"the valid range [{minimum}, {maximum}]."
            )

    # -----------------------------------------------------
    # Timestamp validation
    # -----------------------------------------------------

    timestamps = pd.to_datetime(
        df["timestamp"],
        errors="coerce",
    )

    invalid_timestamps = int(timestamps.isna().sum())

    if invalid_timestamps > 0:
        errors.append(
            f"timestamp: {invalid_timestamps} invalid datetime values."
        )

    # -----------------------------------------------------
    # Report
    # -----------------------------------------------------

    print(f"Rows checked: {len(df)}")
    print(f"Columns checked: {len(df.columns)}")
    print(f"Missing values: {missing_total}")
    print(f"Duplicate rows: {duplicate_rows}")
    print(f"Duplicate observation IDs: {duplicate_ids}")
    print(f"Invalid timestamps: {invalid_timestamps}")

    print()

    if errors:
        print("VALIDATION FAILED")
        print("-" * 30)

        for error in errors:
            print(f"- {error}")

        return False

    print("VALIDATION PASSED")
    print("-" * 30)
    print("Dataset structure and basic value constraints are valid.")

    return True


if __name__ == "__main__":
    success = validate_dataset(DATA_PATH)

    if not success:
        raise SystemExit(1)