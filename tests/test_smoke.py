import subprocess
import time
import requests
import pytest


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


def test_containers_start_and_metadata_persists():
    subprocess.run(["docker", "compose", "up", "-d"], check = True)
    assert wait_for_service("http://localhost:8080/health"), "Airflow not healthy"
    subprocess.run(
        [
            "docker", "exec", "crypto_airflow", "airflow", 
            "variables", "set", "smoke_test", "persist"
        ],
        check = True, capture_output = True, text = True
    )
    subprocess.run(
        ["docker", "compose", "restart", "postgres", "airflow"], 
        check = True
    )
    time.sleep(15)
    assert wait_for_service("http://localhost:8080/health"), "Airflow not healthy after restart"
    result = subprocess.run(
        [
            "docker", "exec", "crypto_airflow", 
            "airflow", "variables", "get", "smoke_test"
        ],
        capture_output = True, text = True, check = True
    )
    assert result.stdout.strip() == "persist", "Metadata did not persist across restart"
    subprocess.run(
        [
            "docker", "exec", "crypto_airflow", "airflow", 
            "variables", "delete", "smoke_test"
        ],
        check = False
    )
