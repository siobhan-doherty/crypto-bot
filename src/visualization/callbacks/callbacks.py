import pandas as pd
from dash.dependencies import Input, Output


def register_callbacks(app, fetch_historical_data):
    @app.callback(
        Output('close-price-graph', 'figure'),
        Input('lineplot-time-slider', 'value')
    )
    def update_lineplot(date_range):
        df = fetch_historical_data()
        if df.empty:
            return {'data': [], 'layout': {}}
            
        # Convert close_time to datetime if it's not already
        if not pd.api.types.is_datetime64_any_dtype(df['close_time']):
            df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
        
        df = df.sort_values('close_time')
        
        if date_range:
            start_ts, end_ts = date_range
            start_date = pd.to_datetime(start_ts, unit='s')
            end_date = pd.to_datetime(end_ts, unit='s')
            df = df[(df['close_time'] >= start_date) & (df['close_time'] <= end_date)]
        
        return {    
            'data': [{
                'x': df['close_time'],
                'y': df['close'],
                'type': 'line',
                'name': 'Close Price'
            }],
            'layout': {
                'title': 'BITCUSDT Close Price',
                'xaxis': {
                    'title': 'Time',
                    'type': 'date',
                    'rangeselector': {
                        'buttons': [
                            {'count': 1, 'label': '1d', 'step': 'day', 'stepmode': 'backward'},
                            {'count': 7, 'label': '1w', 'step': 'day', 'stepmode': 'backward'},
                            {'step': 'all'}
                        ]
                    }
                },
                'yaxis': {'title': 'Close Price (USDT)'},
                'margin': {'l': 60, 'r': 30, 't': 80, 'b': 120},
                'height': 600,
                'showlegend': False
            }
        }

    @app.callback(
        Output('candlestick-graph', 'figure'),
        Input('candlestick-time-slider', 'value')
    )
    def update_candlestick(date_range):
        df = fetch_historical_data()
        if df.empty:
            return {'data': [], 'layout': {}}
            
        # Convert close_time to datetime if it's not already
        if not pd.api.types.is_datetime64_any_dtype(df['close_time']):
            df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
        
        df = df.sort_values('close_time')
        
        if date_range:
            start_ts, end_ts = date_range
            start_date = pd.to_datetime(start_ts, unit='s')
            end_date = pd.to_datetime(end_ts, unit='s')
            df = df[(df['close_time'] >= start_date) & (df['close_time'] <= end_date)]
        
        return {
            'data': [{
                'x': df['close_time'],
                'open': df['open'],
                'high': df['high'],
                'low': df['low'],
                'close': df['close'],
                'type': 'candlestick',
                'name': 'Candlestick'
            }],
            'layout': {
                'title': 'BITCUSDT Candlestick Chart',
                'xaxis': {
                    'title': 'Time',
                    'type': 'date',
                    'rangeslider': {'visible': False}
                },
                'yaxis': {'title': 'Price (USDT)'},
                'margin': {'l': 60, 'r': 30, 't': 80, 'b': 80},
                'height': 600,
                'showlegend': False
            }
        }
