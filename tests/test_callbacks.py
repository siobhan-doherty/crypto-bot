from __future__ import annotations
from pathlib import Path
from dash import Dash
from datetime import datetime, timezone, timedelta
import importlib
import json
import sys
import types
import pandas as pd
import plotly.graph_objects as go
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"


@pytest.fixture
def callbacks_module(monkeypatch):
    visualization_pkg = types.ModuleType("api_user.visualization")
    visualization_pkg.__path__ = [str(SRC_DIR / "api_user" / "visualization")]

    data_store_stub = types.ModuleType("api_user.visualization.data_store")
    data_store_stub.prepare_data = lambda: pd.DataFrame(
        {
            "symbol": ["BTCUSDT", "ETHUSDT"],
            "close_datetime": pd.to_datetime(
                ["2026-05-19T10:00:00Z", "2026-05-19T10:05:00Z"],
                utc = True,
            ),
            "open": [100.0, 200.0],
            "high": [110.0, 210.0],
            "low": [95.0, 195.0],
            "close": [105.0, 205.0],
            "volume": [1000.0, 2000.0],
        }
    )

    controls_stub = types.ModuleType("api_user.visualization.layout.controls")
    controls_stub.create_range_selector = lambda y_col: {
        "title": {"text": f"Range: {y_col}"}
    }

    lineplot_stub = types.ModuleType("api_user.visualization.plots.lineplot")
    lineplot_stub.create_lineplot = lambda df, trading_pair, show_emas = False: go.Figure(
        data=[
            go.Scatter(
                x = df["close_datetime"],
                y = df["close"],
                mode = "lines",
                name = trading_pair,
            )
        ]
    )

    candlestick_stub = types.ModuleType("api_user.visualization.plots.candlestickplot")
    candlestick_stub.create_candlestickplot = lambda df, trading_pair: go.Figure(
        data=[
            go.Candlestick(
                x = df["close_datetime"],
                open = df["open"],
                high = df["high"],
                low = df["low"],
                close = df["close"],
                name = trading_pair,
            )
        ]
    )

    volumeplot_stub = types.ModuleType("api_user.visualization.plots.volumeplot")
    volumeplot_stub.create_volumeplot = lambda df, trading_pair: go.Figure(
        data=[
            go.Bar(
                x = df["close_datetime"],
                y = df["volume"],
                name = trading_pair,
            )
        ]
    )

    volatilityplot_stub = types.ModuleType(
        "api_user.visualization.plots.volatilityplot"
    )
    volatilityplot_stub.create_volatility_plot = lambda pair_data, period: go.Figure(
        data=[
            go.Scatter(
                x = next(iter(pair_data.values()))["close_datetime"],
                y = [float(period or 14)] * len(next(iter(pair_data.values()))),
                mode = "lines",
                name = "volatility",
            )
        ]
    )

    utils_stub = types.ModuleType("api_user.visualization.utils")

    def stub_filter_df(full_dataframe, trading_pair, date_range):
        if full_dataframe is None or full_dataframe.empty:
            return pd.DataFrame()

        filtered = full_dataframe[full_dataframe["symbol"] == trading_pair].copy()
        if filtered.empty:
            return filtered

        if date_range is None:
            return filtered

        if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
            start_idx = max(int(date_range[0]), 0)
            end_idx = min(int(date_range[1]), len(filtered) - 1)
            if start_idx > end_idx:
                return pd.DataFrame(columns = filtered.columns)
            return filtered.iloc[start_idx : end_idx + 1].copy()

        return filtered

    utils_stub.filter_df = stub_filter_df

    monkeypatch.setitem(sys.modules, "api_user.visualization", visualization_pkg)
    monkeypatch.setitem(
        sys.modules, "api_user.visualization.data_store", data_store_stub
    )
    monkeypatch.setitem(
        sys.modules, "api_user.visualization.layout.controls", controls_stub
    )
    monkeypatch.setitem(
        sys.modules, "api_user.visualization.plots.lineplot", lineplot_stub
    )
    monkeypatch.setitem(
        sys.modules,
        "api_user.visualization.plots.candlestickplot",
        candlestick_stub,
    )
    monkeypatch.setitem(
        sys.modules,
        "api_user.visualization.plots.volumeplot",
        volumeplot_stub,
    )
    monkeypatch.setitem(
        sys.modules,
        "api_user.visualization.plots.volatilityplot",
        volatilityplot_stub,
    )
    monkeypatch.setitem(sys.modules, "api_user.visualization.utils", utils_stub)

    sys.modules.pop("api_user.visualization.callbacks", None)
    module = importlib.import_module("api_user.visualization.callbacks")
    return importlib.reload(module)


def test_extract_ws_records_valid_payload(callbacks_module):
    # complete mock streaming record matching StreamingData schema
    now = datetime.now(timezone.utc)
    mock_record = {
        "symbol": "BTCUSDT",
        "open_time": int(now.timestamp() * 1000),
        "open": 50000.0,
        "high": 50200.0,
        "low": 49900.0,
        "close": 100000.0,
        "volume": 1.5,
        "close_time": int(now.timestamp() * 1000) + 60000,
        "quote_volume": 75000.0,
        "num_trades": 120,
        "taker_base_volume": 0.8,
        "taker_quote_volume": 40000.0,
        "open_datetime": now.isoformat(),
        "close_datetime": (now + timedelta(minutes=1)).isoformat(),
        "price_change": 100.0,
        "price_change_pct": 0.2,
        "high_low_spread": 300.0,
        "high_low_spread_pct": 0.6,
        "ts": now.isoformat(),
        "is_closed": True,
    }
    ws_message = {
        "data": json.dumps({"data": [mock_record]})
    }

    records, status = callbacks_module._extract_ws_records(ws_message)

    assert records is not None
    assert status == "WebSocket connected"
    assert len(records) == 1
    assert records[0]["symbol"] == "BTCUSDT"


def test_extract_ws_records_invalid_json(callbacks_module):
    records, status = callbacks_module._extract_ws_records({"data": "{bad json"})

    assert records is None
    assert status == "Invalid WebSocket payload"


def test_extract_ws_records_payload_error(callbacks_module):
    records, status = callbacks_module._extract_ws_records(
        {"data": json.dumps({"error": "boom"})}
    )

    assert records is None
    assert status == "WebSocket error: boom"


def test_missing_columns(callbacks_module):
    dataframe = pd.DataFrame({"close": [1.0]})

    result = callbacks_module._missing_columns(
        dataframe,
        ("close_datetime", "close", "volume"),
    )

    assert result == ["close_datetime", "volume"]


def test_coerce_datetime_column_converts_timezone(callbacks_module):
    dataframe = pd.DataFrame(
        {"close_datetime": ["2026-05-19T10:00:00Z", "2026-05-19T10:05:00Z"]}
    )

    result = callbacks_module._coerce_datetime_column(dataframe, "close_datetime")

    assert not result.empty
    assert str(result["close_datetime"].dtype).startswith("datetime64[ns,")
    assert "Europe/Berlin" in str(result["close_datetime"].dt.tz)


def test_first_available_numeric_column(callbacks_module):
    dataframe = pd.DataFrame(
        {
            "timestamp": [1],
            "close_time": [2],
            "close_datetime": pd.to_datetime(["2026-05-19T10:00:00Z"], utc = True),
            "close": [100.0],
            "volume": [5.0],
        }
    )

    result = callbacks_module._first_available_numeric_column(dataframe)

    assert result == "close"


def test_build_realtime_dataframe_valid_records(callbacks_module):
    dataframe, y_col, error = callbacks_module._build_realtime_dataframe(
        [
            {
                "symbol": "BTCUSDT",
                "close_datetime": "2026-05-19T10:00:00Z",
                "close": 100000.0,
                "volume": 5.0,
            },
            {
                "symbol": "BTCUSDT",
                "close_datetime": "2026-05-19T10:01:00Z",
                "close": 100100.0,
                "volume": 6.0,
            },
        ]
    )

    assert error is None
    assert y_col == "close"
    assert list(dataframe.columns) == ["symbol", "close_datetime", "close", "volume"]
    assert len(dataframe) == 2


def test_build_realtime_dataframe_missing_required_column(callbacks_module):
    dataframe, y_col, error = callbacks_module._build_realtime_dataframe(
        [{"symbol": "BTCUSDT", "close": 100000.0}]
    )

    assert isinstance(dataframe, pd.DataFrame)
    assert y_col is None
    assert error == "Missing realtime columns: close_datetime"


def test_build_realtime_dataframe_missing_symbol(callbacks_module):
    dataframe, y_col, error = callbacks_module._build_realtime_dataframe(
        [{"close_datetime": "2026-05-19T10:00:00Z", "close": 100000.0}]
    )

    assert isinstance(dataframe, pd.DataFrame)
    assert y_col is None
    assert error == "Realtime symbol missing"


def test_build_realtime_dataframe_no_numeric_column(callbacks_module):
    dataframe, y_col, error = callbacks_module._build_realtime_dataframe(
        [{"symbol": "BTCUSDT", "close_datetime": "2026-05-19T10:00:00Z"}]
    )

    assert isinstance(dataframe, pd.DataFrame)
    assert y_col is None
    assert error == "No numeric realtime field available"


def test_empty_figure(callbacks_module):
    figure = callbacks_module._empty_figure("Test Title", "Nothing to show")

    assert isinstance(figure, go.Figure)
    assert figure.layout.title.text == "Test Title"
    assert len(figure.layout.annotations) == 1
    assert figure.layout.annotations[0].text == "Nothing to show"


def test_build_realtime_plot(callbacks_module):
    dataframe = pd.DataFrame(
        {
            "close_datetime": pd.to_datetime(
                ["2026-05-19T10:00:00Z", "2026-05-19T10:01:00Z"],
                utc=True,
            ),
            "close": [100000.0, 100100.0],
        }
    )

    figure = callbacks_module._build_realtime_plot(dataframe, "BTCUSDT", "close")

    assert isinstance(figure, go.Figure)
    assert len(figure.data) == 1
    assert figure.data[0].name == "BTCUSDT"


def test_filtered_dataframe_or_empty_returns_empty_on_exception(
    callbacks_module, monkeypatch
):
    def boom(*args, **kwargs):
        raise RuntimeError("filter failed")

    monkeypatch.setattr(callbacks_module, "filter_df", boom)

    result = callbacks_module._filtered_dataframe_or_empty(
        pd.DataFrame({"symbol": ["BTCUSDT"]}),
        "BTCUSDT",
        [0, 1],
    )

    assert isinstance(result, pd.DataFrame)
    assert result.empty


def test_historical_figure_or_empty_returns_placeholder_for_empty_data(
    callbacks_module,
):
    result = callbacks_module._historical_figure_or_empty(
        full_df = pd.DataFrame(),
        trading_pair = "BTCUSDT",
        date_range = [0, 1],
        required_columns = ("close_datetime", "close"),
        title = "Historical Line Chart",
        empty_message = "No data available",
        figure_builder = lambda data, trading_pair: go.Figure(),
    )

    assert isinstance(result, go.Figure)
    assert result.layout.title.text == "Historical Line Chart"
    assert result.layout.annotations[0].text == "No data available"


def test_historical_figure_or_empty_returns_placeholder_for_missing_columns(
    callbacks_module,
):
    data_without_close = pd.DataFrame(
        {
            "symbol": ["BTCUSDT"],
            "close_datetime": pd.to_datetime(["2026-05-19T10:00:00Z"], utc = True),
        }
    )

    result = callbacks_module._historical_figure_or_empty(
        full_df = data_without_close,
        trading_pair = "BTCUSDT",
        date_range = None,
        required_columns = ("close_datetime", "close"),
        title = "Historical Line Chart",
        empty_message = "No data available",
        figure_builder = lambda data, trading_pair: go.Figure(),
    )

    assert isinstance(result, go.Figure)
    assert result.layout.annotations[0].text == "Missing required data: close"


def test_register_callbacks_smoke(callbacks_module):
    app = Dash(__name__)
    callbacks_module.register_callbacks(app)

    callback_keys = set(app.callback_map.keys())

    assert "trading-pair-title.children" in callback_keys
    assert "historical-lineplot.figure" in callback_keys
    assert "historical-candleplot.figure" in callback_keys
    assert "historical-volumeplot.figure" in callback_keys
    assert "historical-volatilityplot.figure" in callback_keys
    assert any(
        "real-time.figure" in key and "ws-status.children" in key
        for key in callback_keys
    )
