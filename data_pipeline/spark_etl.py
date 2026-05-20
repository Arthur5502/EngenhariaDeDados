import os
os.environ["_JAVA_OPTIONS"] = "-Djava.security.manager=allow"

from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp
from pyspark.sql.types import (
    StructType, StructField,
    StringType, IntegerType, DoubleType, BooleanType,
)
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

SCHEMA = StructType([
    StructField("numero_controle_pncp", StringType(), True),
    StructField("ano_compra", IntegerType(), True),
    StructField("numero_compra", StringType(), True),
    StructField("processo", StringType(), True),
    StructField("objeto_compra", StringType(), True),
    StructField("modalidade_id", IntegerType(), True),
    StructField("modalidade_nome", StringType(), True),
    StructField("modo_disputa_nome", StringType(), True),
    StructField("situacao_compra_id", IntegerType(), True),
    StructField("situacao_compra_nome", StringType(), True),
    StructField("tipo_instrumento_convocatorio", StringType(), True),
    StructField("valor_total_estimado", DoubleType(), True),
    StructField("valor_total_homologado", DoubleType(), True),
    StructField("srp", BooleanType(), True),
    StructField("orgao_cnpj", StringType(), True),
    StructField("orgao_razao_social", StringType(), True),
    StructField("orgao_poder_id", StringType(), True),
    StructField("orgao_esfera_id", StringType(), True),
    StructField("unidade_codigo", StringType(), True),
    StructField("unidade_nome", StringType(), True),
    StructField("municipio_nome", StringType(), True),
    StructField("municipio_ibge", StringType(), True),
    StructField("uf_sigla", StringType(), True),
    StructField("uf_nome", StringType(), True),
    StructField("amparo_legal_codigo", IntegerType(), True),
    StructField("amparo_legal_nome", StringType(), True),
    StructField("data_inclusao", StringType(), True),
    StructField("data_atualizacao", StringType(), True),
    StructField("data_publicacao_pncp", StringType(), True),
    StructField("data_abertura_proposta", StringType(), True),
    StructField("data_encerramento_proposta", StringType(), True),
    StructField("link_sistema_origem", StringType(), True),
    StructField("data_extracao", StringType(), True),
])


def create_spark_session():
    return SparkSession.builder.appName("ETL_PNCP_Data").getOrCreate()


def extract_data(spark: SparkSession):
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")

    try:
        if not db_user or not db_password:
            raise ValueError("Credenciais ausentes")

        mongo_uri = (
            f"mongodb+srv://{db_user}:{db_password}"
            "@cluster0.cpevj4j.mongodb.net/?appName=Cluster0"
        )
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=10000)
        data = list(client["pncp"]["contratacoes"].find({}, {"_id": 0}))
        client.close()

        if not data:
            raise ValueError("Coleção vazia no MongoDB")

        print(f"\n{len(data)} documentos lidos do MongoDB.\n")
        rows = [{k: doc.get(k) for k in [f.name for f in SCHEMA]} for doc in data]
        return spark.createDataFrame(rows, schema=SCHEMA)

    except Exception as e:
        print(f"\nALERTA: Falha ao conectar/ler o MongoDB! Motivo: {e}")
        print("Caindo para o modo MOCK de segurança...\n")
        mock_data = [
            {"id_contrato": 101, "orgao": "Ministério da Saúde", "valor_total": 50000.0},
            {"id_contrato": 102, "orgao": "Secretaria de Educação", "valor_total": 15000.0},
        ]
        return spark.createDataFrame(mock_data)


def transform_data(df):
    return df.withColumn("data_processamento_etl", current_timestamp())


def load_data(df, output_path: str):
    df.write.mode("overwrite").parquet(output_path)


def run_spark_pipeline():
    spark = create_spark_session()

    try:
        df_raw = extract_data(spark)

        if df_raw.count() == 0:
            print("Nenhum dado encontrado.")
            return

        df_clean = transform_data(df_raw)

        print("Amostra dos dados processados:")
        df_clean.show(5, truncate=False)

        output_dir = os.path.join(
            os.path.dirname(__file__), "..", "output_data", "contratos_pncp.parquet"
        )
        load_data(df_clean, output_dir)
        print(f"Parquet salvo em: {output_dir}")

    finally:
        spark.stop()


if __name__ == "__main__":
    run_spark_pipeline()
