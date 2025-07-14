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
    full_df = prepare_data()

    @app.callback(
        Output("trading-pair-title", "children"),
        Input("trading-pair-dropdown", "value")
    )
    def update_trading_pair_title(trading_pair):
        return f"{trading_pair} Real-time Price"

    @app.callback(
        [Output("real-time", "figure"),
         Output("ws-status", "children")],
        [Input("ws", "message"),
         Input("trading-pair-dropdown", "value")],
        prevent_initial_call=True
    )
    def update_real_time(ws_message, trading_pair):
        if 'stored_data' not in update_real_time.__dict__:
            update_real_time.stored_data = {}

        if not ws_message:
            return dash.no_update, "WebSocket not connected"

        try:
            message = json.loads(ws_message["data"])

            if "error" in message:
                return dash.no_update, "WebSocket error: " + str(message['error'])

            if not isinstance(message.get("data"), list):
                return dash.no_update, "Invalid data format"

            data = message["data"]
            if not data:
                return dash.no_update, "No data received"

            df = pd.DataFrame(data)
            if not df.empty:
                df['close_datetime'] = pd.to_datetime(df['close_datetime']).dt.tz_convert('Europe/Berlin')
            

            symbol = df.iloc[0]['symbol'] if not df.empty else None
            if not symbol:
                return dash.no_update, "No symbol found"
            numeric_cols = [col for col in df.select_dtypes(include=['number']).columns 
                          if col not in ['timestamp', 'close_time', 'close_datetime']]
            if not numeric_cols:
                return dash.no_update, "No numeric data"
            y_col = numeric_cols[0]

            update_real_time.stored_data[symbol] = df.to_dict('records')

            try:
                if not isinstance(update_real_time.stored_data, dict):
                    return dash.no_update, "Invalid data structure"

                if trading_pair in update_real_time.stored_data:
                    df = pd.DataFrame(update_real_time.stored_data[trading_pair])
                    if not df.empty:
                        plot_df = df[['close_datetime', y_col]].copy()
                        plot_df.columns = ['close_datetime', 'close']
                        
                        plot_df = plot_df.sort_values('close_datetime')
                        plot_df = plot_df.drop_duplicates(subset='close_datetime', keep='last')

                        try:
                            fig = create_lineplot(plot_df, trading_pair=trading_pair, show_emas=False)
                            fig['layout'].update(create_range_selector(y_col))
                            ws_status = "WebSocket connected"
                            return fig, ws_status
                        except Exception as e:
                            return dash.no_update, "Error creating plot"
                    else:
                        return dash.no_update, "WebSocket connected"
                else:
                    return dash.no_update, "WebSocket connected"
            except Exception as e:
                return dash.no_update, "Error creating plot"
        except Exception as e:
            return dash.no_update, "Error: " + str(e)

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

