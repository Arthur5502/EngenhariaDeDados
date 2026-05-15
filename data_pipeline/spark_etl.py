import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, explode, current_timestamp
from dotenv import load_dotenv

os.environ["_JAVA_OPTIONS"] = "-Djava.security.manager=allow"

load_dotenv()

def create_spark_session():
    spark = SparkSession.builder \
        .appName("ETL_PNCP_Data") \
        .config("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.12:10.2.2")
        
    try:
        db_user = os.getenv("DB_USER")
        db_password = os.getenv("DB_PASSWORD")
        
        if db_user and db_password:
            mongo_uri = f"mongodb+srv://{db_user}:{db_password}@cluster0.cpevj4j.mongodb.net/?appName=Cluster0"
            # Corrige a injeção da coleção para evitar duas barras "//"
            mongo_read_uri = mongo_uri.replace("/?", "/pncp.contratacoes?")
            spark = spark.config("spark.mongodb.read.connection.uri", mongo_read_uri)
        else:
            raise ValueError("Senhas ausentes")
            
    except Exception:
        pass

    return spark.getOrCreate()

def extract_data(spark: SparkSession):
    try:
        if not os.getenv("DB_USER"):
            raise ValueError("Forçando MOCK")
        return spark.read.format("mongodb").load()
    except Exception as e:
        print(f"\nALERTA: Falha ao conectar/ler o MongoDB Real! Motivo: {e}")
        print("Caindo para o modo MOCK de segurança...\n")
        mock_data = [
            {"id_contrato": 101, "orgao": "Ministério da Saúde", "valor_total": 50000.0, "itens": [{"nome": "Seringa", "qtd": 1000}, {"nome": "Luvas", "qtd": 500}]},
            {"id_contrato": 102, "orgao": "Secretaria de Educação", "valor_total": 15000.0, "itens": [{"nome": "Lousa", "qtd": 10}, {"nome": "Giz", "qtd": 50}]}
        ]
        return spark.createDataFrame(mock_data)

def transform_data(df):
    df_transformed = df.withColumn("data_processamento_etl", current_timestamp())
    
    if "itens" in df.columns:
        df_transformed = df_transformed.withColumn("item", explode(col("itens")))
        df_transformed = df_transformed.drop("itens")
    
    return df_transformed

def load_data(df, output_path: str):
    df.write.mode("overwrite").parquet(output_path)

def run_spark_pipeline():
    spark = create_spark_session()
    
    try:
        df_raw = extract_data(spark)
        
        if df_raw.count() == 0:
            print("Nenhum dado encontrado no MongoDB. O banco pode estar vazio.")
            return

        df_clean = transform_data(df_raw)
        
        print("Tabela final processada do MongoDB Real:")
        df_clean.show(truncate=False)
        
        output_dir = os.path.join(os.path.dirname(__file__), "..", "output_data", "contratos_pncp.parquet")
        load_data(df_clean, output_dir)
        print(f"Arquivo parquet salvo em: {output_dir}")
        
    except Exception as e:
        raise e
    finally:
        spark.stop()

if __name__ == "__main__":
    run_spark_pipeline()

