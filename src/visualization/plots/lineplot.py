import pandas as pd

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
    
    return {
        'data': [{
            'x': df['close_time'],
            'y': df['close'],
            'type': 'line',
            'name': 'Close Price',
            'line': {'color': '#1f77b4'}
        }],
        'layout': {
            'title': 'BITCUSDT Close Price',
            'xaxis': {
                'title': 'Time'
            },
            'yaxis': {
                'title': 'Close Price (USDT)',
                'gridcolor': 'rgba(0,0,0,0.1)'
            },
            'margin': {'l': 60, 'r': 30, 't': 80, 'b': 100},
            'height': 500,
            'plot_bgcolor': 'white',
            'paper_bgcolor': 'white',
            'font': {'color': '#2c3e50'},
            'hovermode': 'x unified'
        }
    }