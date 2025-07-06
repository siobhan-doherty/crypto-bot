import plotly.graph_objects as go
import pandas as pd
from ..layout.theme import PLOT_LAYOUT, COLORS, VOLATILITY_PLOT

def calculate_atr(df, period=14):
    """
    Calculate Average True Range (ATR) for volatility measurement
    
    Args:
        df (pd.DataFrame): DataFrame containing 'high', 'low', 'close' columns
        period (int): Period for ATR calculation (default: 14)
        
    Returns:
        pd.Series: ATR values
    """
    high = df['high']
    low = df['low']
    close = df['close']
    
    # Calculate True Range
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # Calculate ATR using exponential moving average
    atr = true_range.ewm(span=period, adjust=False).mean()
    return atr

def create_volatility_plot(df, period=14):
    """
    Create a volatility plot using ATR (Average True Range) for BTCUSDT and ETHUSDT
    
    Args:
        df (dict): Dictionary of DataFrames keyed by trading pair
        period (int): Period for ATR calculation (default: 14)
        
    Returns:
        dict: Plotly figure as a dictionary
    """
    # Always use these two pairs
    trading_pairs = ['BTCUSDT', 'ETHUSDT']
    
    # Filter to only include our target pairs that exist in the data
    valid_pairs = [pair for pair in trading_pairs if pair in df]
    if not valid_pairs:
        return {'data': [], 'layout': {}}
    
    # Create figure with secondary y-axis
    fig = go.Figure()
    
    # Colors for each pair
    colors = [COLORS['primary'], COLORS['secondary']]
    
    # Add traces for BTCUSDT and ETHUSDT
    for i, pair in enumerate(trading_pairs):
        if pair not in df:
            continue
            
        pair_df = df[pair].sort_values('close_datetime')
        atr = calculate_atr(pair_df, period)
        
        # First pair uses left y-axis, second uses right y-axis
        y_axis = 'y' if i == 0 else 'y2'
        
        fig.add_trace(go.Scatter(
            x=pair_df['close_datetime'],
            y=atr,
            mode='lines',
            name=pair,  # Just the pair name, no prefix
            line=dict(color=colors[i], width=2),
            yaxis=y_axis,
            showlegend=True
        ))
    
    # Create base layout from theme
    layout = {
        **VOLATILITY_PLOT['layout'],
        'title': {
            **PLOT_LAYOUT.get('title', {}),
            'text': f'Volatility (ATR {period})'
        },
        'xaxis': {**PLOT_LAYOUT['xaxis'], 'title': 'Time'},
        'plot_bgcolor': COLORS['background'],
        'paper_bgcolor': COLORS['background'],
        'showlegend': True
    }
    
    if 'BTCUSDT' in df:
        layout['yaxis'] = {
            **VOLATILITY_PLOT['yaxis'],
            'title': 'BTCUSDT ATR',
            'color': colors[0],
            'tickfont': {'color': colors[0]}
        }
    
    if 'ETHUSDT' in df:
        layout['yaxis2'] = {
            **VOLATILITY_PLOT['yaxis2'],
            'title': 'ETHUSDT ATR',
            'color': colors[1],
            'tickfont': {'color': colors[1]}
        }
    
    fig.update_layout(layout)
    return fig.to_dict()