import pandas as pd
import dash
import json
from dash.dependencies import Input, Output
from .plots.lineplot import create_lineplot
from .plots.candlestickplot import create_candlestickplot
from .plots.volumeplot import create_volumeplot
from .plots.volatilityplot import create_volatility_plot
from .layout.controls import create_range_selector
from .data_store import prepare_data
from .utils import filter_df

def register_callbacks(app):
    print("Pumpkin Registering callbacks...")
    
    # Get the full data initially
    full_df = prepare_data()

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
        # Log WebSocket connection status
        if not ws_message:
            return dash.no_update, dash.no_update, "WebSocket not connected", "WebSocket not connected"

        try:
            # Parse the data as JSON
            message = json.loads(ws_message["data"])
            if "error" in message:
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
            return dash.no_update, dash.no_update, f"Error: {str(e)}", f"Error: {str(e)}"


    @app.callback( 
        Output("historical-lineplot", "figure"),
        Input("trading-pair-dropdown", "value"),
        Input("line-slider", "value"),
        prevent_initial_call=True
    )
    def update_lineplot(trading_pair, date_range):
        data = filter_df(full_df, trading_pair, date_range)
        try:
            if data.empty:
                return dash.no_update
            
            # Ensure we have the required columns
            required_columns = ['close_datetime', 'close']
            missing_columns = [col for col in required_columns if col not in data.columns]
            if missing_columns:
                return dash.no_update
           
            fig = create_lineplot(data, trading_pair=trading_pair, show_emas=True)
            return fig

        except Exception as e:
            return dash.no_update

    @app.callback( 
        Output("historical-candleplot", "figure"),
        Input("trading-pair-dropdown", "value"),
        Input("candle-slider", "value"),
        prevent_initial_call=True
    )
    def update_candlestick(trading_pair, date_range):
        data = filter_df(full_df, trading_pair, date_range)
        try:
            if data.empty:
                return dash.no_update
            
            # Ensure we have the required columns
            required_columns = ['close_datetime', 'close', 'open', 'high', 'low']
            missing_columns = [col for col in required_columns if col not in data.columns]
            if missing_columns:
                return dash.no_update
           
            fig = create_candlestickplot(data, trading_pair=trading_pair)
            return fig

        except Exception as e:
            return dash.no_update


    @app.callback( 
        Output("historical-volumeplot", "figure"),
        Input("trading-pair-dropdown", "value"),
        Input("volume-slider", "value"),
        prevent_initial_call=True
    )
    def update_volume(trading_pair, date_range):
        data = filter_df(full_df, trading_pair, date_range)
        try:
            if data.empty:
                return dash.no_update
            
            # Ensure we have the required columns
            required_columns = ['close_datetime', 'volume']
            missing_columns = [col for col in required_columns if col not in data.columns]
            if missing_columns:
                return dash.no_update
           
            fig = create_volumeplot(data, trading_pair=trading_pair)
            return fig

        except Exception as e:
            return dash.no_update

    @app.callback(
        Output("historical-volatilityplot", "figure"),
        Input("atr-period-input", "value"),
        Input("volatility-slider", "value"),
        Input("data-init-trigger", "children"),
        prevent_initial_call=False
    )
    def update_volatility(atr_period, date_range, _):
        try:
            # Filter the data for both BTCUSDT and ETHUSDT
            trading_pairs = ["BTCUSDT", "ETHUSDT"]
            pair_data = {}
            
            for pair in trading_pairs:
                filtered_df = filter_df(full_df, pair, date_range)
                if not filtered_df.empty:
                    pair_data[pair] = filtered_df
            
            if not pair_data:
                return dash.no_update
            
            fig = create_volatility_plot(pair_data, period=atr_period)
            return fig

        except Exception as e:
            return dash.no_update

