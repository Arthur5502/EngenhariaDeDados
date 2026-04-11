import os
import logging
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from config import settings

logger = logging.getLogger(__name__)

class MongoDBLoader:
    
    def __init__(self):
        uri = settings.MONGO_URI
        if not uri:
            logger.error("MONGO_URI não encontrada nas configurações!")
            raise ValueError("MONGO_URI não foi encontrada no arquivo .env!")
        self.client = MongoClient(uri, server_api=ServerApi("1"))

    def load(self, data: list[dict], db_name: str, collection_name: str) -> int:
        if not data:
            logger.warning("Nenhum dado para inserir.")
            return 0

        collection = self.client[db_name][collection_name]
        result = collection.insert_many(data)
        inserted = len(result.inserted_ids)
        logger.info(f"{inserted} documento(s) inserido(s) em '{db_name}.{collection_name}'")
        return inserted

    def close(self):
        self.client.close()
