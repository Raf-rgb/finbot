import logging
import streamlit as st

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")

st.set_page_config(
    page_title="Dashboard | Finbot",
    page_icon="📊",
    layout="wide"
)

def show_dashboard_page():
    st.title("📊 Dashboard")

if "authentication_status" in st.session_state and st.session_state.authentication_status:
    show_dashboard_page()
else:
    st.switch_page("./main.py")