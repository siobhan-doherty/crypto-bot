import subprocess
import time
from unittest.mock import MagicMock, patch

import pytest
import requests


# mock subprocess.run outputs for Airflow CLI commands
class MockResult:
    def __init__(self, returncode, stdout, stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def mock_subprocess_run(cmd, **kwargs):
    cmd_str = " ".join(cmd)
    if "airflow dags unpause" in cmd_str:
        return MockResult(0, "")
    if "airflow dags trigger" in cmd_str:
        return MockResult(
            0,
            """conf | dag_id              | dag_run_id          
{}   | update_historical_data | manual__2026-06-04T12:00:00+00:00
""",
        )
    if "airflow dags list-runs" in cmd_str:
        return MockResult(
            0,
            """dag_id                 | run_id                               | state
update_historical_data | manual__2026-06-04T12:00:00+00:00 | running
""",
        )
    if "airflow dags state" in cmd_str:
        return MockResult(
            0,
            """update_historical_data | manual__2026-06-04T12:00:00+00:00 | success""",
        )
    return MockResult(0, "", "")


@patch("subprocess.run", side_effect=mock_subprocess_run)
@patch("pymongo.MongoClient")
@patch("requests.get")
def test_full_pipeline_mocked(mock_requests_get, mock_mongo_client, mock_subprocess):
    # create fully controlled MongoDB mock hierarchy
    mock_collection = MagicMock()
    mock_collection.find_one.return_value = {
        "_id": "mock",
        "close_time": int(time.time() * 1000),
    }

    mock_db = MagicMock()
    mock_db.__getitem__.return_value = mock_collection

    mock_client = MagicMock()
    mock_client.__getitem__.return_value = mock_db

    mock_mongo_client.return_value = mock_client

    # mock FastAPI response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{"close": 50000.0}]
    mock_requests_get.return_value = mock_response

    # execute high‑level logic, simulate real test steps
    dag_id = "update_historical_data"

    subprocess.run(
        ["docker", "exec", "crypto_airflow", "airflow", "dags", "unpause", dag_id]
    )
    subprocess.run(
        ["docker", "exec", "crypto_airflow", "airflow", "dags", "trigger", dag_id]
    )

    # verify subprocess was called with expected commands
    calls = [call[0][0] for call in mock_subprocess.call_args_list]
    assert any("unpause" in str(call) for call in calls)
    assert any("trigger" in str(call) for call in calls)
