import os
import time
import subprocess
import requests
from pymongo import MongoClient


def run_cmd(cmd):
    result = subprocess.run(cmd, capture_output = True, text = True)
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def get_latest_run_id(dag_id):
    """Fetch most recent dag_run_id for given DAG using docker exec."""
    stdout, _, rc = run_cmd([
        "docker", "exec", "crypto_airflow", "airflow", 
        "dags", "list-runs", "-d", dag_id
    ])
    if rc != 0:
        return None
    lines = stdout.split("\n")
    for line in lines:
        if line.strip() and not line.startswith("=") and not line.startswith("dag_id"):
            parts = line.split()
            if len(parts) >= 2:
                return parts[1]   # run_id is second column
    return None


def wait_for_dag_success(dag_id, run_id, timeout = 600):
    start = time.time()
    while time.time() - start < timeout:
        stdout, _, rc = run_cmd([
            "docker", "exec", "crypto_airflow", "airflow", "dags", 
            "state", "--dag-id", dag_id, "--run-id", run_id
        ])
        if rc == 0:
            for line in stdout.split("\n"):
                if dag_id in line and run_id in line:
                    parts = line.split()
                    if len(parts) >= 3:
                        state = parts[2]
                        if state == "success":
                            return True
                        elif state == "failed":
                            return False
        time.sleep(5)
    raise TimeoutError(f"DAG run {run_id} did not complete within {timeout}s")


def test_full_pipeline():
    fastapi_url = os.getenv("FASTAPI_URL", "http://localhost:8000/api")
    mongo_endpoint = os.getenv("MONGO_ENDPOINT", "mongodb://localhost:27017")
    dag_id = "update_historical_data"
    # unpause DAG
    run_cmd([
        "docker", "exec", "crypto_airflow", 
        "airflow", "dags", "unpause", dag_id
    ])
    # get current latest run ID before triggering
    old_run_id = get_latest_run_id(dag_id)
    # trigger DAG
    _, stderr, rc = run_cmd([
        "docker", "exec", "crypto_airflow", 
        "airflow", "dags", "trigger", dag_id
    ])
    assert rc == 0, f"Failed to trigger DAG: {stderr}"
    # wait for new run to appear
    time.sleep(3)
    new_run_id = get_latest_run_id(dag_id)
    assert new_run_id is not None, "No new DAG run appeared after trigger"
    assert new_run_id != old_run_id, "Trigger did not create a new DAG run"
    # poll for success
    success = wait_for_dag_success(dag_id, new_run_id)
    assert success, f"DAG run {new_run_id} failed"
    # verify new historical data in MongoDB
    mongo_client = MongoClient(mongo_endpoint)
    collection = mongo_client["cryptobot"]["historical_data_15m"]
    now = int(time.time() * 1000)
    two_hours_ago = now - 2 * 60 * 60 * 1000
    doc = collection.find_one({"close_time": {"$gt": two_hours_ago}})
    assert doc is not None, "No recent historical data found after DAG run"
    mongo_client.close()
    # verify FastAPI serves data
    ohlcv_url = f"{fastapi_url}/market/ohlcv?symbol=BTCUSDT&limit=5"
    resp = requests.get(ohlcv_url, timeout = 10)
    resp.raise_for_status()
    data = resp.json()
    assert len(data) > 0, "FastAPI returned no historical data"
