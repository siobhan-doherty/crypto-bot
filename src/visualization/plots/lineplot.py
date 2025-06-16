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
            'line': {'color': '#00bc8c', 'width': 2}
        }],
        'layout': {
            'title': {'text': 'BITCUSDT Close Price', 'font': {'color': '#f8f9fa'}},
            'xaxis': {
                'title': 'Time',
                'titlefont': {'color': '#f8f9fa'},
                'tickfont': {'color': '#f8f9fa'},
                'gridcolor': 'rgba(255, 255, 255, 0.1)',
                'linecolor': 'rgba(255, 255, 255, 0.1)',
                'zerolinecolor': 'rgba(255, 255, 255, 0.1)',
                'showgrid': True,
                'showline': True
            },
            'yaxis': {
                'title': 'Close Price (USDT)',
                'titlefont': {'color': '#f8f9fa'},
                'tickfont': {'color': '#f8f9fa'},
                'gridcolor': 'rgba(255, 255, 255, 0.1)',
                'linecolor': 'rgba(255, 255, 255, 0.1)',
                'zerolinecolor': 'rgba(255, 255, 255, 0.1)',
                'showgrid': True,
                'showline': True
            },
            'margin': {'l': 60, 'r': 30, 't': 80, 'b': 100},
            'height': 500,
            'plot_bgcolor': '#222',
            'paper_bgcolor': '#222',
            'font': {'color': '#f8f9fa'},
            'hovermode': 'x unified',
            'hoverlabel': {
                'font': {'color': '#f8f9fa'},
                'bgcolor': '#303030'
            },
            'legend': {
                'font': {'color': '#f8f9fa'},
                'bgcolor': '#222',
                'bordercolor': 'rgba(255, 255, 255, 0.1)'
            },
            'transition': {'duration': 300}
        }
    }