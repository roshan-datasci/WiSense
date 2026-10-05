"""Pure analytics over real scan frames (no I/O, no invented data)."""
from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

from analysis.live_wifi import signal_state

TASK_WEIGHTS: dict[str, dict[str, float]] = {
    "General":    {"signal": 0.35, "stability": 0.20, "congestion": 0.25, "band": 0.20},
    "Browsing":   {"signal": 0.35, "stability": 0.20, "congestion": 0.25, "band": 0.20},
    "Video Call": {"signal": 0.30, "stability": 0.30, "congestion": 0.25, "band": 0.15},
    "Gaming":     {"signal": 0.25, "stability": 0.35, "congestion": 0.25, "band": 0.15},
    "Download":   {"signal": 0.30, "stability": 0.10, "congestion": 0.25, "band": 0.35},
}
BAND_SCORE = {"6 GHz": 100.0, "5 GHz": 85.0, "2.4 GHz": 45.0, "Unknown": 50.0}

CANDIDATE_CHANNELS = {
    "2.4 GHz": [1, 6, 11],
    "5 GHz": [36, 40, 44, 48, 149, 153, 157, 161, 165],
}


# ---------------------------------------------------------------------------
# Generic scoring helpers
# ---------------------------------------------------------------------------

def higher_score(value: float, poor: float, excellent: float) -> float:
    if value <= poor:
        return 0.0
    if value >= excellent:
        return 100.0
    return (value - poor) / (excellent - poor) * 100.0


def lower_score(value: float, excellent: float, poor: float) -> float:
    if value <= excellent:
        return 100.0
    if value >= poor:
        return 0.0
    return (poor - value) / (poor - excellent) * 100.0


def suitability_label(score: float) -> str:
    if score >= 80:
        return "HIGH"
    if score >= 60:
        return "MODERATE"
    if score >= 40:
        return "LIMITED"
    return "LOW"


def is_open_network(authentication: Any) -> bool:
    return str(authentication).strip().lower() in {"open", "none", ""}


# ---------------------------------------------------------------------------
# Network / access-point summaries
# ---------------------------------------------------------------------------

def ssid_summary(latest: pd.DataFrame) -> pd.DataFrame:
    if latest.empty:
        return pd.DataFrame()
    rows = []
    for ssid, group in latest.groupby("ssid", dropna=False):
        best = group.loc[group["signal_percent"].idxmax()]
        channels = sorted(int(c) for c in group["channel"].dropna().unique())
        rows.append({
            "SSID": ssid,
            "ACCESS POINTS": int(group["ap_id"].nunique()),
            "BEST SIGNAL %": float(group["signal_percent"].max()),
            "AVG SIGNAL %": round(float(group["signal_percent"].mean()), 1),
            "BEST dBm": float(best["rssi_dbm"]) if pd.notna(best["rssi_dbm"]) else None,
            "BANDS": ", ".join(sorted(group["band"].dropna().unique())),
            "CHANNELS": ", ".join(str(c) for c in channels),
            "SECURITY": best["authentication"],
        })
    return pd.DataFrame(rows).sort_values("BEST SIGNAL %", ascending=False).reset_index(drop=True)


def ap_signal_stats(history: pd.DataFrame) -> pd.DataFrame:
    """Per-access-point statistics over repeated scans."""
    if history.empty:
        return pd.DataFrame()
    rows = []
    for ap_id, group in history.sort_values("timestamp").groupby("ap_id"):
        values = pd.to_numeric(group["signal_percent"], errors="coerce").dropna()
        if values.empty:
            continue
        last = group.iloc[-1]
        rows.append({
            "SSID": last["ssid"], "BSSID": last["bssid"] if pd.notna(last["bssid"]) else "—",
            "CHANNEL": last["channel"], "CURRENT %": float(values.iloc[-1]),
            "AVERAGE %": round(float(values.mean()), 1), "MIN %": float(values.min()),
            "MAX %": float(values.max()), "VARIATION (σ)": round(float(values.std(ddof=0)), 2),
            "SCANS": int(len(values)), "STATE": signal_state(values.iloc[-1]),
        })
    return pd.DataFrame(rows).sort_values("CURRENT %", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Channel analysis
# ---------------------------------------------------------------------------

def overlap_factor(freq_a: float, freq_b: float) -> float:
    """How strongly two 20 MHz transmissions interfere (1 = same channel, 0 = none)."""
    if pd.isna(freq_a) or pd.isna(freq_b):
        return 0.0
    gap = abs(float(freq_a) - float(freq_b))
    if float(freq_a) < 3000:                      # 2.4 GHz: channels 5 MHz apart, 20 MHz wide
        if gap == 0:
            return 1.0
        return max(0.0, 1.0 - gap / 25.0) if gap < 25 else 0.0
    return 1.0 if gap < 10 else 0.0               # 5/6 GHz: same 20 MHz channel only


def channel_summary(latest: pd.DataFrame) -> pd.DataFrame:
    if latest.empty or latest["channel"].dropna().empty:
        return pd.DataFrame()
    work = latest.dropna(subset=["channel"]).copy()
    out = (work.groupby(["band", "channel"])
           .agg(frequency_mhz=("frequency_mhz", "first"),
                access_points=("ap_id", "nunique"),
                networks=("ssid", "nunique"),
                strongest=("signal_percent", "max"),
                mean_signal=("signal_percent", "mean"))
           .reset_index())
    out["channel"] = out["channel"].astype(int)
    out["mean_signal"] = out["mean_signal"].round(1)
    return out.sort_values(["band", "channel"]).reset_index(drop=True)


def channel_interference(latest: pd.DataFrame, band: str, channel: int, exclude_ap: str | None = None) -> float:
    """Weighted interference load on a candidate channel (signal-weighted overlap)."""
    from analysis.live_wifi import channel_to_frequency_mhz
    freq = channel_to_frequency_mhz(channel, band)
    if freq is None or latest.empty:
        return 0.0
    work = latest[latest["band"] == band]
    if exclude_ap:
        work = work[work["ap_id"] != exclude_ap]
    load = 0.0
    for _, row in work.iterrows():
        load += overlap_factor(freq, row["frequency_mhz"]) * (row["signal_percent"] / 100.0)
    return round(load, 2)


def recommend_channels(latest: pd.DataFrame) -> pd.DataFrame:
    """Rank candidate channels per band by the interference they would meet *here*."""
    rows = []
    for band, candidates in CANDIDATE_CHANNELS.items():
        if latest.empty or not (latest["band"] == band).any():
            continue
        scored = [(ch, channel_interference(latest, band, ch)) for ch in candidates]
        best = min(score for _, score in scored)
        for ch, score in scored:
            rows.append({"BAND": band, "CHANNEL": ch, "INTERFERENCE LOAD": score,
                         "RECOMMENDED": "◀ least crowded" if score == best else ""})
    return pd.DataFrame(rows)


def ap_congestion(latest: pd.DataFrame) -> pd.DataFrame:
    """For every AP: how many other APs overlap it and the weighted interference load."""
    if latest.empty:
        return pd.DataFrame()
    rows = []
    for _, row in latest.iterrows():
        others = latest[(latest["ap_id"] != row["ap_id"]) & (latest["band"] == row["band"])]
        load, count = 0.0, 0
        for _, other in others.iterrows():
            factor = overlap_factor(row["frequency_mhz"], other["frequency_mhz"])
            if factor > 0:
                count += 1
                load += factor * other["signal_percent"] / 100.0
        rows.append({"SSID": row["ssid"], "BSSID": row["bssid"] if pd.notna(row["bssid"]) else "—",
                     "BAND": row["band"], "CHANNEL": row["channel"], "SIGNAL %": row["signal_percent"],
                     "OVERLAPPING APs": count, "INTERFERENCE LOAD": round(load, 2)})
    return pd.DataFrame(rows).sort_values("INTERFERENCE LOAD", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Estimated distance (clearly an estimate, never a measurement)
# ---------------------------------------------------------------------------

def estimate_distance_m(rssi_dbm: float, freq_mhz: float, tx_dbm: float = 20.0, exponent: float = 3.0) -> float | None:
    """Log-distance path-loss estimate. Walls/people make real distance differ a lot."""
    if pd.isna(rssi_dbm) or pd.isna(freq_mhz):
        return None
    fspl_1m = 20 * math.log10(float(freq_mhz)) - 27.55
    distance = 10 ** ((tx_dbm - float(rssi_dbm) - fspl_1m) / (10 * exponent))
    return round(float(min(max(distance, 0.5), 200.0)), 1)


# ---------------------------------------------------------------------------
# Task suitability from live measurements
# ---------------------------------------------------------------------------

def score_networks(latest: pd.DataFrame, history: pd.DataFrame, task: str) -> pd.DataFrame:
    """Heuristic suitability per SSID from measured signal, stability, channel load and band."""
    if latest.empty:
        return pd.DataFrame()
    weights = TASK_WEIGHTS.get(task, TASK_WEIGHTS["General"])
    rows = []
    for ssid, group in latest.groupby("ssid"):
        best = group.loc[group["signal_percent"].idxmax()]
        hist = history[history["ap_id"] == best["ap_id"]]["signal_percent"] if not history.empty else pd.Series(dtype=float)
        scores: dict[str, float | None] = {
            "signal": higher_score(float(best["signal_percent"]), poor=20, excellent=80),
            "congestion": lower_score(ap_load(latest, best), excellent=0.4, poor=4.0),
            "band": BAND_SCORE.get(best["band"], 50.0),
            "stability": lower_score(float(hist.std(ddof=0)), excellent=1.5, poor=12.0) if len(hist) >= 3 else None,
        }
        usable = {k: v for k, v in scores.items() if v is not None}
        total_w = sum(weights[k] for k in usable)
        score = sum(usable[k] * weights[k] for k in usable) / total_w if total_w else 0.0
        notes = []
        if is_open_network(best["authentication"]):
            notes.append("open / unencrypted")
        if scores["stability"] is None:
            notes.append("stability pending (needs 3+ scans)")
        rows.append({
            "SSID": ssid, "SCORE": round(score, 1), "SUITABILITY": suitability_label(score),
            "SIGNAL %": float(best["signal_percent"]), "BAND": best["band"], "CHANNEL": best["channel"],
            "CHANNEL LOAD": ap_load(latest, best), "NOTES": ", ".join(notes),
        })
    return pd.DataFrame(rows).sort_values("SCORE", ascending=False).reset_index(drop=True)


def ap_load(latest: pd.DataFrame, row: pd.Series) -> float:
    others = latest[(latest["ap_id"] != row["ap_id"]) & (latest["band"] == row["band"])]
    return round(sum(overlap_factor(row["frequency_mhz"], o["frequency_mhz"]) * o["signal_percent"] / 100.0
                     for _, o in others.iterrows()), 2)


# ---------------------------------------------------------------------------
# Insight sentences for the overview
# ---------------------------------------------------------------------------

def overview_insights(latest: pd.DataFrame, connected: dict[str, Any]) -> list[str]:
    if latest.empty:
        return []
    out: list[str] = []
    best = latest.loc[latest["signal_percent"].idxmax()]
    out.append(f"Strongest signal nearby: **{best['ssid']}** at {best['signal_percent']:.0f}% "
               f"({best['band']}, channel {int(best['channel']) if pd.notna(best['channel']) else '?'}).")
    if connected.get("ssid") and connected.get("signal_percent") is not None:
        out.append(f"You are connected to **{connected['ssid']}** — signal {connected['signal_percent']:.0f}% "
                   f"({signal_state(connected['signal_percent']).lower()}).")
    channels = channel_summary(latest)
    if not channels.empty:
        top = channels.sort_values("access_points", ascending=False).iloc[0]
        if top["access_points"] > 1:
            out.append(f"Busiest channel: **{top['band']} channel {top['channel']}** with {int(top['access_points'])} access points "
                       f"from {int(top['networks'])} network(s).")
    open_count = int(latest[latest["authentication"].map(is_open_network)]["ssid"].nunique())
    if open_count:
        out.append(f"{open_count} nearby network(s) are **open (no encryption)** — avoid sensitive logins on them.")
    bands = latest["band"].value_counts().to_dict()
    out.append("Band mix: " + ", ".join(f"{count} AP(s) on {band}" for band, count in bands.items()) + ".")
    rec = recommend_channels(latest)
    if not rec.empty:
        for band, group in rec.groupby("BAND"):
            best_rows = group[group["RECOMMENDED"] != ""]
            chans = ", ".join(str(c) for c in best_rows["CHANNEL"].tolist()[:3])
            out.append(f"Least crowded {band} channel(s) at your location right now: **{chans}**.")
    return out


# ---------------------------------------------------------------------------
# K-Means connectivity clusters on the LIVE scan (NumPy only, deterministic)
# ---------------------------------------------------------------------------

def cluster_access_points(latest: pd.DataFrame, k: int = 3) -> pd.DataFrame:
    """Group access points by measured signal, channel overlap and band quality."""
    if len(latest) < 2:
        return pd.DataFrame()
    work = latest.reset_index(drop=True).copy()
    work["load"] = [ap_load(latest, row) for _, row in latest.reset_index(drop=True).iterrows()]
    work["band_score"] = work["band"].map(lambda b: BAND_SCORE.get(b, 50.0))
    work["est_distance_m"] = [estimate_distance_m(r, f) for r, f in zip(work["rssi_dbm"], work["frequency_mhz"])]
    features = work[["signal_percent", "load", "band_score"]].astype(float).to_numpy()
    spread = features.std(axis=0)
    spread[spread == 0] = 1.0
    z = (features - features.mean(axis=0)) / spread
    k = max(1, min(k, len(work)))
    order = np.argsort(z[:, 0])
    centres = z[order[np.linspace(0, len(order) - 1, k).astype(int)]].copy()
    labels = np.zeros(len(z), dtype=int)
    for _ in range(25):
        distances = ((z[:, None, :] - centres[None, :, :]) ** 2).sum(axis=2)
        new_labels = distances.argmin(axis=1)
        for c in range(k):
            if (new_labels == c).any():
                centres[c] = z[new_labels == c].mean(axis=0)
        if (new_labels == labels).all():
            break
        labels = new_labels
    work["cluster"] = labels
    rank = work.groupby("cluster")["signal_percent"].mean().sort_values(ascending=False)
    work["cluster"] = work["cluster"].map({old: new for new, old in enumerate(rank.index)})
    return work
