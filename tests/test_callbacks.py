import json
from unittest.mock import MagicMock, patch

import pandas as pd
import plotly.graph_objects as go

from api_user.visualization import callbacks


# helper create a valid WebSocket message
def make_ws_message(records=None):
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


# tests for _extract_ws_records
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
    ws_msg = {"data": json.dumps(({"data": []}))}
    records, status = callbacks._extract_ws_records(ws_msg)
    assert records is None
    assert status == "No realtime data received"


# tests for _build_realtime_dataframe
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
    records = [{"symbol": "BTCUSDT", "close": 50000.0}]  # missing close_datetime
    df, y_col, error = callbacks._build_realtime_dataframe(records)
    assert error == "Missing realtime columns: close_datetime"


def test_build_realtime_dataframe_no_numeric():
    records = [{"symbol": "BTCUSDT", "close_datetime": "2026-06-04T10:00:00Z"}]
    df, y_col, error = callbacks._build_realtime_dataframe(records)
    assert error == "No numeric realtime field available"


# tests for _build_realtime_plot
def test_build_realtime_plot():
    df = pd.DataFrame(
        {"close_datetime": pd.to_datetime(["2026-06-04T10:00:00Z"]), "close": [50000.0]}
    )
    fig = callbacks._build_realtime_plot(df, "BTCUSDT", "close")
    assert isinstance(fig, dict)
    assert "data" in fig
    assert fig["layout"]["title"]["text"] == "BTCUSDT Close Price"


# tests for _filtered_dataframe_or_empty
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


# tests for _historical_figure_or_empty
def test_historical_figure_or_empty_empty_data():
    df = pd.DataFrame()
    fig = callbacks._historical_figure_or_empty(
        full_df=df,
        trading_pair="BTCUSDT",
        date_range=None,
        required_columns=("close_datetime", "close"),
        title="Test",
        empty_message="No data",
        figure_builder=lambda data, tp: go.Figure(),
    )
    assert fig.layout.title.text == "Test"
    assert fig.layout.annotations[0].text == "No data"


def test_historical_figure_or_empty_missing_columns():
    df = pd.DataFrame({"symbol": ["BTCUSDT"]})
    fig = callbacks._historical_figure_or_empty(
        full_df=df,
        trading_pair="BTCUSDT",
        date_range=None,
        required_columns=("close_datetime", "close"),
        title="Test",
        empty_message="No data",
        figure_builder=lambda data, tp: go.Figure(),
    )
    # fig is a dict
    assert (
        "Missing required data: close_datetime, close"
        in fig["layout"]["annotations"][0]["text"]
    )


# smoke test for register_callbacks, ensures no exceptions
def test_register_callbacks_smoke():
    app = MagicMock()
    with patch(
        "api_user.visualization.data_store.prepare_data", return_value=pd.DataFrame()
    ):
        callbacks.register_callbacks(app)
    # no exception = success
