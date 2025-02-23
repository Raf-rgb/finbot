import pytz
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
from utils.models import Movement, MovementType
from utils.database import get_collection
from utils.utils import get_model, get_sources, validate_or_add_category, update_source_balance, insert_movement

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")

st.set_page_config(
    page_title="Sign In | Finbot 🤖",
    page_icon="🤖",
    initial_sidebar_state="collapsed",
    layout="wide"
)

if "movement_accepted" not in st.session_state:
    st.session_state.movement_accepted = False

for key in ["authenticator_config", "authenticator", "profile_data", 
            "movement", "user_input", "model_output"]:
    if key not in st.session_state:
        st.session_state[key] = None

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
    elif st.session_state.authentication_status is False:
        st.error("Username/Password incorrect")

def load_profile_data():
    st.session_state.profile_data = st.session_state.authenticator_config["credentials"]["usernames"][st.session_state.username]

def display_message(message, chat_window):
    if message["user"] == "Finbot":
        with st.chat_message(message["user"], avatar=message["profile_picture"]):
            if message["message"] is not None:
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

                if not st.session_state.movement_accepted:
                    if st.button("Accept"):
                        movement = Movement(**message["message"])
                        movement = asyncio.run(validate_or_add_category(movement, st.session_state.username))

                        asyncio.run(insert_movement(movement, st.session_state.username))
                        asyncio.run(update_source_balance(movement, st.session_state.username))

                        st.toast("Movement accepted!", icon="👍")
                        st.session_state.movement_accepted = True
            else:
                st.write("Sorry, I can't help you with that.")
    else:
        chat_window.chat_message(message["user"], avatar=message["profile_picture"]).write(message["message"])
            
def display_messages(messages, chat_window):
    for message in messages:
        if message["user"] == "Finbot":
            with st.chat_message(message["user"], avatar=message["profile_picture"]):
                if message["message"] is not None:
                    st.write(message["message"]["description"])

                    response_df = pd.DataFrame(message["message"], index=[0])

                    st.dataframe(
                        response_df.drop(columns=["description"]),
                        column_config= {
                            "datetime": "📅 Fecha y hora",
                            "name": "👤 Movimiento",
                            "movement_type": "🔘 Tipo",
                            "source_name": "💳 Fuente",
                            "source_type": "🌀 Tipo",
                            "category": "🏷️ Categoría",
                            "amount": "💲 Cantidad"
                        },
                        hide_index=True
                    )

                    if not st.session_state.movement_accepted:
                        if st.button("Accept", type="primary"):
                            movement = Movement(**message["message"])
                            movement = asyncio.run(validate_or_add_category(movement, st.session_state.username))

                            asyncio.run(insert_movement(movement, st.session_state.username))
                            asyncio.run(update_source_balance(movement, st.session_state.username))

                            st.session_state.movement_accepted = True
                            st.toast("Movement accepted!", icon="👍")
                            st.rerun()
                else:
                    st.write("Sorry, I can't help you with that.")
        else:
            chat_window.chat_message(message["user"], avatar=message["profile_picture"]).write(message["message"])

def show_chat_window():
    chat_window = st.container()

    model        = get_model()
    parser       = PydanticOutputParser(pydantic_object=Movement)
    user_sources = asyncio.run(get_sources(st.session_state.username))

    prompt_template = PromptTemplate(
        template="Answer the user query. Identify the money source according to the user sources: {user_sources}\n{format_instructions}\n{query}\n",
        input_variables=["query"],
        partial_variables={"format_instructions": parser.get_format_instructions(), "user_sources": user_sources},
    )

    if prompt := st.chat_input("Di algo..."):
        st.session_state.user_input = {
            "user": st.session_state.profile_data["first_name"],
            "message": prompt,
            "profile_picture": st.session_state.profile_data["picture"],
            "timestamp": datetime.now().isoformat()
        }
        
        st.session_state.movement_accepted = False

    if st.session_state.user_input is not None:
        display_message(st.session_state.user_input, chat_window)

        if st.session_state.model_output is None:
            with chat_window:
                with st.spinner("Finbot is typing..."):
                    prompt_and_model = prompt_template | model

                    output = prompt_and_model.invoke({"query": prompt})
                    
                    if asyncio.iscoroutine(output):
                        output = asyncio.run(output)

                    movement_data = parser.invoke(output)

                    if isinstance(movement_data, list):
                        movement_data = movement_data[0]

                    if not isinstance(movement_data, dict):
                        movement_data = movement_data.model_dump()

                    movement = Movement(**movement_data)

                    if movement.datetime is None:
                        movement.datetime = datetime.now(tz=pytz.timezone('America/Mexico_City')).strftime("%Y-%m-%d %H:%M:%S")

                    if movement.movement_type == MovementType.INCOME:
                        movement.category = MovementType.INCOME

                    st.session_state.model_output = {
                        "user": "Finbot",
                        "message": json.loads(movement.model_dump_json()),
                        "profile_picture": "https://github.com/Raf-rgb/finbot/blob/main/app/assets/assistant_picture.png?raw=true",
                        "timestamp": datetime.now().isoformat()
                    }

                    st.rerun()
        else:
            with st.spinner("Finbot is processing..."):
                display_message(st.session_state.model_output, chat_window)

        if st.session_state.movement_accepted:
            st.session_state.user_input = None
            st.rerun()

    if st.session_state.movement_accepted and st.session_state.model_output is not None:
        with st.status("Proccesing movement...", expanded=True):
            st.success("Movement accepted! 🎉")
            display_message(st.session_state.model_output, chat_window)
        
        st.session_state.model_output = None

    # if st.session_state.user_input is not None and st.session_state.model_output is not None:
    #     with st.spinner("Processing..."):
    #         display_messages([st.session_state.user_input, st.session_state.model_output], chat_window)

def show_chat_page():
    if st.session_state.profile_data is None:
        load_profile_data()

    st.header("🗨️ Chat")

    show_chat_window()

def main():
    if st.session_state.authenticator is None:
        load_authenticator()
        
    _, _, loging_col, _, _ = st.columns([0.2, 0.2, 0.2, 0.2, 0.2])
    
    if st.session_state.authentication_status:
        show_chat_page()
    else:        
        with loging_col:

            st.title("Welcome to Finbot 🤖")
            st.divider()
            st.text("Please sign in with your Google account to continue.")
            sign_in()

if __name__ == "__main__":
    main()
