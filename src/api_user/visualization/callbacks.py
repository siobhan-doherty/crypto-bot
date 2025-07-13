import pandas as pd
import dash
import json
from dash.dependencies import Input, Output
from .plots.lineplot import create_lineplot
from .plots.candlestickplot import create_candlestickplot
from .plots.volumeplot import create_volumeplot
from .plots.volatilityplot import create_volatility_plot
from .layout.controls import create_range_selector


def register_callbacks(app, fetch_historical_data):
    print("Registering callbacks...")
    print(f"Available components: {app.layout.children}")
    
    @app.callback(
        [Output("real-time", "figure"),
         Output("ws-data-store", "data"),
         Output("ws-status", "children"),
         Output("data-status", "children")],
        [Input("ws", "message"),
         Input("ws-data-store", "data")],
        prevent_initial_call=True
    )
    def update_real_time(ws_message, stored_data):
        print(f"Callback triggered with ws_message: {ws_message}")
        
        # Log WebSocket connection status
        if not ws_message:
            print("WebSocket message is None")
            return dash.no_update, dash.no_update, "WebSocket not connected", "WebSocket not connected"

        try:
            # Parse the data as JSON
            message = json.loads(ws_message["data"])
            if "error" in message:
                print(f"Error in message: {message['error']}")
                return dash.no_update

            if not isinstance(message.get("data"), list):
                return dash.no_update

            data = message["data"]
            if not data:
                return dash.no_update

            df = pd.DataFrame(data)

            # Find the first numeric column that's not a timestamp
            numeric_cols = [col for col in df.select_dtypes(include=['number']).columns 
                          if col not in ['timestamp', 'close_time']]

            if not numeric_cols:
                return dash.no_update

            y_col = numeric_cols[0]

            plot_df = df[['close_time', y_col]].copy()
            plot_df.columns = ['close_datetime', 'close']  # Rename to match expected column name

            fig = create_lineplot(plot_df, show_emas=False)
            fig['layout'].update(create_range_selector(y_col))
            # Update status
            ws_status = "WebSocket connected"
            data_status = f"Received {len(data)} data points"

            return fig, plot_df.to_dict('records'), ws_status, data_status

        except Exception as e:
            print(f"Error in update_real_time: {str(e)}")
            return dash.no_update, dash.no_update, f"Error: {str(e)}", f"Error: {str(e)}"


    #@app.callback(
    #    Output("close-price-graph", "figure"),
    #    Input("trading-pair-dropdown", "value"),
    #    Input("lineplot-time-slider", "value"),
    #    prevent_initial_call=True,
    #)
    def update_lineplot(trading_pair, date_range):
        trading_pair = trading_pair or "BTCUSDT"
        df = fetch_historical_data(trading_pair)
        if df.empty:
            return {"data": [], "layout": {}}

        # Ensure datetime columns are in the correct format
        if "open_datetime" in df.columns:
            df["open_datetime"] = pd.to_datetime(df["open_datetime"], utc=True)
        if "close_datetime" in df.columns:
            df["close_datetime"] = pd.to_datetime(df["close_datetime"], utc=True)

        time_col = (
            "open_datetime" if "open_datetime" in df.columns else "close_datetime"
        )
        if time_col not in df.columns:
            return {"data": [], "layout": {}}

        df = df.sort_values(time_col)

        # Apply date range filter if provided
        if date_range and len(date_range) == 2:
            start_ts, end_ts = date_range
            start_date = pd.to_datetime(start_ts, unit="s", utc=True)
            end_date = pd.to_datetime(end_ts, unit="s", utc=True)

            # Filter the dataframe based on the selected date range
            mask = (df[time_col] >= start_date) & (df[time_col] <= end_date)
            df = df.loc[mask]

        # Create the line plot
        return create_lineplot(df, trading_pair)

    # Register other callbacks but keep them simple for now
    #@app.callback(
    #    Output("candlestick-graph", "figure"),
    #    Input("candlestick-time-slider", "value"),
    #    Input("trading-pair-dropdown", "value"),
    #)
    def update_candlestick(date_range, trading_pair):
        trading_pair = trading_pair or "BTCUSDT"
        df = fetch_historical_data(trading_pair)
        if df.empty:
            return {"data": [], "layout": {}}

        if not pd.api.types.is_datetime64_any_dtype(df["close_datetime"]):
            df["close_datetime"] = pd.to_datetime(
                df["close_datetime"], unit="ms", utc=True
            )

        df = df.sort_values("close_datetime")

        if date_range:
            start_ts, end_ts = date_range
            start_date = pd.to_datetime(start_ts, unit="s", utc=True)
            end_date = pd.to_datetime(end_ts, unit="s", utc=True)
            df = df[
                (df["close_datetime"] >= start_date)
                & (df["close_datetime"] <= end_date)
            ]

            return create_candlestickplot(df, trading_pair)
    #@app.callback(
    #    Output("volume-graph", "figure"),
    #    Input("volume-time-slider", "value"),
    #    Input("trading-pair-dropdown", "value"),
    #)
    def update_volume(date_range, trading_pair):
        trading_pair = trading_pair or "BTCUSDT"
        df = fetch_historical_data(trading_pair)
        if df.empty:
            return {"data": [], "layout": {}}

        if not pd.api.types.is_datetime64_any_dtype(df["close_datetime"]):
            df["close_datetime"] = pd.to_datetime(
                df["close_datetime"], unit="ms", utc=True
            )

        df = df.sort_values("close_datetime")

        if date_range:
            start_ts, end_ts = date_range
            start_date = pd.to_datetime(start_ts, unit="s", utc=True)
            end_date = pd.to_datetime(end_ts, unit="s", utc=True)
            df = df[
                (df["close_datetime"] >= start_date)
                & (df["close_datetime"] <= end_date)
            ]

            return create_volumeplot(df, trading_pair)

    #@app.callback(
    #    Output("volatility-graph", "figure"),
    #    Input("volatility-time-slider", "value"),
    #    Input("atr-period-input", "value"),
    #)
    def update_volatility(date_range, atr_period):
        atr_period = atr_period or 14

        selected_pairs = ["BTCUSDT", "ETHUSDT"]
        data = {}

        # Fetch data for both trading pairs
        for pair in selected_pairs:
            df = fetch_historical_data(pair)
            if not df.empty:
                if not pd.api.types.is_datetime64_any_dtype(df["close_datetime"]):
                    df["close_datetime"] = pd.to_datetime(
                        df["close_datetime"], unit="ms", utc=True
                    )

                df = df.sort_values("close_datetime")

                # Apply date range filter if provided
                if date_range:
                    start_ts, end_ts = date_range
                    start_date = pd.to_datetime(start_ts, unit="s", utc=True)
                    end_date = pd.to_datetime(end_ts, unit="s", utc=True)
                    df = df[
                        (df["close_datetime"] >= start_date)
                        & (df["close_datetime"] <= end_date)
                    ]

                data[pair] = df

        if not data:
            return {"data": [], "layout": {}}

        return create_volatility_plot(data, atr_period)
