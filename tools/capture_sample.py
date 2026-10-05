"""Capture a REAL sample for the public demo from this computer's Wi-Fi, with anonymization.

    python tools/capture_sample.py                 # 30 scans, 5 s apart, names + MACs anonymized
    python tools/capture_sample.py --keep-names    # keep SSIDs (neighbours' network names become public!)
Writes data/sample_scan.csv (source = sample-captured). Commit that file for the demo.
"""
import argparse
import hashlib
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analysis import live_wifi as lw   # noqa: E402

parser = argparse.ArgumentParser()
parser.add_argument("--scans", type=int, default=30)
parser.add_argument("--interval", type=float, default=5.0)
parser.add_argument("--keep-names", action="store_true", help="do not anonymize SSIDs")
args = parser.parse_args()

frames = []
for i in range(args.scans):
    try:
        frame = lw.scan_once()
    except Exception as exc:
        sys.exit(f"Scan failed: {exc}")
    frame["timestamp"] = pd.Timestamp.now().floor("s")
    frames.append(frame)
    print(f"scan {i + 1}/{args.scans}: {len(frame)} access points")
    if i < args.scans - 1:
        time.sleep(args.interval)

data = pd.concat(frames, ignore_index=True)

def fake_mac(value: str) -> str:
    digest = hashlib.sha1(str(value).encode()).hexdigest()
    return "02:" + ":".join(digest[i:i + 2] for i in range(0, 10, 2))      # locally-administered, irreversible

data["bssid"] = data["bssid"].map(lambda v: fake_mac(v) if pd.notna(v) else None)
if not args.keep_names:
    names = {n: f"Network-{chr(65 + i % 26)}{'' if i < 26 else i // 26}" for i, n in enumerate(sorted(data["ssid"].unique()))}
    data["ssid"] = data["ssid"].map(names)
data["ap_id"] = data["bssid"].fillna(data["ssid"].astype(str) + "|ch" + data["channel"].astype(str))
data["source"] = "sample-captured"
data[lw.COLUMNS].to_csv(lw.SAMPLE_PATH, index=False)
print(f"wrote {lw.SAMPLE_PATH}")
