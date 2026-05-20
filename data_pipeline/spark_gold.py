import os
os.environ["_JAVA_OPTIONS"] = "-Djava.security.manager=allow"

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, count, sum as spark_sum, round as spark_round
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

SILVER_PATH = os.path.join(os.path.dirname(__file__), "..", "output_data", "contratos_pncp.parquet")
GOLD_BASE   = os.path.join(os.path.dirname(__file__), "..", "output_data", "gold")


def _get_mongo_db():
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    uri = (
        f"mongodb+srv://{db_user}:{db_password}"
        "@cluster0.cpevj4j.mongodb.net/?appName=Cluster0"
    )
    client = MongoClient(uri, serverSelectionTimeoutMS=10000)
    return client, client["pncp"]


def _write(df: DataFrame, name: str, db):
    # Salva em Parquet
    path = os.path.join(GOLD_BASE, name)
    df.write.mode("overwrite").parquet(path)

    # Salva no MongoDB
    rows = [row.asDict() for row in df.collect()]
    collection = db[f"gold_{name}"]
    collection.drop()
    if rows:
        collection.insert_many(rows)

    print(f"[GOLD] '{name}': {len(rows)} linhas → Parquet + MongoDB (gold_{name})")


def build_gold_layers(spark: SparkSession, db):
    silver = spark.read.parquet(SILVER_PATH)

    # --- todos os dados (sem filtro) ---
    _write(silver, "todos_contratos", db)

    # --- por UF ---
    _write(
        silver.groupBy("uf_sigla", "uf_nome")
              .agg(
                  count("*").alias("total_contratos"),
                  spark_round(spark_sum("valor_total_estimado"), 2).alias("soma_valor_estimado"),
                  spark_round(spark_sum("valor_total_homologado"), 2).alias("soma_valor_homologado"),
              )
              .orderBy(col("soma_valor_estimado").desc()),
        "resumo_por_uf", db,
    )

    # --- por modalidade ---
    _write(
        silver.groupBy("modalidade_id", "modalidade_nome")
              .agg(
                  count("*").alias("total_contratos"),
                  spark_round(spark_sum("valor_total_estimado"), 2).alias("soma_valor_estimado"),
              )
              .orderBy(col("total_contratos").desc()),
        "resumo_por_modalidade", db,
    )

    # --- por órgão (top 50 por valor estimado) ---
    _write(
        silver.groupBy("orgao_cnpj", "orgao_razao_social")
              .agg(
                  count("*").alias("total_contratos"),
                  spark_round(spark_sum("valor_total_estimado"), 2).alias("soma_valor_estimado"),
              )
              .orderBy(col("soma_valor_estimado").desc())
              .limit(50),
        "top50_orgaos_por_valor", db,
    )

    # --- por ano ---
    _write(
        silver.groupBy("ano_compra")
              .agg(
                  count("*").alias("total_contratos"),
                  spark_round(spark_sum("valor_total_estimado"), 2).alias("soma_valor_estimado"),
              )
              .orderBy("ano_compra"),
        "resumo_por_ano", db,
    )

    # --- por situação de compra ---
    _write(
        silver.groupBy("situacao_compra_id", "situacao_compra_nome")
              .agg(
                  count("*").alias("total_contratos"),
                  spark_round(spark_sum("valor_total_estimado"), 2).alias("soma_valor_estimado"),
              )
              .orderBy(col("total_contratos").desc()),
        "resumo_por_situacao", db,
    )


def run_gold_pipeline():
    spark = SparkSession.builder.appName("Gold_PNCP").getOrCreate()
    client, db = _get_mongo_db()
    try:
        build_gold_layers(spark, db)
        print("[GOLD] Camada Gold gerada com sucesso.")
    finally:
        spark.stop()
        client.close()


if __name__ == "__main__":
    run_gold_pipeline()
