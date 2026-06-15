import sys 
import pytest 
from airflow.models import DagBag


# add DAGs directory to Python path so 'config' can be imported
sys.path.insert(0, "airflow/dags")

def test_no_import_errors():
    dag_bag = DagBag(
        dag_folder = "airflow/dags/", include_examples = False
    )
    assert not dag_bag.import_errors, f"DAG import errors: {dag_bag.import_errors}"
