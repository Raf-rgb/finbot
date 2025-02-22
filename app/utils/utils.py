import logging
import streamlit as st

from utils.models import Movement
from langchain_openai import ChatOpenAI
from langchain_ollama import OllamaLLM
from motor.motor_asyncio import AsyncIOMotorClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")

def get_model():
    try:
        model = ChatOpenAI(
            api_key=st.secrets.openai.api_key, 
            model="gpt-4o"
        )

        # model = OllamaLLM(model="deepseek-r1:14b")

        return model
    except Exception as e:
        st.write(f"Error loading the model: {e}")

async def validate_or_add_source(movement_dict: dict, username: str) -> dict:
    try:
        source_collection = AsyncIOMotorClient(st.secrets.db_credentials.uri)[st.secrets.db_credentials.database_name][st.secrets.db_collections.sources_collection_name]

        source = movement_dict.get("source").upper()

        user_sources = await source_collection.find_one({"username": username})

        if user_sources and "sources" in user_sources:
            existing_sources = user_sources["sources"]
        else:
            existing_sources = []

        if source not in existing_sources:
            await source_collection.update_one(
                {"username": username},
                {"$push": {"sources": source}},
                upsert=True
            )
            logging.info(f"New source added for {username}: {source}")

        return movement_dict
    except Exception as e:
        logging.error(f"Error validating or adding the source: {e}")

async def validate_or_add_category(movement_dict: dict, username:str) -> dict:
    try:
        category_collection = AsyncIOMotorClient(st.secrets.db_credentials.uri)[st.secrets.db_credentials.database_name][st.secrets.db_collections.categories_collection_name]

        category      = movement_dict.get("category").upper()
        movement_type = movement_dict.get("movement_type")

        if movement_type == "Ingreso" and category != "Ingreso":
            raise ValueError("If movement_type is 'income', category must be 'income'")

        user_categories = await category_collection.find_one({"username": username})

        if user_categories and "categories" in user_categories:
            existing_categories = user_categories["categories"]
        else:
            existing_categories = []

        if movement_type == "Gasto" and category not in existing_categories:
            await category_collection.update_one(
                {"username": username},
                {"$push": {"categories": category}},
                upsert=True
            )
            logging.info(f"New category added for {username}: {category}")

        return movement_dict
    except Exception as e:
        logging.error(f"Error validating or adding the category: {e}")

async def insert_movement(movement: Movement, username: str):
    try:
        finance_collection = AsyncIOMotorClient(st.secrets.db_credentials.uri)[st.secrets.db_credentials.database_name][st.secrets.db_collections.finance_collection_name]
        
        movement_dict = movement.model_dump()
        movement_dict["username"] = username
        movement_dict["category"] = movement_dict["category"].upper()
        
        await finance_collection.insert_one(movement_dict)

        logging.info(f"Movement inserted for {username}: {movement_dict}")
    except Exception as e:
        st.write(f"Error processing the movement: {e}")