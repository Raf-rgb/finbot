import yaml
import json
import asyncio
import logging
import pandas as pd
import streamlit as st
import streamlit_authenticator as stauth

from enum import Enum
from bson import ObjectId
from datetime import datetime
from utils.database import get_collection
from utils.utils import get_response_from_model

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")

st.set_page_config(
    page_title="Sign In | Finbot 🤖",
    page_icon="🤖",
    layout="wide"
)

for key in ["authenticator_config", "authenticator", "profile_data", "mongo_client"]:
    if key not in st.session_state:
        st.session_state[key] = None

if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

class AuthOptions(Enum):
    SIGN_IN = "Sign In"
    SIGN_UP = "Sign Up"

def load_authenticator():
    try:
        config_collection = get_collection(
            st.secrets.db_credentials.uri,
            st.secrets.db_credentials.database_name,
            st.secrets.db_collections.config_collection_name
        )

        document = config_collection.find_one({"_id": ObjectId(st.secrets.config.config_id_from_db)})

        if document:
            del document["_id"]
            yaml_config = yaml.dump(document, default_flow_style=False)
            st.session_state.authenticator_config = yaml.safe_load(yaml_config)

            st.session_state.authenticator = stauth.Authenticate(
                st.session_state.authenticator_config['credentials'],
                st.session_state.authenticator_config['cookie']['name'],
                st.session_state.authenticator_config['cookie']['key'],
                st.session_state.authenticator_config['cookie']['expiry_days']
            )
        else:
            logging.info("Auth config not found!")
    except Exception as e:
        st.error(f"Error loading the auth configuration: {e}")

def update_authenticator():
    try:
        config_collection = get_collection(
            st.secrets.db_credentials.uri,
            st.secrets.db_credentials.database_name,
            st.secrets.db_collections.config_collection_name
        )

        config_collection.update_one(
            {"_id": ObjectId(st.secrets.config.config_id_from_db)},
            {"$set": st.session_state.authenticator_config}
        )
    except Exception as e:
        st.error(f"Error updating the current auth data: {e}")
        logging.error(f"Error updating the current auth data: {e}")

def sign_in():
    st.session_state.authenticator.experimental_guest_login(
        'Login with Google',
        provider='google',
        oauth2=st.session_state.authenticator_config['oauth2']
    )
        
    if st.session_state.authentication_status:
        st.session_state.initial_sidebar_state = "expanded"
        update_authenticator()
        st.rerun()
    elif st.session_state.authentication_status is None:
        st.warning("Please log in")
    elif st.session_state.authentication_status is False:
        st.error("Username/Password incorrect")

def load_profile_data():
    st.session_state.profile_data = st.session_state.authenticator_config["credentials"]["usernames"][st.session_state.username]

def display_messages(message, chat_window):
    if message["user"] == "Finbot":
        with st.chat_message(message["user"], avatar=message["profile_picture"]):
            with st.spinner("Finbot is typing..."):
                model_response = get_response_from_model(message["message"])

                if model_response is not None:
                    message["message"] = json.loads(model_response.model_dump_json())

                    logging.info(f"Finbot message: {message['message']}")
                    st.write(message["message"]["description"])

                    response_df = pd.DataFrame(message["message"], index=[0])

                    st.dataframe(
                        response_df.drop(columns=["description"]),
                        column_config= {
                            "datetime": "📅 Fecha y hora",
                            "name": "👤 Movimiento",
                            "movement_type": "🔘 Tipo",
                            "source": "💳 Fuente",
                            "category": "🏷️ Categoría",
                            "amount": "💲 Cantidad"
                        },
                        hide_index=True
                    )
                else:
                    st.write(message["message"])
    else:
        chat_window.chat_message(message["user"], avatar=message["profile_picture"]).write(message["message"])

def show_chat_window():
    chat_window = st.container()

    if prompt := st.chat_input("Di algo..."):
        display_messages(
            {
                "user": st.session_state.profile_data["first_name"],
                "message": prompt,
                "profile_picture": st.session_state.profile_data["picture"],
                "timestamp": datetime.now().isoformat()
            },
            chat_window
        )

        display_messages(
            {
                "user": "Finbot",
                "message": "Sorry, I can't help you with that yet.",
                "profile_picture": "./assets/assistant_picture.png",
                "timestamp": datetime.now().isoformat()
            },
            chat_window
        )
        
    logging.info(f"Chat history: {st.session_state.chat_history}")

def show_chat_page():
    if st.session_state.profile_data is None:
        load_profile_data()

    st.title("🗨️ Chat")

    show_chat_window()

def main():
    if st.session_state.authenticator is None:
        load_authenticator()
        
    _, _, loging_col, _, _ = st.columns([0.1, 0.1, 0.6, 0.1, 0.1])
    
    if st.session_state.authentication_status:
        show_chat_page()
    else:
        with loging_col:
            st.header("Welcome to")
            st.header("Finbot 🤖")
            st.divider()
            st.subheader("Your personal finance bot")
            st.text("Please sign in with your Google account to continue.")
            sign_in()

if __name__ == "__main__":
    main()
