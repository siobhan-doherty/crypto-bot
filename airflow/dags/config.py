import os

# data collector container name, used in 'docker exec' commands
DATA_COLLECTOR_CONTAINER = os.getenv(
    "DATA_COLLECTOR_CONTAINER", "crypto_data_collector"
)

# alerts container name, used in 'docker exec' commands
ALERTS_CONTAINER = os.getenv(
    "ALERTS_CONTAINER", "crypto_price_alerts"
)

# paths to scripts inside data collector container
INIT_HISTORICAL_SCRIPT = os.getenv(
    "INIT_HISTORICAL_SCRIPT",
    "/app/src/collection_admin/data/initialize_historical_data.py",
)

UPDATE_HISTORICAL_SCRIPT = os.getenv(
    "UPDATE_HISTORICAL_SCRIPT",
    "/app/src/collection_admin/data/update_historical_data.py",
)

# path to alerts script inside alerts container
ALERTS_SCRIPT = os.getenv(
    "ALERTS_SCRIPT",
    "/app/scripts/run_alerts.py --once",
)

# default DAG arguments, reused across all DAGs
DEFAULT_DAG_ARGS = {
    "owner": "airflow",
    "retries": 1,
    "start_date": None,  # use default
}
