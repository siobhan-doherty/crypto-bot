import pandas as pd


def filter_df(df, symbol="BTCUSDT", date_range=None):
    if symbol:
        filtered_df = df[df["symbol"] == symbol]
    else:
        filtered_df = df
    if filtered_df.empty:
        print("Utils: No data for symbol: ", symbol)

    if "open_datetime" in filtered_df.columns:
        filtered_df["open_datetime"] = pd.to_datetime(
            filtered_df["open_datetime"], utc=True
        )
    if "close_datetime" in filtered_df.columns:
        filtered_df["close_datetime"] = pd.to_datetime(
            filtered_df["close_datetime"], utc=True
        )

    time_col = (
        "open_datetime" if "open_datetime" in filtered_df.columns else "close_datetime"
    )
    if time_col not in df.columns:
        print("Utils: No time column found")

    filtered_df = filtered_df.sort_values(time_col)

    # Apply date range filter if provided
    if date_range and len(date_range) == 2:
        start_ts, end_ts = date_range
        start_date = pd.to_datetime(start_ts, unit="s", utc=True)
        end_date = pd.to_datetime(end_ts, unit="s", utc=True)

        # Filter the dataframe based on the selected date range
        mask = (filtered_df[time_col] >= start_date) & (
            filtered_df[time_col] <= end_date
        )
        filtered_df = filtered_df.loc[mask]
    print("Utils: Filtered data for symbol: ", symbol)
    print(filtered_df.head())
    return filtered_df
