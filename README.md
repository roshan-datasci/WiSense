# 📡 WiSense

## Wi-Fi Intelligence & Analytics Dashboard

[**Open Live Dashboard**](https://wisense-xpct7ici3cynnqhifnkp87.streamlit.app/) &nbsp;·&nbsp; *(public link runs in [demo mode](#-public-dashboard-demo-mode))*

WiSense is a Data Science / Networking project that collects **real Wi-Fi measurements** from a device and turns them into understandable insights about signal quality, access points, channels, congestion, and connection performance — using Python, Pandas, NumPy, Plotly and Streamlit.

The project exists to answer practical questions: *Which nearby network is strongest? Which channel is overcrowded? Why is my Wi-Fi slow or unstable? How fast is the connection on this device right now?*

> **Design rule:** WiSense never presents unavailable data as real. No invented network names, no fabricated speeds, no made-up router locations. If something cannot be measured, the dashboard says so.

---

## ✨ What it measures

| Source | What is collected |
|---|---|
| **Wi-Fi adapter scan** (the computer running WiSense) | SSIDs, BSSIDs, signal %, estimated dBm, channel, frequency, band, radio standard, authentication, encryption, connected network and link rate |
| **Browser probe** (whichever device opens the page — phone, tablet or laptop) | Latency, jitter, packet loss, real download speed, Wi-Fi link throughput to the host, connection type |
| **Browser location** (optional, one button) | Where each scan was taken, so scans can be plotted on a map |
| **Imported scan file** (optional) | Scans exported from a phone (Termux JSON or CSV) analysed with the same pipeline |

---

## 📊 Dashboard sections

The page keeps one continuous layout, and the nav bar jumps to each section. Everything refreshes together every 3 seconds.

* **Local Wi-Fi Collector** — live access points, connected network, per-SSID expandable BSSID details, real-time signal history
* **Live Network Overview** — networks, access points, mean signal, link rate, plus plain-language insights
* **Interactive Wi-Fi Map** — scans placed at the real device location (never at invented router positions)
* **Signal Strength / Network Performance** — signal by SSID and current link rate
* **Wi-Fi Channel Analysis** — channel and frequency distribution, **2.4 / 5 / 6 GHz spectrum charts**, least-crowded channel recommendations
* **Wi-Fi Environment** — access points and mean signal per network, channel overlap, estimated distance
* **Connection Intelligence** — connected signal vs measured latency / speed
* **Performance Relationships** — signal vs channel interference
* **ML Insights** — K-Means connectivity clusters computed on the live scan
* **Task Suitability** — which network best suits browsing, video calls, gaming or downloads
* **Performance Trends** — latency, jitter and speed-test history of the viewing device, plus live signal trend
* **Advanced Analytics Complete** — eleven views: overall, network performance, correlations, signal analysis, distance, congestion, hourly, peak periods, rolling performance, extremes, data quality

---

## 📱 Works on any device

| Device | Nearby-network scan | Own-device speed & latency |
|---|---|---|
| Windows laptop | ✅ automatic (`netsh wlan`, with a forced fresh scan) | ✅ |
| Linux laptop | ✅ automatic (NetworkManager `nmcli`) | ✅ |
| Mac | ✅ automatic (`system_profiler`) | ✅ |
| Android phone | ✅ via Termux, or export a scan and import it | ✅ open the page in the phone's browser |
| iPhone / iPad | ❌ iOS does not allow any app to list nearby networks | ✅ open the page in Safari |

**Why phones are handled differently:** a web browser is not allowed to list nearby Wi-Fi networks (iOS and Android both block it). So the nearby-network list comes from the computer running WiSense, while the speed and latency panel measures **the phone itself**. The page tells you which device each number comes from.

---

## 🧰 Tech stack

Python · Streamlit · Pandas · NumPy · Plotly · a small JavaScript browser probe (custom Streamlit component) · OS Wi-Fi tools (`netsh`, `nmcli`, `system_profiler`, Termux:API)

---

## 🚀 Installation & run

```powershell
pip install -r requirements.txt
streamlit run app\app.py
```

Open **http://localhost:8501** in Chrome or Edge.

Check the scanner on its own if the network list is empty:

```powershell
python -m analysis.live_wifi
```

**Windows:** if the scan fails, turn on *Settings → Privacy & security → Location* and *Let desktop apps access your location*.
**macOS:** give your terminal *Location Services*, otherwise macOS hides network names.

### Open it from a phone

Start the app so it is reachable on your network:

```powershell
streamlit run app\app.py --server.address 0.0.0.0
```

Then open `http://<your-computer-ip>:8501` on the phone (same Wi-Fi; find the IP with `ipconfig`; allow the Windows firewall prompt). Press **RUN SPEED TEST** to measure the phone's own connection.

### Analyse a phone's own scan (Android)

In Termux run `termux-wifi-scaninfo > scan.json`, then upload the file under **Import a scan from a phone**. Any CSV with `ssid, bssid, signal (or rssi), channel (or frequency)` also works.

---

## 🌐 Public dashboard (demo mode)

A public website cannot scan *your* Wi-Fi — scanning happens on the machine hosting the app, and a cloud server has no Wi-Fi adapter. So the public link runs in **demo mode**:

* shows a clearly labelled **sample scan** (nothing is scanned, nothing is written to disk, nobody's surroundings are exposed)
* every visitor still gets a **real speed and latency test of their own device**, and can upload their own scan file
* running locally keeps full live scanning — demo mode is a switch, not a rewrite

**Deploy on Streamlit Community Cloud (free):**

1. Push this folder to a GitHub repository.
2. At <https://share.streamlit.io> choose **Create app**, select the repo, set *Main file path* to `app/app.py`.
3. Deploy. Demo mode turns on automatically on Streamlit Cloud (or force it with `WISENSE_DEMO=1`).
4. Paste the URL into the *Open Live Dashboard* link at the top of this README.

**Use a real sample (recommended).** The bundled `data/sample_scan.csv` is synthetic and labelled as such. Capture a real one on your laptop and commit it:

```powershell
python tools/capture_sample.py              # 30 real scans; SSIDs and MAC addresses anonymized
python tools/capture_sample.py --keep-names # keeps names — neighbours' network names become public
```

To preview demo mode locally: `$env:WISENSE_DEMO="1"; streamlit run app\app.py`

---

## 🗂 Project structure

```
WiSense_project_final_fixed/
├── app/
│   ├── app.py                      # Streamlit dashboard
│   ├── theme.css                   # terminal-style theme
│   └── components/wisense_probe/   # browser probe (latency, jitter, loss, speed)
├── analysis/
│   ├── live_wifi.py                # cross-platform scanner, scan store, import, demo helpers
│   └── metrics.py                  # channel overlap, recommendations, scoring, K-Means
├── data/
│   ├── sample_scan.csv             # sample used by demo mode
│   └── live_wifi_history.csv       # local scan archive (auto-created, capped at 5 MB)
├── tools/
│   ├── make_sample.py              # builds the synthetic demo sample
│   └── capture_sample.py           # captures a real, anonymized sample
├── tests/                          # scanner parsers + full app tests
├── .streamlit/config.toml
└── requirements.txt
```

---

## ⚙️ How it works

1. **Scan** — the OS Wi-Fi tool is queried and normalized into one table (SSID, BSSID, signal, channel, frequency, band, security).
2. **Share** — one scan loop serves every open browser; the latest 400 scans stay in memory and are appended to a size-capped CSV about every 30 s.
3. **Analyse** — channel overlap, interference load, stability, signal statistics, K-Means clusters and task scores are all computed from those real measurements.
4. **Probe** — the viewing device's browser measures latency to the server, jitter, loss, throughput and a public speed-test download.
5. **Present** — everything is shown in one auto-refreshing page.

---

## ⚠️ Honest limitations

* **Distance is an estimate**, derived from signal strength with a path-loss model; walls change it a lot. It is labelled as an estimate everywhere.
* **Connected-device counts cannot be read** from a nearby-network scan, so congestion is measured as **channel overlap** between access points.
* **Router GPS positions are not in Wi-Fi scans**, so routers are never placed on the map — only where *scans* were taken.
* **Signal % → dBm** is the standard linear approximation when the OS reports only a percentage.
* **Task suitability is a heuristic** of radio conditions, not a speed test.
* The **speed test downloads ~1.5 MB** each time it runs (manual by default). A campus network may block the public speed-test server; the Wi-Fi-link measurement to the host still works.
* Phones need **HTTPS or localhost** for browser location; on plain `http://<ip>` the map button may be blocked.
* iOS cannot scan Wi-Fi at all; that is an operating-system rule, not a WiSense limitation.

---

## 🧪 Tests

```powershell
python tests/test_scanner.py   # Windows / Linux / macOS / Termux / CSV parsers, shared scan store
python tests/test_app.py       # full dashboard: live, demo mode, import, probe, speed test, nav links, archive cap
```

---

## 🛠 Troubleshooting

| Problem | Fix |
|---|---|
| `ERR_ADDRESS_INVALID` at `0.0.0.0` | Open `http://localhost:8501` instead |
| Empty network list | Run `python -m analysis.live_wifi`; enable Wi-Fi and Windows Location access |
| Old version still showing | `Ctrl+C`, run from the newest extracted folder, then hard refresh (`Ctrl+F5`) |
| Public link shows sample data | Expected — demo mode; run locally for live scanning |
| Speed test shows a warning | The campus network blocks the public server; use the Wi-Fi-link result |

---

## 👤 Author

**Roshan T** — Data Science  / Sathyabama University · [GitHub](https://github.com/roshan-datasci) · [LinkedIn](https://www.linkedin.com/in/roshan-t-b8500b380)

---

<sub>WiSense reads only what the device's own Wi-Fi adapter and browser report. Scan data can include names of nearby networks — do not publish raw scans without anonymizing them.</sub>
