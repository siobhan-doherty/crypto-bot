from __future__ import annotations

import logging

import pandas as pd

from .fetch_data import fetch_historical_data

logger = logging.getLogger(__name__)

_OPEN_DATETIME_COL = "open_datetime"
_CLOSE_DATETIME_COL = "close_datetime"
_TIME_COLUMNS = (_OPEN_DATETIME_COL, _CLOSE_DATETIME_COL)


def _normalize_datetime_columns(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    for column in _TIME_COLUMNS:
        if column in normalized.columns:
            normalized[column] = pd.to_datetime(
                normalized[column],
                utc = True,
                errors = "coerce",
            )
    return normalized


def _resolve_time_column(df: pd.DataFrame) -> str | None:
    for column in _TIME_COLUMNS:
        if column in df.columns:
            return column
    return None


def prepare_data() -> pd.DataFrame:
    try:
        df = fetch_historical_data(symbol = "BTCUSDT")
    except Exception:
        logger.exception("Failed to fetch historical data for visualization.")
        return pd.DataFrame()

    if df is None or df.empty:
        logger.warning("Historical dataset is empty.")
        return pd.DataFrame()

    normalized = _normalize_datetime_columns(df)
    time_column = _resolve_time_column(normalized)

    if time_column is None:
        logger.warning(
            "Historical dataset does not contain a supported time column. Columns=%s",
            list(normalized.columns),
        )
        return normalized.reset_index(drop = True)

    normalized = normalized.sort_values(time_column, kind = "stable").reset_index(
        drop = True
    )

    logger.info(
        "Prepared historical dataset with %d rows using time column '%s'.",
        len(normalized),
        time_column,
    )
    return normalized
