import pandas as pd
from dash.dependencies import Input, Output
from plots.lineplot import create_lineplot
from plots.candlestickplot import create_candlestickplot
from plots.volumeplot import create_volumeplot
from plots.volatilityplot import create_volatility_plot


def register_callbacks(app, fetch_historical_data):
    @app.callback(
        Output('close-price-graph', 'figure'),
        Input('lineplot-time-slider', 'value'),
        Input('trading-pair-dropdown', 'value')
    )
    def update_lineplot(date_range, trading_pair):
        trading_pair = trading_pair or 'BTCUSDT'
        df = fetch_historical_data(trading_pair)
        if df.empty:
            return {'data': [], 'layout': {}}
            
        if not pd.api.types.is_datetime64_any_dtype(df['close_time']):
            df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
        
        df = df.sort_values('close_time')
        
        if date_range:
            start_ts, end_ts = date_range
            start_date = pd.to_datetime(start_ts, unit='s')
            end_date = pd.to_datetime(end_ts, unit='s')
            df = df[(df['close_time'] >= start_date) & (df['close_time'] <= end_date)]
        
        return create_lineplot(df, trading_pair)

    @app.callback(
        Output('candlestick-graph', 'figure'),
        Input('candlestick-time-slider', 'value'),
        Input('trading-pair-dropdown', 'value')
    )
    def update_candlestick(date_range, trading_pair):
        trading_pair = trading_pair or 'BTCUSDT'
        df = fetch_historical_data(trading_pair)
        if df.empty:
            return {'data': [], 'layout': {}}
            
        if not pd.api.types.is_datetime64_any_dtype(df['close_time']):
            df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
        
        df = df.sort_values('close_time')
        
        if date_range:
            start_ts, end_ts = date_range
            start_date = pd.to_datetime(start_ts, unit='s')
            end_date = pd.to_datetime(end_ts, unit='s')
            df = df[(df['close_time'] >= start_date) & (df['close_time'] <= end_date)]
        
        return create_candlestickplot(df, trading_pair) 

    @app.callback(
        Output('volume-graph', 'figure'),
        Input('volume-time-slider', 'value'),
        Input('trading-pair-dropdown', 'value')
    )
    def update_volume(date_range, trading_pair):
        trading_pair = trading_pair or 'BTCUSDT'
        df = fetch_historical_data(trading_pair)
        if df.empty:
            return {'data': [], 'layout': {}}
            
        if not pd.api.types.is_datetime64_any_dtype(df['close_time']):
            df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
        
        df = df.sort_values('close_time')
        
        if date_range:
            start_ts, end_ts = date_range
            start_date = pd.to_datetime(start_ts, unit='s')
            end_date = pd.to_datetime(end_ts, unit='s')
            df = df[(df['close_time'] >= start_date) & (df['close_time'] <= end_date)]
        
        return create_volumeplot(df, trading_pair)

    @app.callback(
        Output('volatility-graph', 'figure'),
        Input('volatility-time-slider', 'value'),
        Input('atr-period-input', 'value')
    )
    def update_volatility(date_range, atr_period):
        atr_period = atr_period or 14
        
        selected_pairs = ['BTCUSDT', 'ETHUSDT']
        data = {}
        
        # Fetch data for both trading pairs
        for pair in selected_pairs:
            df = fetch_historical_data(pair)
            if not df.empty:
                if not pd.api.types.is_datetime64_any_dtype(df['close_time']):
                    df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
                
                df = df.sort_values('close_time')
                
                # Apply date range filter if provided
                if date_range:
                    start_ts, end_ts = date_range
                    start_date = pd.to_datetime(start_ts, unit='s')
                    end_date = pd.to_datetime(end_ts, unit='s')
                    df = df[(df['close_time'] >= start_date) & (df['close_time'] <= end_date)]
                
                data[pair] = df
        
        if not data:
            return {'data': [], 'layout': {}}
            
        return create_volatility_plot(data, atr_period)
