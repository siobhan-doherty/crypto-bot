"""Smoke tests with mocked Docker dependencies."""
import subprocess
import time
import pytest
import requests
from unittest.mock import MagicMock, patch


def wait_for_service(url, timeout = 60):
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = requests.get(url, timeout = 2)
            if resp.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(2)
    return False


@patch("subprocess.run")
@patch("requests.get")
def test_containers_start_and_metadata_persists(mock_get, mock_run):
    """Test with mocked subprocess and requests."""
    # mock subprocess.run to do nothing and return success
    mock_result = MagicMock()
    mock_result.check = MagicMock(return_value = True)
    mock_result.returncode = 0
    mock_result.stdout = "persist"
    mock_result.stderr = ""
    mock_run.return_value = mock_result
    
    # mock requests.get to return 200
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_get.return_value = mock_response
    
    # run test
    subprocess.run(["docker", "compose", "up", "-d"], check = True)
    assert wait_for_service("http://localhost:8080/health"), "Airflow not healthy"
    
    subprocess.run(
        [
            "docker",
            "exec",
            "crypto_airflow",
            "airflow",
            "variables",
            "set",
            "smoke_test",
            "persist",
        ],
        check = True,
        capture_output = True,
        text = True,
    )
    
    subprocess.run(["docker", "compose", "restart", "postgres", "airflow"], check = True)
    time.sleep(0.1)  # reduced from 15s for faster testing
    assert wait_for_service("http://localhost:8080/health"), "Airflow not healthy after restart"
    
    result = subprocess.run(
        [
            "docker",
            "exec",
            "crypto_airflow",
            "airflow",
            "variables",
            "get",
            "smoke_test",
        ],
        capture_output = True,
        text = True,
        check = True,
    )
    assert result.stdout.strip() == "persist", "Metadata did not persist across restart"
    
    subprocess.run(
        [
            "docker",
            "exec",
            "crypto_airflow",
            "airflow",
            "variables",
            "delete",
            "smoke_test",
        ],
        check = False,
    )
    
    # verify mocks were called
    assert mock_run.call_count >= 4
    assert mock_get.call_count >= 2
