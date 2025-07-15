import pandas as pd
from .fetch_data import fetch_historical_data


def prepare_data():
    """
    Shared function to prepare data for all historical plots

    Returns:
        DataFrame: Prepared data with datetime columns and sorted by datetime
    """
    full_df = fetch_historical_data()

    if full_df.empty:
        return None

    # Convert timestamp columns to datetime
    if "open_datetime" in full_df.columns:
        full_df["open_datetime"] = pd.to_datetime(full_df["open_datetime"], utc=True)
    if "close_datetime" in full_df.columns:
        full_df["close_datetime"] = pd.to_datetime(full_df["close_datetime"], utc=True)

    # Sort by datetime
    time_col = (
        "open_datetime" if "open_datetime" in full_df.columns else "close_datetime"
    )
    full_df = full_df.sort_values(time_col)

    return full_df
