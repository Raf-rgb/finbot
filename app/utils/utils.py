import asyncio
import logging
import streamlit as st

from datetime import datetime
from utils.models import Movement
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from motor.motor_asyncio import AsyncIOMotorClient
from langchain_core.output_parsers import PydanticOutputParser

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")

def get_model():
    try:
        model = ChatOpenAI(
            api_key=st.secrets.openai.api_key, 
            model_name="gpt-4o"
        )

        return model
    except Exception as e:
        st.write(f"Error loading the model: {e}")


def get_response_from_model(prompt: str) -> str:
    try:
        model  = get_model()
        parser = PydanticOutputParser(pydantic_object=Movement)

        prompt_template = PromptTemplate(
            template="Responde a la consulta siguiendo las instrucciones de formato:\n{format_instructions}\n{query}\n",
            input_variables=["query"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )

        prompt_and_model = prompt_template | model

        output = prompt_and_model.invoke({"query": prompt})
        
        if asyncio.iscoroutine(output):
            output = asyncio.run(output)

        movement_data = parser.invoke(output)

        if isinstance(movement_data, list):
            movement_data = movement_data[0]

        if not isinstance(movement_data, dict):
            movement_data = movement_data.model_dump()

        validated_data = asyncio.run(validate_or_add_category(movement_data, st.session_state.username))
        asyncio.run(validate_or_add_source(validated_data, st.session_state.username))

        final_movement = Movement(**validated_data)

        if final_movement.datetime is None:
            final_movement.datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        asyncio.run(insert_movement(final_movement, st.session_state.username))

        return final_movement
    except Exception as e:
        st.write(f"Error getting the response from the model: {e}")

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