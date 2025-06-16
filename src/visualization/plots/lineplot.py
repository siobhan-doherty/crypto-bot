from layout.theme import PLOT_LAYOUT, COLORS

def calculate_ema(series, periods):
    """Calculate Exponential Moving Average"""
    return series.ewm(span=periods, min_periods=periods, adjust=False).mean()

def create_lineplot(df):
    """
    Create a line plot of the close price over time with EMA indicators.
    
    Args:
        df (pd.DataFrame): DataFrame containing 'close_time' and 'close' columns
        
    Returns:
        dict: Plotly figure as a dictionary
    """
    if df.empty:
        return {'data': [], 'layout': {}}
        
    df = df.sort_values('close_time')
    
    # Calculate EMAs with different periods
    ema_periods = [9, 21, 50, 200]
    for period in ema_periods:
        df[f'ema_{period}'] = calculate_ema(df['close'], period)
    
    layout = PLOT_LAYOUT.copy()
    
    layout.update({
        'title': {'text': 'BITCUSDT Close Price with EMAs', 'font': {'color': PLOT_LAYOUT['font']['color']}},
        'xaxis': {**PLOT_LAYOUT['xaxis'], 'title': 'Time'},
        'yaxis': {**PLOT_LAYOUT['yaxis'], 'title': 'Price (USDT)'},
        'legend': {
            'orientation': 'h',
            'yanchor': 'bottom',
            'y': 1.02,
            'xanchor': 'right',
            'x': 1,
            'bgcolor': 'rgba(0,0,0,0)'
        }
    })
    
    traces = []
    
    ema_colors = {
        9: '#FF9800',  # Orange
        21: '#E91E63',  # Pink
        50: '#9C27B0',  # Purple
        200: '#2196F3'   # Blue
    }
    
    for period in ema_periods:
        traces.append({
            'x': df['close_time'],
            'y': df[f'ema_{period}'],
            'type': 'line',
            'name': f'EMA {period}',
            'line': {
                'color': ema_colors[period],
                'width': 1.5 if period != 200 else 2,
                'dash': 'dot' if period in [9, 21] else 'solid'
            },
            'opacity': 0.9
        })
    
    traces.append({
        'x': df['close_time'],
        'y': df['close'],
        'type': 'line',
        'name': 'Close Price',
        'line': {
            'color': COLORS['primary'],
            'width': 2
        }
    })
    
    return {
        'data': traces,
        'layout': layout
    }