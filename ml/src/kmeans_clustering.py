from pathlib import Path

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler


DATA_PATH = Path("data/wifi_observations.csv")
OUTPUT_PATH = Path("data/wifi_clustered.csv")

FEATURES = [
    "rssi_dbm",
    "signal_std_dbm",
    "distance_to_ap_m",
    "connected_devices",
    "avg_download_mbps",
    "peak_usage_hours",
]

RANDOM_STATE = 42
FINAL_K = 3


def load_data() -> pd.DataFrame:
    """Load the Wi-Fi observation dataset."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_PATH}"
        )

    df = pd.read_csv(DATA_PATH)

    missing_features = [
        column for column in FEATURES
        if column not in df.columns
    ]

    if missing_features:
        raise ValueError(
            f"Missing required features: {missing_features}"
        )

    return df


def prepare_features(df: pd.DataFrame):
    """Standardize numerical features for K-Means."""
    X = df[FEATURES].copy()

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    return X_scaled, scaler


def evaluate_k_values(X_scaled):
    """Evaluate several cluster counts."""
    print("\n[1] K-MEANS MODEL EVALUATION")
    print("-" * 40)

    results = []

    for k in range(2, 6):
        model = KMeans(
            n_clusters=k,
            random_state=RANDOM_STATE,
            n_init=20,
        )

        labels = model.fit_predict(X_scaled)

        inertia = model.inertia_
        silhouette = silhouette_score(X_scaled, labels)

        results.append(
            {
                "k": k,
                "inertia": inertia,
                "silhouette_score": silhouette,
            }
        )

        print(
            f"k={k} | "
            f"inertia={inertia:.3f} | "
            f"silhouette={silhouette:.3f}"
        )

    return pd.DataFrame(results)


def fit_final_model(X_scaled):
    """Fit the final K-Means model."""
    model = KMeans(
        n_clusters=FINAL_K,
        random_state=RANDOM_STATE,
        n_init=20,
    )

    labels = model.fit_predict(X_scaled)

    return model, labels


def print_cluster_profiles(df: pd.DataFrame):
    """Display average feature values for each cluster."""
    print("\n[3] CLUSTER PROFILES")
    print("-" * 40)

    profile = (
        df.groupby("cluster")[FEATURES]
        .mean()
        .round(2)
    )

    print(profile)

    print("\nCluster sizes:")
    print(df["cluster"].value_counts().sort_index())


def main():
    print("=" * 60)
    print("WISENSE — K-MEANS CONNECTIVITY CLUSTERING")
    print("=" * 60)

    # Load dataset
    df = load_data()

    print("\nDataset:")
    print(f"Observations : {len(df)}")
    print(f"Features used: {len(FEATURES)}")

    print("\nFeatures:")
    for feature in FEATURES:
        print(f"- {feature}")

    # Prepare standardized features
    X_scaled, scaler = prepare_features(df)

    print("\n[2] FEATURE STANDARDIZATION")
    print("-" * 40)
    print("StandardScaler applied.")
    print("Mean approximately 0 and standard deviation approximately 1.")

    # Evaluate candidate k values
    evaluation = evaluate_k_values(X_scaled)

    # Fit final model
    model, labels = fit_final_model(X_scaled)

    df["cluster"] = labels

    print("\n[4] FINAL MODEL")
    print("-" * 40)
    print(f"Selected clusters : k={FINAL_K}")
    print(f"Random state      : {RANDOM_STATE}")
    print(f"Inertia            : {model.inertia_:.3f}")

    final_silhouette = silhouette_score(
        X_scaled,
        labels,
    )

    print(f"Silhouette score   : {final_silhouette:.3f}")

    # Cluster profiles
    print_cluster_profiles(df)

    # Save clustered dataset
    df.to_csv(OUTPUT_PATH, index=False)

    print("\n[5] OUTPUT")
    print("-" * 40)
    print(f"Saved clustered dataset: {OUTPUT_PATH}")

    print("\nK-Means clustering complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()