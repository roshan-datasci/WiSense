"""Parser and store tests (run with:  python -m pytest tests  or  python tests/test_scanner.py)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analysis import live_wifi as lw

NETSH = """
Interface name : Wi-Fi
There are 4 networks currently visible.

SSID 1 : sathyabama-campus@sathyabama-ac-in
    Network type            : Infrastructure
    Authentication          : WPA2-Enterprise
    Encryption              : CCMP
    BSSID 1                 : aa:bb:cc:00:00:01
         Signal             : 88%
         Radio type         : 802.11ac
         Band               : 5 GHz
         Channel            : 44
         Basic rates (Mbps) : 6 12 24
    BSSID 2                 : aa:bb:cc:00:00:02
         Signal             : 61%
         Radio type         : 802.11n
         Band               : 2.4 GHz
         Channel            : 6

SSID 2 : Anthony_hostel
    Authentication          : WPA2-Personal
    Encryption              : CCMP
    BSSID 1                 : de:ad:be:ef:00:10
         Signal             : 45%
         Radio type         : 802.11n
         Band               : 2.4 GHz
         Channel            : 1

SSID 3 :
    Authentication          : Open
    Encryption              : None
    BSSID 1                 : 11:22:33:44:55:66
         Signal             : 20%
         Radio type         : 802.11g
         Band               : 2.4 GHz
         Channel            : 11

SSID 4 : Samsung A55
    Authentication          : WPA3-Personal
    Encryption              : CCMP
    BSSID 1                 : 02:00:00:00:00:99
         Signal             : 72%
         Radio type         : 802.11ax
         Band               : 5 GHz
         Channel            : 149
"""

NMCLI = (
    " :Home\\:Net:AA\\:BB\\:CC\\:DD\\:EE\\:01:6:2437 MHz:130 Mbit/s:81:WPA2\n"
    "*:Office:AA\\:BB\\:CC\\:DD\\:EE\\:02:36:5180 MHz:540 Mbit/s:67:WPA2 WPA3\n"
    " ::AA\\:BB\\:CC\\:DD\\:EE\\:03:11:2462 MHz:65 Mbit/s:30:\n"
)

MAC = json.dumps({"SPAirPortDataType": [{"spairport_airport_interfaces": [{
    "_name": "en0",
    "spairport_current_network_information": {
        "_name": "MyWiFi", "spairport_network_channel": "149 (5GHz, 80MHz)",
        "spairport_signal_noise": "-55 dBm / -92 dBm", "spairport_network_phymode": "802.11ax",
        "spairport_network_rate": 866, "spairport_security_mode": "spairport_security_mode_wpa2_personal"},
    "spairport_airport_other_local_wireless_networks": [
        {"_name": "Neighbour", "spairport_network_channel": "1 (2GHz, 20MHz)",
         "spairport_signal_noise": "-78 dBm / -92 dBm", "spairport_network_phymode": "802.11n",
         "spairport_security_mode": "spairport_security_mode_wpa2_personal"}]}]}]})

TERMUX = json.dumps([
    {"bssid": "AA:BB:CC:11:22:33", "frequency_mhz": 2412, "rssi": -52, "ssid": "PhoneSeesThis", "timestamp": 1790000000000},
    {"bssid": "AA:BB:CC:11:22:34", "frequency_mhz": 5745, "rssi": -71, "ssid": "Cafe5G"},
])

CSV = "ssid,bssid,signal,channel\nLab,aa:aa:aa:aa:aa:01,-60,36\nLab2,aa:aa:aa:aa:aa:02,75,1\n"


def test_netsh():
    df = lw.parse_netsh_bssid_output(NETSH)
    assert len(df) == 5
    assert set(df["ssid"]) == {"sathyabama-campus@sathyabama-ac-in", "Anthony_hostel", lw.HIDDEN_SSID, "Samsung A55"}
    row = df[df["bssid"] == "aa:bb:cc:00:00:01"].iloc[0]
    assert row["signal_percent"] == 88 and row["channel"] == 44 and row["band"] == "5 GHz"
    assert row["frequency_mhz"] == 5220 and row["rssi_dbm"] == -56
    assert df[df["ssid"] == lw.HIDDEN_SSID].iloc[0]["authentication"] == "Open"


def test_nmcli():
    df = lw.parse_nmcli_output(NMCLI)
    assert len(df) == 3
    assert df.iloc[0]["bssid"] == "aa:bb:cc:dd:ee:01" and df.iloc[0]["ssid"] == "Home:Net"
    assert df.iloc[1]["band"] == "5 GHz" and df.iloc[1]["channel"] == 36
    assert df.iloc[2]["ssid"] == lw.HIDDEN_SSID


def test_macos():
    df, connected = lw.parse_macos_profiler(MAC)
    assert len(df) == 2 and connected["ssid"] == "MyWiFi" and connected["transmit_rate"] == 866
    assert df[df.ssid == "Neighbour"].iloc[0]["band"] == "2.4 GHz"
    assert df.iloc[0]["bssid"] is None and df.iloc[0]["ap_id"].startswith("MyWiFi|")   # no invented BSSID


def test_termux_and_csv_import():
    df = lw.import_scan_bytes("t.json", TERMUX.encode())
    assert len(df) == 2 and df.iloc[0]["channel"] == 1 and df.iloc[1]["band"] == "5 GHz"
    assert df.iloc[0]["signal_percent"] == 96
    csv = lw.import_scan_bytes("scan.csv", CSV.encode())
    assert csv.iloc[0]["rssi_dbm"] == -60 and csv.iloc[0]["channel"] == 36 and csv.iloc[1]["signal_percent"] == 75


def test_store_dedupes_viewers_and_reports_errors():
    store = lw.ScanStore()
    calls = {"n": 0}

    def fake():
        calls["n"] += 1
        return lw.parse_netsh_bssid_output(NETSH)

    store.scan(force=True, scanner=fake, connected_getter=lambda: {"ssid": "x", "signal_percent": 80}, persist=False)
    store.scan(min_interval=60, scanner=fake, connected_getter=lambda: {}, persist=False)   # second viewer
    assert calls["n"] == 1 and store.scan_count == 1
    store.scan(force=True, scanner=fake, connected_getter=lambda: {}, persist=False)
    assert store.history["scan_id"].nunique() == 2

    def boom():
        raise RuntimeError("adapter off")
    frame, err = store.scan(force=True, scanner=boom, persist=False)
    assert err == "adapter off" and len(frame) == 5      # keeps last real data, reports error


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("PASS", name)
