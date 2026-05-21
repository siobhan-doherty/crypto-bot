from __future__ import annotations
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Tuple
from api_user.visualization.data_store import prepare_data
from api_user.visualization.layout.controls import create_range_selector
from api_user.visualization.plots.candlestickplot import create_candlestickplot
from api_user.visualization.plots.lineplot import create_lineplot
from api_user.visualization.plots.volatilityplot import create_volatility_plot
from api_user.visualization.plots.volumeplot import create_volumeplot
from api_user.visualization.utils import filter_df
from dash.dependencies import Input, Output
import json
import logging
import dash
import pandas as pd
import plotly.graph_objects as go

logger = logging.getLogger(__name__)
DISPLAY_TIMEZONE = "Europe/Berlin"
REALTIME_REQUIRED_COLUMNS = ("close_datetime",)
HISTORICAL_LINE_REQUIRED_COLUMNS = ("close_datetime", "close")
HISTORICAL_CANDLE_REQUIRED_COLUMNS = ("close_datetime", "open", "high", "low", "close")
HISTORICAL_VOLUME_REQUIRED_COLUMNS = ("close_datetime", "volume")
VOLATILITY_TRADING_PAIRS = ("BTCUSDT", "ETHUSDT")


def _empty_figure(title: str, message: str) -> go.Figure:
    """Create a plotly figure with a centered message and no axes."""
    figure = go.Figure()
    figure.update_layout(
        title=title,
        template="plotly_dark",
        xaxis={"visible": False},
        yaxis={"visible": False},
        annotations=[
            {
                "text": message,
                "xref": "paper",
                "yref": "paper",
                "x": 0.5,
                "y": 0.5,
                "showarrow": False,
                "font": {"size": 16},
            }
        ],
        margin={"l": 40, "r": 40, "t": 60, "b": 40},
    )
    return figure


def _missing_columns(
    dataframe: pd.DataFrame, required_columns: Sequence[str]
) -> list[str]:
    return [col for col in required_columns if col not in dataframe.columns]


def _coerce_datetime_column(
    dataframe: pd.DataFrame,
    column_name: str,
    timezone_name: str = DISPLAY_TIMEZONE,
) -> pd.DataFrame:
    if column_name not in dataframe.columns or dataframe.empty:
        return dataframe

    result = dataframe.copy()
    parsed = pd.to_datetime(result[column_name], utc=True, errors="coerce")
    result = result.loc[parsed.notna()].copy()
    if result.empty:
        return result

    result[column_name] = parsed.loc[parsed.notna()].dt.tz_convert(timezone_name)
    return result


def _first_available_numeric_column(dataframe: pd.DataFrame) -> Optional[str]:
    excluded_columns = {"timestamp", "close_time", "close_datetime"}
    numeric_cols = [
        col
        for col in dataframe.select_dtypes(include=["number"]).columns
        if col not in excluded_columns
    ]
    return numeric_cols[0] if numeric_cols else None


def _extract_ws_records(
    ws_message: Mapping[str, Any]
) -> Tuple[Optional[list[dict[str, Any]]], str]:
    raw_payload = ws_message.get("data")
    if raw_payload is None:
        return None, "WebSocket payload missing data field"

    try:
        payload = json.loads(raw_payload)
    except (TypeError, json.JSONDecodeError) as e:
        logger.warning("Failed to decode websocket payload: %s", e)
        return None, "Invalid WebSocket payload"

    if not isinstance(payload, dict):
        return None, "Unexpected WebSocket payload format"

    if "error" in payload:
        return None, f"WebSocket error: {payload['error']}"

    records = payload.get("data")
    if not isinstance(records, list):
        return None, "Invalid WebSocket data format"

    if not records:
        return None, "No realtime data received"

    return records, "WebSocket connected"


def _build_realtime_dataframe(
    records: Sequence[Mapping[str, Any]]
) -> Tuple[pd.DataFrame, Optional[str], Optional[str]]:
    df = pd.DataFrame(records)
    if df.empty:
        return df, None, "No realtime rows available"

    missing = _missing_columns(df, REALTIME_REQUIRED_COLUMNS)
    if missing:
        return df, None, f"Missing realtime columns: {', '.join(missing)}"

    df = _coerce_datetime_column(df, "close_datetime")
    if df.empty:
        return df, None, "Realtime timestamps could not be parsed"

    symbol = df.iloc[0].get("symbol")
    if not symbol:
        return df, None, "Realtime symbol missing"

    y_col = _first_available_numeric_column(df)
    if not y_col:
        return df, None, "No numeric realtime field available"

    df = df.sort_values("close_datetime").drop_duplicates(
        subset="close_datetime",
        keep="last",
    )
    return df, y_col, None


def _build_realtime_plot(df: pd.DataFrame, trading_pair: str, y_col: str) -> go.Figure:
    plot_df = df[["close_datetime", y_col]].copy()
    plot_df.columns = ["close_datetime", "close"]
    fig = create_lineplot(plot_df, trading_pair=trading_pair, show_emas=False)
    fig["layout"].update(create_range_selector(y_col))
    return fig


def _filtered_dataframe_or_empty(
    full_df: pd.DataFrame,
    trading_pair: str,
    date_range: Any,
) -> pd.DataFrame:
    try:
        filtered = filter_df(full_df, trading_pair, date_range)
    except Exception as e:
        logger.exception("Failed to filter dataframe for %s: %s", trading_pair, e)
        return pd.DataFrame()
    if filtered is None:
        return pd.DataFrame()
    return filtered


def _historical_figure_or_empty(
    *,
    full_df: pd.DataFrame,
    trading_pair: str,
    date_range: Any,
    required_columns: Sequence[str],
    title: str,
    empty_message: str,
    figure_builder: Any,
) -> go.Figure:
    data = _filtered_dataframe_or_empty(full_df, trading_pair, date_range)
    if data.empty:
        return _empty_figure(title, empty_message)

    missing = _missing_columns(data, required_columns)
    if missing:
        logger.warning(
            "Missing required columns for %s: %s",
            title,
            ", ".join(missing),
        )
        return _empty_figure(
            title,
            f"Missing required data: {', '.join(missing)}",
        )
    try:
        return figure_builder(data, trading_pair=trading_pair)
    except Exception as e:
        logger.exception("Failed to build %s figure: %s", title, e)
        return _empty_figure(title, "Unable to render chart")


def register_callbacks(app: dash.Dash) -> None:
    full_df = prepare_data()
    realtime_store: Dict[str, pd.DataFrame] = {}

    @app.callback(
        Output("trading-pair-title", "children"),
        Input("trading-pair-dropdown", "value"),
    )
    def update_trading_pair_title(trading_pair: Optional[str]) -> str:
        if not trading_pair:
            return "Real-time Price"
        return f"{trading_pair} Real-time Price"

    @app.callback(
        [Output("real-time", "figure"), Output("ws-status", "children")],
        [Input("ws", "message"), Input("trading-pair-dropdown", "value")],
        prevent_initial_call=True,
    )
    def update_real_time(
        ws_message: Optional[Mapping[str, Any]], trading_pair: Optional[str]
    ):
        if not ws_message:
            return dash.no_update, "WebSocket not connected"

        records, status = _extract_ws_records(ws_message)
        if records is None:
            return dash.no_update, status

        df, y_col, error = _build_realtime_dataframe(records)
        if error:
            return dash.no_update, error

        symbol = str(df.iloc[0]["symbol"])
        realtime_store[symbol] = df
        if not trading_pair:
            return dash.no_update, status

        selected_df = realtime_store.get(trading_pair)
        if selected_df is None or selected_df.empty or y_col is None:
            return dash.no_update, status

        try:
            fig = _build_realtime_plot(selected_df, trading_pair, y_col)
        except Exception as e:
            logger.exception("Realtime plot error for %s: %s", trading_pair, e)
            return dash.no_update, "Error creating realtime plot"

        return fig, status

    @app.callback(
        Output("historical-lineplot", "figure"),
        Input("trading-pair-dropdown", "value"),
        Input("line-slider", "value"),
    )
    def update_lineplot(trading_pair, date_range):
        return _historical_figure_or_empty(
            full_df=full_df,
            trading_pair=trading_pair,
            date_range=date_range,
            required_columns=HISTORICAL_LINE_REQUIRED_COLUMNS,
            title="No data available",
            empty_message="No historical data for the selected symbol and date range.",
            figure_builder=lambda df, trading_pair: create_lineplot(
                df, trading_pair=trading_pair, show_emas=True
            ),
        )

    @app.callback(
        Output("historical-candleplot", "figure"),
        Input("trading-pair-dropdown", "value"),
        Input("candle-slider", "value"),
    )
    def update_candlestick(trading_pair, date_range):
        return _historical_figure_or_empty(
            full_df=full_df,
            trading_pair=trading_pair,
            date_range=date_range,
            required_columns=HISTORICAL_CANDLE_REQUIRED_COLUMNS,
            title="No data available",
            empty_message="No historical data for the selected symbol and date range.",
            figure_builder=create_candlestickplot,
        )

    @app.callback(
        Output("historical-volumeplot", "figure"),
        Input("trading-pair-dropdown", "value"),
        Input("volume-slider", "value"),
    )
    def update_volume(trading_pair, date_range):
        return _historical_figure_or_empty(
            full_df=full_df,
            trading_pair=trading_pair,
            date_range=date_range,
            required_columns=HISTORICAL_VOLUME_REQUIRED_COLUMNS,
            title="No data available",
            empty_message="No historical data for the selected symbol and date range.",
            figure_builder=create_volumeplot,
        )

    @app.callback(
        Output("historical-volatilityplot", "figure"),
        Input("atr-period-input", "value"),
        Input("volatility-slider", "value"),
        Input("data-init-trigger", "children"),
    )
    def update_volatility(atr_period, date_range, _):
        # build volatility data for both trading pairs
        pair_data = {}
        for pair in VOLATILITY_TRADING_PAIRS:
            filtered = _filtered_dataframe_or_empty(full_df, pair, date_range)
            if not filtered.empty:
                pair_data[pair] = filtered
        if not pair_data:
            return _empty_figure(
                "No data available", "No volatility data for the selected date range."
            )
        try:
            fig = create_volatility_plot(pair_data, period=atr_period)
        except Exception as e:
            logger.exception("Volatility plot error: %s", e)
            return _empty_figure(
                "Nothing to display", "Unable to render the volatility chart."
            )
        if not fig or not fig.get("data"):
            return _empty_figure(
                "Nothing to display", "Unable to render the volatility chart."
            )
        return fig
