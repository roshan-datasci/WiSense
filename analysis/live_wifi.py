"""Cross-platform live Wi-Fi collection for WiSense.

Only values that the operating system actually reports are recorded. Nothing is
simulated: no invented SSIDs, no invented speeds, no invented router positions.

Supported scan sources
----------------------
* Windows        -> ``netsh wlan show networks mode=bssid`` (+ a WlanScan refresh)
* Linux          -> ``nmcli dev wifi list`` (NetworkManager)
* macOS          -> ``system_profiler SPAirPortDataType -json``
* Android        -> ``termux-wifi-scaninfo`` (Termux:API) or an imported JSON/CSV file
* Any device     -> ``import_scan_bytes`` accepts a scan exported from a phone app

A phone *browser* cannot list nearby networks (iOS and Android both block it for
web pages), so phones are handled through the browser probe in the app plus the
file import above.
"""
from __future__ import annotations

import io
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
HISTORY_PATH = DATA_DIR / "live_wifi_history.csv"

COLUMNS = [
    "timestamp", "ssid", "bssid", "ap_id", "authentication", "encryption",
    "signal_percent", "rssi_dbm", "radio_type", "band", "channel",
    "frequency_mhz", "source",
]

HIDDEN_SSID = "(Hidden network)"
MAX_SCANS_IN_MEMORY = 400          # per-scan history kept in RAM
PERSIST_EVERY_SECONDS = 30         # CSV is appended at most this often
MAX_ARCHIVE_BYTES = 5 * 1024 * 1024  # archive is trimmed (oldest rows dropped) beyond this size
SAMPLE_PATH = DATA_DIR / "sample_scan.csv"


# ---------------------------------------------------------------------------
# Unit conversions
# ---------------------------------------------------------------------------

def pct_to_dbm(percent: float) -> float:
    """Windows/NetworkManager quality % -> approximate dBm (standard linear map)."""
    return float(percent) / 2.0 - 100.0


def dbm_to_pct(dbm: float) -> float:
    return float(max(0.0, min(100.0, 2.0 * (float(dbm) + 100.0))))


def channel_to_frequency_mhz(channel: Any, band: Any = None) -> float | None:
    """Centre frequency from channel number (+ band text when the OS gives it)."""
    try:
        ch = int(channel)
    except (TypeError, ValueError):
        return None
    text = str(band or "").lower().replace(" ", "")
    if ch == 14:
        return 2484.0
    if "2.4" in text or "2,4" in text:
        return float(2407 + 5 * ch)
    if "6ghz" in text:
        return float(5950 + 5 * ch)
    if "5ghz" in text:
        return float(5000 + 5 * ch)
    if 1 <= ch <= 13:
        return float(2407 + 5 * ch)
    if 32 <= ch <= 177:
        return float(5000 + 5 * ch)
    return None


def frequency_to_channel(freq_mhz: Any) -> int | None:
    try:
        f = float(freq_mhz)
    except (TypeError, ValueError):
        return None
    if f == 2484:
        return 14
    if 2400 <= f < 2500:
        return int(round((f - 2407) / 5))
    if 5000 <= f < 5900:
        return int(round((f - 5000) / 5))
    if 5925 <= f <= 7125:
        return int(round((f - 5950) / 5))
    return None


def band_from_frequency(freq_mhz: Any) -> str | None:
    try:
        f = float(freq_mhz)
    except (TypeError, ValueError):
        return None
    if 2400 <= f < 2500:
        return "2.4 GHz"
    if 4900 <= f < 5900:
        return "5 GHz"
    if 5925 <= f <= 7125:
        return "6 GHz"
    return None


def band_of_row(frequency_mhz: Any, band: Any, channel: Any) -> str:
    """Best-effort band label for display/analysis."""
    from_freq = band_from_frequency(frequency_mhz)
    if from_freq:
        return from_freq
    text = str(band or "").lower().replace(" ", "")
    if "2.4" in text:
        return "2.4 GHz"
    if "6ghz" in text:
        return "6 GHz"
    if "5ghz" in text:
        return "5 GHz"
    return band_from_frequency(channel_to_frequency_mhz(channel, band)) or "Unknown"


def signal_state(percent: float) -> str:
    value = float(percent)
    if value >= 80:
        return "EXCELLENT"
    if value >= 60:
        return "GOOD"
    if value >= 40:
        return "FAIR"
    return "WEAK"


# ---------------------------------------------------------------------------
# Normalisation shared by every platform
# ---------------------------------------------------------------------------

def _isnull(value: Any) -> bool:
    return value is None or (isinstance(value, float) and value != value)


def _finalize(rows: list[dict[str, Any]], source: str, timestamp: datetime | None = None) -> pd.DataFrame:
    """Turn raw per-AP dicts into the canonical WiSense frame."""
    stamp = timestamp or datetime.now()
    out: list[dict[str, Any]] = []
    for row in rows:
        ssid = (row.get("ssid") or "").strip() or HIDDEN_SSID
        bssid = (row.get("bssid") or "").strip().lower() or None
        channel, freq = row.get("channel"), row.get("frequency_mhz")
        pct, rssi = row.get("signal_percent"), row.get("rssi_dbm")
        channel = None if _isnull(channel) else channel
        freq = None if _isnull(freq) else freq
        pct = None if _isnull(pct) else pct
        rssi = None if _isnull(rssi) else rssi

        if channel is None and freq is not None:
            channel = frequency_to_channel(freq)
        if freq is None and channel is not None:
            freq = channel_to_frequency_mhz(channel, row.get("band"))
        if pct is None and rssi is not None:
            pct = dbm_to_pct(rssi)
        if rssi is None and pct is not None:
            rssi = pct_to_dbm(pct)
        if pct is None:
            continue

        ch_int = int(channel) if channel is not None else None
        out.append({
            "timestamp": row.get("timestamp", stamp),
            "ssid": ssid,
            "bssid": bssid,
            "ap_id": bssid or f"{ssid}|ch{ch_int if ch_int is not None else '?'}",
            "authentication": row.get("authentication") or "Unknown",
            "encryption": row.get("encryption") or "Unknown",
            "signal_percent": float(pct),
            "rssi_dbm": float(rssi) if rssi is not None else None,
            "radio_type": row.get("radio_type"),
            "band": band_of_row(freq, row.get("band"), ch_int),
            "channel": ch_int,
            "frequency_mhz": float(freq) if freq is not None else None,
            "source": source,
        })
    frame = pd.DataFrame(out, columns=COLUMNS)
    if not frame.empty:
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce")
    return frame


# ---------------------------------------------------------------------------
# Process helper
# ---------------------------------------------------------------------------

def _run(cmd: list[str], timeout: int = 20) -> str:
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=timeout, check=False,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(f"'{cmd[0]}' was not found on this system.") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"'{cmd[0]}' timed out after {timeout} seconds.") from exc
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout or f"{cmd[0]} failed").strip())
    return result.stdout


def _text_after(pattern: str, line: str) -> str | None:
    match = re.match(pattern, line, re.IGNORECASE)
    return match.group(1).strip() if match else None


# ---------------------------------------------------------------------------
# Windows
# ---------------------------------------------------------------------------

def parse_netsh_bssid_output(output: str, timestamp: str | None = None) -> pd.DataFrame:
    """Parse ``netsh wlan show networks mode=bssid`` into one row per BSSID."""
    stamp = pd.to_datetime(timestamp).to_pydatetime() if timestamp else datetime.now()
    rows: list[dict[str, Any]] = []
    ssid = authentication = encryption = None
    current: dict[str, Any] | None = None

    def commit() -> None:
        nonlocal current
        if current:
            rows.append({"ssid": ssid, "authentication": authentication,
                         "encryption": encryption, **current})
            current = None

    for line in output.splitlines():
        m = re.match(r"\s*SSID\s+\d+\s*:\s*(.*)", line, re.IGNORECASE)
        if m:
            commit()
            ssid = m.group(1).strip() or HIDDEN_SSID
            authentication = encryption = None
            continue
        value = _text_after(r"\s*Authentication\s*:\s*(.*)", line)
        if value is not None:
            authentication = value
            continue
        value = _text_after(r"\s*Encryption\s*:\s*(.*)", line)
        if value is not None:
            encryption = value
            continue
        value = _text_after(r"\s*BSSID\s+\d+\s*:\s*(.*)", line)
        if value is not None:
            commit()
            current = {"bssid": value}
            continue
        if current is None:
            continue
        value = _text_after(r"\s*Signal\s*:\s*(\d+)\s*%", line)
        if value is not None:
            current["signal_percent"] = int(value)
            continue
        value = _text_after(r"\s*Radio type\s*:\s*(.*)", line)
        if value is not None:
            current["radio_type"] = value
            continue
        value = _text_after(r"\s*Band\s*:\s*(.*)", line)
        if value is not None:
            current["band"] = value
            continue
        value = _text_after(r"\s*Channel\s*:\s*(\d+)", line)
        if value is not None:
            current["channel"] = int(value)
    commit()
    return _finalize(rows, "windows-netsh", stamp)


def _windows_trigger_scan() -> bool:
    """Ask the Windows WLAN service for a *fresh* scan (netsh alone returns a cache)."""
    if os.name != "nt":
        return False
    try:
        import ctypes
        from ctypes import wintypes

        wlanapi = ctypes.WinDLL("wlanapi")

        class GUID(ctypes.Structure):
            _fields_ = [("Data1", ctypes.c_ulong), ("Data2", ctypes.c_ushort),
                        ("Data3", ctypes.c_ushort), ("Data4", ctypes.c_ubyte * 8)]

        class WLAN_INTERFACE_INFO(ctypes.Structure):
            _fields_ = [("InterfaceGuid", GUID),
                        ("strInterfaceDescription", ctypes.c_wchar * 256),
                        ("isState", ctypes.c_ulong)]

        class WLAN_INTERFACE_INFO_LIST(ctypes.Structure):
            _fields_ = [("dwNumberOfItems", ctypes.c_ulong), ("dwIndex", ctypes.c_ulong),
                        ("InterfaceInfo", WLAN_INTERFACE_INFO * 1)]

        handle = wintypes.HANDLE()
        negotiated = wintypes.DWORD()
        if wlanapi.WlanOpenHandle(2, None, ctypes.byref(negotiated), ctypes.byref(handle)) != 0:
            return False
        try:
            plist = ctypes.POINTER(WLAN_INTERFACE_INFO_LIST)()
            if wlanapi.WlanEnumInterfaces(handle, None, ctypes.byref(plist)) != 0:
                return False
            try:
                ok = False
                base = ctypes.addressof(plist.contents.InterfaceInfo)
                for i in range(plist.contents.dwNumberOfItems):
                    info = WLAN_INTERFACE_INFO.from_address(base + i * ctypes.sizeof(WLAN_INTERFACE_INFO))
                    if wlanapi.WlanScan(handle, ctypes.byref(info.InterfaceGuid), None, None, None) == 0:
                        ok = True
                return ok
            finally:
                wlanapi.WlanFreeMemory(plist)
        finally:
            wlanapi.WlanCloseHandle(handle, None)
    except Exception:
        return False


_WINDOWS_PRIMED = False


def _scan_windows() -> pd.DataFrame:
    global _WINDOWS_PRIMED
    if not _WINDOWS_PRIMED:
        _WINDOWS_PRIMED = True
        if _windows_trigger_scan():
            time.sleep(2.5)       # first call only: give the adapter time to scan
    try:
        output = _run(["netsh", "wlan", "show", "networks", "mode=bssid"], timeout=15)
    except RuntimeError as exc:
        message = str(exc)
        if re.search(r"location|elevation", message, re.I):
            message += (" — Open Windows Settings > Privacy & security > Location and turn on "
                        "Location services and 'Let desktop apps access your location'.")
        raise RuntimeError(message) from exc
    frame = parse_netsh_bssid_output(output)
    _windows_trigger_scan()       # refresh the cache so the *next* call is fresh
    return frame


def _connected_windows() -> dict[str, Any]:
    output = _run(["netsh", "wlan", "show", "interfaces"], timeout=15)
    result: dict[str, Any] = {}
    patterns = {
        "interface": r"\s*Name\s*:\s*(.*)",
        "ssid": r"\s*SSID\s*:\s*(.*)",
        "bssid": r"\s*(?:AP )?BSSID\s*:\s*(.*)",
        "signal_percent": r"\s*Signal\s*:\s*(\d+)\s*%",
        "radio_type": r"\s*Radio type\s*:\s*(.*)",
        "channel": r"\s*Channel\s*:\s*(\d+)",
        "receive_rate": r"\s*Receive rate \(Mbps\)\s*:\s*([\d.]+)",
        "transmit_rate": r"\s*Transmit rate \(Mbps\)\s*:\s*([\d.]+)",
    }
    for line in output.splitlines():
        for key, pattern in patterns.items():
            value = _text_after(pattern, line)
            if value is None:
                continue
            if key in {"receive_rate", "transmit_rate"}:
                result[key] = float(value)
            elif key in {"signal_percent", "channel"}:
                result[key] = int(value)
            else:
                result.setdefault(key, value)
            break
    return result


# ---------------------------------------------------------------------------
# Linux (NetworkManager)
# ---------------------------------------------------------------------------

def _split_nmcli(line: str) -> list[str]:
    parts = re.split(r"(?<!\\):", line)
    return [p.replace("\\:", ":").replace("\\\\", "\\") for p in parts]


def parse_nmcli_output(output: str, timestamp: datetime | None = None) -> pd.DataFrame:
    """Parse ``nmcli -t -f IN-USE,SSID,BSSID,CHAN,FREQ,RATE,SIGNAL,SECURITY dev wifi list``."""
    rows: list[dict[str, Any]] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        fields = _split_nmcli(line)
        if len(fields) < 8:
            continue
        _in_use, ssid, bssid, chan, freq, _rate, signal, security = fields[:8]
        freq_val = re.match(r"\s*(\d+)", freq)
        rows.append({
            "ssid": ssid,
            "bssid": bssid,
            "channel": int(chan) if chan.strip().isdigit() else None,
            "frequency_mhz": float(freq_val.group(1)) if freq_val else None,
            "signal_percent": int(signal) if signal.strip().isdigit() else None,
            "authentication": security.strip() or "Open",
            "encryption": security.strip() or "None",
        })
    return _finalize(rows, "linux-nmcli", timestamp)


def _scan_linux() -> pd.DataFrame:
    if not shutil.which("nmcli"):
        raise RuntimeError("NetworkManager 'nmcli' is not installed. Install it (e.g. `sudo apt install network-manager`).")
    output = _run(["nmcli", "-t", "-f", "IN-USE,SSID,BSSID,CHAN,FREQ,RATE,SIGNAL,SECURITY",
                   "dev", "wifi", "list", "--rescan", "yes"], timeout=25)
    return parse_nmcli_output(output)


def _connected_linux() -> dict[str, Any]:
    result: dict[str, Any] = {}
    try:
        output = _run(["nmcli", "-t", "-f", "IN-USE,SSID,BSSID,CHAN,FREQ,SIGNAL", "dev", "wifi", "list"], timeout=15)
    except RuntimeError:
        return result
    for line in output.splitlines():
        fields = _split_nmcli(line)
        if len(fields) >= 6 and fields[0].strip() == "*":
            result.update({
                "ssid": fields[1], "bssid": fields[2],
                "channel": int(fields[3]) if fields[3].isdigit() else None,
                "signal_percent": int(fields[5]) if fields[5].isdigit() else None,
            })
            break
    if shutil.which("iw") and result:
        try:
            dev = _run(["nmcli", "-t", "-f", "DEVICE,TYPE,STATE", "dev"], timeout=10)
            iface = next((l.split(":")[0] for l in dev.splitlines() if ":wifi:connected" in l), None)
            if iface:
                result["interface"] = iface
                link = _run(["iw", "dev", iface, "link"], timeout=10)
                for key, pat in (("receive_rate", r"rx bitrate:\s*([\d.]+)"), ("transmit_rate", r"tx bitrate:\s*([\d.]+)")):
                    m = re.search(pat, link)
                    if m:
                        result[key] = float(m.group(1))
        except RuntimeError:
            pass
    return result


# ---------------------------------------------------------------------------
# macOS
# ---------------------------------------------------------------------------

def _mac_security(text: str | None) -> str:
    raw = (text or "").replace("spairport_security_mode_", "").replace("_", " ").strip()
    return raw.title().replace("Wpa", "WPA").replace("Wep", "WEP") or "Unknown"


def parse_macos_profiler(output: str, timestamp: datetime | None = None) -> tuple[pd.DataFrame, dict[str, Any]]:
    data = json.loads(output)
    rows: list[dict[str, Any]] = []
    connected: dict[str, Any] = {}
    try:
        interfaces = data["SPAirPortDataType"][0]["spairport_airport_interfaces"]
    except (KeyError, IndexError, TypeError):
        return _finalize([], "macos-system_profiler", timestamp), connected

    def make_row(item: dict[str, Any]) -> dict[str, Any]:
        channel_text = str(item.get("spairport_network_channel", ""))
        ch = re.match(r"\s*(\d+)", channel_text)
        band = re.search(r"(2|5|6)\s*GHz", channel_text)
        sig = re.search(r"(-?\d+)\s*dBm", str(item.get("spairport_signal_noise", "")))
        name = item.get("_name") or ""
        if name.strip().lower() in {"<redacted>", "redacted"}:
            name = ""
        security = _mac_security(item.get("spairport_security_mode") or item.get("spairport_network_security_mode"))
        return {
            "ssid": name, "bssid": None,
            "channel": int(ch.group(1)) if ch else None,
            "band": {"2": "2.4 GHz", "5": "5 GHz", "6": "6 GHz"}.get(band.group(1)) if band else None,
            "rssi_dbm": float(sig.group(1)) if sig else None,
            "radio_type": item.get("spairport_network_phymode"),
            "authentication": security, "encryption": security,
        }

    for iface in interfaces:
        current = iface.get("spairport_current_network_information")
        if isinstance(current, dict):
            row = make_row(current)
            rows.append(row)
            connected = {
                "interface": iface.get("_name", "Wi-Fi"), "ssid": row["ssid"] or None,
                "channel": row["channel"], "radio_type": row["radio_type"],
                "signal_percent": dbm_to_pct(row["rssi_dbm"]) if row["rssi_dbm"] is not None else None,
                "transmit_rate": float(current["spairport_network_rate"]) if current.get("spairport_network_rate") else None,
            }
        for item in iface.get("spairport_airport_other_local_wireless_networks", []) or []:
            if isinstance(item, dict):
                rows.append(make_row(item))
    return _finalize(rows, "macos-system_profiler", timestamp), connected


_MAC_CACHE: dict[str, Any] = {}


def _scan_macos() -> pd.DataFrame:
    output = _run(["system_profiler", "SPAirPortDataType", "-json"], timeout=40)
    frame, connected = parse_macos_profiler(output)
    _MAC_CACHE["connected"] = connected
    if not frame.empty and (frame["ssid"] == HIDDEN_SSID).all():
        raise RuntimeError("macOS returned only redacted network names. Grant Location Services to your terminal "
                           "(System Settings > Privacy & Security > Location Services).")
    return frame


# ---------------------------------------------------------------------------
# Android (Termux:API) and imported files
# ---------------------------------------------------------------------------

def _first(item: dict[str, Any], *keys: str) -> Any:
    lowered = {str(k).lower(): v for k, v in item.items()}
    for key in keys:
        value = lowered.get(key.lower())
        if value not in (None, "") and not _isnull(value):
            return value
    return None


def _num(value: Any) -> float | None:
    if value is None or _isnull(value):
        return None
    match = re.search(r"-?\d+(?:\.\d+)?", str(value))
    return float(match.group(0)) if match else None


def _rows_from_records(records: list[dict[str, Any]], use_timestamp: bool = True) -> list[dict[str, Any]]:
    rows = []
    for item in records:
        if not isinstance(item, dict):
            continue
        rssi = _num(_first(item, "rssi", "rssi_dbm", "level", "signal_dbm"))
        pct = _num(_first(item, "signal_percent", "signal", "quality", "signal %"))
        if pct is not None and pct < 0:          # a column called "signal" that holds dBm
            rssi, pct = pct, None
        freq = _num(_first(item, "frequency_mhz", "frequency", "freq", "freq_mhz"))
        chan = _num(_first(item, "channel", "chan"))
        security = _first(item, "authentication", "security", "capabilities", "auth")
        row = {
            "ssid": str(_first(item, "ssid", "name", "network") or ""),
            "bssid": str(_first(item, "bssid", "mac", "mac_address") or ""),
            "signal_percent": pct, "rssi_dbm": rssi, "frequency_mhz": freq,
            "channel": int(chan) if chan is not None else None,
            "band": _first(item, "band"),
            "radio_type": _first(item, "radio_type", "radio", "standard"),
            "authentication": str(security) if security else None,
            "encryption": str(_first(item, "encryption") or security or "") or None,
        }
        ts = _first(item, "timestamp", "time", "datetime") if use_timestamp else None
        if ts is not None:
            parsed = pd.to_datetime(ts, errors="coerce")
            if not pd.isna(parsed):
                row["timestamp"] = parsed.to_pydatetime()
        rows.append(row)
    return rows


def parse_scan_json(text: str, source: str = "android-termux") -> pd.DataFrame:
    data = json.loads(text)
    if isinstance(data, dict):
        data = next((v for v in data.values() if isinstance(v, list)), [data])
    return _finalize(_rows_from_records(data, use_timestamp=False), source)


def import_scan_bytes(name: str, payload: bytes) -> pd.DataFrame:
    """Parse a scan exported from a phone/laptop app (JSON from Termux, or any CSV)."""
    text = payload.decode("utf-8-sig", errors="replace")
    source = f"import:{name}"
    if text.lstrip().startswith(("[", "{")):
        return parse_scan_json(text, source)
    table = pd.read_csv(io.StringIO(text))
    return _finalize(_rows_from_records(table.to_dict("records")), source)


def _scan_termux() -> pd.DataFrame:
    return parse_scan_json(_run(["termux-wifi-scaninfo"], timeout=30), "android-termux")


def _connected_termux() -> dict[str, Any]:
    if not shutil.which("termux-wifi-connectioninfo"):
        return {}
    data = json.loads(_run(["termux-wifi-connectioninfo"], timeout=15))
    rssi = _num(data.get("rssi"))
    ssid = str(data.get("ssid", "")).strip('"')
    return {
        "interface": "wlan0", "ssid": ssid or None, "bssid": data.get("bssid"),
        "signal_percent": dbm_to_pct(rssi) if rssi is not None else None,
        "transmit_rate": _num(data.get("link_speed_mbps")),
    }


# ---------------------------------------------------------------------------
# Platform dispatch
# ---------------------------------------------------------------------------

def detect_platform() -> str:
    if os.name == "nt":
        return "windows"
    if shutil.which("termux-wifi-scaninfo"):
        return "android-termux"
    system = platform.system()
    if system == "Darwin":
        return "macos"
    if system == "Linux":
        return "linux"
    return "unknown"


PLATFORM_LABELS = {
    "windows": "Windows (netsh WLAN)",
    "linux": "Linux (NetworkManager)",
    "macos": "macOS (system_profiler)",
    "android-termux": "Android (Termux:API)",
    "unknown": "Unsupported OS",
}


def scan_once() -> pd.DataFrame:
    """One real scan with whatever mechanism this operating system offers."""
    kind = detect_platform()
    if kind == "windows":
        return _scan_windows()
    if kind == "linux":
        return _scan_linux()
    if kind == "macos":
        return _scan_macos()
    if kind == "android-termux":
        return _scan_termux()
    raise RuntimeError("Live scanning is not supported on this operating system. Use the file import instead.")


def get_connected_wifi() -> dict[str, Any]:
    """Details of the network this host is currently connected to (may be empty)."""
    kind = detect_platform()
    try:
        if kind == "windows":
            return _connected_windows()
        if kind == "linux":
            return _connected_linux()
        if kind == "macos":
            return dict(_MAC_CACHE.get("connected") or {})
        if kind == "android-termux":
            return _connected_termux()
    except Exception:
        return {}
    return {}


# ---------------------------------------------------------------------------
# Shared scan store (one scan loop for every browser/device viewing the app)
# ---------------------------------------------------------------------------

def coerce_types(frame: pd.DataFrame) -> pd.DataFrame:
    """Guarantee numeric/datetime dtypes (empty-frame concatenation can leave 'object')."""
    if frame.empty:
        return frame
    frame = frame.copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce")
    for column in ("signal_percent", "rssi_dbm", "frequency_mhz", "channel", "scan_id"):
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame


class ScanStore:
    """Thread-safe latest scan + rolling history. Safe for several viewers at once."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.latest = pd.DataFrame(columns=COLUMNS)
        self.history = pd.DataFrame(columns=COLUMNS + ["scan_id"])
        self.connected: dict[str, Any] = {}
        self.connected_history: list[dict[str, Any]] = []
        self.last_scan_time: datetime | None = None
        self.last_error: str | None = None
        self.scan_count = 0
        self._last_persist = 0.0
        self._last_scan_monotonic = 0.0

    def scan(self, min_interval: float = 0.0, force: bool = False, scanner=None,
             connected_getter=None, persist: bool = True) -> tuple[pd.DataFrame, str | None]:
        """Scan unless a recent result exists. Returns (latest_frame, error_or_None)."""
        scanner = scanner or scan_once
        connected_getter = connected_getter or get_connected_wifi
        with self._lock:
            age = time.monotonic() - self._last_scan_monotonic
            if not force and self.scan_count > 0 and age < min_interval:
                return self.latest, self.last_error
            self._last_scan_monotonic = time.monotonic()
            try:
                frame = scanner()
                self.last_error = None
            except Exception as exc:                      # surface, never fake data
                self.last_error = str(exc)
                return self.latest, self.last_error

            self.last_scan_time = datetime.now()
            self.scan_count += 1
            self.latest = frame.copy()
            if frame.empty:
                return self.latest, None

            tagged = frame.copy()
            tagged["scan_id"] = self.scan_count
            parts = [p for p in (self.history, tagged) if not p.empty]
            self.history = coerce_types(pd.concat(parts, ignore_index=True))
            cutoff = self.scan_count - MAX_SCANS_IN_MEMORY
            if cutoff > 0:
                self.history = self.history[self.history["scan_id"] > cutoff].reset_index(drop=True)

            self.connected = connected_getter() or {}
            if self.connected.get("signal_percent") is not None:
                self.connected_history.append({
                    "timestamp": self.last_scan_time,
                    "ssid": self.connected.get("ssid"),
                    "signal_percent": self.connected.get("signal_percent"),
                    "receive_rate": self.connected.get("receive_rate"),
                    "transmit_rate": self.connected.get("transmit_rate"),
                })
                self.connected_history = self.connected_history[-MAX_SCANS_IN_MEMORY:]

            if persist:
                self._persist(frame, force)
            return self.latest, None

    def _persist(self, frame: pd.DataFrame, force: bool) -> None:
        now = time.time()
        if not force and now - self._last_persist < PERSIST_EVERY_SECONDS:
            return
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            frame[COLUMNS].to_csv(HISTORY_PATH, mode="a", header=not HISTORY_PATH.exists(), index=False)
            self._last_persist = now
            trim_archive()
        except OSError:
            pass

    def snapshot(self) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any], pd.DataFrame]:
        with self._lock:
            return (self.latest.copy(), self.history.copy(), dict(self.connected),
                    pd.DataFrame(self.connected_history))

    def clear(self) -> None:
        with self._lock:
            self.latest = pd.DataFrame(columns=COLUMNS)
            self.history = pd.DataFrame(columns=COLUMNS + ["scan_id"])
            self.connected, self.connected_history = {}, []
            self.scan_count = 0


STORE = ScanStore()


def scan_wifi_now() -> pd.DataFrame:
    """Backward-compatible helper: force one scan and return the frame."""
    frame, error = STORE.scan(force=True)
    if error:
        raise RuntimeError(error)
    return frame


def trim_archive(path: Path = HISTORY_PATH, max_bytes: int = MAX_ARCHIVE_BYTES) -> bool:
    """Keep the saved archive bounded: when it passes max_bytes, drop the oldest half."""
    try:
        if not path.exists() or path.stat().st_size <= max_bytes:
            return False
        frame = pd.read_csv(path, on_bad_lines="skip")
        frame.iloc[len(frame) // 2:].to_csv(path, index=False)
        return True
    except (OSError, pd.errors.ParserError):
        return False


def load_archive(max_rows: int = 60000) -> pd.DataFrame:
    """Previously persisted real scans (used for hour-of-day / long-term analysis)."""
    if not HISTORY_PATH.exists():
        return pd.DataFrame(columns=COLUMNS)
    try:
        frame = pd.read_csv(HISTORY_PATH, on_bad_lines="skip").tail(max_rows)
    except Exception:
        return pd.DataFrame(columns=COLUMNS)
    for column in COLUMNS:
        if column not in frame.columns:
            frame[column] = None
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce")
    for column in ("signal_percent", "channel", "frequency_mhz", "rssi_dbm"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame["ap_id"] = frame["ap_id"].fillna(frame["bssid"]).fillna(
        frame["ssid"].astype(str) + "|ch" + frame["channel"].astype(str))
    frame["band"] = [band_of_row(f, b, c) for f, b, c in zip(frame["frequency_mhz"], frame["band"], frame["channel"])]
    return frame.dropna(subset=["timestamp", "signal_percent"])[COLUMNS].reset_index(drop=True)


# ---------------------------------------------------------------------------
# Demo mode (public dashboard link): no host scanning, nothing written to disk
# ---------------------------------------------------------------------------

def is_demo() -> bool:
    """True for a public deployment. Force with WISENSE_DEMO=1 / 0; auto-on for Streamlit Community Cloud."""
    flag = os.environ.get("WISENSE_DEMO", "").strip().lower()
    if flag in {"1", "true", "yes", "on"}:
        return True
    if flag in {"0", "false", "no", "off"}:
        return False
    return Path("/mount/src").exists()          # Streamlit Community Cloud mounts the repo here


def load_sample() -> tuple[pd.DataFrame, pd.DataFrame, str]:
    """Bundled sample scans -> (latest, history, description). Timestamps are re-anchored to now."""
    if not SAMPLE_PATH.exists():
        return pd.DataFrame(columns=COLUMNS), pd.DataFrame(columns=COLUMNS + ["scan_id"]), "no sample file"
    frame = coerce_types(pd.read_csv(SAMPLE_PATH))
    frame = frame.dropna(subset=["timestamp", "signal_percent"])
    frame["bssid"] = frame["bssid"].where(frame["bssid"].notna(), None)
    frame["scan_id"] = pd.factorize(frame["timestamp"])[0]
    shift = pd.Timestamp.now() - frame["timestamp"].max()
    frame["timestamp"] = frame["timestamp"] + shift
    source = str(frame["source"].iloc[0]) if "source" in frame and len(frame) else ""
    if source.startswith("sample-captured"):
        note = "a real scan captured earlier on the author's computer (network names and MAC addresses anonymized)"
    else:
        note = "an ILLUSTRATIVE synthetic sample — not real measurements"
    history = frame[COLUMNS + ["scan_id"]].reset_index(drop=True)
    latest = history[history["scan_id"] == history["scan_id"].max()][COLUMNS].reset_index(drop=True)
    return latest, history, note


# ---------------------------------------------------------------------------
# Device location (optional, never invented)
# ---------------------------------------------------------------------------

_LOCATION_CACHE: dict[str, Any] | None = None
_LOCATION_CACHE_TIME = 0.0


def _get_location_from_winrt() -> dict[str, Any] | None:
    try:
        import asyncio
        import winrt.windows.devices.geolocation as geolocation  # type: ignore
    except Exception:
        return None

    async def _read() -> dict[str, Any] | None:
        position = await geolocation.Geolocator().get_geoposition_async()
        coordinate = position.coordinate
        accuracy = getattr(coordinate, "accuracy", None)
        return {
            "latitude": float(coordinate.point.position.latitude),
            "longitude": float(coordinate.point.position.longitude),
            "accuracy_m": float(accuracy) if accuracy is not None else None,
            "method": "Windows device location",
        }

    try:
        return asyncio.run(_read())
    except Exception:
        return None


def _get_location_from_environment() -> dict[str, Any] | None:
    try:
        lat = float(os.environ["WISENSE_LATITUDE"])
        lon = float(os.environ["WISENSE_LONGITUDE"])
    except (KeyError, TypeError, ValueError):
        return None
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return None
    return {"latitude": lat, "longitude": lon, "accuracy_m": None, "method": "WISENSE_LATITUDE/WISENSE_LONGITUDE"}


def get_device_location(force_refresh: bool = False) -> dict[str, Any] | None:
    global _LOCATION_CACHE, _LOCATION_CACHE_TIME
    now = time.time()
    if not force_refresh and _LOCATION_CACHE is not None and now - _LOCATION_CACHE_TIME < 300:
        return _LOCATION_CACHE
    for getter in (_get_location_from_winrt, _get_location_from_environment):
        location = getter()
        if location:
            _LOCATION_CACHE, _LOCATION_CACHE_TIME = location, now
            return location
    return None


def host_label() -> str:
    try:
        return socket.gethostname()
    except OSError:
        return "this computer"


if __name__ == "__main__":      # quick diagnostic:  python -m analysis.live_wifi
    print(f"Platform: {PLATFORM_LABELS.get(detect_platform())}")
    try:
        result = scan_once()
        print(result[["ssid", "bssid", "signal_percent", "band", "channel"]].to_string(index=False)
              if not result.empty else "Scan returned no networks.")
        print("Connected:", get_connected_wifi())
    except Exception as exc:
        print("SCAN FAILED:", exc)
