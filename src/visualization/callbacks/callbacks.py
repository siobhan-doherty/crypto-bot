import pandas as pd
from dash.dependencies import Input, Output
from plots.lineplot import create_lineplot
from plots.candlestickplot import create_candlestickplot
from plots.volumeplot import create_volumeplot


def register_callbacks(app, fetch_historical_data):
    @app.callback(
        Output('close-price-graph', 'figure'),
        Input('lineplot-time-slider', 'value')
    )
    def update_lineplot(date_range):
        df = fetch_historical_data()
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
        
        return create_lineplot(df)

    @app.callback(
        Output('candlestick-graph', 'figure'),
        Input('candlestick-time-slider', 'value')
    )
    def update_candlestick(date_range):
        df = fetch_historical_data()
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
        
        return create_candlestickplot(df)

    @app.callback(
        Output('volume-graph', 'figure'),
        Input('volume-time-slider', 'value')
    )
    def update_volume(date_range):
        df = fetch_historical_data()
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
        
        return create_volumeplot(df)
