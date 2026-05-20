from prefect import flow, task
from data_pipeline.spark_etl import run_spark_pipeline
from data_pipeline.spark_gold import run_gold_pipeline

@task(name="Camada Silver — Job PySpark", log_prints=True, retries=2, retry_delay_seconds=60)
def task_run_silver():
    run_spark_pipeline()

@task(name="Camada Gold — Agregações PySpark", log_prints=True, retries=1, retry_delay_seconds=30)
def task_run_gold():
    run_gold_pipeline()

@flow(name="ETL Pipeline - PNCP", log_prints=True)
def main_flow():
    task_run_silver()
    task_run_gold()

if __name__ == "__main__":
    main_flow()
