import streamlit as st

st.set_page_config(
    page_title="WiSense Test",
    page_icon="📡",
    layout="wide"
)

st.markdown(
    """
    <style>
    .stApp {
        background-color: #050505;
        color: white;
    }

    h1, h2, h3, p {
        color: white;
    }

    </style>
    """,
    unsafe_allow_html=True
)

st.title("WiSense")
st.subheader("Wi-Fi Intelligence & Analytics")

st.success("Application is running successfully!")

col1, col2, col3 = st.columns(3)

col1.metric("Signal Strength", "99%")
col2.metric("Channel", "11")
col3.metric("Status", "Connected")

st.write("Welcome to WiSense.")