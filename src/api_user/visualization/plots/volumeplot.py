import plotly.graph_objects as go
from layout.theme import PLOT_LAYOUT, COLORS

def create_volumeplot(df, trading_pair='BTCUSDT'):
    """
    Create a volume plot with color-coded bars based on price movement.
    
    Args:
        df (pd.DataFrame): DataFrame containing 'close_time', 'volume', 'close', and 'open' columns
        
    Returns:
        dict: Plotly figure as a dictionary
    """
    if df.empty:
        return {'data': [], 'layout': {}}
        
    df = df.sort_values('close_time')
    
    layout = PLOT_LAYOUT.copy()
    
    # Create a copy of the default title config and update the text
    title_config = PLOT_LAYOUT.get('title', {}).copy()
    title_config['text'] = f'{trading_pair} Volume'
    
    layout.update({
        'title': title_config,
        'xaxis': {**PLOT_LAYOUT['xaxis'], 'title': 'Time'},
        'yaxis': {**PLOT_LAYOUT['yaxis'], 'title': 'Volume (USDT)'},
        'showlegend': False
    })
    
    increasing_mask = df['close'] > df['open']
    
    increasing_bars = go.Bar(
        x=df[increasing_mask]['close_time'],
        y=df[increasing_mask]['volume'],
        name='Increasing Volume',
        marker_color=COLORS['primary'],
        opacity=0.7,
        hoverinfo='y+text',
        hovertext=[f"Volume: {v:,.2f} USDT" for v in df[increasing_mask]['volume']],
        showlegend=False
    )
    
    decreasing_bars = go.Bar(
        x=df[~increasing_mask]['close_time'],
        y=df[~increasing_mask]['volume'],
        name='Decreasing Volume',
        marker_color=COLORS['secondary'],
        opacity=0.7,
        hoverinfo='y+text',
        hovertext=[f"Volume: {v:,.2f} USDT" for v in df[~increasing_mask]['volume']],
        showlegend=False
    )
    
    fig = go.Figure(data=[increasing_bars, decreasing_bars], layout=layout)
    
    avg_volume = df['volume'].mean()
    fig.add_hline(
        y=avg_volume,
        line_dash='dash',
        line_color=COLORS['text'],
        opacity=0.5,
        annotation_text=f'Avg: {avg_volume:,.2f}',
        annotation_position='top right'
    )
    
    return fig.to_dict()