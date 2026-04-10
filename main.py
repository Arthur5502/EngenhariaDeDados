from src.extract import PNCPExtractor
from src.transform import PNCPTransformer
from src.load import MongoDBLoader

UF = "pe"
CODIGO_MUNICIPIO_IBGE = "2611606" #Código de recife
CODIGO_MODALIDADE = "8" #Código de dispensa eletrônica
DATA_FINAL = "20260331"

DB_NAME = "pncp"
COLLECTION_NAME = "contratacoes"

def run_etl() -> None:
    print("=" * 50)
    print("Iniciando ETL — PNCP")
    print("=" * 50)

    print("\n[1/3] EXTRACT")
    extractor = PNCPExtractor(UF, CODIGO_MUNICIPIO_IBGE, CODIGO_MODALIDADE)
    raw_data = extractor.extract_all(DATA_FINAL)
    print(f"Total extraído: {len(raw_data)} registros\n")

    print("[2/3] TRANSFORM")
    transformer = PNCPTransformer()
    transformed_data = transformer.transform(raw_data)
    print(f"Total transformado: {len(transformed_data)} registros\n")

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