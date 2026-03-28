"""ETL – Portal Nacional de Contratações Públicas (PNCP).

Ponto de entrada do pipeline. Orquestra as três etapas:
    1. Extract  – coleta dados da API do PNCP com paginação automática.
    2. Transform – normaliza e seleciona os campos relevantes.
    3. Load      – persiste os documentos no MongoDB Atlas.
"""

from src.extract import PNCPExtractor
from src.transform import PNCPTransformer
from src.load import MongoDBLoader

UF = "pe"
CODIGO_MUNICIPIO_IBGE = "2611606"   # Recife
CODIGO_MODALIDADE = "8"             # Dispensa Eletrônica
DATA_FINAL = "20260331"

DB_NAME = "pncp"
COLLECTION_NAME = "contratacoes"

def run_etl() -> None:
    """Executa o pipeline completo de Extract → Transform → Load.

    Instancia as classes de cada etapa, executa cada fase em sequência e
    imprime o progresso no console. A conexão com o MongoDB é encerrada
    ao final, independentemente de erros.
    """
    print("=" * 50)
    print("Iniciando ETL — PNCP")
    print("=" * 50)

    # --- Extract ---
    print("\n[1/3] EXTRACT")
    extractor = PNCPExtractor(UF, CODIGO_MUNICIPIO_IBGE, CODIGO_MODALIDADE)
    raw_data = extractor.extract_all(DATA_FINAL)
    print(f"Total extraído: {len(raw_data)} registros\n")

    # --- Transform ---
    print("[2/3] TRANSFORM")
    transformer = PNCPTransformer()
    transformed_data = transformer.transform(raw_data)
    print(f"Total transformado: {len(transformed_data)} registros\n")

    # --- Load ---
    print("[3/3] LOAD")
    loader = MongoDBLoader()
    try:
        loader.load(transformed_data, DB_NAME, COLLECTION_NAME)
    finally:
        loader.close()

    print("\n" + "=" * 50)
    print("ETL concluído com sucesso!")
    print("=" * 50)


if __name__ == "__main__":
    run_etl()
