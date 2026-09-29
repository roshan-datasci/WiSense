from pathlib import Path

import pandas as pd


DATA_PATH = Path("data/wifi_clustered.csv")


TASK_PROFILES = {
    "General": {
        "speed": 0.35,
        "signal": 0.25,
        "stability": 0.15,
        "congestion": 0.15,
        "distance": 0.10,
    },
    "Browsing": {
        "speed": 0.25,
        "signal": 0.25,
        "stability": 0.20,
        "congestion": 0.20,
        "distance": 0.10,
    },
    "Video Call": {
        "speed": 0.25,
        "signal": 0.25,
        "stability": 0.25,
        "congestion": 0.20,
        "distance": 0.05,
    },
    "Gaming": {
        "speed": 0.20,
        "signal": 0.25,
        "stability": 0.30,
        "congestion": 0.20,
        "distance": 0.05,
    },
    "Download": {
        "speed": 0.55,
        "signal": 0.20,
        "stability": 0.10,
        "congestion": 0.10,
        "distance": 0.05,
    },
}


REQUIRED_COLUMNS = [
    "network_name",
    "rssi_dbm",
    "signal_std_dbm",
    "distance_to_ap_m",
    "connected_devices",
    "avg_download_mbps",
    "cluster",
]


def load_data() -> pd.DataFrame:
    """Load and validate the clustered Wi-Fi dataset."""

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Clustered dataset not found: {DATA_PATH}"
        )

    df = pd.read_csv(DATA_PATH)

    missing = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    return df


def score_higher_better(
    value: float,
    poor: float,
    excellent: float,
) -> float:
    """Score a metric where larger values are better."""

    if value <= poor:
        return 0.0

    if value >= excellent:
        return 100.0

    score = (value - poor) / (excellent - poor)

    return score * 100.0


def score_lower_better(
    value: float,
    excellent: float,
    poor: float,
) -> float:
    """Score a metric where smaller values are better."""

    if value <= excellent:
        return 100.0

    if value >= poor:
        return 0.0

    score = (poor - value) / (poor - excellent)

    return score * 100.0


def calculate_metric_scores(
    summary: pd.DataFrame,
) -> pd.DataFrame:
    """
    Convert observed Wi-Fi metrics into domain-based 0-100 scores.

    The thresholds are project-defined reference ranges.
    They are not universal Wi-Fi standards.
    """

    result = summary.copy()

    # Download speed:
    # <= 10 Mbps is treated as poor.
    # >= 100 Mbps is treated as excellent.
    result["speed_score"] = result["avg_speed_mbps"].apply(
        lambda value: score_higher_better(
            value,
            poor=10,
            excellent=100,
        )
    )

    # RSSI:
    # <= -85 dBm is treated as poor.
    # >= -45 dBm is treated as excellent.
    result["signal_score"] = result["avg_rssi_dbm"].apply(
        lambda value: score_higher_better(
            value,
            poor=-85,
            excellent=-45,
        )
    )

    # Signal standard deviation:
    # <= 1 dBm is treated as very stable.
    # >= 8 dBm is treated as unstable.
    result["stability_score"] = result[
        "avg_signal_std_dbm"
    ].apply(
        lambda value: score_lower_better(
            value,
            excellent=1,
            poor=8,
        )
    )

    # Connected devices:
    # <= 2 devices is treated as low congestion.
    # >= 15 devices is treated as high congestion.
    result["congestion_score"] = result[
        "avg_devices"
    ].apply(
        lambda value: score_lower_better(
            value,
            excellent=2,
            poor=15,
        )
    )

    # Distance:
    # <= 5 m is treated as excellent.
    # >= 50 m is treated as poor.
    result["distance_score"] = result[
        "avg_distance_m"
    ].apply(
        lambda value: score_lower_better(
            value,
            excellent=5,
            poor=50,
        )
    )

    return result


def build_network_summary(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Aggregate observations into network-level metrics."""

    summary = (
        df.groupby("network_name")
        .agg(
            observations=("network_name", "size"),
            avg_rssi_dbm=("rssi_dbm", "mean"),
            avg_signal_std_dbm=("signal_std_dbm", "mean"),
            avg_distance_m=("distance_to_ap_m", "mean"),
            avg_devices=("connected_devices", "mean"),
            avg_speed_mbps=("avg_download_mbps", "mean"),
            dominant_cluster=(
                "cluster",
                lambda values: values.mode().iloc[0],
            ),
        )
        .reset_index()
    )

    return summary


def calculate_task_scores(
    scored_networks: pd.DataFrame,
    task_name: str,
) -> pd.DataFrame:
    """Calculate task-specific suitability scores."""

    if task_name not in TASK_PROFILES:
        raise ValueError(
            f"Unknown task: {task_name}"
        )

    weights = TASK_PROFILES[task_name]

    result = scored_networks.copy()

    result["suitability_score"] = (
        result["speed_score"] * weights["speed"]
        + result["signal_score"] * weights["signal"]
        + result["stability_score"] * weights["stability"]
        + result["congestion_score"] * weights["congestion"]
        + result["distance_score"] * weights["distance"]
    )

    result["suitability_score"] = (
        result["suitability_score"]
        .clip(0, 100)
        .round(2)
    )

    return result


def classify_suitability(score: float) -> str:
    """Convert a numerical score into a readable category."""

    if score >= 80:
        return "Excellent"

    if score >= 65:
        return "Good"

    if score >= 50:
        return "Moderate"

    return "Limited"


def print_results(
    scored_networks: pd.DataFrame,
    task_name: str,
) -> None:
    """Display recommendation results."""

    results = scored_networks.copy()

    results["suitability"] = results[
        "suitability_score"
    ].apply(classify_suitability)

    results = results.sort_values(
        "suitability_score",
        ascending=False,
    )

    print("\n" + "=" * 60)
    print("WISENSE — NETWORK RECOMMENDATION")
    print("=" * 60)

    print(f"\nTask: {task_name}")

    print("\nNETWORK SCORES")
    print("-" * 40)

    display_columns = [
        "network_name",
        "avg_speed_mbps",
        "avg_rssi_dbm",
        "avg_signal_std_dbm",
        "avg_devices",
        "avg_distance_m",
        "speed_score",
        "signal_score",
        "stability_score",
        "congestion_score",
        "distance_score",
        "suitability_score",
        "suitability",
    ]

    print(
        results[display_columns]
        .round(2)
        .to_string(index=False)
    )

    recommended = results.iloc[0]

    print("\nNETWORK RECOMMENDATION")
    print("-" * 40)
    print(
        f"Recommended network : "
        f"{recommended['network_name']}"
    )
    print(
        f"Suitability score   : "
        f"{recommended['suitability_score']:.2f}/100"
    )
    print(
        f"Suitability level   : "
        f"{recommended['suitability']}"
    )


def main():
    print("=" * 60)
    print("WISENSE — RECOMMENDATION ENGINE")
    print("=" * 60)

    df = load_data()

    print(f"\nObservations loaded: {len(df)}")

    summary = build_network_summary(df)

    print("\n[1] NETWORK SUMMARY")
    print("-" * 40)
    print(
        summary.round(2)
        .to_string(index=False)
    )

    scored_networks = calculate_metric_scores(
        summary
    )

    print("\n[2] DOMAIN-BASED METRIC SCORING")
    print("-" * 40)
    print(
        "Project-defined Wi-Fi reference ranges "
        "converted metrics to 0-100 scores."
    )

    print("\nScoring ranges:")
    print("- Speed: 10–100 Mbps")
    print("- RSSI: -85 to -45 dBm")
    print("- Signal stability: 1–8 dBm standard deviation")
    print("- Connected devices: 2–15")
    print("- Distance: 5–50 m")

    for task_name in TASK_PROFILES:
        task_results = calculate_task_scores(
            scored_networks,
            task_name,
        )

        print_results(
            task_results,
            task_name,
        )

    print("\n" + "=" * 60)
    print("RECOMMENDATION ENGINE COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()