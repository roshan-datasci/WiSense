from __future__ import annotations

import csv
import re
import subprocess
from datetime import datetime
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_FILE = ROOT_DIR / "data" / "live_wifi.csv"


def run_netsh() -> str:
    result = subprocess.run(
        ["netsh", "wlan", "show", "interfaces"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Windows netsh command failed:\n"
            + result.stderr.strip()
        )

    return result.stdout


def parse_value(output: str, label: str) -> str | None:
    pattern = rf"^\s*{re.escape(label)}\s*:\s*(.*?)\s*$"
    match = re.search(pattern, output, flags=re.MULTILINE)

    if match:
        return match.group(1).strip()

    return None


def parse_signal_percent(value: str | None) -> int | None:
    if value is None:
        return None

    match = re.search(r"(\d+)", value)

    if not match:
        return None

    return int(match.group(1))


def parse_integer(value: str | None) -> int | None:
    if value is None:
        return None

    match = re.search(r"(\d+)", value)

    if not match:
        return None

    return int(match.group(1))


def collect_wifi_info() -> dict:
    output = run_netsh()

    state = parse_value(output, "State")

    if state is None:
        raise RuntimeError(
            "Could not determine Wi-Fi interface state."
        )

    timestamp = datetime.now().isoformat(
        timespec="seconds"
    )

    if state.lower() != "connected":
        return {
            "timestamp": timestamp,
            "state": state,
            "interface": None,
            "ssid": None,
            "bssid": None,
            "radio_type": None,
            "channel": None,
            "signal_percent": None,
            "receive_rate_mbps": None,
            "transmit_rate_mbps": None,
        }

    return {
        "timestamp": timestamp,
        "state": state,
        "interface": parse_value(output, "Name"),
        "ssid": parse_value(output, "SSID"),
        "bssid": parse_value(output, "BSSID"),
        "radio_type": parse_value(output, "Radio type"),
        "channel": parse_integer(
            parse_value(output, "Channel")
        ),
        "signal_percent": parse_signal_percent(
            parse_value(output, "Signal")
        ),
        "receive_rate_mbps": parse_integer(
            parse_value(output, "Receive rate (Mbps)")
        ),
        "transmit_rate_mbps": parse_integer(
            parse_value(output, "Transmit rate (Mbps)")
        ),
    }


def save_reading(data: dict) -> None:
    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    file_exists = OUTPUT_FILE.exists()

    fieldnames = [
        "timestamp",
        "state",
        "interface",
        "ssid",
        "bssid",
        "radio_type",
        "channel",
        "signal_percent",
        "receive_rate_mbps",
        "transmit_rate_mbps",
    ]

    with OUTPUT_FILE.open(
        "a",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        if not file_exists:
            writer.writeheader()

        writer.writerow(data)


def print_wifi_info(data: dict) -> None:
    print()
    print("WISENSE — REAL-TIME WI-FI COLLECTOR")
    print("=" * 45)

    for key, value in data.items():
        label = key.replace("_", " ").title()
        print(f"{label:<24}: {value}")

    print()
    print(f"Saved to: {OUTPUT_FILE}")
    print()
    print("COLLECTION COMPLETE")


if __name__ == "__main__":
    try:
        wifi_data = collect_wifi_info()

        save_reading(wifi_data)

        print_wifi_info(wifi_data)

    except Exception as exc:
        print()
        print("WISENSE WI-FI COLLECTOR ERROR")
        print("=" * 45)
        print(str(exc))