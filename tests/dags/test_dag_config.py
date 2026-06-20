import sys

import pytest
from airflow.models import DagBag

DAGS_DIR = "airflow/dags/"
if DAGS_DIR not in sys.path:
    sys.path.insert(0, DAGS_DIR)


@pytest.fixture
def dag_bag():
    return DagBag(dag_folder=DAGS_DIR, include_examples=False)


def test_no_import_errors(dag_bag):
    assert not dag_bag.import_errors, f"DAG import errors: {dag_bag.import_errors}"


def test_max_active_runs_not_one(dag_bag):
    """Prevent a single DAG run from blocking all others"""
    # list actual DAG IDs
    dag_ids = ["update_historical_data", "initialize_historical_data"]
    for dag_id in dag_ids:
        dag = dag_bag.dags.get(dag_id)
        assert dag is not None, f"{dag_id} not found"
        assert (
            dag.max_active_runs > 1
        ), f"{dag_id} has max_active_runs = {dag.max_active_runs} (would block)"


def test_task_timeouts_are_set(dag_bag):
    """Ensure all operators have a timeout to avoid indefinite hang"""
    risky_operator_types = ["BashOperator", "PythonOperator", "Sensor"]
    for dag in dag_bag.dags.values():
        for task in dag.tasks:
            if task.task_type in risky_operator_types:
                assert (
                    task.execution_timeout is not None
                ), f"Task {task.task_id} in {dag.dag_id} missing timeout"
