from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2025, 7, 11),
    'retries': 1,
}

# One-off task for initialization
with DAG(
    dag_id='initialize_historical_data',
    default_args=default_args,
    schedule_interval=None,    # Run manually
    catchup=False,
    tags=['cryptobot'],
) as dag_init:

    initialize = BashOperator(
        task_id='initialize_historical_data',
        bash_command=(
            "docker exec -i crypto_data_collector "
            "python3 /app/data/initialize_historical_data.py"
        )
    )

# Daily update task
with DAG(
    dag_id='update_historical_data',
    default_args=default_args,
    schedule_interval="0 0 * * *",   # Every day at midnight
    catchup=False,
    tags=['cryptobot'],
) as dag_update:

    update = BashOperator(
        task_id='update_historical_data',
        bash_command=(
            "docker exec -i crypto_data_collector "
            "python3 /app/data/update_historical_data.py"
        )
    )