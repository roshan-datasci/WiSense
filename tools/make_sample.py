"""Create data/sample_scan.csv — an ILLUSTRATIVE synthetic sample used by the public demo.

It is NOT real measurement data. Replace it with a real (anonymized) capture using:
    python tools/capture_sample.py
"""
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analysis import live_wifi as lw   # noqa: E402

APS = [  # ssid, bssid, auth, band, channel, base signal %
    ("Demo-Campus-WiFi", "02:00:00:00:00:01", "WPA2-Enterprise", "5 GHz", 44, 86),
    ("Demo-Campus-WiFi", "02:00:00:00:00:02", "WPA2-Enterprise", "2.4 GHz", 6, 64),
    ("Demo-Hostel", "02:00:00:00:00:03", "WPA2-Personal", "2.4 GHz", 1, 52),
    ("Demo-Hostel", "02:00:00:00:00:04", "WPA2-Personal", "2.4 GHz", 11, 40),
    ("Demo-Cafe-Guest", "02:00:00:00:00:05", "Open", "2.4 GHz", 6, 47),
    ("Demo-Phone-Hotspot", "02:00:00:00:00:06", "WPA3-Personal", "5 GHz", 149, 73),
    ("Demo-Lab-5G", "02:00:00:00:00:07", "WPA2-Personal", "5 GHz", 36, 58),
    ("", "02:00:00:00:00:08", "WPA2-Personal", "2.4 GHz", 6, 33),
]

rng = random.Random(42)
start = datetime(2026, 1, 1, 10, 0, 0)
levels = {a[1]: float(a[5]) for a in APS}
rows = []
for scan in range(40):
    stamp = start + timedelta(seconds=5 * scan)
    for ssid, bssid, auth, band, channel, _ in APS:
        levels[bssid] = min(99, max(5, levels[bssid] + rng.uniform(-3.5, 3.5)))
        rows.append({"ssid": ssid, "bssid": bssid, "authentication": auth, "encryption": "None" if auth == "Open" else "CCMP",
                     "signal_percent": round(levels[bssid]), "radio_type": "802.11ac" if band == "5 GHz" else "802.11n",
                     "band": band, "channel": channel, "timestamp": stamp})
frames = []
for stamp, group in pd.DataFrame(rows).groupby("timestamp"):
    frames.append(lw._finalize(group.drop(columns="timestamp").to_dict("records"), "sample-synthetic", stamp.to_pydatetime()))
out = pd.concat(frames, ignore_index=True)[lw.COLUMNS]
lw.DATA_DIR.mkdir(exist_ok=True)
out.to_csv(lw.SAMPLE_PATH, index=False)
print(f"wrote {lw.SAMPLE_PATH} — {len(out)} rows, {out['timestamp'].nunique()} scans")
