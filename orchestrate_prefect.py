from dotenv import load_dotenv
from prefect import flow, task, get_run_logger
from config import settings
from src.extract import PNCPExtractor
from src.transform import PNCPTransformer
from src.load import MongoDBLoader

load_dotenv()

@task(retries=3, retry_delay_seconds=15, name="Extração PNCP")
def extract(uf: str, codigo_municipio_ibge: str, data_final: str) -> list[dict]:
    logger = get_run_logger()
    logger.info(f"Iniciando extração — UF: {uf} | Município IBGE: {codigo_municipio_ibge} | Data: {data_final}")
    extractor = PNCPExtractor(uf, codigo_municipio_ibge, settings.CODIGO_MODALIDADE)
    raw_data = extractor.extract_all(data_final, settings.TAMANHO_PAGINA)
    logger.info(f"{len(raw_data)} registros brutos extraídos da API PNCP")
    return raw_data

@task(name="Transformação PNCP")
def transform(raw_data: list[dict]) -> list[dict]:
    logger = get_run_logger()
    logger.info(f"Iniciando transformação de {len(raw_data)} registros")
    transformer = PNCPTransformer()
    transformed = transformer.transform(raw_data)
    descartados = len(raw_data) - len(transformed)
    if descartados:
        logger.warning(f"{descartados} registro(s) descartado(s) por falha na validação")
    logger.info(f"{len(transformed)} registros válidos prontos para carga")
    return transformed

@task(name="Carga MongoDB")
def load(data: list[dict], db_name: str, collection_name: str) -> int:
    logger = get_run_logger()
    logger.info(f"Carregando {len(data)} registros em '{db_name}.{collection_name}'")
    loader = MongoDBLoader()
    try:
        inserted = loader.load(data, db_name, collection_name)
        logger.info(f"{inserted} documento(s) inserido(s) com sucesso no MongoDB Atlas")
        return inserted
    finally:
        loader.close()

@flow(name="ETL PNCP Prefect", log_prints=True)
def etl_pncp_flow(
    uf: str = settings.UF,
    codigo_municipio_ibge: str = settings.CODIGO_MUNICIPIO_IBGE,
    data_final: str = settings.DATA_FINAL,
    db_name: str = settings.DB_NAME,
    collection_name: str = settings.COLLECTION_NAME,
):
    settings.validate()

    raw_data = extract(uf, codigo_municipio_ibge, data_final)
    transformed_data = transform(raw_data)
    total_inserido = load(transformed_data, db_name, collection_name)

    print(f"Pipeline concluído — {total_inserido} contratos carregados no MongoDB Atlas")

if __name__ == "__main__":
    # etl_pncp_flow.serve(
    #     name="etl-pncp-schedule",
    #     cron="0 8 * * *",
    #     tags=["etl", "pncp", "mongodb"],
    # )
    etl_pncp_flow()
