from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
from config import DATA_COLLECTOR_CONTAINER, INIT_HISTORICAL_SCRIPT, DEFAULT_DAG_ARGS 

default_args = DEFAULT_DAG_ARGS.copy()
default_args["start_date"] = datetime(2025, 7, 11)

# One-off task for initialization
with DAG(
    dag_id = "initialize_historical_data",
    default_args = default_args,
    schedule = None,    # Run manually
    catchup = False,
    tags = ["cryptobot"],
    max_active_runs = 2,
) as dag:
    initialize = BashOperator(
        task_id = "initialize_historical_data",
        bash_command = f"docker exec -i {DATA_COLLECTOR_CONTAINER} python {INIT_HISTORICAL_SCRIPT}",
        execution_timeout = timedelta(hours = 2),
        retries = 1,
        retry_delay = timedelta(minutes = 5),
    )
