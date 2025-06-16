import pandas as pd
from plotly.graph_objs import Figure, Candlestick
from layout.theme import PLOT_LAYOUT, CANDLESTICK

def create_candlestickplot(df):
    if df.empty:
        return {'data': [], 'layout': {}}
        
    df = df.sort_values('close_time')
    
    layout = PLOT_LAYOUT.copy()
    
    layout.update({
        'title': {'text': 'BITCUSDT Candlestick Chart', 'font': {'color': PLOT_LAYOUT['font']['color']}},
        'xaxis': {**PLOT_LAYOUT['xaxis'], 'title': 'Time', 'type': 'date', 'rangeslider': {'visible': False}},
        'yaxis': {**PLOT_LAYOUT['yaxis'], 'title': 'Price (USDT)'}
    })
    
    candlestick = Candlestick(
        x=df['close_time'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name='Candlesticks',
        increasing_line_color=CANDLESTICK['increasing'],
        decreasing_line_color=CANDLESTICK['decreasing'],
        increasing_fillcolor=CANDLESTICK['increasing'],
        decreasing_fillcolor=CANDLESTICK['decreasing'],
        line=dict(width=1),
        opacity=0.8
    )
    
    fig = Figure(data=[candlestick], layout=layout)
    
    return fig.to_dict()
