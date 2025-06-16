def create_candlestickplot(df):
    if df.empty:
        return {'data': [], 'layout': {}}
        
    df = df.sort_values('close_time')
    
    # Define colors for increasing and decreasing candlesticks
    increasing_color = '#00bc8c'  # Green for increasing
    decreasing_color = '#e74c3c'  # Red for decreasing
    
    return {
        'data': [{
            'x': df['close_time'],
            'open': df['open'],
            'high': df['high'],
            'low': df['low'],
            'close': df['close'],
            'type': 'candlestick',
            'name': 'Price',
            'increasing': {
                'line': {'color': increasing_color},
                'fillcolor': increasing_color
            },
            'decreasing': {
                'line': {'color': decreasing_color},
                'fillcolor': decreasing_color
            },
            'line': {'width': 1},
            'whiskerwidth': 0.8
        }],
        'layout': {
            'title': {'text': 'BITCUSDT Candlestick Chart', 'font': {'color': '#f8f9fa'}},
            'xaxis': {
                'title': 'Time',
                'titlefont': {'color': '#f8f9fa'},
                'tickfont': {'color': '#f8f9fa'},
                'type': 'date',
                'gridcolor': 'rgba(255, 255, 255, 0.1)',
                'linecolor': 'rgba(255, 255, 255, 0.1)',
                'zerolinecolor': 'rgba(255, 255, 255, 0.1)'
            },
            'yaxis': {
                'title': 'Price (USDT)',
                'titlefont': {'color': '#f8f9fa'},
                'tickfont': {'color': '#f8f9fa'},
                'gridcolor': 'rgba(255, 255, 255, 0.1)',
                'linecolor': 'rgba(255, 255, 255, 0.1)',
                'zerolinecolor': 'rgba(255, 255, 255, 0.1)'
            },
            'margin': {'l': 60, 'r': 30, 't': 80, 'b': 100},
            'height': 600,
            'plot_bgcolor': '#303030',
            'paper_bgcolor': '#222',
            'font': {'color': '#f8f9fa'},
            'hovermode': 'x unified',
            'hoverlabel': {'font': {'color': '#f8f9fa'}},
            'legend': {'font': {'color': '#f8f9fa'}},
            'showlegend': False
        }
    }
