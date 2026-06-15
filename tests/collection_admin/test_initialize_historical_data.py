import pytest
import requests
from unittest.mock import patch, MagicMock
# try to import module, skip whole test file if findspark is missing
initialize_historical_data = pytest.importorskip(
    "collection_admin.data.initialize_historical_data"
)


def test_initialize_success():
    with patch(
        "collection_admin.data.initialize_historical_data.requests"
    ) as mock_requests:
        mock_response = MagicMock()
        mock_response.json.return_value = [
            [
                1620000000000, "50000", "50200", "49900", "50100", "100",
                1620000060000, "5000000", 100, "1000", "500", "0"
            ],
            [
                1620000060000, "50100", "50300", "50000", "50200", "120",
                1620000120000, "6000000", 120, "1200", "600", "0"
            ]
        ]
        mock_response.raise_for_status = MagicMock()
        mock_requests.get.return_value = mock_response

        with patch(
            "collection_admin.db.mongo_utils.save_to_collection"
        ) as mock_save:
            initialize_historical_data.main()
            assert mock_save.call_count >= 1


def test_initialize_api_failure():
    with patch(
        "collection_admin.data.initialize_historical_data.requests"
    ) as mock_requests:
        mock_requests.get.side_effect = requests.RequestException("API error")
        with pytest.raises(requests.RequestException):
            initialize_historical_data.main()
