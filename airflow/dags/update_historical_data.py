from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
from config import DATA_COLLECTOR_CONTAINER, UPDATE_HISTORICAL_SCRIPT, DEFAULT_DAG_ARGS 

default_args = DEFAULT_DAG_ARGS.copy()
default_args["start_date"] = datetime(2025, 7, 11)

with DAG(
    dag_id = "update_historical_data",
    default_args = default_args,
    schedule = "0 0 * * *",   # Daily at midnight
    catchup = False,
    tags = ["cryptobot"],
    max_active_runs = 2,
) as dag:
    update = BashOperator(
        task_id = "update_historical_data",
        bash_command = f"docker exec -i {DATA_COLLECTOR_CONTAINER} python {UPDATE_HISTORICAL_SCRIPT}",
        execution_timeout = timedelta(hours = 2),
        retries = 1,
        retry_delay = timedelta(minutes = 5),
    )
