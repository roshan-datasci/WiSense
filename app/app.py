import streamlit as st


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="WiSense — Wi-Fi Intelligence & Analytics",
    page_icon="📶",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# GLOBAL UI
# ============================================================

st.html("""
<style>

html,
body,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > section,
[data-testid="stMain"] {
    background: #050505 !important;
}

[data-testid="stHeader"] {
    background: #050505 !important;
}

[data-testid="stSidebar"] {
    display: none;
}

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}


/* ==========================================================
   DOT GRID
   ========================================================== */

[data-testid="stAppViewContainer"]::before {
    content: "";

    position: fixed;
    inset: 0;

    pointer-events: none;

    background-image:
        radial-gradient(
            circle,
            rgba(255,255,255,0.16) 1px,
            transparent 1px
        );

    background-size: 22px 22px;

    opacity: 0.35;

    z-index: 0;
}


/* ==========================================================
   MAIN CONTAINER
   ========================================================== */

.block-container {
    max-width: 1400px !important;

    padding-top: 2rem !important;
    padding-bottom: 3rem !important;

    position: relative;
    z-index: 1;
}


/* ==========================================================
   HEADER
   ========================================================== */

.wisense-header {
    text-align: center;

    padding: 1.5rem 1rem 1.8rem 1rem;

    margin-bottom: 1.2rem;

    border-top: 1px solid #303030;
    border-bottom: 1px solid #303030;
}

.wisense-title {
    margin: 0;

    color: #ffffff;

    font-family: "Courier New", monospace;

    font-size: clamp(2rem, 5vw, 4rem);

    font-weight: 700;

    letter-spacing: 0.18em;
}

.wisense-subtitle {
    margin-top: 0.55rem;

    color: #8e8e8e;

    font-family: "Courier New", monospace;

    font-size: clamp(0.72rem, 1.5vw, 1rem);

    letter-spacing: 0.22em;
}


/* ==========================================================
   NAV
   ========================================================== */

.wisense-nav {
    display: flex;

    justify-content: center;
    align-items: center;

    gap: 2.5rem;

    padding: 0.8rem 1rem;

    margin-bottom: 1.4rem;

    border-bottom: 1px solid #242424;

    flex-wrap: wrap;
}

.wisense-nav-item {
    color: #666666;

    font-family: "Courier New", monospace;

    font-size: 0.76rem;

    font-weight: 600;

    letter-spacing: 0.12em;
}

.wisense-nav-item.active {
    color: #ffffff;
}


/* ==========================================================
   LIVE
   ========================================================== */

.wisense-live {
    text-align: center;

    color: #ffffff;

    font-family: "Courier New", monospace;

    font-size: 0.78rem;

    letter-spacing: 0.14em;

    margin-bottom: 1.5rem;
}


/* ==========================================================
   TASK
   ========================================================== */

.task-selector-label {
    color: #777777;

    font-family: "Courier New", monospace;

    font-size: 0.7rem;

    letter-spacing: 0.13em;

    margin-bottom: 0.35rem;
}

div[data-testid="stSelectbox"] {
    max-width: 320px;

    margin-bottom: 1.5rem;
}

div[data-testid="stSelectbox"] label {
    display: none;
}

div[data-baseweb="select"] > div {
    background: #080808 !important;

    border: 1px solid #303030 !important;

    border-radius: 0 !important;

    color: #ffffff !important;

    min-height: 42px;
}

div[data-baseweb="select"] span {
    color: #ffffff !important;

    font-family: "Courier New", monospace !important;
}

div[data-baseweb="select"] svg {
    fill: #ffffff !important;
}


/* ==========================================================
   PANELS
   ========================================================== */

.wisense-panel {
    background: rgba(8,8,8,0.96);

    border: 1px solid #292929;

    padding: 1.5rem;

    margin-top: 1.2rem;
}

.panel-label {
    color: #ffffff;

    font-family: "Courier New", monospace;

    font-size: 0.82rem;

    font-weight: 700;

    letter-spacing: 0.14em;

    margin-bottom: 1.2rem;
}

.panel-muted {
    color: #666666;

    font-family: "Courier New", monospace;

    font-size: 0.72rem;

    line-height: 1.8;
}


/* ==========================================================
   PLACEHOLDER VISUAL
   ========================================================== */

.placeholder-box {
    min-height: 230px;

    border: 1px solid #252525;

    background: #070707;

    display: flex;

    align-items: center;

    justify-content: center;

    text-align: center;

    padding: 2rem;
}

.placeholder-title {
    color: #777777;

    font-family: "Courier New", monospace;

    font-size: 0.75rem;

    letter-spacing: 0.12em;
}

.placeholder-text {
    color: #4f4f4f;

    font-family: "Courier New", monospace;

    font-size: 0.68rem;

    margin-top: 0.7rem;

    line-height: 1.7;
}


/* ==========================================================
   METRIC GRID
   ========================================================== */

.metric-grid {
    display: grid;

    grid-template-columns:
        repeat(5, minmax(0, 1fr));

    gap: 1px;

    background: #292929;

    border: 1px solid #292929;
}

.metric {
    background: #080808;

    padding: 1.15rem;

    min-height: 92px;
}

.metric-label {
    color: #666666;

    font-family: "Courier New", monospace;

    font-size: 0.67rem;

    letter-spacing: 0.12em;

    margin-bottom: 0.65rem;
}

.metric-value {
    color: #ffffff;

    font-family: "Courier New", monospace;

    font-size: 1rem;

    font-weight: 600;
}


/* ==========================================================
   STATUS GRID
   ========================================================== */

.status-grid {
    display: grid;

    grid-template-columns:
        repeat(3, minmax(0, 1fr));

    gap: 1px;

    background: #292929;

    border: 1px solid #292929;
}

.status-item {
    background: #080808;

    padding: 1rem;
}

.status-label {
    color: #666666;

    font-family: "Courier New", monospace;

    font-size: 0.65rem;

    letter-spacing: 0.1em;

    margin-bottom: 0.45rem;
}

.status-value {
    color: #ffffff;

    font-family: "Courier New", monospace;

    font-size: 0.9rem;
}


/* ==========================================================
   TABLE PLACEHOLDER
   ========================================================== */

.environment-table {
    width: 100%;

    border-collapse: collapse;

    font-family: "Courier New", monospace;

    font-size: 0.72rem;
}

.environment-table th {
    color: #666666;

    text-align: left;

    font-weight: normal;

    padding: 0.75rem;

    border-bottom: 1px solid #292929;
}

.environment-table td {
    color: #888888;

    padding: 0.75rem;

    border-bottom: 1px solid #1d1d1d;
}


/* ==========================================================
   FOOTER
   ========================================================== */

.wisense-footer {
    text-align: center;

    color: #4f4f4f;

    font-family: "Courier New", monospace;

    font-size: 0.65rem;

    letter-spacing: 0.1em;

    margin-top: 3rem;

    padding-top: 1rem;

    border-top: 1px solid #222222;
}


/* ==========================================================
   RESPONSIVE
   ========================================================== */

@media (max-width: 850px) {

    .metric-grid {
        grid-template-columns: 1fr 1fr;
    }

    .status-grid {
        grid-template-columns: 1fr;
    }

    .wisense-nav {
        gap: 1.3rem;
    }
}


@media (max-width: 520px) {

    .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }

    .wisense-nav {
        gap: 0.8rem;
    }

    .wisense-nav-item {
        font-size: 0.63rem;
    }

    .metric-grid {
        grid-template-columns: 1fr;
    }

    .wisense-panel {
        padding: 1rem;
    }
}

</style>
""")


# ============================================================
# HEADER
# ============================================================

st.html("""
<div class="wisense-header">

    <div class="wisense-title">
        WISENSE
    </div>

    <div class="wisense-subtitle">
        WI-FI INTELLIGENCE &amp; ANALYTICS
    </div>

</div>
""")


# ============================================================
# NAVIGATION
# ============================================================

st.html("""
<div class="wisense-nav">

    <div class="wisense-nav-item active">
        OVERVIEW
    </div>

    <div class="wisense-nav-item">
        MAP
    </div>

    <div class="wisense-nav-item">
        SIGNAL
    </div>

    <div class="wisense-nav-item">
        CHANNELS
    </div>

    <div class="wisense-nav-item">
        INSIGHTS
    </div>

</div>
""")


# ============================================================
# LIVE STATUS
# ============================================================

st.html("""
<div class="wisense-live">
    ● LIVE
</div>
""")


# ============================================================
# TASK SELECTOR
# ============================================================

st.html("""
<div class="task-selector-label">
    TASK SELECTOR
</div>
""")

task = st.selectbox(
    "Task",
    [
        "General",
        "Gaming",
        "Video Call",
        "Browsing",
        "Download",
        "Social Media",
    ],
    index=0,
    label_visibility="collapsed",
)


# ============================================================
# LIVE NETWORK OVERVIEW
# ============================================================

st.html("""
<div class="wisense-panel">

    <div class="panel-label">
        LIVE NETWORK OVERVIEW
    </div>

    <div class="metric-grid">

        <div class="metric">
            <div class="metric-label">SSID</div>
            <div class="metric-value">---</div>
        </div>

        <div class="metric">
            <div class="metric-label">SIGNAL</div>
            <div class="metric-value">-- dBm</div>
        </div>

        <div class="metric">
            <div class="metric-label">SPEED</div>
            <div class="metric-value">-- Mbps</div>
        </div>

        <div class="metric">
            <div class="metric-label">BAND</div>
            <div class="metric-value">---</div>
        </div>

        <div class="metric">
            <div class="metric-label">QUALITY</div>
            <div class="metric-value">-- / 100</div>
        </div>

    </div>

    <div style="height:18px;"></div>

    <div class="panel-muted">
        Network telemetry will be connected in a later phase.
    </div>

</div>
""")


# ============================================================
# INTERACTIVE WI-FI MAP
# ============================================================

st.html("""
<div class="wisense-panel">

    <div class="panel-label">
        INTERACTIVE WI-FI MAP
    </div>

    <div class="placeholder-box">

        <div>

            <div class="placeholder-title">
                SPATIAL VISUALIZATION
            </div>

            <div class="placeholder-text">
                Access-point and signal-location data<br>
                will be visualized here in Phase 8.
            </div>

        </div>

    </div>

</div>
""")


# ============================================================
# SIGNAL + QUALITY
# ============================================================

st.html("""
<div style="
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:1.2rem;
">

    <div class="wisense-panel">

        <div class="panel-label">
            SIGNAL STRENGTH
        </div>

        <div class="placeholder-box">

            <div>
                <div class="placeholder-title">
                    RSSI HISTORY
                </div>

                <div class="placeholder-text">
                    Time-series signal data<br>
                    will be connected in Phase 7.
                </div>
            </div>

        </div>

    </div>


    <div class="wisense-panel">

        <div class="panel-label">
            NETWORK QUALITY
        </div>

        <div class="placeholder-box">

            <div>
                <div class="placeholder-title">
                    QUALITY SCORE
                </div>

                <div class="placeholder-text">
                    Quality metrics will be<br>
                    calculated from observed data.
                </div>
            </div>

        </div>

    </div>

</div>
""")


# ============================================================
# CHANNEL ANALYSIS
# ============================================================

st.html("""
<div class="wisense-panel">

    <div class="panel-label">
        WI-FI CHANNEL ANALYSIS
    </div>

    <div class="placeholder-box">

        <div>

            <div class="placeholder-title">
                CHANNEL / INTERFERENCE ANALYSIS
            </div>

            <div class="placeholder-text">
                Channel utilization and neighboring-network<br>
                analysis will be implemented in Phase 7.
            </div>

        </div>

    </div>

</div>
""")


# ============================================================
# NETWORK ENVIRONMENT
# ============================================================

st.html("""
<div class="wisense-panel">

    <div class="panel-label">
        WI-FI ENVIRONMENT
    </div>

    <table class="environment-table">

        <thead>
            <tr>
                <th>NETWORK</th>
                <th>BAND</th>
                <th>CHANNEL</th>
                <th>SIGNAL</th>
                <th>SPEED</th>
            </tr>
        </thead>

        <tbody>

            <tr>
                <td>---</td>
                <td>---</td>
                <td>---</td>
                <td>---</td>
                <td>---</td>
            </tr>

            <tr>
                <td>---</td>
                <td>---</td>
                <td>---</td>
                <td>---</td>
                <td>---</td>
            </tr>

            <tr>
                <td>---</td>
                <td>---</td>
                <td>---</td>
                <td>---</td>
                <td>---</td>
            </tr>

        </tbody>

    </table>

    <div style="height:14px;"></div>

    <div class="panel-muted">
        Environment data will be populated by the Wi-Fi
        collection layer.
    </div>

</div>
""")


# ============================================================
# CONNECTION INTELLIGENCE
# ============================================================

st.html("""
<div style="
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:1.2rem;
">

    <div class="wisense-panel">

        <div class="panel-label">
            CONNECTION INTELLIGENCE
        </div>

        <div class="status-grid">

            <div class="status-item">
                <div class="status-label">
                    SIGNAL ↔ SPEED
                </div>

                <div class="status-value">
                    ---
                </div>
            </div>

            <div class="status-item">
                <div class="status-label">
                    DEVICES ↔ SPEED
                </div>

                <div class="status-value">
                    ---
                </div>
            </div>

            <div class="status-item">
                <div class="status-label">
                    DISTANCE ↔ SPEED
                </div>

                <div class="status-value">
                    ---
                </div>
            </div>

        </div>

    </div>


    <div class="wisense-panel">

        <div class="panel-label">
            PERFORMANCE RELATIONSHIPS
        </div>

        <div class="placeholder-box">

            <div>
                <div class="placeholder-title">
                    CORRELATION ANALYSIS
                </div>

                <div class="placeholder-text">
                    Statistical relationships will be<br>
                    calculated during Phase 3.
                </div>
            </div>

        </div>

    </div>

</div>
""")


# ============================================================
# ML INSIGHTS
# ============================================================

st.html("""
<div class="wisense-panel">

    <div class="panel-label">
        ML INSIGHTS
    </div>

    <div class="placeholder-box">

        <div>

            <div class="placeholder-title">
                CONNECTIVITY CLUSTERS
            </div>

            <div class="placeholder-text">
                K-Means connectivity patterns will appear here<br>
                after the machine-learning phase.
            </div>

        </div>

    </div>

    <div style="height:14px;"></div>

    <div class="panel-muted">
        Features planned:
        signal • stability • speed • devices • distance
    </div>

</div>
""")


# ============================================================
# TASK SUITABILITY + RECOMMENDATION
# ============================================================

st.html("""
<div style="
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:1.2rem;
">

    <div class="wisense-panel">

        <div class="panel-label">
            TASK SUITABILITY
        </div>

        <div class="status-grid">

            <div class="status-item">
                <div class="status-label">GAMING</div>
                <div class="status-value">-- %</div>
            </div>

            <div class="status-item">
                <div class="status-label">VIDEO CALL</div>
                <div class="status-value">-- %</div>
            </div>

            <div class="status-item">
                <div class="status-label">BROWSING</div>
                <div class="status-value">-- %</div>
            </div>

        </div>

    </div>


    <div class="wisense-panel">

        <div class="panel-label">
            NETWORK RECOMMENDATION
        </div>

        <div class="placeholder-box">

            <div>

                <div class="placeholder-title">
                    BEST OBSERVED NETWORK
                </div>

                <div class="placeholder-text">
                    Recommendation engine will be<br>
                    connected during Phase 5.
                </div>

            </div>

        </div>

    </div>

</div>
""")


# ============================================================
# PERFORMANCE TRENDS
# ============================================================

st.html("""
<div class="wisense-panel">

    <div class="panel-label">
        PERFORMANCE TRENDS
    </div>

    <div class="placeholder-box">

        <div>

            <div class="placeholder-title">
                PERFORMANCE HISTORY
            </div>

            <div class="placeholder-text">
                Speed • Signal • Devices<br><br>
                Historical trends will be visualized<br>
                after the analytical pipeline is connected.
            </div>

        </div>

    </div>

</div>
""")


# ============================================================
# PLATFORM STATUS
# ============================================================

st.html("""
<div class="wisense-panel">

    <div class="panel-label">
        WISENSE DATA SCIENCE PLATFORM
    </div>

    <div class="panel-muted">
        Streamlit dashboard foundation initialized successfully.
    </div>

    <div style="height:16px;"></div>

    <div class="status-grid">

        <div class="status-item">
            <div class="status-label">
                DATA COLLECTION
            </div>
            <div class="status-value">
                PENDING
            </div>
        </div>

        <div class="status-item">
            <div class="status-label">
                ANALYTICS
            </div>
            <div class="status-value">
                PENDING
            </div>
        </div>

        <div class="status-item">
            <div class="status-label">
                MACHINE LEARNING
            </div>
            <div class="status-value">
                PENDING
            </div>
        </div>

    </div>

</div>
""")


# ============================================================
# FOOTER
# ============================================================

st.html("""
<div class="wisense-footer">

    WISENSE
    &nbsp;•&nbsp;
    WI-FI INTELLIGENCE &amp; ANALYTICS

</div>
""")