import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from api_user.config import settings
from api_user.visualization.schemas import HistoricalData, KlineData

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL.upper()))
logger = logging.getLogger(__name__)

API_BASE_URL = settings.API_BASE_URL
DEFAULT_INTERVAL = "15m"


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(requests.RequestException),
)
def _call_api(endpoint: str, params: Optional[dict] = None) -> Dict[str, Any]:
    """ "Make a GET request to the FastAPI endpoint with retries."""
    url = f"{API_BASE_URL}/{endpoint.lstrip('/')}"
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()  # type: ignore[no-any-return]
    except requests.RequestException as e:
        logger.error(f"API call failed: {e}")
        raise


def get_available_date_range() -> Tuple[datetime, datetime]:
    """
    Fetch the available date range from the FastAPI endpoint.
    Returns (min_date, max_date) as UTC datetime objects.
    """
    try:
        data = _call_api("market/range")
        min_date = datetime.fromisoformat(data["min_date"]).replace(tzinfo=timezone.utc)
        max_date = datetime.fromisoformat(data["max_date"]).replace(tzinfo=timezone.utc)
        logger.info(f"Date range fetched: {min_date} to {max_date}")
        return min_date, max_date

    except Exception as e:
        logger.error(f"Error fetching date range from API: {e}")
        # fallback to last 7 days
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=7)
        return start_date, end_date


def fetch_historical_data(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> pd.DataFrame:
    """
    Fetch historical OHLCV data from the FastAPI endpoint.
    Returns a pandas DataFrame with columns: open_datetime, close, volume, etc.
    """
    params = {"interval": DEFAULT_INTERVAL, "limit": 10000}
    if start_time:
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)
        params["start_time"] = int(start_time.timestamp() * 1000)
    if end_time:
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=timezone.utc)
        params["end_time"] = int(end_time.timestamp() * 1000)

    try:
        data = _call_api("market/ohlcv", params=params)
        if not data:
            logger.warning("No data returned from API")
            return pd.DataFrame()

        df = pd.DataFrame(data)
        # convert datetime columns
        for col in ["open_datetime", "close_datetime"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], utc=True)
        # ensure numeric columns
        numeric_cols = [
            "open",
            "high",
            "low",
            "close",
            "volume",
            "quote_asset_volume",
            "number_of_trades",
            "taker_buy_base_asset_volume",
            "taker_buy_quote_asset_volume",
        ]

        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        # sort by time
        if "open_time" in df.columns:
            df = df.sort_values("open_time")
        elif "open_datetime" in df.columns:
            df = df.sort_values("open_datetime")
        logger.info(f"Fetched {len(df)} historical records")
        return df

    except Exception as e:
        print(f"Unexpected error: {e}")
        return pd.DataFrame()


def get_historical_data(symbol: str) -> HistoricalData:
    response = requests.get(f"{API_BASE_URL}/historical/{symbol}", timeout=30)
    response.raise_for_status()
    return HistoricalData.model_validate_json(response.text)


def get_streaming_data(symbol: str) -> List[KlineData]:
    response = requests.get(f"{API_BASE_URL}/streaming/{symbol}", timeout=30)
    response.raise_for_status()
    return [KlineData.model_validate(item) for item in response.json()]
