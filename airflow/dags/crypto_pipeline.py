from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2025, 7, 10),
    'retries': 2,
}

dag = DAG(
    dag_id='crypto_pipeline',
    default_args=default_args,
    schedule_interval=None,  # Manual trigger for initialize
    catchup=False,
    tags=['cryptobot'],
)

# One-time task (run manually in UI): initialize historical data
initialize = BashOperator(
    task_id='initialize_historical_data',
    bash_command='python /app/data/initialize_historical_data.py',
    dag=dag,
)

# Scheduled daily task: update historical data
update_dag = DAG(
    dag_id='update_historical_data',
    default_args=default_args,
    schedule_interval='0 0 * * *',  # Every day at midnight
    catchup=False,
    tags=['cryptobot'],
)

update = BashOperator(
    task_id='update_historical_data',
    bash_command='python /app/data/update_historical_data.py',
    dag=update_dag,
)
