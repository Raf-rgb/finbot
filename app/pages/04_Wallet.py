import logging
import pandas as pd
import streamlit as st

from datetime import datetime
from utils.models import SourceType
from utils.database import get_collection

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")

source_icons = {
    SourceType.CASH.value: "💵",
    SourceType.CREDIT_CARD.value: "💳",
    SourceType.DEBIT_CARD.value: "💳",
    SourceType.VALE.value: "🎫",
}

def get_wallet():
    try:
        sources_collection = get_collection(
            st.secrets.db_credentials.uri,
            st.secrets.db_credentials.database_name,
            st.secrets.db_collections.sources_collection_name
        )

        sources = sources_collection.find(
            {
                "username": st.session_state.username
            }
        )

        if sources:
            return pd.DataFrame(list(sources))
        else:
            return None
    except Exception as e:
        logging.error(f"Error getting the sources: {e}")
        return None

def show_source_card(source:dict):
    icon = source_icons[source["source_type"]]

    with st.expander(f"{icon} {source['source_name']} - {source['source_type']}"):
        st.subheader("Details")

        if source["source_balance"] < 0:
            st.markdown(f"**Balance:** :red[${source['source_balance']:.2f}]")
        else:
            st.markdown(f"**Balance:** :green[${source['source_balance']:.2f}]")

        if source["source_type"] != SourceType.CASH.value:
            st.write(f"**Last 4 digits:** *{source['last_digits']}*")
        st.write(f"**Type:** :blue-background[{source['source_type']}]")


def show_form():
    st.write("### Add a new source to your wallet")

    source_types   = [source_type.value for source_type in SourceType]

    source_name    = st.text_input("Source name")
    source_type    = st.selectbox("Source type", source_types)
    last_digits    = None
    
    if source_type != SourceType.CASH.value:
        last_digits = st.text_input("Last 4 digits of the card")
    
    source_balance = st.number_input("Source balance", value=0.0)

    if st.button("Add wallet"):
        try:
            sources_collection = get_collection(
                st.secrets.db_credentials.uri,
                st.secrets.db_credentials.database_name,
                st.secrets.db_collections.sources_collection_name
            )

            sources_collection.insert_one(
                {
                    "username": st.session_state.username,
                    "source_name": source_name,
                    "source_type": source_type,
                    "last_digits": last_digits,
                    "source_balance": source_balance,
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            )

            st.success("Source added to wallet successfully!")
        except Exception as e:
            logging.error(f"Error adding the source to the wallet: {e}")
            st.error("Error adding the source")

def show_wallet_page():
    st.title("💰 Wallet")

    col_wallet, col_add_source = st.tabs(["Wallets", "Add a new wallet"])

    with col_wallet:
        wallets = get_wallet()

        if wallets is None or wallets.empty:
            st.warning("There are nothing in your wallet yet. Add a new source!")
        else:
            for _, source in wallets.iterrows():
                show_source_card(source)
    
    with col_add_source:
        show_form()

if "authentication_status" in st.session_state and st.session_state.authentication_status:
    show_wallet_page()
else:
    st.switch_page("./main.py")