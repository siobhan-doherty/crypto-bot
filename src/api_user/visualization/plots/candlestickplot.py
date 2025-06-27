from plotly.graph_objs import Figure, Candlestick
from layout.theme import PLOT_LAYOUT, COLORS

def create_candlestickplot(df, trading_pair='BTCUSDT'):
    if df.empty:
        return {'data': [], 'layout': {}}
        
    df = df.sort_values('close_datetime')
    
    layout = PLOT_LAYOUT.copy()
    
    # Create a copy of the default title config and update the text
    title_config = PLOT_LAYOUT.get('title', {}).copy()
    title_config['text'] = f'{trading_pair} Candlestick Chart'
    
    layout.update({
        'title': title_config,
        'xaxis': {**PLOT_LAYOUT['xaxis'], 'title': 'Time', 'type': 'date', 'rangeslider': {'visible': False}},
        'yaxis': {**PLOT_LAYOUT['yaxis'], 'title': 'Price (USDT)'}
    })
    
    candlestick = Candlestick(
        x=df['close_datetime'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name='Candlesticks',
        increasing_line_color=COLORS['increase'],
        decreasing_line_color=COLORS['decrease'],
        increasing_fillcolor=COLORS['increase'],
        decreasing_fillcolor=COLORS['decrease'],
        line=dict(width=1),
        opacity=0.8
    )
    
    fig = Figure(data=[candlestick], layout=layout)
    
    return fig.to_dict()
