from plotly.graph_objs import Figure, Candlestick
from layout.theme import PLOT_LAYOUT, COLORS

def create_candlestickplot(df, trading_pair='BTCUSDT'):
    """
    Create a candlestick plot for the given OHLC data.
    
    Args:
        df (pd.DataFrame): DataFrame containing OHLC data with 'close_datetime' column
        trading_pair (str): Name of the trading pair for the title
        
    Returns:
        dict: Plotly figure as a dictionary
    """
    
    if 'close_datetime' not in df.columns or 'open' not in df.columns or 'high' not in df.columns or 'low' not in df.columns or 'close' not in df.columns:
        print("Error: Missing required columns in DataFrame")
        return {'data': [], 'layout': {}}
    
    # Make a copy to avoid modifying the original dataframe
    df = df.copy()
    

    df = df.sort_values('close_datetime')
    
    layout = PLOT_LAYOUT.copy()
    layout.update({
        'title': f'{trading_pair} Candlestick Chart',
        'xaxis': {
            **PLOT_LAYOUT['xaxis'],
            'title': 'Time',
            'type': 'date',
            'rangeslider': {'visible': False}
        },
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
