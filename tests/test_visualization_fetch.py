from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests

from api_user.visualization import fetch_data


# test call_api with retries
@patch("api_user.visualization.fetch_data.requests.get")
def test_call_api_success(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {"key": "value"}
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response
    result = fetch_data._call_api("test_endpoint")
    assert result == {"key": "value"}


@patch("api_user.visualization.fetch_data.requests.get")
def test_call_api_retry_on_failure(mock_get):
    mock_get.side_effect = requests.RequestException("fail")
    with pytest.raises(Exception):  # tenacity.RetryError
        fetch_data._call_api("test_endpoint")
    assert mock_get.call_count == 3  # initial + 2 times


# test get_available_date_range
@patch("api_user.visualization.fetch_data._call_api")
def test_get_available_date_range_success(mock_api):
    mock_api.return_value = {
        "min_date": "2025-01-01T00:00:00Z",
        "max_date": "2025-12-31T23:59:59Z",
    }
    min_date, max_date = fetch_data.get_available_date_range()
    assert min_date.year == 2025
    assert max_date.year == 2025


@patch("api_user.visualization.fetch_data._call_api")
def test_get_available_date_range_fallback(mock_api):
    mock_api.side_effect = Exception("API error")
    min_date, max_date = fetch_data.get_available_date_range()
    # fallback last 7 days
    assert (datetime.now(timezone.utc) - min_date).days <= 7


# test fetch_historical data
@patch("api_user.visualization.fetch_data._call_api")
def test_fetch_historical_data_success(mock_api):
    mock_api.return_value = [
        {
            "open_datetime": "2026-06-04T10:00:00Z",
            "close_datetime": "2026-06-04T10:15:00Z",
            "open": 50000.0,
            "high": 51000.0,
            "low": 49000.0,
            "close": 50500.0,
            "volume": 100.0,
        }
    ]
    df = fetch_data.fetch_historical_data()
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "close" in df.columns


@patch("api_user.visualization.fetch_data._call_api")
def test_fetch_historical_data_empty(mock_api):
    mock_api.return_value = []
    df = fetch_data.fetch_historical_data()
    assert df.empty


@patch("api_user.visualization.fetch_data._call_api")
def test_fetch_historical_data_uses_params(mock_api):
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    end = datetime(2025, 1, 2, tzinfo=timezone.utc)
    fetch_data.fetch_historical_data(start_time=start, end_time=end)
    call_args = mock_api.call_args
    # second argument is params dict
    params = call_args[1]["params"]
    assert "start_time" in params
    assert "end_time" in params


# test get historical_data / get streaming data, pydantic validation
@patch("api_user.visualization.fetch_data.requests.get")
def test_get_historical_data(mock_get):
    mock_response = MagicMock()
    mock_response.text = '{"symbol": "BTCUSDT", "data": []}'
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response
    result = fetch_data.get_historical_data("BTCUSDT")
    assert result.symbol == "BTCUSDT"


@patch("api_user.visualization.fetch_data.requests.get")
def test_get_streaming_data(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {
            "symbol": "BTCUSDT",
            "close": 50000.0,
            "open": 49000.0,
            "high": 51000.0,
            "low": 48500.0,
            "volume": 10.0,
            "close_time": 123,
            "quote_volume": 5000,
            "num_trades": 100,
            "taker_base_volume": 5,
            "taker_quote_volume": 5,
            "open_datetime": "2026-06-04T10:00:00Z",
            "close_datetime": "2026-06-04T10:15:00Z",
            "price_change": 1000,
            "price_change_pct": 2,
            "high_low_spread": 500,
            "high_low_spread_pct": 1,
            "ts": "2026-06-04T10:15:00Z",
            "is_closed": True,
        }
    ]
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response
    result = fetch_data.get_streaming_data("BTCUSDT")
    assert len(result) == 1
    assert result[0].symbol == "BTCUSDT"
