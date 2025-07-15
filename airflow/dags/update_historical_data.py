from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2025, 7, 11),
    'retries': 1,
}

with DAG(
    dag_id='update_historical_data',
    default_args=default_args,
    schedule_interval="0 0 * * *",   # Daily at midnight
    catchup=False,
    tags=['cryptobot'],
) as dag:

    update_task = BashOperator(
        task_id='update_historical_data',
        bash_command=(
            "docker exec -i crypto_data_collector "
            "python3 /app/src/collection_admin/data/update_historical_data.py"
        )
    )
    
    update_task
