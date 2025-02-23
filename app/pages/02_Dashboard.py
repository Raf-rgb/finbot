import logging
import pandas as pd
import streamlit as st

from utils.database import get_collection
from utils.plotter import *

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")

st.set_page_config(
    page_title="Dashboard | Finbot",
    page_icon="📊",
    layout="wide"
)

if "movements" not in st.session_state:
    st.session_state.movements = None

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

def show_metrics_by_movement_type(movements: pd.DataFrame, movement_type: MovementType):
    current_month_total = get_current_month_movements(movements, movement_type)
    last_month_total    = get_last_month_movements(movements, movement_type)

    current_week_total  = get_current_week_movements(movements, movement_type)
    last_week_total     = get_last_week_movements(movements, movement_type)

    current_day_total   = get_current_day_movements(movements, movement_type)
    last_day_total      = get_last_day_movements(movements, movement_type)

    col_1, col_2, col_3 = st.columns(3)

    with col_1:
        st.metric(
            f"Total {movement_type.value} this Month",
            f"${current_month_total:,.2f}",
            delta=last_month_total,
            delta_color="inverse" if current_month_total > last_month_total else "normal",
            border=True
        )
    
    with col_2:
        st.metric(
            f"Total {movement_type.value} this Week",
            f"${current_week_total:,.2f}",
            delta=last_week_total,
            delta_color="inverse" if current_week_total > last_week_total else "normal",
            border=True
        )
    
    with col_3:
        st.metric(
            f"Total {movement_type.value} today",
            f"${current_day_total:,.2f}",
            delta=last_day_total,
            delta_color="inverse" if current_day_total > last_day_total else "normal",
            border=True
        )

@st.fragment(run_every=10)
def show_metrics_cards(movements: pd.DataFrame):
    show_metrics_by_movement_type(movements, MovementType.EXPENSE)
    show_metrics_by_movement_type(movements, MovementType.INCOME)

@st.fragment(run_every=10)
def show_plots(movements: pd.DataFrame):
    col_1, col_2 = st.columns(2)

    with col_1:
        st.plotly_chart(plot_pie_movement_by_category(movements, MovementType.EXPENSE))
        st.plotly_chart(plot_total_movements_by_month(movements, MovementType.EXPENSE))
        st.plotly_chart(plot_line_total_movements_by_month(movements, MovementType.EXPENSE))
        st.plotly_chart(plot_bar_movement_by_source_name(movements, MovementType.EXPENSE))
    
    with col_2:
        st.plotly_chart(plot_pie_movement_by_category(movements, MovementType.INCOME))
        st.plotly_chart(plot_total_movements_by_month(movements, MovementType.INCOME))
        st.plotly_chart(plot_line_total_movements_by_month(movements, MovementType.INCOME))
        st.plotly_chart(plot_bar_movement_by_source_name(movements, MovementType.INCOME))


def show_dashboard_page():
    st.subheader("📊 Dashboard")

    st.divider()

    movements = get_all_movements()
    
    if movements is None or movements.empty:
        st.warning("No movements found")
    else:
        show_metrics_cards(movements)
        show_plots(movements)

if "authentication_status" in st.session_state and st.session_state.authentication_status:
    show_dashboard_page()
else:
    st.switch_page("./Home.py")