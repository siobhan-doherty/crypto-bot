def create_candlestickplot(df):
    if df.empty:
        return {'data': [], 'layout': {}}
        
    df = df.sort_values('close_time')
    
    return {
        'data': [{
            'x': df['close_time'],
            'open': df['open'],
            'high': df['high'],
            'low': df['low'],
            'close': df['close'],
            'type': 'candlestick',
            'name': 'Close Price'
        }],
        'layout': {
            'title': 'BITCUSDT Close Price',
            'xaxis': {
                'title': 'Time',
                'type': 'date'
            },
            'yaxis': {'title': 'Close Price (USDT)'},
            'margin': {'l': 60, 'r': 30, 't': 80, 'b': 100},
            'height': 600
        }
    }
