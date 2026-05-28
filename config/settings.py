import os
from datetime import date, timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

PNCP_BASE_URL = os.getenv(
    "PNCP_BASE_URL",
    "https://pncp.gov.br/api/consulta/v1/contratacoes/proposta"
)

UF = os.getenv("PNCP_UF", "pe")
CODIGO_MUNICIPIO_IBGE = os.getenv("PNCP_CODIGO_MUNICIPIO_IBGE", "2611606")
CODIGO_MODALIDADE = os.getenv("PNCP_CODIGO_MODALIDADE", "8")

DATA_INICIAL = os.getenv("PNCP_DATA_INICIAL") or (date.today() - timedelta(days=90)).strftime("%Y%m%d")
DATA_FINAL = os.getenv("PNCP_DATA_FINAL") or (date.today() + timedelta(days=60)).strftime("%Y%m%d")

TAMANHO_PAGINA = int(os.getenv("PNCP_TAMANHO_PAGINA", "50"))

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB_NAME", "pncp")
COLLECTION_NAME = os.getenv("MONGO_COLLECTION_NAME", "bronze_pncp")

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

def validate():
    obrigatorias = {
        "MONGO_URI": MONGO_URI,
    }
    faltando = [k for k, v in obrigatorias.items() if not v]
    if faltando:
        raise EnvironmentError(
            f"Variáveis de ambiente obrigatórias não definidas: {', '.join(faltando)}\n"
            "Verifique seu arquivo .env ou as variáveis de ambiente do ambiente cloud."
        )
