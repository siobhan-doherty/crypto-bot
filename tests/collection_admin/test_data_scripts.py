from unittest.mock import patch

import pytest


# tests for initialize_historical_data.py
@pytest.mark.skip(reason="Patching path needs refactoring; script is low-priority")
@patch("collection_admin.data.initialize_historical_data.save_to_collection")
@patch("collection_admin.data.initialize_historical_data.requests.get")
def test_initialize_historical_data_success(mock_get, mock_save):
    pass


@pytest.mark.skip(reason="Patching path needs refactoring; script is low-priority")
@patch("collection_admin.data.initialize_historical_data.requests.get")
def test_initialize_historical_data_api_failure(mock_get):
    pass


# tests for update_historical_data.py
@patch("collection_admin.data.update_historical_data.save_to_collection")
@patch("collection_admin.data.update_historical_data.get_last_ts")
@patch("collection_admin.data.update_historical_data.get_klines")
def test_update_historical_data_success(mock_get_klines, mock_get_last_ts, mock_save):
    mock_get_last_ts.side_effect = [1620000000000, 1620000000000]
    mock_get_klines.side_effect = [
        [
            [
                1620000060000,
                "50100",
                "50300",
                "50000",
                "50200",
                "120",
                1620000120000,
                "6000000",
                120,
                "1200",
                "600",
                "0",
            ]
        ],
        [],
    ]
    from collection_admin.data import update_historical_data

    update_historical_data.main()
    mock_save.assert_called_once()


@patch("collection_admin.data.update_historical_data.save_to_collection")
@patch("collection_admin.data.update_historical_data.get_last_ts")
@patch("collection_admin.data.update_historical_data.get_klines")
def test_update_historical_data_no_new_data(
    mock_get_klines, mock_get_last_ts, mock_save
):
    mock_get_last_ts.side_effect = [1620000060000, 1620000060000]
    mock_get_klines.side_effect = [[], []]
    from collection_admin.data import update_historical_data

    update_historical_data.main()
    mock_save.assert_not_called()


@patch("collection_admin.data.update_historical_data.save_to_collection")
@patch("collection_admin.data.update_historical_data.get_last_ts")
@patch("collection_admin.data.update_historical_data.get_klines")
def test_update_historical_data_no_existing_timestamp(
    mock_get_klines, mock_get_last_ts, mock_save
):
    mock_get_last_ts.side_effect = [None, None]
    mock_get_klines.side_effect = [
        [
            [
                1620000000000,
                "50000",
                "50200",
                "49900",
                "50100",
                "100",
                1620000060000,
                "5000000",
                100,
                "1000",
                "500",
                "0",
            ]
        ],
        [
            [
                1620000000000,
                "3000",
                "3100",
                "2900",
                "3050",
                "500",
                1620000060000,
                "1500000",
                500,
                "5000",
                "250",
                "0",
            ]
        ],
    ]
    from collection_admin.data import update_historical_data

    update_historical_data.main()
    assert mock_save.call_count == 2
