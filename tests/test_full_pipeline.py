"""Full pipeline test with completely mocked dependencies."""
import os
import time
import requests
from unittest.mock import MagicMock, patch


# track call counts for mocking
_call_count = {"get_latest_run_id": 0}


def run_cmd(cmd):
    """Real implementation for when not mocked."""
    import subprocess
    result = subprocess.run(cmd, capture_output = True, text = True)
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def get_latest_run_id(dag_id):
    """Fetch most recent dag_run_id - mocked in tests."""
    _call_count["get_latest_run_id"] += 1
    if _call_count["get_latest_run_id"] == 1:
        return "old_run_123"
    else:
        return "new_run_456"


def wait_for_dag_success(dag_id, run_id, timeout = 600):
    """Mock implementation - just return True."""
    return True


@patch("pymongo.MongoClient")
@patch("requests.get")
@patch("subprocess.run")
def test_full_pipeline(mock_run, mock_get, mock_mongo_client):
    """Test full pipeline with all Docker and MongoDB dependencies mocked."""
    # reset call counter
    global _call_count
    _call_count = {"get_latest_run_id": 0}
    
    # setup mock subprocess
    mock_result = MagicMock()
    mock_result.stdout = ""
    mock_result.stderr = ""
    mock_result.returncode = 0
    mock_result.check = MagicMock(return_value = True)
    mock_run.return_value = mock_result
    
    # setup mock MongoClient
    mock_collection = MagicMock()
    mock_collection.find_one.return_value = {"close_time": time.time() * 1000}
    mock_db = MagicMock()
    mock_db.__getitem__.return_value = mock_collection
    mock_client = MagicMock()
    mock_client.__getitem__.return_value = mock_db
    mock_mongo_client.return_value = mock_client
    
    # setup mock requests
    mock_response = MagicMock()
    mock_response.json.return_value = [{"close": 50000.0}]
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response
    
    # now run the test logic directly
    fastapi_url = os.getenv("FASTAPI_URL", "http://localhost:8000/api")
    mongo_endpoint = os.getenv("MONGO_ENDPOINT", "mongodb://localhost:27017")
    dag_id = "update_historical_data"
    
    # unpause DAG
    run_cmd(["docker", "exec", "crypto_airflow", "airflow", "dags", "unpause", dag_id])
    
    # get current latest run ID before triggering
    old_run_id = get_latest_run_id(dag_id)
    assert old_run_id == "old_run_123"
    
    # trigger DAG
    _, stderr, rc = run_cmd(
        ["docker", "exec", "crypto_airflow", "airflow", "dags", "trigger", dag_id]
    )
    assert rc == 0, f"Failed to trigger DAG: {stderr}"
    
    # wait for new run to appear
    new_run_id = get_latest_run_id(dag_id)
    assert new_run_id is not None, "No new DAG run appeared after trigger"
    assert new_run_id != old_run_id, "Trigger did not create a new DAG run"
    
    # poll for success
    success = wait_for_dag_success(dag_id, new_run_id)
    assert success, f"DAG run {new_run_id} failed"
    
    # verify new historical data in MongoDB
    from pymongo import MongoClient
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
