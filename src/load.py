import os
from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

load_dotenv()

class MongoDBLoader:
    
    def __init__(self):
        db_user = os.getenv("DB_USER")
        db_password = os.getenv("DB_PASSWORD")
        uri = (
            f"mongodb+srv://{db_user}:{db_password}"
            "@cluster0.cpevj4j.mongodb.net/?appName=Cluster0"
        )
        self.client = MongoClient(uri, server_api=ServerApi("1"))

    def load(self, data: list[dict], db_name: str, collection_name: str) -> int:
        if not data:
            print("Nenhum dado para inserir.")
            return 0

        collection = self.client[db_name][collection_name]
        result = collection.insert_many(data)
        inserted = len(result.inserted_ids)
        print(f"{inserted} documento(s) inserido(s) em '{db_name}.{collection_name}'")
        return inserted

    def close(self):
        self.client.close()
