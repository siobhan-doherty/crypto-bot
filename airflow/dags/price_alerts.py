"""
Airflow DAG for running the Price Alert Engine.

This DAG schedules the price alert engine to run at regular intervals,
replacing the standalone long-running service with a managed, scheduled process.

Uses BashOperator to exec into the alerts container, consistent with other DAGs.
The alerts container must be running for this DAG to work.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from config import DEFAULT_DAG_ARGS, ALERTS_CONTAINER, ALERTS_SCRIPT


# Default arguments
default_args = DEFAULT_DAG_ARGS.copy()
default_args.update({
    "start_date": datetime(2025, 7, 11),
    "retries": 3,
    "retry_delay": timedelta(minutes = 1),
    "execution_timeout": timedelta(minutes = 10),
})

# Define the DAG
with DAG(
    dag_id = "price_alerts",
    default_args = default_args,
    description = "Run price alert engine on a schedule to check and send alerts",
    schedule = "*/5 * * * *",  # Every 5 minutes
    catchup = False,
    tags = ["cryptobot", "alerts"],
    max_active_runs = 1,  # Prevent overlapping runs
) as dag:
    
    run_alerts = BashOperator(
        task_id = "run_price_alerts",
        bash_command = f"docker exec -i {ALERTS_CONTAINER} python {ALERTS_SCRIPT}",
        retries = 3,
        retry_delay = timedelta(minutes = 1),
    )
