import logging
import streamlit as st

from langchain_ollama import OllamaLLM
from langchain_openai import ChatOpenAI
from utils.models import Movement, MovementType
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

def find_source_by_name(sources_list, source_name):
    for source in sources_list:
        if source["source_name"].upper() == source_name.upper():
            return source
    return None

async def get_sources(username: str):
    try:
        source_collection = AsyncIOMotorClient(st.secrets.db_credentials.uri)[st.secrets.db_credentials.database_name][st.secrets.db_collections.sources_collection_name]

        cursor = source_collection.find({"username": username})
        sources = await cursor.to_list(length=None)

        if sources:
            return sources
        else:
            return None
    except Exception as e:
        logging.error(f"Error getting the sources: {e}")
        return None

async def update_source_balance(movement: Movement, username: str):
    try:
        source_name   = movement.source_name
        source_type   = movement.source_type
        movement_type = movement.movement_type
        amount        = movement.amount

        source_collection = AsyncIOMotorClient(st.secrets.db_credentials.uri)[st.secrets.db_credentials.database_name][st.secrets.db_collections.sources_collection_name]

        source = await source_collection.find_one(
            {
                "username": username,
                "source_name": source_name, 
                "source_type": source_type
            }
        )

        if source:
            source_balance     = source["source_balance"]
            new_source_balance = source_balance
            
            if movement_type == MovementType.EXPENSE:
                new_source_balance -= amount
            elif movement_type == MovementType.INCOME:
                new_source_balance += amount

            if new_source_balance != source_balance:
                await source_collection.update_one(
                    {
                        "username": username,
                        "source_name": source_name, 
                        "source_type": source_type
                    },
                    {
                        "$set": {
                            "source_balance": new_source_balance
                        }
                    }
                )

                logging.info(f"Source balance updated for {username}: {source_name}")
    except Exception as e:
        logging.error(f"Error updating the source balance: {e}")

async def validate_or_add_source(movement_dict: dict, username: str) -> dict:
    try:
        source_collection = AsyncIOMotorClient(st.secrets.db_credentials.uri)[st.secrets.db_credentials.database_name][st.secrets.db_collections.sources_collection_name]

        source_name = movement_dict.get("source_name").upper()

        user_sources = await source_collection.find(
            {
                "username": username,
                "source_name": source_name
            }
        )

        existing_sources = []

        if user_sources:
            user_sources     = list(user_sources)
            existing_sources = [user_source["source_name"] for user_source in user_sources]

        if source_name not in existing_sources:
            await source_collection.update_one(
                {"username": username},
                {
                    "$push": {
                        "username": username,
                        "source_name": source_name,
                        "source_type": movement_dict.get("source_type"),
                        "last_digits": None,
                        "source_balance": movement_dict.get("amount")
                    }
                },
                upsert=True
            )

            logging.info(f"New source added for {username}: {source_name}")

        return movement_dict
    except Exception as e:
        logging.error(f"Error validating or adding the source: {e}")

async def validate_or_add_category(movement: Movement, username:str) -> dict:
    try:
        category_collection = AsyncIOMotorClient(st.secrets.db_credentials.uri)[st.secrets.db_credentials.database_name][st.secrets.db_collections.categories_collection_name]

        logging.info(f"Validating movement: {movement}")

        category      = movement.category.upper()
        movement_type = movement.movement_type

        if movement_type == MovementType.INCOME.value and category != MovementType.INCOME.value.upper():
            raise ValueError(f"If movement_type is '{movement_type}', category must be '{MovementType.INCOME.value}, not '{category}'")

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

        return movement
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