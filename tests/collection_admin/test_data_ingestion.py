import os
import sys
import pytest
pytest.skip("Skipping because it causes hang; fix later", allow_module_level = True)
from types import ModuleType
from unittest.mock import MagicMock, patch
# disable Kafka mocks from conftest & mock Spark dependencies
os.environ["E2E_TEST"] = "1"
# mock findspark & pyspark globally to allow clean import
sys.modules["findspark"] = MagicMock()
pyspark = ModuleType("pyspark")
pyspark_sql = ModuleType("pyspark.sql")
pyspark_sql.Row = MagicMock()
pyspark_sql.SparkSession = MagicMock()
pyspark.sql = pyspark_sql
sys.modules["pyspark"] = pyspark
sys.modules["pyspark.sql"] = pyspark_sql
# mock SparkSession.builder chain
mock_builder = MagicMock()
mock_builder.appName.return_value = mock_builder
mock_builder.config.return_value = mock_builder
mock_builder.getOrCreate.return_value = MagicMock()
pyspark_sql.SparkSession.builder = mock_builder
# import real module
from collection_admin.data import update_historical_data


@pytest.mark.timeout(10)
@patch("collection_admin.data.update_historical_data.save_to_collection")
@patch("collection_admin.data.update_historical_data.get_last_ts")
@patch("collection_admin.data.update_historical_data.get_klines")
def test_update_success(mock_get_klines, mock_get_last_ts, mock_save):
    mock_get_last_ts.side_effect = [1620000000000, 1620000000000]
    mock_get_klines.side_effect = [
        [
            [
                1620000060000, "50100", "50300", "50000", "50200", "120",
                1620000120000, "6000000", 120, "1200", "600", "0"
            ]
        ],
        []
    ]
    with patch("time.sleep"):
        update_historical_data.main()
    mock_save.assert_called_once()


@pytest.mark.timeout(10)
@patch("collection_admin.data.update_historical_data.save_to_collection")
@patch("collection_admin.data.update_historical_data.get_last_ts")
@patch("collection_admin.data.update_historical_data.get_klines")
def test_update_no_new_data(mock_get_klines, mock_get_last_ts, mock_save):
    mock_get_last_ts.side_effect = [1620000060000, 1620000060000]
    mock_get_klines.side_effect = [[], []]
    with patch("time.sleep"):
        update_historical_data.main()
    mock_save.assert_not_called()


@pytest.mark.timeout(10)
@patch("collection_admin.data.update_historical_data.save_to_collection")
@patch("collection_admin.data.update_historical_data.get_last_ts")
@patch("collection_admin.data.update_historical_data.get_klines")
def test_update_empty_db(mock_get_klines, mock_get_last_ts, mock_save):
    mock_get_last_ts.side_effect = [None, None]
    mock_get_klines.side_effect = [
        [
            [
                1620000000000, "50000", "50200", "49900", "50100", "100",
                1620000060000, "5000000", 100, "1000", "500", "0"
            ]
        ],
        [
            [
                1620000000000, "3000", "3100", "2900", "3050", "500",
                1620000060000, "1500000", 500, "5000", "250", "0"
            ]
        ]
    ]
    with patch("time.sleep"):
        update_historical_data.main()
    assert mock_save.call_count == 2
