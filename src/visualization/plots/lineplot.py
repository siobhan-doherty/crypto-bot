import pandas as pd
from layout.theme import PLOT_LAYOUT, LINE_PLOT

def create_lineplot(df):
    """
    Create a line plot for the given DataFrame.
    
    Args:
        df (pd.DataFrame): DataFrame containing 'close_time' and 'close' columns
        
    Returns:
        dict: Plotly figure dictionary for the line plot
    """
    if df.empty:
        return {'data': [], 'layout': {}}
        
    df = df.sort_values('close_time')
    
    layout = PLOT_LAYOUT.copy()
    
    layout.update({
        'title': {'text': 'BITCUSDT Close Price', 'font': {'color': PLOT_LAYOUT['font']['color']}},
        'xaxis': {**PLOT_LAYOUT['xaxis'], 'title': 'Time'},
        'yaxis': {**PLOT_LAYOUT['yaxis'], 'title': 'Close Price (USDT)'}
    })
    
    return {
        'data': [{
            'x': df['close_time'],
            'y': df['close'],
            'type': 'line',
            'name': 'Close Price',
            'line': {
                'color': LINE_PLOT['line_color'],
                'width': LINE_PLOT['line_width']
            }
        }],
        'layout': layout
    }