from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# ============================================================
# WISENSE — STREAMLIT APPLICATION
# ============================================================

st.set_page_config(
    page_title="WiSense",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# PATHS
# ============================================================

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT_DIR / "data" / "wifi_clustered.csv"


# ============================================================
# GLOBAL CSS
# ============================================================

st.html(
    """
    <style>

    /* ========================================================
       GLOBAL PAGE
    ======================================================== */

    :root {
        --bg: #050505;
        --panel: #090909;
        --panel-2: #0d0d0d;

        --border: #363636;
        --border-soft: #252525;

        --text: #ffffff;
        --text-secondary: #c2c2c2;
        --text-dim: #a0a0a0;
        --text-faint: #888888;
    }


    html,
    body {
        background: #050505 !important;
        color: #ffffff !important;
    }


    body {
        font-family: "Courier New", monospace !important;
    }


    [data-testid="stAppViewContainer"] {

        background-color: #050505 !important;

        /* Clearly visible scientific dot grid */
        background-image:
            radial-gradient(
                rgba(255, 255, 255, 0.32) 1px,
                transparent 1px
            ) !important;

        background-size: 22px 22px !important;

        background-position: 0 0 !important;
    }


    [data-testid="stAppViewContainer"] > .main {
        background: transparent !important;
    }


    [data-testid="stHeader"] {
        background: transparent !important;
    }


    [data-testid="stToolbar"] {
        display: none !important;
    }


    #MainMenu {
        visibility: hidden !important;
    }


    footer {
        visibility: hidden !important;
    }


    .block-container {

        max-width: 1500px;

        padding-top: 1.5rem;
        padding-bottom: 3rem;

        background: transparent !important;
    }


    /* ========================================================
       TERMINAL HEADER
    ======================================================== */

    .wisense-header {

        text-align: center;

        padding: 1.4rem 1rem 1.6rem 1rem;

        margin-bottom: 1.2rem;

        border-top: 1px solid #454545;
        border-bottom: 1px solid #454545;

        background: rgba(5, 5, 5, 0.82);
    }


    .terminal-line {

        color: #ffffff;

        font-family:
            "Courier New",
            monospace;

        font-size:
            clamp(
                0.75rem,
                2vw,
                1.1rem
            );

        font-weight: 700;

        letter-spacing: 0.10em;

        line-height: 1.1;

        white-space: nowrap;
    }


    .terminal-name {

        margin: 0.25rem 0;

        color: #ffffff;

        font-family:
            "Courier New",
            monospace;

        font-size:
            clamp(
                1.8rem,
                4vw,
                3.3rem
            );

        font-weight: 700;

        letter-spacing: 0.18em;

        line-height: 1.05;
    }


    .wisense-subtitle {

        margin-top: 0.8rem;

        color: #c4c4c4;

        font-family:
            "Courier New",
            monospace;

        font-size:
            clamp(
                0.68rem,
                1.4vw,
                0.95rem
            );

        letter-spacing: 0.20em;

        line-height: 1.5;
    }


    /* ========================================================
       NAVIGATION
    ======================================================== */

    .nav-row {

        display: flex;

        justify-content: center;

        align-items: center;

        gap: 2rem;

        flex-wrap: wrap;

        margin:
            0.8rem
            0
            1.4rem
            0;

        padding:
            0.8rem
            0;

        border-bottom:
            1px solid
            #303030;

        background:
            rgba(5, 5, 5, 0.65);
    }


    .nav-item {

        color: #a9a9a9;

        font-family:
            "Courier New",
            monospace;

        font-size: 0.78rem;

        font-weight: 600;

        letter-spacing: 0.12em;

        white-space: nowrap;
    }


    .nav-item.active {
        color: #ffffff;
    }


    /* ========================================================
       LIVE
    ======================================================== */

    .live-row {

        display: flex;

        justify-content: flex-end;

        align-items: center;

        margin:
            0.4rem
            0
            1.2rem
            0;
    }


    .live-indicator {

        color: #eeeeee;

        font-family:
            "Courier New",
            monospace;

        font-size: 0.75rem;

        font-weight: 600;

        letter-spacing: 0.12em;
    }


    .live-dot {
        color: #ffffff;
    }


    /* ========================================================
       SECTION HEADINGS
    ======================================================== */

    .section-title {

        color: #ffffff;

        font-family:
            "Courier New",
            monospace;

        font-size: 0.94rem;

        font-weight: 700;

        letter-spacing: 0.13em;

        margin:
            1.6rem
            0
            0.65rem
            0;

        padding-bottom: 0.55rem;

        border-bottom:
            1px solid
            #3a3a3a;

        background:
            rgba(5, 5, 5, 0.62);
    }


    .section-subtitle {

        color: #bcbcbc;

        font-family:
            "Courier New",
            monospace;

        font-size: 0.74rem;

        font-weight: 500;

        letter-spacing: 0.04em;

        line-height: 1.6;

        margin-bottom: 0.8rem;

        background:
            rgba(5, 5, 5, 0.52);
    }


    /* ========================================================
       METRIC CARDS
    ======================================================== */

    .metric-card {

        background:
            rgba(9, 9, 9, 0.92);

        border:
            1px solid
            #3a3a3a;

        padding: 1rem;

        min-height: 115px;
    }


    .metric-label {

        color: #bcbcbc;

        font-family:
            "Courier New",
            monospace;

        font-size: 0.68rem;

        font-weight: 600;

        letter-spacing: 0.08em;

        margin-bottom: 0.7rem;
    }


    .metric-value {

        color: #ffffff;

        font-family:
            "Courier New",
            monospace;

        font-size: 1.65rem;

        font-weight: 700;
    }


    .metric-detail {

        color: #999999;

        font-family:
            "Courier New",
            monospace;

        font-size: 0.67rem;

        line-height: 1.5;

        margin-top: 0.45rem;
    }


    /* ========================================================
       SELECTBOX
    ======================================================== */

    div[data-baseweb="select"] > div {

        background-color:
            #0b0b0b !important;

        border-color:
            #4a4a4a !important;

        color:
            #ffffff !important;
    }


    div[data-baseweb="select"] span {
        color: #ffffff !important;
    }


    label {

        color:
            #bcbcbc !important;

        font-family:
            "Courier New",
            monospace !important;

        font-size:
            0.72rem !important;

        font-weight:
            500 !important;

        letter-spacing:
            0.08em !important;
    }


    /* ========================================================
       PLOTLY — GLOBAL VISIBILITY FIX
    ======================================================== */

    .js-plotly-plot {

        background:
            #070707 !important;
    }


    .js-plotly-plot .plotly {

        background:
            #070707 !important;
    }


    /* Legend text */
    .js-plotly-plot
    .plotly
    .legendtext {

        fill: #ffffff !important;

        color: #ffffff !important;

        font-family:
            "Courier New",
            monospace !important;

        font-size:
            13px !important;
    }


    /* Legend title */
    .js-plotly-plot
    .plotly
    .legendtitletext {

        fill: #ffffff !important;

        color: #ffffff !important;

        font-family:
            "Courier New",
            monospace !important;
    }


    /* X axis labels */
    .js-plotly-plot
    .plotly
    .xtick
    text {

        fill: #c7c7c7 !important;

        color: #c7c7c7 !important;

        font-family:
            "Courier New",
            monospace !important;
    }


    /* Y axis labels */
    .js-plotly-plot
    .plotly
    .ytick
    text {

        fill: #c7c7c7 !important;

        color: #c7c7c7 !important;

        font-family:
            "Courier New",
            monospace !important;
    }


    /* Chart titles */
    .js-plotly-plot
    .plotly
    .gtitle {

        fill: #ffffff !important;

        color: #ffffff !important;

        font-family:
            "Courier New",
            monospace !important;

        font-weight: 700 !important;
    }


    /* Axis titles */
    .js-plotly-plot
    .plotly
    .axis-title {

        fill: #dddddd !important;

        color: #dddddd !important;

        font-family:
            "Courier New",
            monospace !important;
    }


    /* Plotly modebar */
    .js-plotly-plot
    .plotly
    .modebar-btn {

        color: #aaaaaa !important;
    }


    /* ========================================================
       CUSTOM TABLE
    ======================================================== */

    .ml-table-wrapper {

        width: 100%;

        overflow-x: auto;

        border:
            1px solid
            #363636;

        background:
            rgba(8, 8, 8, 0.94);
    }


    .ml-table {

        width: 100%;

        border-collapse:
            collapse;

        font-family:
            "Courier New",
            monospace;

        font-size:
            0.70rem;

        color:
            #dddddd;
    }


    .ml-table th {

        color:
            #ffffff;

        background:
            #101010;

        font-weight:
            700;

        letter-spacing:
            0.05em;

        text-align:
            left;

        padding:
            0.65rem;

        border-bottom:
            1px solid
            #454545;
    }


    .ml-table td {

        color:
            #c2c2c2;

        padding:
            0.65rem;

        border-bottom:
            1px solid
            #292929;
    }


    .ml-table tr:last-child td {
        border-bottom: none;
    }


    /* ========================================================
       FOOTER
    ======================================================== */

    .wisense-footer {

        margin-top: 2rem;

        padding-top: 1rem;

        border-top:
            1px solid
            #2d2d2d;

        color:
            #888888;

        font-family:
            "Courier New",
            monospace;

        font-size:
            0.65rem;

        letter-spacing:
            0.06em;

        text-align:
            center;
    }


    /* ========================================================
       MOBILE
    ======================================================== */

    @media (max-width: 768px) {

        .block-container {

            padding-left:
                0.8rem;

            padding-right:
                0.8rem;
        }


        .nav-row {

            gap:
                0.75rem;

            justify-content:
                space-between;
        }


        .nav-item {

            font-size:
                0.65rem;
        }


        .terminal-line {

            font-size:
                0.68rem;
        }


        .terminal-name {

            font-size:
                1.7rem;

            letter-spacing:
                0.10em;
        }


        .wisense-subtitle {

            font-size:
                0.65rem;

            letter-spacing:
                0.10em;
        }


        .section-title {

            font-size:
                0.82rem;
        }


        .section-subtitle {

            font-size:
                0.68rem;
        }
    }

    </style>
    """
)


# ============================================================
# DATA LOADING
# ============================================================

@st.cache_data
def load_data() -> pd.DataFrame:

    if not DATA_PATH.exists():
        return pd.DataFrame()

    data = pd.read_csv(DATA_PATH)

    if "timestamp" in data.columns:

        data["timestamp"] = pd.to_datetime(
            data["timestamp"],
            errors="coerce",
        )

    return data


df = load_data()


# ============================================================
# HEADER
# ============================================================

st.html(
    """
    <div class="wisense-header">

        <div class="terminal-line">
            ================================
        </div>

        <div class="terminal-name">
            WiSense
        </div>

        <div class="terminal-line">
            ================================
        </div>

        <div class="wisense-subtitle">
            WI-FI INTELLIGENCE &amp; ANALYTICS
        </div>

    </div>
    """
)


# ============================================================
# NAVIGATION
# ============================================================

st.html(
    """
    <div class="nav-row">

        <div class="nav-item active">
            [ OVERVIEW ]
        </div>

        <div class="nav-item">
            [ MAP ]
        </div>

        <div class="nav-item">
            [ SIGNAL ]
        </div>

        <div class="nav-item">
            [ CHANNELS ]
        </div>

        <div class="nav-item">
            [ INSIGHTS ]
        </div>

    </div>
    """
)


# ============================================================
# LIVE STATUS
# ============================================================

st.html(
    """
    <div class="live-row">

        <div class="live-indicator">

            <span class="live-dot">
                ●
            </span>

            LIVE

        </div>

    </div>
    """
)


# ============================================================
# TASK SELECTOR
# ============================================================

st.html(
    """
    <div class="section-title">
        TASK SELECTOR
    </div>
    """
)


task = st.selectbox(
    "Select network task",

    [
        "General",
        "Browsing",
        "Video Call",
        "Gaming",
        "Download",
    ],

    label_visibility="collapsed",
)


# ============================================================
# DATA CHECK
# ============================================================

if df.empty:

    st.error(
        "Wi-Fi dataset not found. "
        "Run the Phase 4 clustering pipeline first."
    )

    st.stop()


# ============================================================
# NETWORK SUMMARY
# ============================================================

network_summary = (
    df.groupby("network_name")
    .agg(
        observations=("network_name", "size"),
        avg_rssi=("rssi_dbm", "mean"),
        avg_speed=("avg_download_mbps", "mean"),
        avg_devices=("connected_devices", "mean"),
        avg_distance=("distance_to_ap_m", "mean"),
        avg_signal_std=("signal_std_dbm", "mean"),
    )
    .reset_index()
)


# ============================================================
# LIVE NETWORK OVERVIEW
# ============================================================

st.html(
    """
    <div class="section-title">
        LIVE NETWORK OVERVIEW
    </div>

    <div class="section-subtitle">
        Current analytical view of the Wi-Fi environment
    </div>
    """
)


total_observations = len(df)
network_count = df["network_name"].nunique()
mean_speed = df["avg_download_mbps"].mean()
mean_rssi = df["rssi_dbm"].mean()


col1, col2, col3, col4 = st.columns(4)


with col1:

    st.html(
        f"""
        <div class="metric-card">

            <div class="metric-label">
                NETWORKS OBSERVED
            </div>

            <div class="metric-value">
                {network_count}
            </div>

            <div class="metric-detail">
                distinct Wi-Fi networks
            </div>

        </div>
        """
    )


with col2:

    st.html(
        f"""
        <div class="metric-card">

            <div class="metric-label">
                OBSERVATIONS
            </div>

            <div class="metric-value">
                {total_observations:,}
            </div>

            <div class="metric-detail">
                recorded measurements
            </div>

        </div>
        """
    )


with col3:

    st.html(
        f"""
        <div class="metric-card">

            <div class="metric-label">
                AVG SPEED
            </div>

            <div class="metric-value">
                {mean_speed:.1f}
            </div>

            <div class="metric-detail">
                Mbps
            </div>

        </div>
        """
    )


with col4:

    st.html(
        f"""
        <div class="metric-card">

            <div class="metric-label">
                AVG SIGNAL
            </div>

            <div class="metric-value">
                {mean_rssi:.1f}
            </div>

            <div class="metric-detail">
                dBm
            </div>

        </div>
        """
    )


# ============================================================
# INTERACTIVE WI-FI MAP
# ============================================================

st.html(
    """
    <div class="section-title">
        INTERACTIVE WI-FI MAP
    </div>

    <div class="section-subtitle">
        Observed network locations from the WiSense dataset
    </div>
    """
)


map_fig = px.scatter_map(
    df,

    lat="latitude",

    lon="longitude",

    color="network_name",

    hover_name="network_name",

    hover_data={
        "rssi_dbm": ":.1f",
        "avg_download_mbps": ":.1f",
        "connected_devices": True,
        "latitude": False,
        "longitude": False,
    },

    zoom=11,

    height=480,
)


map_fig.update_layout(

    map_style="carto-darkmatter",

    margin=dict(
        l=0,
        r=0,
        t=0,
        b=0,
    ),

    paper_bgcolor="#070707",

    plot_bgcolor="#070707",

    font=dict(
        family="Courier New",
        color="#ffffff",
    ),

    legend=dict(
        font=dict(
            family="Courier New",
            size=13,
            color="#ffffff",
        ),

        title=dict(
            font=dict(
                family="Courier New",
                size=13,
                color="#ffffff",
            )
        ),
    ),
)


st.plotly_chart(
    map_fig,

    use_container_width=True,

    config={
        "displaylogo": False,
    },
)


# ============================================================
# SIGNAL / NETWORK QUALITY
# ============================================================

st.html(
    """
    <div class="section-title">
        SIGNAL STRENGTH       NETWORK QUALITY
    </div>
    """
)


signal_col, quality_col = st.columns(2)


with signal_col:

    signal_fig = px.bar(

        network_summary,

        x="network_name",

        y="avg_rssi",

        title="Average signal strength",
    )


    signal_fig.update_layout(

        height=350,

        paper_bgcolor="#070707",

        plot_bgcolor="#070707",

        font=dict(
            family="Courier New",
            color="#ffffff",
        ),

        legend=dict(
            font=dict(
                family="Courier New",
                size=13,
                color="#ffffff",
            )
        ),

        xaxis=dict(

            title=dict(
                text="",
                font=dict(
                    color="#dddddd",
                ),
            ),

            tickfont=dict(
                family="Courier New",
                color="#c7c7c7",
            ),
        ),

        yaxis=dict(

            title=dict(
                text="RSSI (dBm)",
                font=dict(
                    family="Courier New",
                    color="#dddddd",
                ),
            ),

            tickfont=dict(
                family="Courier New",
                color="#c7c7c7",
            ),
        ),
    )


    st.plotly_chart(
        signal_fig,

        use_container_width=True,

        config={
            "displaylogo": False,
        },
    )


with quality_col:

    quality_fig = px.bar(

        network_summary,

        x="network_name",

        y="avg_speed",

        title="Average download speed",
    )


    quality_fig.update_layout(

        height=350,

        paper_bgcolor="#070707",

        plot_bgcolor="#070707",

        font=dict(
            family="Courier New",
            color="#ffffff",
        ),

        xaxis=dict(

            title=dict(
                text="",
                font=dict(
                    color="#dddddd",
                ),
            ),

            tickfont=dict(
                family="Courier New",
                color="#c7c7c7",
            ),
        ),

        yaxis=dict(

            title=dict(
                text="Mbps",
                font=dict(
                    family="Courier New",
                    color="#dddddd",
                ),
            ),

            tickfont=dict(
                family="Courier New",
                color="#c7c7c7",
            ),
        ),
    )


    st.plotly_chart(
        quality_fig,

        use_container_width=True,

        config={
            "displaylogo": False,
        },
    )


# ============================================================
# WI-FI CHANNEL ANALYSIS
# ============================================================

st.html(
    """
    <div class="section-title">
        WI-FI CHANNEL ANALYSIS
    </div>

    <div class="section-subtitle">
        Frequency distribution across observed networks
    </div>
    """
)


channel_summary = (
    df.groupby("frequency_mhz")
    .size()
    .reset_index(
        name="observations"
    )
)


channel_fig = px.bar(

    channel_summary,

    x="frequency_mhz",

    y="observations",

    title="Observed Wi-Fi frequencies",
)


channel_fig.update_layout(

    height=350,

    paper_bgcolor="#070707",

    plot_bgcolor="#070707",

    font=dict(
        family="Courier New",
        color="#ffffff",
    ),

    xaxis=dict(

        title=dict(
            text="Frequency (MHz)",
            font=dict(
                family="Courier New",
                color="#dddddd",
            ),
        ),

        tickfont=dict(
            family="Courier New",
            color="#c7c7c7",
        ),
    ),

    yaxis=dict(

        title=dict(
            text="Observations",
            font=dict(
                family="Courier New",
                color="#dddddd",
            ),
        ),

        tickfont=dict(
            family="Courier New",
            color="#c7c7c7",
        ),
    ),
)


st.plotly_chart(

    channel_fig,

    use_container_width=True,

    config={
        "displaylogo": False,
    },
)


# ============================================================
# WI-FI ENVIRONMENT
# ============================================================

st.html(
    """
    <div class="section-title">
        WI-FI ENVIRONMENT
    </div>

    <div class="section-subtitle">
        Network density and connected-device conditions
    </div>
    """
)


environment_col1, environment_col2 = st.columns(2)


with environment_col1:

    device_fig = px.bar(

        network_summary,

        x="network_name",

        y="avg_devices",

        title="Average connected devices",
    )


    device_fig.update_layout(

        height=330,

        paper_bgcolor="#070707",

        plot_bgcolor="#070707",

        font=dict(
            family="Courier New",
            color="#ffffff",
        ),

        xaxis=dict(

            title=dict(
                text="",
                font=dict(
                    color="#dddddd",
                ),
            ),

            tickfont=dict(
                family="Courier New",
                color="#c7c7c7",
            ),
        ),

        yaxis=dict(

            title=dict(
                text="Devices",
                font=dict(
                    family="Courier New",
                    color="#dddddd",
                ),
            ),

            tickfont=dict(
                family="Courier New",
                color="#c7c7c7",
            ),
        ),
    )


    st.plotly_chart(

        device_fig,

        use_container_width=True,

        config={
            "displaylogo": False,
        },
    )


with environment_col2:

    distance_fig = px.bar(

        network_summary,

        x="network_name",

        y="avg_distance",

        title="Average distance to access point",
    )


    distance_fig.update_layout(

        height=330,

        paper_bgcolor="#070707",

        plot_bgcolor="#070707",

        font=dict(
            family="Courier New",
            color="#ffffff",
        ),

        xaxis=dict(

            title=dict(
                text="",
                font=dict(
                    color="#dddddd",
                ),
            ),

            tickfont=dict(
                family="Courier New",
                color="#c7c7c7",
            ),
        ),

        yaxis=dict(

            title=dict(
                text="Distance (m)",
                font=dict(
                    family="Courier New",
                    color="#dddddd",
                ),
            ),

            tickfont=dict(
                family="Courier New",
                color="#c7c7c7",
            ),
        ),
    )


    st.plotly_chart(

        distance_fig,

        use_container_width=True,

        config={
            "displaylogo": False,
        },
    )


# ============================================================
# CONNECTION INTELLIGENCE
# ============================================================

st.html(
    """
    <div class="section-title">
        CONNECTION INTELLIGENCE
    </div>

    <div class="section-subtitle">
        Relationships between signal, distance, congestion and speed
    </div>
    """
)


relationship_fig = px.scatter(

    df,

    x="rssi_dbm",

    y="avg_download_mbps",

    color="network_name",

    hover_data=[
        "distance_to_ap_m",
        "connected_devices",
    ],

    title="Signal strength vs download speed",
)


relationship_fig.update_layout(

    height=420,

    paper_bgcolor="#070707",

    plot_bgcolor="#070707",

    font=dict(
        family="Courier New",
        color="#ffffff",
    ),

    legend=dict(

        font=dict(
            family="Courier New",
            size=13,
            color="#ffffff",
        ),

        title=dict(

            font=dict(
                family="Courier New",
                size=13,
                color="#ffffff",
            )
        ),
    ),

    xaxis=dict(

        title=dict(
            text="RSSI (dBm)",
            font=dict(
                family="Courier New",
                color="#dddddd",
            ),
        ),

        tickfont=dict(
            family="Courier New",
            color="#c7c7c7",
        ),
    ),

    yaxis=dict(

        title=dict(
            text="Download speed (Mbps)",
            font=dict(
                family="Courier New",
                color="#dddddd",
            ),
        ),

        tickfont=dict(
            family="Courier New",
            color="#c7c7c7",
        ),
    ),
)


st.plotly_chart(

    relationship_fig,

    use_container_width=True,

    config={
        "displaylogo": False,
    },
)


# ============================================================
# PERFORMANCE RELATIONSHIPS
# ============================================================

st.html(
    """
    <div class="section-title">
        PERFORMANCE RELATIONSHIPS
    </div>

    <div class="section-subtitle">
        Distance between device and access point versus network speed
    </div>
    """
)


distance_speed_fig = px.scatter(

    df,

    x="distance_to_ap_m",

    y="avg_download_mbps",

    color="network_name",

    hover_data=[
        "rssi_dbm",
        "connected_devices",
    ],

    title="Distance to access point vs speed",
)


distance_speed_fig.update_layout(

    height=400,

    paper_bgcolor="#070707",

    plot_bgcolor="#070707",

    font=dict(
        family="Courier New",
        color="#ffffff",
    ),

    legend=dict(

        font=dict(
            family="Courier New",
            size=13,
            color="#ffffff",
        ),

        title=dict(

            font=dict(
                family="Courier New",
                size=13,
                color="#ffffff",
            )
        ),
    ),

    xaxis=dict(

        title=dict(
            text="Distance (m)",
            font=dict(
                family="Courier New",
                color="#dddddd",
            ),
        ),

        tickfont=dict(
            family="Courier New",
            color="#c7c7c7",
        ),
    ),

    yaxis=dict(

        title=dict(
            text="Download speed (Mbps)",
            font=dict(
                family="Courier New",
                color="#dddddd",
            ),
        ),

        tickfont=dict(
            family="Courier New",
            color="#c7c7c7",
        ),
    ),
)


st.plotly_chart(

    distance_speed_fig,

    use_container_width=True,

    config={
        "displaylogo": False,
    },
)


# ============================================================
# ML INSIGHTS
# ============================================================

st.html(
    """
    <div class="section-title">
        ML INSIGHTS
    </div>

    <div class="section-subtitle">
        K-Means connectivity clusters generated in Phase 4
    </div>
    """
)


cluster_summary = (
    df.groupby("cluster")
    .agg(
        observations=("cluster", "size"),
        avg_rssi=("rssi_dbm", "mean"),
        avg_speed=("avg_download_mbps", "mean"),
        avg_devices=("connected_devices", "mean"),
        avg_distance=("distance_to_ap_m", "mean"),
    )
    .reset_index()
)


cluster_col1, cluster_col2 = st.columns([1, 2])


# ============================================================
# CUSTOM CLUSTER TABLE
# ============================================================

with cluster_col1:

    table_rows = ""

    for _, row in cluster_summary.iterrows():

        table_rows += f"""
        <tr>

            <td>
                {int(row["cluster"])}
            </td>

            <td>
                {int(row["observations"])}
            </td>

            <td>
                {row["avg_rssi"]:.2f}
            </td>

            <td>
                {row["avg_speed"]:.2f}
            </td>

            <td>
                {row["avg_devices"]:.2f}
            </td>

            <td>
                {row["avg_distance"]:.2f}
            </td>

        </tr>
        """


    st.html(
        f"""
        <div class="ml-table-wrapper">

            <table class="ml-table">

                <thead>

                    <tr>

                        <th>CLUSTER</th>
                        <th>OBS.</th>
                        <th>RSSI</th>
                        <th>SPEED</th>
                        <th>DEVICES</th>
                        <th>DIST.</th>

                    </tr>

                </thead>

                <tbody>

                    {table_rows}

                </tbody>

            </table>

        </div>
        """
    )


# ============================================================
# CLUSTER CHART
# ============================================================

with cluster_col2:

    cluster_fig = px.bar(

        cluster_summary,

        x="cluster",

        y="avg_speed",

        title="Average speed by connectivity cluster",
    )


    cluster_fig.update_layout(

        height=330,

        paper_bgcolor="#070707",

        plot_bgcolor="#070707",

        font=dict(
            family="Courier New",
            color="#ffffff",
        ),

        xaxis=dict(

            title=dict(
                text="Cluster",
                font=dict(
                    family="Courier New",
                    color="#dddddd",
                ),
            ),

            tickfont=dict(
                family="Courier New",
                color="#c7c7c7",
            ),
        ),

        yaxis=dict(

            title=dict(
                text="Mbps",
                font=dict(
                    family="Courier New",
                    color="#dddddd",
                ),
            ),

            tickfont=dict(
                family="Courier New",
                color="#c7c7c7",
            ),
        ),
    )


    st.plotly_chart(

        cluster_fig,

        use_container_width=True,

        config={
            "displaylogo": False,
        },
    )


# ============================================================
# TASK SUITABILITY
# ============================================================

st.html(
    """
    <div class="section-title">
        TASK SUITABILITY
    </div>

    <div class="section-subtitle">
        Task-aware network suitability based on WiSense scoring logic
    </div>
    """
)


TASK_WEIGHTS = {

    "General": {
        "speed": 0.35,
        "signal": 0.25,
        "stability": 0.15,
        "congestion": 0.15,
        "distance": 0.10,
    },

    "Browsing": {
        "speed": 0.25,
        "signal": 0.25,
        "stability": 0.20,
        "congestion": 0.20,
        "distance": 0.10,
    },

    "Video Call": {
        "speed": 0.25,
        "signal": 0.25,
        "stability": 0.25,
        "congestion": 0.20,
        "distance": 0.05,
    },

    "Gaming": {
        "speed": 0.20,
        "signal": 0.25,
        "stability": 0.30,
        "congestion": 0.20,
        "distance": 0.05,
    },

    "Download": {
        "speed": 0.55,
        "signal": 0.20,
        "stability": 0.10,
        "congestion": 0.10,
        "distance": 0.05,
    },
}


# ============================================================
# SCORING
# ============================================================

def higher_score(
    value: float,
    poor: float,
    excellent: float,
) -> float:

    if value <= poor:
        return 0.0

    if value >= excellent:
        return 100.0

    return (
        (value - poor)
        / (excellent - poor)
        * 100.0
    )


def lower_score(
    value: float,
    excellent: float,
    poor: float,
) -> float:

    if value <= excellent:
        return 100.0

    if value >= poor:
        return 0.0

    return (
        (poor - value)
        / (poor - excellent)
        * 100.0
    )


recommendation_data = network_summary.copy()


recommendation_data["speed_score"] = (
    recommendation_data["avg_speed"]
    .apply(
        lambda value:
        higher_score(
            value,
            poor=10,
            excellent=100,
        )
    )
)


recommendation_data["signal_score"] = (
    recommendation_data["avg_rssi"]
    .apply(
        lambda value:
        higher_score(
            value,
            poor=-85,
            excellent=-45,
        )
    )
)


recommendation_data["stability_score"] = (
    recommendation_data["avg_signal_std"]
    .apply(
        lambda value:
        lower_score(
            value,
            excellent=1,
            poor=8,
        )
    )
)


recommendation_data["congestion_score"] = (
    recommendation_data["avg_devices"]
    .apply(
        lambda value:
        lower_score(
            value,
            excellent=2,
            poor=15,
        )
    )
)


recommendation_data["distance_score"] = (
    recommendation_data["avg_distance"]
    .apply(
        lambda value:
        lower_score(
            value,
            excellent=5,
            poor=50,
        )
    )
)


weights = TASK_WEIGHTS[task]


recommendation_data["suitability_score"] = (

    recommendation_data["speed_score"]
    * weights["speed"]

    + recommendation_data["signal_score"]
    * weights["signal"]

    + recommendation_data["stability_score"]
    * weights["stability"]

    + recommendation_data["congestion_score"]
    * weights["congestion"]

    + recommendation_data["distance_score"]
    * weights["distance"]
)


recommendation_data["suitability_score"] = (

    recommendation_data[
        "suitability_score"
    ]

    .clip(0, 100)

    .round(2)
)


recommendation_data = (
    recommendation_data
    .sort_values(
        "suitability_score",
        ascending=False,
    )
)


def suitability_label(
    score: float,
) -> str:

    if score >= 80:
        return "Excellent"

    if score >= 65:
        return "Good"

    if score >= 50:
        return "Moderate"

    return "Limited"


recommendation_data["suitability"] = (
    recommendation_data[
        "suitability_score"
    ]
    .apply(suitability_label)
)


# ============================================================
# NETWORK RECOMMENDATION
# ============================================================

recommendation_col1, recommendation_col2 = (
    st.columns([1, 2])
)


with recommendation_col1:

    recommended = recommendation_data.iloc[0]


    st.html(
        f"""
        <div class="metric-card">

            <div class="metric-label">
                RECOMMENDED NETWORK
            </div>

            <div class="metric-value">
                {recommended["network_name"]}
            </div>

            <div class="metric-detail">
                TASK:
                {task.upper()}
            </div>

            <div class="metric-detail">
                SCORE:
                {recommended["suitability_score"]:.2f}/100
                ·
                {recommended["suitability"]}
            </div>

        </div>
        """
    )


with recommendation_col2:

    recommendation_fig = px.bar(

        recommendation_data,

        x="network_name",

        y="suitability_score",

        title=
            f"Network suitability — {task}",
    )


    recommendation_fig.update_layout(

        height=330,

        paper_bgcolor="#070707",

        plot_bgcolor="#070707",

        font=dict(
            family="Courier New",
            color="#ffffff",
        ),

        xaxis=dict(

            title=dict(
                text="",
                font=dict(
                    color="#dddddd",
                ),
            ),

            tickfont=dict(
                family="Courier New",
                color="#c7c7c7",
            ),
        ),

        yaxis=dict(

            range=[
                0,
                100,
            ],

            title=dict(
                text="Suitability score",
                font=dict(
                    family="Courier New",
                    color="#dddddd",
                ),
            ),

            tickfont=dict(
                family="Courier New",
                color="#c7c7c7",
            ),
        ),
    )


    st.plotly_chart(

        recommendation_fig,

        use_container_width=True,

        config={
            "displaylogo": False,
        },
    )


# ============================================================
# PERFORMANCE TRENDS
# ============================================================

st.html(
    """
    <div class="section-title">
        PERFORMANCE TRENDS
    </div>

    <div class="section-subtitle">
        Recorded changes in download speed, signal strength and network performance
    </div>
    """
)


# ------------------------------------------------------------
# Aggregate the raw 5-minute observations into 30-minute
# intervals. This keeps the real data while making the trend
# readable instead of plotting 1,000 noisy points.
# ------------------------------------------------------------

trend_source = df.copy()

trend_source["trend_period"] = (
    trend_source["timestamp"]
    .dt.floor("30min")
)


trend_data = (
    trend_source
    .groupby("trend_period", as_index=False)
    .agg(
        avg_speed=(
            "avg_download_mbps",
            "mean",
        ),
        avg_rssi=(
            "rssi_dbm",
            "mean",
        ),
        avg_devices=(
            "connected_devices",
            "mean",
        ),
    )
    .sort_values("trend_period")
)


# ------------------------------------------------------------
# DOWNLOAD SPEED TREND
# ------------------------------------------------------------

st.html(
    """
    <div class="section-subtitle">
        Download speed over the recorded observation period
    </div>
    """
)


speed_trend_fig = px.line(
    trend_data,
    x="trend_period",
    y="avg_speed",
    markers=True,
    title="Average download speed over time",
)


speed_trend_fig.update_traces(
    line=dict(
        color="#ffffff",
        width=2,
    ),
    marker=dict(
        color="#ffffff",
        size=4,
    ),
)


speed_trend_fig.update_layout(
    height=390,
    paper_bgcolor="#070707",
    plot_bgcolor="#070707",
    font=dict(
        family="Courier New",
        color="#ffffff",
    ),
    hoverlabel=dict(
        bgcolor="#101010",
        font=dict(
            family="Courier New",
            color="#ffffff",
        ),
    ),
    title=dict(
        font=dict(
            family="Courier New",
            size=16,
            color="#ffffff",
        )
    ),
    xaxis=dict(
        title=dict(
            text="Time",
            font=dict(
                family="Courier New",
                color="#dddddd",
            ),
        ),
        tickfont=dict(
            family="Courier New",
            color="#c7c7c7",
        ),
        gridcolor="#333333",
        zerolinecolor="#444444",
    ),
    yaxis=dict(
        title=dict(
            text="Mbps",
            font=dict(
                family="Courier New",
                color="#dddddd",
            ),
        ),
        tickfont=dict(
            family="Courier New",
            color="#c7c7c7",
        ),
        gridcolor="#333333",
        zerolinecolor="#444444",
    ),
    margin=dict(
        l=60,
        r=25,
        t=60,
        b=55,
    ),
)


st.plotly_chart(
    speed_trend_fig,
    use_container_width=True,
    config={
        "displaylogo": False,
    },
)


# ------------------------------------------------------------
# SIGNAL STRENGTH TREND
# ------------------------------------------------------------

st.html(
    """
    <div class="section-subtitle">
        Average Wi-Fi signal strength over the recorded observation period
    </div>
    """
)


signal_trend_fig = px.line(
    trend_data,
    x="trend_period",
    y="avg_rssi",
    markers=True,
    title="Average signal strength over time",
)


signal_trend_fig.update_traces(
    line=dict(
        color="#ffffff",
        width=2,
    ),
    marker=dict(
        color="#ffffff",
        size=4,
    ),
)


signal_trend_fig.update_layout(
    height=390,
    paper_bgcolor="#070707",
    plot_bgcolor="#070707",
    font=dict(
        family="Courier New",
        color="#ffffff",
    ),
    hoverlabel=dict(
        bgcolor="#101010",
        font=dict(
            family="Courier New",
            color="#ffffff",
        ),
    ),
    title=dict(
        font=dict(
            family="Courier New",
            size=16,
            color="#ffffff",
        )
    ),
    xaxis=dict(
        title=dict(
            text="Time",
            font=dict(
                family="Courier New",
                color="#dddddd",
            ),
        ),
        tickfont=dict(
            family="Courier New",
            color="#c7c7c7",
        ),
        gridcolor="#333333",
        zerolinecolor="#444444",
    ),
    yaxis=dict(
        title=dict(
            text="RSSI (dBm)",
            font=dict(
                family="Courier New",
                color="#dddddd",
            ),
        ),
        tickfont=dict(
            family="Courier New",
            color="#c7c7c7",
        ),
        gridcolor="#333333",
        zerolinecolor="#444444",
    ),
    margin=dict(
        l=60,
        r=25,
        t=60,
        b=55,
    ),
)


st.plotly_chart(
    signal_trend_fig,
    use_container_width=True,
    config={
        "displaylogo": False,
    },
)


# ------------------------------------------------------------
# NETWORK PERFORMANCE
# ------------------------------------------------------------

st.html(
    """
    <div class="section-subtitle">
        Average download performance across observed Wi-Fi networks
    </div>
    """
)


network_trend_data = (
    network_summary[[
        "network_name",
        "avg_speed",
    ]]
    .sort_values(
        "avg_speed",
        ascending=False,
    )
)


network_performance_fig = px.bar(
    network_summary,
    x="network_name",
    y="avg_speed",
    title="Average download speed by network",
    color_discrete_sequence=["#0088ff"],
)

network_performance_fig.update_traces(
    marker_color="#0088ff",
    texttemplate="%{y:.1f} Mbps",
    textposition="outside",
    textfont=dict(
        family="Courier New",
        color="#ffffff",
        size=13,
    ),
)

network_performance_fig.update_layout(
    height=400,
    paper_bgcolor="#070707",
    plot_bgcolor="#070707",
    font=dict(
        family="Courier New",
        color="#ffffff",
    ),
    xaxis=dict(
        title=dict(
            text="Network",
            font=dict(
                family="Courier New",
                color="#dddddd",
            ),
        ),
        tickfont=dict(
            family="Courier New",
            color="#c7c7c7",
        ),
    ),
    yaxis=dict(
        title=dict(
            text="Average speed (Mbps)",
            font=dict(
                family="Courier New",
                color="#dddddd",
            ),
        ),
        tickfont=dict(
            family="Courier New",
            color="#c7c7c7",
        ),
    ),
)

st.plotly_chart(
    network_performance_fig,
    use_container_width=True,
    config={
        "displaylogo": False,
    },
)

# FOOTER
# ============================================================

st.html(
    """
    <div class="wisense-footer">

        WISENSE · WI-FI INTELLIGENCE &amp; ANALYTICS
        · STREAMLIT INTERFACE · PHASE 7

    </div>
    """
)