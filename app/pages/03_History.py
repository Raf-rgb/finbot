import logging
import pandas as pd
import streamlit as st
from datetime import datetime

from utils.database import get_collection

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")

st.set_page_config(
    page_title="History | Finbot",
    page_icon="📋",
    layout="wide"
)

def get_all_movements():
    try:
        finance_collection = get_collection(
            st.secrets.db_credentials.uri,
            st.secrets.db_credentials.database_name,
            st.secrets.db_collections.finance_collection_name
        )

        all_movements = finance_collection.find()

        if all_movements:
            return pd.DataFrame(list(all_movements))
        else:
            return None
    except Exception as e:
        logging.error(f"Error getting the movements collection: {e}")
        return None

def show_history_page():
    st.title("📋 History")

    movements = get_all_movements()
    
    if movements is None or movements.empty:
        st.warning("No movements found")
    else:
        movements['_id'] = movements['_id'].astype(str)


        categories     = movements["category"].unique()
        source_names   = movements["source_name"].unique()
        movement_types = movements["movement_type"].unique()
        source_types   = movements["source_type"].unique()

        with st.expander("🔍 Filters"):

            col_1, col_2 = st.columns(2)

            with col_1:
                selected_category      = st.selectbox("Select a category", categories, index=None)
                selected_source_name   = st.selectbox("Select a source name", source_names, index=None)
                init_date              = st.date_input("Select a initial date", movements["datetime"].min())
            
            with col_2:
                selected_movement_type = st.selectbox("Select a movement type", movement_types, index=None)
                selected_source_type   = st.selectbox("Select a source type", source_types, index=None)
                end_date               = st.date_input("Select a end date", movements["datetime"].max())

            if selected_category:
                movements = movements[movements["category"] == selected_category]
            
            if selected_source_name:
                movements = movements[movements["source_name"] == selected_source_name]
            
            if selected_movement_type:
                movements = movements[movements["movement_type"] == selected_movement_type]
            
            if selected_source_type:
                movements = movements[movements["source_type"] == selected_source_type]
            
            if init_date and end_date:
                if init_date > end_date:
                    st.warning("The initial date must be less than the end date")
                elif init_date == end_date:
                    movements["datetime"] = pd.to_datetime(movements["datetime"])
                    movements = movements[movements["datetime"].dt.date == init_date]
                else:
                    movements["datetime"] = pd.to_datetime(movements["datetime"])  # Convertir a datetime
                    logging.info(f"Filtering movements from {init_date} to {end_date}")
                    movements = movements[(movements["datetime"].dt.date >= init_date) & (movements["datetime"].dt.date <= end_date)]

        st.subheader("📜 Movements")
        st.dataframe(
            movements.drop(columns=["_id", "username"]),
            column_config= {
                "datetime": "📅 Fecha y hora",
                "name": "👤 Movimiento",
                "description": "📝 Descripción",
                "movement_type": "🔘 Tipo",
                "source_name": "💳 Fuente",
                "source_type": "🌀 Tipo",
                "category": "🏷️ Categoría",
                "amount": "💲 Cantidad"
            },
            hide_index=True,
            use_container_width=True
        )

if "authentication_status" in st.session_state and st.session_state.authentication_status:
    show_history_page()
else:
    st.switch_page("./Home.py")