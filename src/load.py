import os

from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

load_dotenv()


class MongoDBLoader:
    """Responsável pelo carregamento dos dados transformados no MongoDB Atlas.

    Gerencia a conexão com o cluster remoto utilizando credenciais carregadas
    via variáveis de ambiente e expõe métodos para inserção em coleções.

    Attributes:
        client (MongoClient): Cliente ativo de conexão com o MongoDB Atlas.
    """

    def __init__(self):
        """Inicializa a conexão com o MongoDB Atlas.

        Lê as variáveis de ambiente DB_USER e DB_PASSWORD (definidas no arquivo .env)
        para construir a URI de conexão com o cluster.

        Raises:
            pymongo.errors.ConnectionFailure: Se não for possível conectar ao cluster.
        """
        db_user = os.getenv("DB_USER")
        db_password = os.getenv("DB_PASSWORD")
        uri = (
            f"mongodb+srv://{db_user}:{db_password}"
            "@cluster0.cpevj4j.mongodb.net/?appName=Cluster0"
        )
        self.client = MongoClient(uri, server_api=ServerApi("1"))

    def load(self, data: list[dict], db_name: str, collection_name: str) -> int:
        """Insere uma lista de documentos em uma coleção do MongoDB Atlas.

        Args:
            data: Lista de dicionários a serem inseridos como documentos.
            db_name: Nome do banco de dados de destino.
            collection_name: Nome da coleção de destino.

        Returns:
            Quantidade de documentos inseridos com sucesso.
        """
        if not data:
            print("Nenhum dado para inserir.")
            return 0

        collection = self.client[db_name][collection_name]
        result = collection.insert_many(data)
        inserted = len(result.inserted_ids)
        print(f"{inserted} documento(s) inserido(s) em '{db_name}.{collection_name}'")
        return inserted

    def close(self):
        """Encerra a conexão com o MongoDB Atlas."""
        self.client.close()
