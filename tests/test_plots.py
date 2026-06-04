import pandas as pd

from api_user.visualization.plots.candlestickplot import create_candlestickplot
from api_user.visualization.plots.lineplot import create_lineplot
from api_user.visualization.plots.volatilityplot import (
    calculate_atr,
    create_volatility_plot,
)
from api_user.visualization.plots.volumeplot import create_volumeplot


# helper sample DataFrame
def sample_df():
    return pd.DataFrame(
        {
            "close_datetime": pd.to_datetime(
                ["2026-06-04T10:00:00Z", "2026-06-04T10:15:00Z"]
            ),
            "open": [50000.0, 50200.0],
            "high": [50500.0, 50700.0],
            "low": [49800.0, 50000.0],
            "close": [50200.0, 50500.0],
            "volume": [100.0, 150.0],
        }
    )


# candlestick plot
def test_candlestickplot_returns_dict():
    df = sample_df()
    fig = create_candlestickplot(df, "BTCUSDT")
    assert isinstance(fig, dict)
    assert "data" in fig
    assert len(fig["data"]) > 0


def test_candlestickplot_missing_columns_returns_empty():
    df = pd.DataFrame({"not_ohlc": [1, 2]})
    fig = create_candlestickplot(df, "BTCUSDT")
    assert fig["data"] == []
    assert fig["layout"] == {}


# line plot
def test_lineplot_returns_dict():
    df = sample_df()
    fig = create_lineplot(df, "BTCUSDT", show_emas=True)
    assert isinstance(fig, dict)
    assert any(trace["name"] == "Price" for trace in fig["data"])


def test_lineplot_missing_close():
    df = pd.DataFrame({"close_datetime": ["2026-06-04T10:00:00Z"]})
    fig = create_lineplot(df, "BTCUSDT")
    assert fig["data"] == []


# volume plot
def test_volumeplot_returns_dict():
    df = sample_df()
    fig = create_volumeplot(df, "BTCUSDT")
    assert isinstance(fig, dict)
    assert "data" in fig


def test_volumeplot_empty_df():
    fig = create_volumeplot(pd.DataFrame(), "BTCUSDT")
    assert fig["data"] == []
    assert fig["layout"] == {}


# volatility plot + ATR
def test_calculate_atr():
    df = sample_df()
    atr = calculate_atr(df, period=2)
    assert len(atr) == 2
    assert atr.iloc[-1] > 0  # ATR should be positive


def test_create_volatility_plot():
    df_dict = {"BTCUSDT": sample_df(), "ETHUSDT": sample_df().copy()}
    fig = create_volatility_plot(df_dict, period=14)
    assert isinstance(fig, dict)
    assert "data" in fig


def test_volatility_plot_missing_pairs():
    df_dict = {}
    fig = create_volatility_plot(df_dict)
    assert fig["data"] == []
    assert fig["layout"] == {}
