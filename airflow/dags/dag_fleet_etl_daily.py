from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT_DIR = "/Users/kloutruben/fleet-logistics-otif"
VENV_BIN = f"{PROJECT_DIR}/.venv/bin"

default_args = {
    "owner": "ruben_kuyota",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    # Requisito não funcional: alta resiliência nas retentativas de extração
    "retries": 3,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="fleet_logistics_otif_daily",
    default_args=default_args,
    description="Pipeline ETL diário TMS (PostgreSQL -> DuckDB -> dbt -> Gold BI)",
    schedule="@daily",
    start_date=datetime(2026, 11, 1),
    catchup=False,
    # Requisito não funcional: SLA máximo de 15 minutos
    dagrun_timeout=timedelta(minutes=15),
    tags=["logistica", "otif", "dbt", "duckdb"],
) as dag:

    extract_task = BashOperator(
        task_id="extrair_postgres_para_duckdb",
        bash_command=f"cd {PROJECT_DIR} && {VENV_BIN}/python scripts/extract_to_duckdb.py",
    )

    dbt_run_task = BashOperator(
        task_id="dbt_run_silver_gold",
        bash_command=f"cd {PROJECT_DIR}/dbt_project && {VENV_BIN}/dbt run --profiles-dir .",
    )

    dbt_test_task = BashOperator(
        task_id="dbt_test_qualidade",
        bash_command=f"cd {PROJECT_DIR}/dbt_project && {VENV_BIN}/dbt test --profiles-dir .",
    )

    export_bi_task = BashOperator(
        task_id="exportar_gold_para_bi",
        bash_command=f"cd {PROJECT_DIR} && {VENV_BIN}/python scripts/export_gold_parquet.py",
    )

    extract_task >> dbt_run_task >> dbt_test_task >> export_bi_task
