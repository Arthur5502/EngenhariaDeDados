from prefect import flow, task
from data_pipeline.spark_etl import run_spark_pipeline

@task(name="Executar Job PySpark", log_prints=True, retries=2, retry_delay_seconds=60)
def task_run_spark():
    run_spark_pipeline()

@flow(name="ETL Pipeline - PNCP", log_prints=True)
def main_flow():
    task_run_spark()

if __name__ == "__main__":
    main_flow()
