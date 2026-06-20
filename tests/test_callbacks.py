import json
from unittest.mock import MagicMock, patch

import dash
import pandas as pd
import plotly.graph_objects as go
from dash import no_update

from api_user.visualization import callbacks


# helpers
def make_ws_message(records = None):
    if records is None:
        records = [
            {
                "symbol": "BTCUSDT",
                "close_datetime": "2026-06-04T10:00:00Z",
                "close": 50000.0,
                "volume": 10.0,
                "open": 49000.0,
                "high": 51000.0,
                "low": 48500.0,
            }
        ]
    return {"data": json.dumps({"data": records})}


# tests for helper functions
def test_extract_ws_records_valid():
    ws_msg = make_ws_message()
    records, status = callbacks._extract_ws_records(ws_msg)
    assert records is not None
    assert len(records) == 1
    assert status == "WebSocket connected"


def test_extract_ws_records_missing_data():
    ws_msg = {}
    records, status = callbacks._extract_ws_records(ws_msg)
    assert records is None
    assert status == "WebSocket payload missing data field"


def test_extract_ws_records_invalid_json():
    ws_msg = {"data": "not json"}
    records, status = callbacks._extract_ws_records(ws_msg)
    assert records is None
    assert "Invalid WebSocket payload" in status


def test_extract_ws_records_error_payload():
    ws_msg = {"data": json.dumps({"error": "rate limit"})}
    records, status = callbacks._extract_ws_records(ws_msg)
    assert records is None
    assert "WebSocket error" in status


def test_extract_ws_records_empty_data():
    ws_msg = {"data": json.dumps({"data": []})}
    records, status = callbacks._extract_ws_records(ws_msg)
    assert records is None
    assert status == "No realtime data received"


def test_build_realtime_dataframe_valid():
    records = [
        {
            "symbol": "BTCUSDT",
            "close_datetime": "2026-06-04T10:00:00Z",
            "close": 50000.0,
            "volume": 10.0,
        }
    ]
    df, y_col, error = callbacks._build_realtime_dataframe(records)
    assert not df.empty
    assert y_col == "close"
    assert error is None


def test_build_realtime_dataframe_missing_column():
    records = [{"symbol": "BTCUSDT", "close": 50000.0}]
    df, y_col, error = callbacks._build_realtime_dataframe(records)
    assert error == "Missing realtime columns: close_datetime"


def test_build_realtime_dataframe_no_numeric():
    records = [{"symbol": "BTCUSDT", "close_datetime": "2026-06-04T10:00:00Z"}]
    df, y_col, error = callbacks._build_realtime_dataframe(records)
    assert error == "No numeric realtime field available"


def test_build_realtime_plot():
    df = pd.DataFrame({
        "close_datetime": pd.to_datetime(["2026-06-04T10:00:00Z"]), 
        "close": [50000.0]
    })
    fig = callbacks._build_realtime_plot(df, "BTCUSDT", "close")
    assert isinstance(fig, dict)
    assert "data" in fig
    assert fig["layout"]["title"]["text"] == "BTCUSDT Close Price"


def test_filtered_dataframe_or_empty_valid():
    df = pd.DataFrame(
        {
            "symbol": ["BTCUSDT", "ETHUSDT"],
            "close_datetime": pd.to_datetime(
                ["2026-06-04T10:00:00Z", "2026-06-04T11:00:00Z"]
            ),
            "close": [50000, 3000],
        }
    )
    filtered = callbacks._filtered_dataframe_or_empty(df, "BTCUSDT", None)
    assert len(filtered) == 1
    assert filtered.iloc[0]["symbol"] == "BTCUSDT"


def test_filtered_dataframe_or_empty_exception():
    df = pd.DataFrame()
    filtered = callbacks._filtered_dataframe_or_empty(df, "BTCUSDT", None)
    assert filtered.empty


def test_historical_figure_or_empty_empty_data():
    df = pd.DataFrame()
    fig = callbacks._historical_figure_or_empty(
        full_df = df,
        trading_pair = "BTCUSDT",
        date_range = None,
        required_columns = ("close_datetime", "close"),
        title = "Test",
        empty_message = "No data",
        figure_builder = lambda data, tp: go.Figure(),
    )
    assert fig.layout.title.text == "Test"
    assert fig.layout.annotations[0].text == "No data"


def test_historical_figure_or_empty_missing_columns():
    df = pd.DataFrame({"symbol": ["BTCUSDT"]})
    fig = callbacks._historical_figure_or_empty(
        full_df = df,
        trading_pair = "BTCUSDT",
        date_range = None,
        required_columns = ("close_datetime", "close"),
        title = "Test",
        empty_message = "No data",
        figure_builder = lambda data, tp: go.Figure(),
    )
    assert (
        "Missing required data: close_datetime, close"
        in fig["layout"]["annotations"][0]["text"]
    )


def test_historical_figure_or_empty_handles_builder_exception():
    def failing_builder(data, tp):
        raise ValueError("Something went wrong")

    df = pd.DataFrame({
        "close_datetime": pd.date_range("2026-06-15", periods = 5),
        "close": [1, 2, 3, 4, 5]
    })
    fig = callbacks._historical_figure_or_empty(
        full_df = df,
        trading_pair = "BTCUSDT",
        date_range = None,
        required_columns = ("close_datetime", "close"),
        title = "Test",
        empty_message = "No data",
        figure_builder = failing_builder
    )
    # exception is caught + empty_message is returned
    assert fig.layout.annotations[0].text == "No data"


# tests for module level callback handlers
def test_update_trading_pair_title():
    assert callbacks.update_trading_pair_title(None) == "Real-time Price"
    assert callbacks.update_trading_pair_title("BTCUSDT") == "BTCUSDT Real-time Price"


def test_update_real_time_no_message():
    fig, status = callbacks.update_real_time(None, "BTCUSDT")
    assert fig == dash.no_update
    assert status == "WebSocket not connected"


def test_update_real_time_bad_ws_message():
    ws_msg = {"something": "else"}
    fig, status = callbacks.update_real_time(ws_msg, "BTCUSDT")
    assert fig == dash.no_update
    assert status == "WebSocket payload missing data field"


def test_update_real_time_error_payload():
    ws_msg = {"data": json.dumps({"error": "rate limit"})}
    fig, status = callbacks.update_real_time(ws_msg, "BTCUSDT")
    assert fig == dash.no_update
    assert "WebSocket error" in status


def test_update_real_time_empty_data():
    ws_msg = {"data": json.dumps({"data": []})}
    fig, status = callbacks.update_real_time(ws_msg, "BTCUSDT")
    assert fig == dash.no_update
    assert status == "No realtime data received"


def test_update_real_time_valid_data():
    # set up realtime store
    callbacks._realtime_store = {}
    ws_msg = make_ws_message()
    fig, status = callbacks.update_real_time(ws_msg, "BTCUSDT")
    assert status == "WebSocket connected"
    assert isinstance(fig, dict)
    assert "data" in fig


def test_update_lineplot_returns_figure():
    df = pd.DataFrame({
        "symbol": ["BTCUSDT"] * 5,
        "close_datetime": pd.date_range("2026-06-15", periods = 5),
        "close": [1, 2, 3, 4, 5]
    })
    callbacks._full_df = df
    fig = callbacks.update_lineplot("BTCUSDT", None)
    assert isinstance(fig, dict)    # changed to dict
    assert len(fig["data"]) > 0
    assert fig["layout"]["title"]["text"] == "BTCUSDT Close Price with Exponential Moving Averages"


def test_update_candlestick_returns_figure():
    df = pd.DataFrame({
        "symbol": ["BTCUSDT"] * 5,
        "close_datetime": pd.date_range("2026-06-15", periods = 5),
        "open": [1, 2, 3, 4, 5],
        "high": [2, 3, 4, 5, 6],
        "low": [0, 1, 2, 3, 4],
        "close": [1, 2, 3, 4, 5]
    })
    callbacks._full_df = df
    fig = callbacks.update_candlestick("BTCUSDT", None)
    assert isinstance(fig, dict)    # changed to dict
    assert len(fig["data"]) > 0
    assert any(trace.get("type") == "candlestick" for trace in fig["data"])


def test_update_volume_returns_figure():
    df = pd.DataFrame({
        "symbol": ["BTCUSDT"] * 5,
        "close_datetime": pd.date_range("2026-06-15", periods = 5),
        "volume": [100, 200, 300, 400, 500],
        "open": [1, 2, 3, 4, 5],
        "close": [1, 2, 3, 4, 5]
    })
    callbacks._full_df = df
    fig = callbacks.update_volume("BTCUSDT", None)
    assert isinstance(fig, dict)    # changed to dict
    assert len(fig["data"]) > 0


def test_update_volatility_returns_figure():
    df = pd.DataFrame({
        "close_datetime": pd.date_range("2026-06-15", periods = 5),
        "close": [1, 2, 3, 4, 5],
        "high": [2, 3, 4, 5, 6],
        "low": [0, 1, 2, 3, 4]
    })
    callbacks._full_df = df
    # need to mock _filtered_dataframe_or_empty to return df for both pairs
    with patch("api_user.visualization.callbacks._filtered_dataframe_or_empty") as mock_filter:
        mock_filter.side_effect = [df, df]  # BTCUSDT, ETHUSDT
        fig = callbacks.update_volatility(14, None, None)
    assert isinstance(fig, dict)
    assert "data" in fig


def test_register_callbacks_smoke():
    app = MagicMock()
    with patch(
        "api_user.visualization.data_store.prepare_data", return_value = pd.DataFrame()
    ):
        callbacks.register_callbacks(app)
    # no exception equals success
