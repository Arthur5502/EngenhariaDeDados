import logging
from src.extract import PNCPExtractor
from src.transform import PNCPTransformer
from src.load import MongoDBLoader
from config import settings

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

settings.validate()

def run_etl() -> None:
    logger.info("Iniciando Pipeline ETL — PNCP")
    extractor = PNCPExtractor(settings.UF, settings.CODIGO_MUNICIPIO_IBGE, settings.CODIGO_MODALIDADE)
    raw_data = extractor.extract_all(settings.DATA_FINAL)
    logger.info(f"Total extraído: {len(raw_data)} registros")

    transformer = PNCPTransformer()
    transformed_data = transformer.transform(raw_data)
    logger.info(f"Total transformado: {len(transformed_data)} registros")

    loader = MongoDBLoader()
    try:
        loader.load(transformed_data, settings.DB_NAME, settings.COLLECTION_NAME)
    finally:
        loader.close()

    logger.info("ETL concluído com sucesso!")

if __name__ == "__main__":
    run_etl()