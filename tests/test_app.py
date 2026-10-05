"""Headless end-to-end runs of the Streamlit app with Streamlit's AppTest."""
import datetime as dt
import random
import sys
import tempfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from streamlit.testing.v1 import AppTest

from analysis import live_wifi as lw
from test_scanner import NETSH, TERMUX

APP = str(Path(__file__).resolve().parents[1] / "app" / "app.py")
SECTIONS = ["LOCAL WI-FI COLLECTOR", "LIVE NETWORK OVERVIEW", "INTERACTIVE WI-FI MAP", "SIGNAL STRENGTH", "WI-FI CHANNEL ANALYSIS",
            "WI-FI ENVIRONMENT", "CONNECTION INTELLIGENCE", "PERFORMANCE RELATIONSHIPS", "ML INSIGHTS", "TASK SUITABILITY",
            "PERFORMANCE TRENDS", "ADVANCED ANALYTICS COMPLETE"]


def run():
    at = AppTest.from_file(APP, default_timeout=60)
    return at


def sections_in(at):
    blob = " ".join(str(getattr(e, "value", "")) for e in at.get("html"))
    return [s for s in SECTIONS if s in blob], blob


def fake_environment(scans=6):
    lw.STORE.clear()
    rng, n = random.Random(7), {"n": 0}

    def fake_scan():
        n["n"] += 1
        f = lw.parse_netsh_bssid_output(NETSH)
        f["signal_percent"] = (f["signal_percent"] + [rng.randint(-6, 6) for _ in range(len(f))]).clip(5, 99)
        f["rssi_dbm"] = f["signal_percent"] / 2 - 100
        f["timestamp"] = f["timestamp"] + pd.Timedelta(seconds=5 * n["n"])
        return f

    lw.scan_once = fake_scan
    lw.get_connected_wifi = lambda: {"interface": "Wi-Fi", "ssid": "sathyabama-campus@sathyabama-ac-in", "signal_percent": 84,
                                      "receive_rate": 433.0, "transmit_rate": 390.0}
    lw.detect_platform = lambda: "windows"
    for _ in range(scans):
        lw.STORE.scan(force=True, persist=False)


def test_no_wifi_reports_error_without_crashing():
    lw.STORE.clear()
    lw.detect_platform = lambda: "unknown"
    at = run(); at.run()
    assert not at.exception, [e.value for e in at.exception]
    found, _ = sections_in(at)
    assert found == SECTIONS, f"missing sections: {set(SECTIONS) - set(found)}"
    print("OK  no Wi-Fi: no crash, error shown, all", len(found), "sections present in original order")


def test_live_scans_original_layout():
    fake_environment()
    at = run(); at.run()
    assert not at.exception, [e.value for e in at.exception]
    found, blob = sections_in(at)
    assert found == SECTIONS
    assert "nav-row" in blob and "TASK SELECTOR" in blob and "LIVE" in blob
    for target in ("sec-overview", "sec-map", "sec-signal", "sec-channels", "sec-insights"):
        assert f'href="#{target}"' in blob, f"nav link to {target} missing"
        assert f'id="{target}"' in blob, f"anchor {target} missing"
    print("OK  nav links all have matching section anchors")
    assert len(at.tabs) == 0, "UI must not use tabs"
    assert len(at.expander) == 4, f"expected one expander per SSID, got {len(at.expander)}"
    assert len(at.metric) == 5
    print(f"OK  live: original layout, {len(at.expander)} SSID expanders, {len(at.get('plotly_chart'))} charts, {len(at.dataframe)} tables")
    assert len(at.get("plotly_chart")) >= 12
    at.selectbox[0].select("Gaming").run()
    assert not at.exception, [e.value for e in at.exception]
    print("OK  task selector change re-scores networks")


def test_phone_import_probe_map_and_hourly():
    tmp = Path(tempfile.mkdtemp())
    lw.HISTORY_PATH = tmp / "live_wifi_history.csv"
    base, rows = dt.datetime(2026, 10, 3, 9), []
    for h in range(6):
        f = lw.parse_netsh_bssid_output(NETSH); f["timestamp"] = base + dt.timedelta(hours=h); f["signal_percent"] -= h * 2; rows.append(f)
    pd.concat(rows).to_csv(lw.HISTORY_PATH, index=False)
    fake_environment(3)
    at = run()
    at.session_state["wisense_probe_samples"] = [
        {"seq": i, "client_time_ms": i, "timestamp": dt.datetime.now() + dt.timedelta(seconds=5 * i), "device": "Android phone", "conn_type": "wifi",
         "server_rtt_ms": 8 + i % 4, "server_jitter_ms": 1.5, "server_loss_pct": 0.0, "internet_rtt_ms": 30 + i,
         "download_mbps": 40.0 + i if i % 2 == 0 else None, "signal_percent": 45 + i * 3} for i in range(12)]
    at.session_state["wisense_device_location"] = {"latitude": 12.8723, "longitude": 80.2207, "accuracy_m": 20, "method": "Browser device geolocation"}
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    n = len(at.get("plotly_chart"))
    print("OK  probe samples + location + multi-hour archive render; charts:", n)
    assert n >= 15

    at2 = run()
    at2.session_state["wisense_imported"] = [lw.import_scan_bytes("phone.json", TERMUX.encode())]
    at2.run()
    assert not at2.exception, [e.value for e in at2.exception]
    assert any("PhoneSeesThis" in str(e.label) for e in at2.expander)
    print("OK  imported phone scan analysed (SSIDs from the phone shown)")


if __name__ == "__main__":
    test_no_wifi_reports_error_without_crashing()
    test_live_scans_original_layout()
    test_phone_import_probe_map_and_hourly()


def test_speed_test_panel_states():
    fake_environment(3)
    base = {"seq": 1, "client_time_ms": 1, "timestamp": dt.datetime.now(), "device": "Android phone", "conn_type": "wifi",
            "server_rtt_ms": 9.0, "server_jitter_ms": 1.2, "server_loss_pct": 0.0, "internet_rtt_ms": 35.0}
    # pressed, nothing back yet -> must say it is running
    at = run(); at.session_state["_speed_run_id"] = 1; at.session_state["wisense_probe_samples"] = [dict(base, speed_run_id=None)]
    at.run(); assert not at.exception, [e.value for e in at.exception]
    assert any("RUNNING SPEED TEST" in str(i.value) for i in at.info), "pending state not shown"
    # finished -> result cards visible
    at = run(); at.session_state["_speed_run_id"] = 1
    at.session_state["wisense_probe_samples"] = [dict(base, speed_run_id=1, local_mbps=87.4, download_mbps=None, speed_error="internet download blocked or failed (Failed to fetch)")]
    at.run(); assert not at.exception, [e.value for e in at.exception]
    blob = " ".join(str(getattr(e, "value", "")) for e in at.get("html"))
    assert "87.4 Mbps" in blob and "WI-FI LINK TO HOST" in blob
    assert any("could not run" in str(w.value) for w in at.warning), "blocked-internet warning missing"
    print("OK  speed test: pending state, result cards (Wi-Fi link 87.4 Mbps) and blocked-internet warning all shown")


if __name__ == "__main__":
    test_speed_test_panel_states()


def test_demo_mode_never_scans_or_writes():
    import os
    tmp = Path(tempfile.mkdtemp())
    lw.HISTORY_PATH = tmp / "live_wifi_history.csv"
    lw.STORE.clear()

    def forbidden():
        raise AssertionError("demo mode must never scan the host Wi-Fi")

    lw.scan_once = forbidden
    os.environ["WISENSE_DEMO"] = "1"
    try:
        at = run(); at.run()
        assert not at.exception, [e.value for e in at.exception]
        found, blob = sections_in(at)
        assert found == SECTIONS and "DEMO MODE" in blob and "ILLUSTRATIVE" in blob
        assert at.button(key="wisense_scan_now").disabled and at.checkbox(key="wisense_auto_update").disabled
        assert not lw.HISTORY_PATH.exists(), "demo mode must not write the archive"
        assert lw.STORE.scan_count == 0
        print(f"OK  demo mode: sample shown + labelled, controls disabled, host never scanned, nothing written; charts: {len(at.get('plotly_chart'))}")
    finally:
        os.environ.pop("WISENSE_DEMO", None)


def test_archive_is_capped():
    tmp = Path(tempfile.mkdtemp()) / "a.csv"
    pd.DataFrame({"timestamp": range(60000), "ssid": ["x" * 40] * 60000}).to_csv(tmp, index=False)
    before = tmp.stat().st_size
    assert lw.trim_archive(tmp, max_bytes=before // 2) is True
    after = tmp.stat().st_size
    assert after < before * 0.6 and len(pd.read_csv(tmp)) == 30000
    assert lw.trim_archive(tmp, max_bytes=before) is False        # already small enough -> untouched
    print(f"OK  archive cap: {before/1e6:.1f} MB -> {after/1e6:.1f} MB (oldest half dropped), small files untouched")


if __name__ == "__main__":
    test_demo_mode_never_scans_or_writes()
    test_archive_is_capped()
