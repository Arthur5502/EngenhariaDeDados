import os
from datetime import date
from dotenv import load_dotenv

load_dotenv()

PNCP_BASE_URL = os.getenv(
    "PNCP_BASE_URL",
    "https://pncp.gov.br/api/consulta/v1/contratacoes/proposta"
)

UF = os.getenv("PNCP_UF", "pe")
CODIGO_MUNICIPIO_IBGE = os.getenv("PNCP_CODIGO_MUNICIPIO_IBGE", "2611606")
CODIGO_MODALIDADE = os.getenv("PNCP_CODIGO_MODALIDADE", "8")

DATA_FINAL = os.getenv("PNCP_DATA_FINAL") or date.today().strftime("%Y%m%d")

TAMANHO_PAGINA = int(os.getenv("PNCP_TAMANHO_PAGINA", "50"))

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB_NAME", "pncp")
COLLECTION_NAME = os.getenv("MONGO_COLLECTION_NAME", "bronze_pncp")

def validate():
    """Valida se todas as configurações críticas estão presentes."""
    obrigatorias = {
        "MONGO_URI": MONGO_URI,
    }
    faltando = [k for k, v in obrigatorias.items() if not v]
    if faltando:
        raise EnvironmentError(
            f"Variáveis de ambiente obrigatórias não definidas: {', '.join(faltando)}\n"
            "Verifique seu arquivo .env ou as variáveis de ambiente do ambiente cloud."
        )
