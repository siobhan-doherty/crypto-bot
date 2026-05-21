from __future__ import annotations
from api_user.visualization.utils import filter_df
from api_user.visualization import data_store
from api_user.visualization.data_store import prepare_data
from pathlib import Path
import sys
import pandas as pd
import pandas.testing as pdt

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))


def test_prepare_data_returns_empty_dataframe_when_fetch_is_empty(monkeypatch):
    monkeypatch.setattr(data_store, "fetch_historical_data", lambda: pd.DataFrame())
    result = prepare_data()
    assert isinstance(result, pd.DataFrame)
    assert result.empty


def test_prepare_data_normalizes_and_sorts(monkeypatch):
    df = pd.DataFrame(
        {
            "symbol": ["BTCUSDT", "BTCUSDT"],
            "open_datetime": ["2026-05-19T10:05:00+00:00", "2026-05-19T10:00:00+00:00"],
            "close_datetime": [
                "2026-05-19T10:19:59+00:00",
                "2026-05-19T10:14:59+00:00",
            ],
            "close": [2.0, 1.0],
        }
    )
    monkeypatch.setattr(data_store, "fetch_historical_data", lambda: df)
    result = prepare_data()
    assert list(result["close"]) == [1.0, 2.0]
    assert str(result["open_datetime"].dtype).startswith("datetime64[ns, UTC]")


def test_filter_df_returns_empty_for_none():
    result = filter_df(None)
    assert isinstance(result, pd.DataFrame)
    assert result.empty


def test_filter_df_filters_symbol_and_date_range():
    df = pd.DataFrame(
        {
            "symbol": ["BTCUSDT", "ETHUSDT", "BTCUSDT"],
            "open_datetime": pd.to_datetime(
                [
                    "2026-05-19T10:00:00Z",
                    "2026-05-19T10:01:00Z",
                    "2026-05-19T10:02:00Z",
                ],
                utc=True,
            ),
            "close": [1.0, 2.0, 3.0],
        }
    )

    start_ts = int(pd.Timestamp("2026-05-19T10:00:00Z").timestamp())
    end_ts = int(pd.Timestamp("2026-05-19T10:02:00Z").timestamp())

    result = filter_df(df, symbol="BTCUSDT", date_range=[start_ts, end_ts])

    expected = pd.DataFrame(
        {
            "symbol": ["BTCUSDT", "BTCUSDT"],
            "open_datetime": pd.to_datetime(
                ["2026-05-19T10:00:00Z", "2026-05-19T10:02:00Z"], utc=True
            ),
            "close": [1.0, 3.0],
        }
    ).reset_index(drop=True)

    pdt.assert_frame_equal(result[expected.columns].reset_index(drop=True), expected)
