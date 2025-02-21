import logging

from pymongo import MongoClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")

def get_mongo_client(uri:str):
    try:
        client = MongoClient(uri)
        return client
    except Exception as e:
        logging.info(f"Error connecting to the Mongo DB: {e}")

def get_collection(uri:str, database_name:str, collection_name:str):
    try:
        client     = get_mongo_client(uri)
        database   = client[database_name]
        collection = database[collection_name]

        return collection
    except Exception as e:
        logging.info(f"Error getting the collection from the Mongo DB: {e}")