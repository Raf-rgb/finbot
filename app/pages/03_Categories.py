import logging
import streamlit as st

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")

st.set_page_config(
    page_title="Categories | Finbot",
    page_icon="🏷️",
    layout="wide"
)

def show_categories_page():
    st.title("🏷️ Categories")

if "authentication_status" in st.session_state and st.session_state.authentication_status:
    show_categories_page()
else:
    st.switch_page("./main.py")