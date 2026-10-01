from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
LIVE_WIFI_FILE = ROOT_DIR / "data" / "live_wifi.csv"


def load_live_wifi() -> pd.DataFrame:
    if not LIVE_WIFI_FILE.exists():
        return pd.DataFrame()

    df = pd.read_csv(LIVE_WIFI_FILE)

    if df.empty:
        return df

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce"
    )

    numeric_columns = [
        "channel",
        "signal_percent",
        "receive_rate_mbps",
        "transmit_rate_mbps",
    ]

    for column in numeric_columns:
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    return df


def get_latest_reading(
    df: pd.DataFrame
) -> dict:
    if df.empty:
        return {}

    latest = df.sort_values(
        "timestamp"
    ).iloc[-1]

    return latest.to_dict()


def get_live_summary(
    df: pd.DataFrame
) -> dict:
    if df.empty:
        return {
            "samples": 0,
            "signal": None,
            "receive_rate": None,
            "transmit_rate": None,
            "channel": None,
            "ssid": None,
        }

    latest = get_latest_reading(df)

    return {
        "samples": len(df),
        "signal": latest.get("signal_percent"),
        "receive_rate": latest.get(
            "receive_rate_mbps"
        ),
        "transmit_rate": latest.get(
            "transmit_rate_mbps"
        ),
        "channel": latest.get("channel"),
        "ssid": latest.get("ssid"),
    }