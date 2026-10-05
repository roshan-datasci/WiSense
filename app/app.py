"""WiSense — Wi-Fi intelligence & analytics (Streamlit).

Every number comes from a real measurement:
  * nearby networks -> OS Wi-Fi scan of the machine running WiSense (Windows / Linux / macOS / Termux)
                       or a scan file imported from a phone
  * device quality  -> a probe running in the BROWSER of whichever device opens the page
                       (phone, tablet or laptop): latency, jitter, loss, real download speed
Nothing is simulated; missing measurements are shown as missing.
"""
from __future__ import annotations

import html
import re
import socket
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

APP_DIR = Path(__file__).resolve().parent
ROOT_DIR = APP_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from analysis import live_wifi as lw          # noqa: E402
from analysis import metrics as mx            # noqa: E402

try:
    from streamlit_geolocation import streamlit_geolocation
except ImportError:
    streamlit_geolocation = None

st.set_page_config(page_title="WiSense", page_icon="◉", layout="wide", initial_sidebar_state="collapsed")

ARCHIVE_DATASET = ROOT_DIR / "data" / "wifi_clustered.csv"
_probe_component = components.declare_component("wisense_probe", path=str(APP_DIR / "components" / "wisense_probe"))

st.html(f"<style>{(APP_DIR / 'theme.css').read_text(encoding='utf-8')}</style>")

_ST_VERSION = tuple(int(x) for x in re.findall(r"\d+", st.__version__)[:2])
_STRETCH = {"width": "stretch"} if _ST_VERSION >= (1, 50) else {"use_container_width": True}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def plot_layout(fig: go.Figure, height: int | None = None) -> go.Figure:
    kwargs = dict(paper_bgcolor="#070707", plot_bgcolor="#070707", font=dict(family="Courier New", color="#ffffff"),
                  legend=dict(font=dict(family="Courier New", color="#ffffff")), margin=dict(l=18, r=18, t=70, b=45),
                  title=dict(font=dict(size=15), x=0.01, xanchor="left", y=0.96, yanchor="top"))
    if height is not None:
        kwargs["height"] = height
    fig.update_layout(**kwargs)
    fig.update_xaxes(automargin=True)
    fig.update_yaxes(automargin=True)
    return fig


def show_fig(fig: go.Figure, key: str, height: int | None = None) -> None:
    plot_layout(fig, height)
    st.plotly_chart(fig, key=key, config={"displaylogo": False}, **_STRETCH)


def show_df(frame: pd.DataFrame, **kwargs) -> None:
    st.dataframe(frame, hide_index=True, **_STRETCH, **kwargs)


def section(title: str, subtitle: str = "", anchor: str = "") -> None:
    sub = f'<div class="section-subtitle">{subtitle}</div>' if subtitle else ""
    attr = f' id="{anchor}"' if anchor else ""
    st.html(f'<div class="section-title"{attr}>{title}</div>{sub}')


def callout(text: str, warn: bool = False) -> None:
    st.html(f'<div class="callout{" warn" if warn else ""}">{text}</div>')


def short(text, limit: int = 28) -> str:
    text = str(text)
    return text if len(text) <= limit else text[: limit - 1] + "…"


def unique_labels(labels) -> list[str]:
    seen: dict[str, int] = {}
    out = []
    for label in labels:
        seen[label] = seen.get(label, 0) + 1
        out.append(label if seen[label] == 1 else f"{label} ({seen[label]})")
    return out


def hbar(frame: pd.DataFrame, label_col: str, value_col: str, title: str, x_title: str, key: str,
         x_range=None, hover: list[str] | None = None, label_values=None) -> None:
    """Horizontal bar chart: long network names sit on the left and can never overlap anything."""
    data = frame.reset_index(drop=True).copy()
    source = label_values if label_values is not None else data[label_col]
    data["_label"] = unique_labels([short(v) for v in source])
    data["_full"] = [str(v) for v in source]
    data = data.iloc[::-1]
    fig = px.bar(data, x=value_col, y="_label", orientation="h", title=title, hover_name="_full",
                 hover_data={**{c: True for c in (hover or [])}, "_label": False, "_full": False})
    fig.update_yaxes(title="", automargin=True, categoryorder="array", categoryarray=list(data["_label"]))
    fig.update_xaxes(title=x_title, range=x_range)
    show_fig(fig, key, max(300, 30 * len(data) + 130))


def metric_card(label: str, value: str, *details: str) -> None:
    extra = "".join(f'<div class="metric-detail">{html.escape(d)}</div>' for d in details)
    st.html(f'<div class="metric-card"><div class="metric-label">{html.escape(label)}</div>'
            f'<div class="metric-value">{html.escape(str(value))}</div>{extra}</div>')


def fmt(value, digits: int = 1, unit: str = "") -> str:
    return "N/A" if value is None or pd.isna(value) else f"{value:.{digits}f}{unit}"


@st.cache_data(ttl=30, show_spinner=False)
def cached_archive() -> pd.DataFrame:
    return lw.load_archive()


def client_is_scan_host() -> bool | None:
    """True when the browser viewing the page runs on the same machine as the scanner."""
    ip = getattr(st.context, "ip_address", None)
    if not ip:
        return None
    if ip in {"127.0.0.1", "::1", "localhost"}:
        return True
    try:
        local = {info[4][0] for info in socket.getaddrinfo(socket.gethostname(), None)}
    except OSError:
        local = set()
    return ip in local


def imported_views() -> tuple[pd.DataFrame, pd.DataFrame]:
    frames = st.session_state.get("wisense_imported", [])
    if not frames:
        return pd.DataFrame(columns=lw.COLUMNS), pd.DataFrame(columns=lw.COLUMNS + ["scan_id"])
    parts, next_id = [], 0
    for frame in frames:
        part = frame.copy()
        minute = pd.to_datetime(part["timestamp"], errors="coerce").dt.floor("min")      # one scan per minute of data
        multi = minute.dropna().nunique() > 1
        part["scan_id"] = (pd.factorize(minute)[0] + next_id) if multi else next_id
        next_id = int(part["scan_id"].max()) + 1
        parts.append(part)
    history = lw.coerce_types(pd.concat(parts, ignore_index=True))
    return history[history["scan_id"] == history["scan_id"].max()][lw.COLUMNS].reset_index(drop=True), history


# ---------------------------------------------------------------------------
# HEADER / NAV / LIVE / TASK  (unchanged layout)
# ---------------------------------------------------------------------------

st.html("""
<div class="wisense-header">
  <div class="terminal-line">================================</div>
  <div class="terminal-name">WiSense</div>
  <div class="terminal-line">================================</div>
  <div class="wisense-subtitle">WI-FI INTELLIGENCE &amp; ANALYTICS</div>
</div>
""")
st.html("""
<div class="nav-row">
  <a class="nav-item active" href="#sec-overview" target="_self">[ OVERVIEW ]</a>
  <a class="nav-item" href="#sec-map" target="_self">[ MAP ]</a>
  <a class="nav-item" href="#sec-signal" target="_self">[ SIGNAL ]</a>
  <a class="nav-item" href="#sec-channels" target="_self">[ CHANNELS ]</a>
  <a class="nav-item" href="#sec-insights" target="_self">[ INSIGHTS ]</a>
</div>
""")
st.html("""
<div class="live-row"><div class="live-indicator"><span class="live-dot">●</span> LIVE</div></div>
""")
st.html('<div class="section-title">TASK SELECTOR</div>')
task = st.selectbox("Select network task", list(mx.TASK_WEIGHTS), label_visibility="collapsed")


# ---------------------------------------------------------------------------
# The whole live page is ONE fragment, so every section below refreshes together
# ---------------------------------------------------------------------------

def live_page(task: str) -> None:
    demo = lw.is_demo()
    host_match = None if demo else client_is_scan_host()

    # ===================== LOCAL WI-FI COLLECTOR =====================
    section("LOCAL WI-FI COLLECTOR",
            "REAL nearby Wi-Fi access points detected by this device. Measured SSIDs, BSSIDs, signal and channel values are read from the available Wi-Fi adapter.")

    sample_note = ""
    if demo:
        _, _, sample_note = lw.load_sample()
        callout(f"<b>DEMO MODE</b> — the network list below is {html.escape(sample_note)}. Live Wi-Fi scanning runs on your own computer "
                "(a web server has no Wi-Fi adapter). The speed &amp; latency test of <b>your device</b> is real, and you can upload your own scan file.")

    controls = st.columns([1.2, 1.2])
    with controls[0]:
        if st.button("SCAN NOW", key="wisense_scan_now", disabled=demo, **_STRETCH):
            st.session_state["_force_scan"] = True
    with controls[1]:
        auto_update = st.checkbox("AUTO UPDATE", value=not demo, key="wisense_auto_update", disabled=demo)

    extra = st.columns([1.2, 1.2])
    with extra[0]:
        probe_on = st.checkbox("MEASURE THIS DEVICE (speed & latency)", value=True, key="wisense_probe_on")
    with extra[1]:
        if st.button("RUN SPEED TEST", key="wisense_speed_btn", **_STRETCH):
            st.session_state["_speed_run_id"] = st.session_state.get("_speed_run_id", 0) + 1

    uploads = st.file_uploader("IMPORT A SCAN FROM A PHONE (optional) — JSON from Termux `termux-wifi-scaninfo`, or CSV with ssid / bssid / signal or rssi / channel or frequency",
                               type=["json", "csv"], accept_multiple_files=True, key="wisense_upload")
    imported = st.session_state.setdefault("wisense_imported", [])
    seen = st.session_state.setdefault("_imported_keys", set())
    for up in uploads or []:
        if (up.name, up.size) in seen:
            continue
        seen.add((up.name, up.size))
        try:
            frame = lw.import_scan_bytes(up.name, up.getvalue())
            if frame.empty:
                st.warning(f"{up.name}: no usable rows (needs an SSID plus signal or RSSI).")
            else:
                imported.append(frame)
        except Exception as exc:
            st.error(f"Could not read {up.name}: {exc}")
    use_imported = bool(imported) and st.checkbox("USE MY IMPORTED SCAN INSTEAD OF THE SAMPLE" if demo else "USE IMPORTED SCAN INSTEAD OF LIVE SCAN", value=True, key="wisense_use_imported")

    force = st.session_state.pop("_force_scan", False)
    error = None
    if use_imported:
        latest, history = imported_views()
        connected, conn_hist = {}, pd.DataFrame()
        now = latest["timestamp"].max() if not latest.empty else datetime.now()
    elif demo:
        latest, history, _ = lw.load_sample()
        connected, conn_hist = {}, pd.DataFrame()
        now = latest["timestamp"].max() if not latest.empty else datetime.now()
    else:
        _, error = lw.STORE.scan(min_interval=2.4 if auto_update else float("inf"), force=force)
        latest, history, connected, conn_hist = lw.STORE.snapshot()
        now = lw.STORE.last_scan_time or datetime.now()

    # --- browser probe: measures whichever device is viewing this page ---
    if probe_on:
        sample = _probe_component(enabled=True, interval_s=5, speed_every_s=0,
                                  run_id=st.session_state.get("_speed_run_id", 0), key="wisense_probe_component", default=None)
        samples = st.session_state.setdefault("wisense_probe_samples", [])
        if isinstance(sample, dict) and sample.get("seq") is not None:
            key = (sample.get("seq"), sample.get("client_time_ms"))
            if key != st.session_state.get("_probe_last_key"):
                st.session_state["_probe_last_key"] = key
                record = dict(sample)
                record["timestamp"] = datetime.now()
                record["signal_percent"] = connected.get("signal_percent") if (host_match and not use_imported and not demo) else None
                samples.append(record)
                del samples[:-500]
    probe = pd.DataFrame(st.session_state.get("wisense_probe_samples", []))

    run_id = st.session_state.get("_speed_run_id", 0)
    if run_id:
        started = st.session_state.setdefault("_speed_started", {}).setdefault(run_id, time.time())
        done = probe[probe["speed_run_id"] == run_id] if "speed_run_id" in probe else pd.DataFrame()
        if not probe_on:
            st.warning("Tick MEASURE THIS DEVICE above, then press RUN SPEED TEST again.")
        elif done.empty:
            if time.time() - started > 60:
                st.warning("The speed test did not report back. Refresh the page and press RUN SPEED TEST again.")
            else:
                st.info("RUNNING SPEED TEST on this device… this takes about 5–15 seconds.")
        else:
            res = done.iloc[-1]
            st.markdown(f"**SPEED TEST RESULT — {res['device']}** · {res['timestamp']:%H:%M:%S}")
            r1, r2, r3, r4 = st.columns(4)
            with r1:
                metric_card("LINK TO THIS WEBSITE" if demo else "WI-FI LINK TO HOST", fmt(res.get("local_mbps"), 1, " Mbps"),
                            "your device ⇄ the dashboard server" if demo else "device ⇄ computer running WiSense")
            with r2:
                metric_card("INTERNET DOWNLOAD", fmt(res.get("download_mbps"), 1, " Mbps"), "public speed-test server")
            with r3:
                metric_card("LATENCY", fmt(res.get("server_rtt_ms"), 1, " ms"), "round trip to the dashboard server" if demo else "round trip to the WiSense host")
            with r4:
                metric_card("JITTER / LOSS", f"{fmt(res.get('server_jitter_ms'), 1)} ms / {fmt(res.get('server_loss_pct'), 0, '%')}", "stability of the link")
            if res.get("speed_error"):
                st.warning(f"Part of the test could not run: {res['speed_error']}. A campus or office network often blocks public speed-test servers — "
                           "the Wi-Fi link result above is measured against the WiSense host and does not need internet access.")

    if error:
        st.error(f"Wi-Fi scan failed: {error}")
        st.caption("Check that the Wi-Fi adapter is enabled. On Windows also allow Location access. "
                   "The speed/latency measurement of this device below still works, and you can import a scan file from a phone.")
    if not demo and not use_imported and host_match is False and not probe.empty:
        st.caption(f"You are viewing from {probe.iloc[-1]['device']}. The network list is what the computer running WiSense "
                   f"({lw.host_label()}) can see — phone browsers are not allowed to scan Wi-Fi — while speed and latency below are measured on YOUR device.")

    count_aps = len(latest)
    network_count = int(latest["ssid"].nunique()) if count_aps else 0
    strongest = float(latest["signal_percent"].max()) if count_aps else None
    weakest = float(latest["signal_percent"].min()) if count_aps else None
    connected_signal = connected.get("signal_percent")

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("VISIBLE APs", count_aps)
    m2.metric("NETWORKS", network_count)
    m3.metric("CONNECTED", connected.get("ssid") or "NONE")
    m4.metric("CONNECTED SIGNAL", f"{connected_signal:.0f}%" if connected_signal is not None else "N/A")
    m5.metric("SIGNAL RANGE", f"{weakest:.0f}%–{strongest:.0f}%" if strongest is not None else "N/A")

    if latest.empty:
        if not error:
            st.warning("No nearby Wi-Fi access points were returned by the device scan.")
    else:
        summary = mx.ssid_summary(latest)[["SSID", "ACCESS POINTS", "BEST SIGNAL %", "AVG SIGNAL %", "CHANNELS"]]
        summary = summary.rename(columns={"AVG SIGNAL %": "AVERAGE SIGNAL %"})
        summary["BEST SIGNAL %"] = summary["BEST SIGNAL %"].round(0).astype(int)
        show_df(summary)

        for ssid, group in latest.groupby("ssid", dropna=False):
            with st.expander(f"{ssid} · {group['ap_id'].nunique()} access point(s)"):
                details = group[["bssid", "signal_percent", "channel", "band", "radio_type", "authentication", "encryption", "timestamp"]].copy()
                details.columns = ["BSSID", "SIGNAL %", "CHANNEL", "BAND", "RADIO", "AUTHENTICATION", "ENCRYPTION", "LAST SCAN"]
                details["SIGNAL %"] = details["SIGNAL %"].round(0).astype("Int64")
                show_df(details)

        hist_df = history.dropna(subset=["timestamp", "ssid", "signal_percent"]) if not history.empty else history
        if not hist_df.empty:
            per_scan = (hist_df.groupby(["scan_id", "ssid"]).agg(timestamp=("timestamp", "max"), signal_percent=("signal_percent", "max")).reset_index())
            fig = px.line(per_scan.sort_values("timestamp"), x="timestamp", y="signal_percent", color="ssid", markers=True,
                          title="REAL-TIME SIGNAL HISTORY — ACTUAL SSIDs")
            fig.update_yaxes(range=[0, 100], title="Measured signal (%)")
            show_fig(fig, "col_signal_hist", 420)

        c1, c2 = st.columns(2)
        with c1:
            counts = latest["channel"].dropna().astype(int).value_counts().sort_index().reset_index()
            counts.columns = ["channel", "access_points"]
            fig = px.bar(counts, x=counts["channel"].astype(str), y="access_points", title="LIVE CHANNEL DISTRIBUTION — ACTUAL SCAN",
                         labels={"x": "channel"})
            fig.update_yaxes(title="Access points")
            show_fig(fig, "col_channel_dist", 360)
        with c2:
            if not hist_df.empty:
                show_df(mx.ap_signal_stats(hist_df))

        if connected:
            rx, tx = connected.get("receive_rate"), connected.get("transmit_rate")
            link_text = f" | Link RX/TX: {rx if rx is not None else 'N/A'} / {tx if tx is not None else 'N/A'} Mbps" if (rx is not None or tx is not None) else ""
            st.caption(f"Connected interface: {connected.get('interface', 'Wi-Fi')} | SSID: {connected.get('ssid', 'NONE')} | "
                       f"Signal: {connected.get('signal_percent', 'N/A')}%{link_text} | Last scan: {now:%H:%M:%S}")

        if not history.empty:
            st.download_button("DOWNLOAD SCAN HISTORY (CSV)", history.drop(columns=["scan_id"], errors="ignore").to_csv(index=False),
                               file_name="wisense_scan_history.csv", mime="text/csv", key="dl_history")

    # ===================== DATA CHECK =====================
    if not ARCHIVE_DATASET.exists() and not demo:
        st.warning("Historical dataset not available. Live Wi-Fi analysis remains active; "
                   "place data/wifi_clustered.csv in the data folder to enable historical analysis.")

    # ===================== LIVE NETWORK OVERVIEW =====================
    section("LIVE NETWORK OVERVIEW", "Current analytical view of the real Wi-Fi environment detected by this device", "sec-overview")
    if not latest.empty:
        rx, tx = connected.get("receive_rate"), connected.get("transmit_rate")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            metric_card("NETWORKS DETECTED", network_count, "actual SSIDs in the latest scan")
        with col2:
            metric_card("ACCESS POINTS", latest["ap_id"].nunique(), "actual BSSIDs returned by the scan")
        with col3:
            metric_card("MEAN SIGNAL", f"{latest['signal_percent'].mean():.1f}%", "measured Wi-Fi signal percentage")
        with col4:
            rate = f"{rx:.1f}/{tx:.1f}" if isinstance(rx, (int, float)) and isinstance(tx, (int, float)) else (f"{tx:.1f}" if isinstance(tx, (int, float)) else "N/A")
            metric_card("LINK RX / TX", rate, "Mbps reported by the connected interface")
        for line in mx.overview_insights(latest, connected):
            st.markdown(f"- {line}")
    else:
        st.info("No live Wi-Fi measurements are available yet. Press SCAN NOW to collect real data.")

    # ===================== INTERACTIVE WI-FI MAP =====================
    section("INTERACTIVE WI-FI MAP",
            "Live Wi-Fi observations are placed at the actual device location when a real location fix is available. Wi-Fi scans do not contain GPS coordinates for individual routers.", "sec-map")
    if streamlit_geolocation is not None:
        try:
            browser_location = streamlit_geolocation()
            lat, lon = float(browser_location["latitude"]), float(browser_location["longitude"])
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                st.session_state["wisense_device_location"] = {"latitude": lat, "longitude": lon,
                                                               "accuracy_m": browser_location.get("accuracy"), "method": "Browser device geolocation"}
        except (TypeError, ValueError, KeyError):
            pass
    location = st.session_state.get("wisense_device_location")
    if location is None and not use_imported and not demo and host_match is not False:
        location = lw.get_device_location()
        if location:
            st.session_state["wisense_device_location"] = location

    if location is None:
        st.info("No exact device location is available yet. Press the location button above and allow location access in the browser/system. "
                "The map will then show where each real scan was taken.")
    else:
        log = st.session_state.setdefault("wisense_location_log", [])
        if not latest.empty:
            stamp = latest["timestamp"].max()
            moved = not log or abs(log[-1]["latitude"] - location["latitude"]) > 1e-5 or abs(log[-1]["longitude"] - location["longitude"]) > 1e-5
            fresh = not log or (stamp - log[-1]["time"]).total_seconds() >= 60
            if moved or fresh:
                top = latest.loc[latest["signal_percent"].idxmax()]
                log.append({"latitude": location["latitude"], "longitude": location["longitude"], "time": stamp,
                            "networks": int(latest["ssid"].nunique()), "strongest_ssid": top["ssid"], "strongest_signal": float(top["signal_percent"])})
                del log[:-300]
        points = pd.DataFrame(log) if log else pd.DataFrame([{**location, "time": datetime.now(), "networks": None,
                                                              "strongest_ssid": "THIS DEVICE", "strongest_signal": None}])
        fig = px.scatter_map(points, lat="latitude", lon="longitude", color="strongest_signal", zoom=16, color_continuous_scale="Turbo",
                             range_color=[0, 100], hover_name="strongest_ssid",
                             hover_data={"networks": True, "strongest_signal": ":.0f", "latitude": False, "longitude": False},
                             labels={"strongest_signal": "Strongest signal %"})
        fig.update_traces(marker=dict(size=15))
        fig.update_layout(map_style="carto-darkmatter", margin=dict(l=0, r=0, t=0, b=0), height=520, paper_bgcolor="#070707",
                          font=dict(family="Courier New", color="#ffffff"))
        st.plotly_chart(fig, key="map_main", config={"displaylogo": False}, **_STRETCH)
        acc = location.get("accuracy_m")
        st.caption(f"Location source: {location.get('method', 'device location')}{f' · accuracy ~{acc:.0f} m' if isinstance(acc, (int, float)) else ''}. "
                   "Each point is where a real scan was taken, coloured by the strongest signal measured there. Nearby router GPS positions are not available from a normal Wi-Fi scan.")

    # ===================== SIGNAL / NETWORK QUALITY =====================
    section("SIGNAL STRENGTH       NETWORK PERFORMANCE", "Current measured signal by the actual SSIDs detected in the latest scan", "sec-signal")
    if not latest.empty:
        by_ssid = (latest.groupby("ssid").agg(avg_signal=("signal_percent", "mean"), best_signal=("signal_percent", "max"),
                                              access_points=("ap_id", "nunique")).reset_index().sort_values("avg_signal", ascending=False))
        c1, c2 = st.columns(2)
        link_rows = [{"Metric": label, "Mbps": float(connected[k])} for k, label in
                     (("receive_rate", "Connected link receive rate"), ("transmit_rate", "Connected link transmit rate")) if connected.get(k) is not None]
        with c1:
            hbar(by_ssid, "ssid", "avg_signal", "AVERAGE SIGNAL STRENGTH — ACTUAL SCANNED SSIDs", "Measured signal (%)", "sig_avg_ssid",
                 x_range=[0, 100], hover=["best_signal", "access_points"])
        with c2:
            downloads = probe["download_mbps"].dropna() if "download_mbps" in probe else pd.Series(dtype=float)
            if link_rows:
                fig = px.bar(pd.DataFrame(link_rows), x="Metric", y="Mbps", title="CURRENT CONNECTED LINK RATE")
                show_fig(fig, "sig_link", 350)
            elif not downloads.empty:
                data = probe.dropna(subset=["download_mbps"])
                fig = px.bar(data, x="timestamp", y="download_mbps", title="MEASURED DOWNLOAD SPEED — THIS DEVICE")
                fig.update_yaxes(title="Mbps")
                show_fig(fig, "sig_download", 350)
            else:
                st.info("The Wi-Fi scan itself does not report internet speed. Press RUN SPEED TEST to measure this device's real download speed.")
    else:
        st.info("Run a live scan to display measured Wi-Fi signal by the actual SSID.")

    # ===================== WI-FI CHANNEL ANALYSIS =====================
    section("WI-FI CHANNEL ANALYSIS", "Channel and frequency analysis from the latest real Wi-Fi scan when available", "sec-channels")
    if not latest.empty and latest["channel"].notna().any():
        chan = mx.channel_summary(latest)
        fig = px.bar(chan, x=chan["channel"].astype(str), y="access_points", color="band", title="LIVE CHANNEL DISTRIBUTION — ACTUAL SCAN",
                     labels={"x": "channel"})
        fig.update_yaxes(title="Access points")
        show_fig(fig, "ch_dist", 350)
        freq = chan.dropna(subset=["frequency_mhz"])
        if not freq.empty:
            fig = px.bar(freq, x="frequency_mhz", y="access_points", color="band", title="LIVE FREQUENCY DISTRIBUTION — DERIVED FROM REPORTED CHANNEL")
            fig.update_xaxes(title="Center frequency (MHz)")
            fig.update_yaxes(title="Access points")
            show_fig(fig, "ch_freq", 350)
        for band in [b for b in ("2.4 GHz", "5 GHz", "6 GHz") if (latest["band"] == b).any()]:
            work = latest[(latest["band"] == band) & latest["frequency_mhz"].notna()]
            half = 11 if band == "2.4 GHz" else 10
            palette = px.colors.qualitative.Bold
            colours = {s: palette[i % len(palette)] for i, s in enumerate(sorted(work["ssid"].unique()))}
            spec, shown = go.Figure(), set()
            for _, ap in work.iterrows():
                f, s = ap["frequency_mhz"], ap["signal_percent"]
                spec.add_trace(go.Scatter(x=[f - half, f - half + 2, f + half - 2, f + half], y=[0, s, s, 0], mode="lines", fill="tozeroy",
                                          line=dict(color=colours[ap["ssid"]], width=2), opacity=0.55, name=ap["ssid"], legendgroup=ap["ssid"],
                                          showlegend=ap["ssid"] not in shown,
                                          hovertemplate=f"{ap['ssid']}<br>channel {ap['channel']} · {s:.0f}%<extra></extra>"))
                shown.add(ap["ssid"])
            if band == "2.4 GHz":
                spec.update_xaxes(range=[2397, 2487], tickvals=[2407 + 5 * c for c in range(1, 14)], ticktext=[str(c) for c in range(1, 14)])
            else:
                chans = sorted({int(c) for c in work["channel"].dropna()})
                spec.update_xaxes(range=[work["frequency_mhz"].min() - 40, work["frequency_mhz"].max() + 40],
                                  tickvals=[lw.channel_to_frequency_mhz(c, band) for c in chans], ticktext=[str(c) for c in chans])
            spec.update_xaxes(title="Channel")
            spec.update_yaxes(title="Signal (%)", range=[0, 100])
            spec.update_layout(title=f"{band.upper()} SPECTRUM — WHO IS ON WHICH CHANNEL")
            show_fig(spec, f"spec_{band}", 360)
        rec = mx.recommend_channels(latest)
        if not rec.empty:
            st.caption("Least-crowded channels at this location (interference = signal-weighted overlap with every access point in the scan):")
            show_df(rec)
    else:
        st.info("No Wi-Fi channel/frequency measurements are available yet. Run SCAN NOW to analyze the real nearby Wi-Fi environment.")

    # ===================== WI-FI ENVIRONMENT =====================
    section("WI-FI ENVIRONMENT", "Live nearby-network conditions from the latest actual scan; distances are estimated from signal, never invented.")
    if not latest.empty:
        env = (latest.groupby("ssid").agg(access_points=("ap_id", "nunique"), mean_signal=("signal_percent", "mean"),
                                          best_signal=("signal_percent", "max")).reset_index().sort_values("mean_signal", ascending=False))
        e1, e2 = st.columns(2)
        with e1:
            hbar(env.sort_values("access_points", ascending=False), "ssid", "access_points", "LIVE ACCESS POINTS BY ACTUAL SSID", "Access points",
                 "env_aps", hover=["mean_signal", "best_signal"])
        with e2:
            hbar(env, "ssid", "mean_signal", "LIVE MEAN SIGNAL BY ACTUAL SSID", "Measured signal (%)", "env_signal",
                 x_range=[0, 100], hover=["best_signal", "access_points"])
        clusters = mx.cluster_access_points(latest)
        e3, e4 = st.columns(2)
        with e3:
            overlap = clusters.sort_values("load", ascending=False).head(12) if not clusters.empty else clusters
            if not overlap.empty:
                overlap = overlap.assign(overlapping=[int(((latest["ap_id"] != r.ap_id) & (latest["band"] == r.band) & (latest["frequency_mhz"].sub(r.frequency_mhz).abs() < 25)).sum())
                                                       if r.band == "2.4 GHz" else int(((latest["ap_id"] != r.ap_id) & (latest["band"] == r.band) & (latest["frequency_mhz"] == r.frequency_mhz)).sum())
                                                       for r in overlap.itertuples()])
                labels = [f"{short(r.ssid, 20)} · ch{r.channel:.0f} · {str(r.bssid)[-5:] if pd.notna(r.bssid) else ''}" for r in overlap.itertuples()]
                hbar(overlap, "ssid", "overlapping", "CHANNEL OVERLAP PER ACCESS POINT", "Overlapping access points", "env_overlap",
                     hover=["load"], label_values=labels)
        with e4:
            if not clusters.empty:
                dist = clusters.dropna(subset=["est_distance_m"]).sort_values("est_distance_m").head(12)
                labels = [f"{short(r.ssid, 20)} · ch{r.channel:.0f} · {str(r.bssid)[-5:] if pd.notna(r.bssid) else ''}" for r in dist.itertuples()]
                hbar(dist, "ssid", "est_distance_m", "ESTIMATED DISTANCE TO ACCESS POINT (from signal)", "Distance (m, estimate)", "env_distance",
                     label_values=labels)
        st.caption("Wi-Fi scans cannot measure device counts or distance. Overlap is measured from channels; distance is a rough path-loss estimate.")
    else:
        st.info("Run SCAN NOW to populate the live Wi-Fi environment charts with actual SSIDs, access points and measured signal values.")

    # ===================== CONNECTION INTELLIGENCE =====================
    section("CONNECTION INTELLIGENCE", "Measured relationships on this device: connected signal vs real latency and speed")
    paired = probe.dropna(subset=["signal_percent"]) if "signal_percent" in probe else pd.DataFrame()
    metric_col = next((c for c in ("download_mbps", "server_rtt_ms") if c in paired and paired[c].notna().sum() >= 5), None)
    if metric_col:
        pts = paired.dropna(subset=[metric_col])
        fig = px.scatter(pts, x="signal_percent", y=metric_col, title="Connected signal vs measured " + metric_col.replace("_", " "),
                         labels={"signal_percent": "Connected signal (%)"})
        if len(pts) >= 8 and pts["signal_percent"].nunique() > 1:
            slope, intercept = np.polyfit(pts["signal_percent"], pts[metric_col], 1)
            xs = np.array([pts["signal_percent"].min(), pts["signal_percent"].max()])
            fig.add_trace(go.Scatter(x=xs, y=slope * xs + intercept, mode="lines", name="trend", line=dict(dash="dash")))
        show_fig(fig, "conn_intel", 420)
    else:
        st.info("This view needs 5+ speed/latency measurements taken on the computer that is scanning. Keep MEASURE THIS DEVICE on and open the dashboard on the scanning computer.")

    # ===================== PERFORMANCE RELATIONSHIPS =====================
    section("PERFORMANCE RELATIONSHIPS", "Signal vs channel overlap for every access point in the latest scan")
    clusters = mx.cluster_access_points(latest) if not latest.empty else pd.DataFrame()
    if not clusters.empty:
        fig = px.scatter(clusters, x="load", y="signal_percent", color="band", hover_name="ssid", hover_data=["channel", "bssid"],
                         title="Access-point signal vs channel interference load", labels={"load": "Interference load (overlapping signal)", "signal_percent": "Signal (%)"})
        fig.update_traces(marker=dict(size=12))
        show_fig(fig, "perf_rel", 400)
    else:
        st.info("Performance relationships need a scan with at least two access points.")

    # ===================== ML INSIGHTS =====================
    section("ML INSIGHTS", "K-Means connectivity clusters computed from the live scan (signal, channel overlap, band)", "sec-insights")
    if not clusters.empty:
        summary_c = (clusters.groupby("cluster").agg(observations=("cluster", "size"), avg_signal=("signal_percent", "mean"), avg_rssi=("rssi_dbm", "mean"),
                                                    avg_load=("load", "mean"), avg_distance=("est_distance_m", "mean")).reset_index())
        cc1, cc2 = st.columns([1, 2])
        with cc1:
            rows = "".join(f"<tr><td>{int(r.cluster)}</td><td>{int(r.observations)}</td><td>{r.avg_signal:.1f}</td><td>{r.avg_rssi:.1f}</td>"
                           f"<td>{r.avg_load:.2f}</td><td>{fmt(r.avg_distance, 1)}</td></tr>" for r in summary_c.itertuples())
            st.html(f'<div class="ml-table-wrapper"><table class="ml-table"><thead><tr><th>CLUSTER</th><th>OBS.</th><th>SIGNAL</th><th>RSSI</th>'
                    f'<th>LOAD</th><th>DIST.</th></tr></thead><tbody>{rows}</tbody></table></div>')
        with cc2:
            fig = px.bar(summary_c, x="cluster", y="avg_signal", title="Average signal by connectivity cluster")
            fig.update_xaxes(title="Cluster (0 = strongest)", type="category")
            fig.update_yaxes(title="Signal (%)", range=[0, 100])
            show_fig(fig, "ml_cluster", 330)
    else:
        st.info("Clustering needs a scan with at least two access points.")

    # ===================== TASK SUITABILITY =====================
    section("TASK SUITABILITY", "Task-aware network suitability based on WiSense scoring logic")
    ranked = mx.score_networks(latest, history, task)
    if ranked.empty:
        st.info("Network recommendation needs a live scan.")
    else:
        top = ranked.iloc[0]
        r1, r2 = st.columns([1, 2])
        with r1:
            metric_card("RECOMMENDED NETWORK", str(top["SSID"])[:30], f"TASK: {task.upper()}", f"SCORE: {top['SCORE']:.2f}/100 · {top['SUITABILITY']}")
        with r2:
            fig = px.bar(ranked.head(12).sort_values("SCORE"), x="SCORE", y="SSID", orientation="h", title=f"Network suitability — {task}")
            fig.update_xaxes(range=[0, 100], title="Suitability score")
            show_fig(fig, "suit", max(300, 30 * min(len(ranked), 12) + 110))
        st.caption("Heuristic from measured signal, stability, channel overlap and band — not a speed test.")

    # ===================== PERFORMANCE TRENDS =====================
    section("PERFORMANCE TRENDS", "Measured speed/latency of this device, and the live Wi-Fi signal trend below.")
    if not probe.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=probe["timestamp"], y=probe["server_rtt_ms"], name="Server RTT (ms)", mode="lines+markers"))
        fig.add_trace(go.Scatter(x=probe["timestamp"], y=probe["server_jitter_ms"], name="Jitter (ms)", mode="lines+markers"))
        if probe["internet_rtt_ms"].notna().any():
            fig.add_trace(go.Scatter(x=probe["timestamp"], y=probe["internet_rtt_ms"], name="Internet RTT (ms)", mode="lines+markers"))
        fig.update_layout(title=f"LATENCY & JITTER OVER TIME — {str(probe.iloc[-1]['device']).upper()}", yaxis_title="Milliseconds", xaxis_title="Measured at")
        show_fig(fig, "trend_latency", 400)
        last = probe.iloc[-1]
        if last.get("conn_type") == "cellular":
            st.warning("This device reports a cellular connection — these numbers describe mobile data, not Wi-Fi.")
        st.caption(f"Browser-measured on {last['device']} · {len(probe)} measurement(s) · connection: {last.get('conn_type') or last.get('effective_type') or 'not exposed'} · "
                   f"packet loss to server {fmt(last.get('server_loss_pct'), 0, '%')}.")
    else:
        st.info("Waiting for the first measurement from this device's browser (enable MEASURE THIS DEVICE).")
    tests = probe.dropna(subset=["speed_run_id"]) if "speed_run_id" in probe else pd.DataFrame()
    if not tests.empty:
        cols = [c for c in ("local_mbps", "download_mbps") if c in tests]
        melted = tests.melt(id_vars="timestamp", value_vars=cols, var_name="test", value_name="Mbps").dropna()
        melted["test"] = melted["test"].map({"local_mbps": "Wi-Fi link to host", "download_mbps": "Internet download"})
        if not melted.empty:
            fig = px.bar(melted, x="timestamp", y="Mbps", color="test", barmode="group", title="SPEED TESTS — THIS DEVICE")
            fig.update_xaxes(title="Measured at")
            show_fig(fig, "trend_speed", 340)
    if not history.empty and history["scan_id"].nunique() >= 1:
        per_scan = history.groupby(["scan_id", "ssid"]).agg(timestamp=("timestamp", "max"), signal_percent=("signal_percent", "max")).reset_index()
        fig = px.line(per_scan.sort_values("timestamp"), x="timestamp", y="signal_percent", color="ssid", markers=True,
                      title="LIVE WI-FI SIGNAL TREND — ACTUAL SSIDs")
        fig.update_yaxes(range=[0, 100], title="Measured signal (%)")
        fig.update_xaxes(title="Actual scan event time")
        show_fig(fig, "trend_signal", 420)
        st.caption(f"Latest real Wi-Fi scan event: {history['timestamp'].max():%Y-%m-%d %H:%M:%S} · {history['ssid'].nunique()} actual SSID(s) · {history['ap_id'].nunique()} actual access point(s)")
    else:
        st.info("No live Wi-Fi trend is available yet. Enable AUTO UPDATE or press SCAN NOW to collect timestamped signal measurements.")
    if ARCHIVE_DATASET.exists():
        st.caption("An archived dataset exists in data/wifi_clustered.csv. It is not live data and is not mixed into the charts above.")

    # ===================== ADVANCED ANALYTICS COMPLETE =====================
    section("ADVANCED ANALYTICS COMPLETE",
            "Eleven analytical views built only from measurements that are actually available: live Wi-Fi scans, the saved scan archive and this device's speed/latency probe.")
    archive = cached_archive() if not (use_imported or demo) else pd.DataFrame(columns=lw.COLUMNS)
    parts = [p for p in (archive, history[lw.COLUMNS] if not history.empty else None) if p is not None and not p.empty]
    long_hist = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=lw.COLUMNS)
    if not long_hist.empty:
        long_hist = lw.coerce_types(long_hist).dropna(subset=["timestamp"]).drop_duplicates(subset=["timestamp", "ap_id"])

    st.markdown("**1. Overall performance**")
    if latest.empty:
        st.caption("No scan yet.")
    else:
        s = latest["signal_percent"]
        show_df(pd.DataFrame([{"VISIBLE APs": len(latest), "NETWORKS": latest["ssid"].nunique(), "MEAN SIGNAL %": round(s.mean(), 1),
                               "MEDIAN SIGNAL %": round(s.median(), 1), "STRONGEST %": s.max(), "WEAKEST %": s.min()}]))

    st.markdown("**2. Network performance**")
    if not latest.empty:
        show_df(mx.ssid_summary(latest))

    st.markdown("**3. Performance correlations**")
    if not latest.empty:
        show_df(latest.groupby("band")["signal_percent"].agg(access_points="size", mean_signal="mean", strongest="max").round(1).reset_index().rename(columns=str.upper))
    if "signal_percent" in probe and probe["signal_percent"].notna().sum() >= 5:
        cols = [c for c in ["signal_percent", "server_rtt_ms", "internet_rtt_ms", "download_mbps"] if probe[c].notna().sum() >= 5]
        if len(cols) >= 2:
            st.dataframe(probe[cols].corr().round(3), **_STRETCH)
    else:
        st.caption("Signal-vs-latency/speed correlation needs 5+ measurements taken on the scanning computer itself.")

    st.markdown("**4. Signal analysis**")
    show_df(mx.ap_signal_stats(history))

    st.markdown("**5. Distance analysis (ESTIMATED)**")
    if not clusters.empty:
        show_df(clusters[["ssid", "band", "channel", "signal_percent", "rssi_dbm", "est_distance_m"]].sort_values("est_distance_m")
                .rename(columns={"est_distance_m": "EST. DISTANCE (m)"}))
        st.caption("Wi-Fi scans do not measure distance. This is a path-loss estimate only.")
    else:
        st.caption("Needs a scan.")

    st.markdown("**6. Device congestion analysis (channel overlap)**")
    if not latest.empty:
        show_df(mx.ap_congestion(latest).head(15))
        st.caption("Connected-device counts cannot be read from a nearby-network scan, so congestion is measured as channel overlap between access points.")

    st.markdown("**7. Hourly performance**")
    hourly_ok = not long_hist.empty and long_hist["timestamp"].dt.floor("h").nunique() >= 2
    if hourly_ok:
        hourly = long_hist.assign(hour=long_hist["timestamp"].dt.hour).groupby("hour").agg(
            observations=("signal_percent", "size"), mean_signal=("signal_percent", "mean"), distinct_access_points=("ap_id", "nunique")).round(1).reset_index()
        show_df(hourly)
    else:
        st.caption("Needs scans from at least two different hours. Leave WiSense running — scans are saved to data/live_wifi_history.csv.")

    st.markdown("**8. Peak period analysis**")
    if hourly_ok:
        peak, low, busy = hourly.loc[hourly["mean_signal"].idxmax()], hourly.loc[hourly["mean_signal"].idxmin()], hourly.loc[hourly["distinct_access_points"].idxmax()]
        st.caption(f"Observed strongest average signal: {int(peak['hour']):02d}:00 ({peak['mean_signal']:.1f}%). Weakest: {int(low['hour']):02d}:00 ({low['mean_signal']:.1f}%). "
                   f"Most access points seen: {int(busy['hour']):02d}:00 ({int(busy['distinct_access_points'])}). Observed values only — no forecasting.")
    else:
        st.caption("Peak periods are reported only from observed hours; not enough yet.")

    st.markdown("**9. Rolling performance**")
    if not history.empty and history["scan_id"].nunique() >= 2:
        roll = history.groupby("scan_id").agg(timestamp=("timestamp", "max"), strongest=("signal_percent", "max"), mean=("signal_percent", "mean")).reset_index()
        roll["strongest (rolling 5)"] = roll["strongest"].rolling(5, min_periods=1).mean()
        roll["mean (rolling 5)"] = roll["mean"].rolling(5, min_periods=1).mean()
        show_fig(px.line(roll, x="timestamp", y=["strongest", "strongest (rolling 5)", "mean", "mean (rolling 5)"],
                         labels={"value": "Signal %", "timestamp": "Scan time", "variable": ""}), "adv_roll", 300)
    else:
        st.caption("Needs 2+ scans.")

    st.markdown("**10. Performance extremes**")
    rows = []
    if not long_hist.empty:
        for col, label in (("signal_percent", "SIGNAL %"), ("rssi_dbm", "RSSI dBm")):
            v = pd.to_numeric(long_hist[col], errors="coerce").dropna()
            if not v.empty:
                rows.append({"METRIC": label, "MIN": v.min(), "MAX": v.max(), "MEAN": v.mean()})
    for col, label in (("server_rtt_ms", "SERVER RTT ms"), ("internet_rtt_ms", "INTERNET RTT ms"), ("download_mbps", "DOWNLOAD Mbps")):
        v = probe[col].dropna() if col in probe else pd.Series(dtype=float)
        if not v.empty:
            rows.append({"METRIC": label, "MIN": v.min(), "MAX": v.max(), "MEAN": v.mean()})
    for col, label in (("receive_rate", "LINK RX Mbps"), ("transmit_rate", "LINK TX Mbps")):
        v = pd.to_numeric(conn_hist[col], errors="coerce").dropna() if col in conn_hist else pd.Series(dtype=float)
        if not v.empty:
            rows.append({"METRIC": label, "MIN": v.min(), "MAX": v.max(), "MEAN": v.mean()})
    if rows:
        show_df(pd.DataFrame(rows).round(2))
    else:
        st.caption("No measurements yet.")

    st.markdown("**11. Analytics data quality**")
    if long_hist.empty:
        st.caption("No data yet.")
    else:
        quality = pd.DataFrame({"FIELD": long_hist.columns, "MISSING": [int(long_hist[c].isna().sum()) for c in long_hist.columns],
                                "MISSING %": [round(float(long_hist[c].isna().mean() * 100), 1) for c in long_hist.columns]})
        show_df(quality)
        st.caption(f"{len(long_hist):,} observations · {long_hist['ap_id'].nunique()} access points · {long_hist['timestamp'].nunique()} scan timestamps · "
                   f"{int((long_hist['ssid'] == lw.HIDDEN_SSID).sum())} hidden-SSID rows · {long_hist['timestamp'].min():%Y-%m-%d %H:%M} → {long_hist['timestamp'].max():%Y-%m-%d %H:%M} · "
                   f"sources: {', '.join(sorted(map(str, long_hist['source'].dropna().unique()))) or 'n/a'}")


st.fragment(run_every=None if lw.is_demo() else "3s")(live_page)(task)

# ---------------------------------------------------------------------------
# FOOTER
# ---------------------------------------------------------------------------

st.html("""
<div class="wisense-footer">
  WISENSE · WI-FI INTELLIGENCE &amp; ANALYTICS · STREAMLIT INTERFACE · LIVE MEASUREMENTS
</div>
""")
