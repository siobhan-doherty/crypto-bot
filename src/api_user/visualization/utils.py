from __future__ import annotations
from typing import Sequence
import pandas as pd
import logging

logger = logging.getLogger(__name__)

_SYMBOL_COL = "symbol"
_OPEN_DATETIME_COL = "open_datetime"
_CLOSE_DATETIME_COL = "close_datetime"
_TIME_COLUMNS = (_OPEN_DATETIME_COL, _CLOSE_DATETIME_COL)


def _normalize_datetime_columns(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()

    for column in _TIME_COLUMNS:
        if column in normalized.columns:
            normalized[column] = pd.to_datetime(
                normalized[column],
                utc=True,
                errors="coerce",
            )
    return normalized


def _resolve_time_column(df: pd.DataFrame) -> str | None:
    for column in _TIME_COLUMNS:
        if column in df.columns:
            return column
    return None


def _apply_symbol_filter(df: pd.DataFrame, symbol: str | None) -> pd.DataFrame:
    if not symbol:
        return df.copy()

    if _SYMBOL_COL not in df.columns:
        logger.warning(
            "Cannot filter by symbol '%s': missing '%s' column. Columns=%s",
            symbol,
            _SYMBOL_COL,
            list(df.columns),
        )
        return pd.DataFrame(columns=df.columns)

    return df.loc[df[_SYMBOL_COL] == symbol].copy()


def _apply_date_range_filter(
    df: pd.DataFrame,
    time_column: str,
    date_range: Sequence[int] | None,
) -> pd.DataFrame:
    if not date_range or len(date_range) != 2:
        return df

    start_ts, end_ts = date_range
    start_date = pd.to_datetime(start_ts, unit="s", utc=True, errors="coerce")
    end_date = pd.to_datetime(end_ts, unit="s", utc=True, errors="coerce")

    if pd.isna(start_date) or pd.isna(end_date):
        logger.warning("Invalid date range received: %s", date_range)
        return df

    return df.loc[
        (df[time_column] >= start_date) & (df[time_column] <= end_date)
    ].copy()


def filter_df(
    df: pd.DataFrame | None,
    symbol: str = "BTCUSDT",
    date_range: Sequence[int] | None = None,
) -> pd.DataFrame:
    if df is None or df.empty:
        logging.warning("filter_df received an empty dataset. symbol=%s", symbol)
        return pd.DataFrame()

    normalized = _normalize_datetime_columns(df)
    filtered = _apply_symbol_filter(normalized, symbol)

    if filtered.empty:
        logger.info("No rows available for symbol=%", symbol)
        return filtered.reset_index(drop=True)

    time_column = _resolve_time_column(filtered)
    if time_column is None:
        logger.warning(
            "No supported time column found after filtering. Columns=%s",
            list(filtered.columns),
        )
        return filtered.reset_index(drop=True)

    filtered = _apply_date_range_filter(filtered, time_column, date_range)
    filtered = filtered.sort_values(time_column, kind="stable").reset_index(drop=True)

    logger.debug(
        "Filtered dataset prepared. symbol=%s rows=%d time_column=%s",
        symbol,
        len(filtered),
        time_column,
    )
    return filtered
