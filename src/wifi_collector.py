from __future__ import annotations

import csv
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_FILE = ROOT_DIR / "data" / "live_wifi.csv"

SAMPLE_INTERVAL_SECONDS = 5


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

    file_exists = OUTPUT_FILE.exists()

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


def print_reading(data: dict, sample_number: int) -> None:
    print()
    print(f"WISENSE — LIVE SAMPLE #{sample_number}")
    print("=" * 45)

    print(f"Timestamp               : {data['timestamp']}")
    print(f"State                   : {data['state']}")
    print(f"Interface               : {data['interface']}")
    print(f"SSID                    : {data['ssid']}")
    print(f"Channel                 : {data['channel']}")
    print(f"Signal Percent          : {data['signal_percent']}")
    print(f"Receive Rate Mbps       : {data['receive_rate_mbps']}")
    print(f"Transmit Rate Mbps      : {data['transmit_rate_mbps']}")

    print()
    print(f"Saved to: {OUTPUT_FILE}")


def collect_continuously() -> None:
    print()
    print("WISENSE — CONTINUOUS WI-FI COLLECTOR")
    print("=" * 45)
    print(f"Sampling interval: {SAMPLE_INTERVAL_SECONDS} seconds")
    print("Press Ctrl+C to stop.")
    print()

    sample_number = 0

    try:
        while True:
            sample_number += 1

            try:
                wifi_data = collect_wifi_info()
                save_reading(wifi_data)
                print_reading(wifi_data, sample_number)

            except Exception as exc:
                print()
                print("COLLECTION ERROR")
                print("-" * 45)
                print(str(exc))

            time.sleep(SAMPLE_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print()
        print("=" * 45)
        print("WISENSE COLLECTION STOPPED")
        print(f"Total samples collected: {sample_number}")
        print(f"Data file: {OUTPUT_FILE}")
        print()


if __name__ == "__main__":
    collect_continuously()