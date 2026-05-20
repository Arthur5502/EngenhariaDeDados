import os
os.environ["_JAVA_OPTIONS"] = "-Djava.security.manager=allow"

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, count, sum as spark_sum, round as spark_round

SILVER_PATH = os.path.join(os.path.dirname(__file__), "..", "output_data", "contratos_pncp.parquet")
GOLD_BASE   = os.path.join(os.path.dirname(__file__), "..", "output_data", "gold")


def _write(df: DataFrame, name: str):
    path = os.path.join(GOLD_BASE, name)
    df.write.mode("overwrite").parquet(path)
    print(f"[GOLD] '{name}' salvo em {path} ({df.count()} linhas)")


def build_gold_layers(spark: SparkSession):
    silver = spark.read.parquet(SILVER_PATH)

    # --- por UF ---
    _write(
        silver.groupBy("uf_sigla", "uf_nome")
              .agg(
                  count("*").alias("total_contratos"),
                  spark_round(spark_sum("valor_total_estimado"), 2).alias("soma_valor_estimado"),
                  spark_round(spark_sum("valor_total_homologado"), 2).alias("soma_valor_homologado"),
              )
              .orderBy(col("soma_valor_estimado").desc()),
        "resumo_por_uf",
    )

    # --- por modalidade ---
    _write(
        silver.groupBy("modalidade_id", "modalidade_nome")
              .agg(
                  count("*").alias("total_contratos"),
                  spark_round(spark_sum("valor_total_estimado"), 2).alias("soma_valor_estimado"),
              )
              .orderBy(col("total_contratos").desc()),
        "resumo_por_modalidade",
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
        "top50_orgaos_por_valor",
    )

    # --- por ano ---
    _write(
        silver.groupBy("ano_compra")
              .agg(
                  count("*").alias("total_contratos"),
                  spark_round(spark_sum("valor_total_estimado"), 2).alias("soma_valor_estimado"),
              )
              .orderBy("ano_compra"),
        "resumo_por_ano",
    )

    # --- por situação de compra ---
    _write(
        silver.groupBy("situacao_compra_id", "situacao_compra_nome")
              .agg(
                  count("*").alias("total_contratos"),
                  spark_round(spark_sum("valor_total_estimado"), 2).alias("soma_valor_estimado"),
              )
              .orderBy(col("total_contratos").desc()),
        "resumo_por_situacao",
    )


def run_gold_pipeline():
    spark = (
        SparkSession.builder
        .appName("Gold_PNCP")
        .getOrCreate()
    )
    try:
        build_gold_layers(spark)
        print("[GOLD] Camada Gold gerada com sucesso.")
    finally:
        spark.stop()


if __name__ == "__main__":
    run_gold_pipeline()
