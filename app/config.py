from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DB_USER: str
    DB_PASSWORD: str
    SECRET_KEY: str

    MONGO_DB: str = "pncp"
    MONGO_COLLECTION: str = "contratacoes"

    PNCP_BASE_URL: str = "https://pncp.gov.br/api/consulta/v1/contratacoes/proposta"
    PNCP_UF: str = "pe"
    PNCP_MUNICIPIO_IBGE: str = "2611606"
    PNCP_MODALIDADE: str = "8"

    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str
    SUPABASE_JWT_SECRET: str

    DATA_ENCRYPTION_KEY: str

    @property
    def mongo_uri(self) -> str:
        return (
            f"mongodb+srv://{self.DB_USER}:{self.DB_PASSWORD}"
            "@cluster0.cpevj4j.mongodb.net/?appName=Cluster0"
        )

settings = Settings()