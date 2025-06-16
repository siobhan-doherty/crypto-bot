"""
Theme configuration for the visualization components.
Defines colors and styles to maintain consistency across all plots.
"""

COLORS = {
    'background': '#222',
    'panel': '#2d2d2d',
    'grid': 'rgba(255, 255, 255, 0.1)',
    'text': '#f8f9fa',
    'primary': '#00bc8c',  # Teal/Green
    'secondary': '#e74c3c',  # Red
    'border': 'rgba(255, 255, 255, 0.1)'
}

PLOT_LAYOUT = {
    'plot_bgcolor': COLORS['background'],
    'paper_bgcolor': COLORS['background'],
    'font': {'color': COLORS['text']},
    'margin': {'l': 60, 'r': 30, 't': 80, 'b': 100},
    'height': 500,
    'hovermode': 'x unified',
    'hoverlabel': {
        'font': {'color': COLORS['text']},
        'bgcolor': COLORS['panel']
    },
    'legend': {
        'font': {'color': COLORS['text']},
        'bgcolor': COLORS['background'],
        'bordercolor': COLORS['border']
    },
    'xaxis': {
        'tickfont': {'color': COLORS['text']},
        'gridcolor': COLORS['grid'],
        'linecolor': COLORS['grid'],
        'zerolinecolor': COLORS['grid'],
        'showgrid': True,
        'showline': True
    },
    'yaxis': {
        'tickfont': {'color': COLORS['text']},
        'gridcolor': COLORS['grid'],
        'linecolor': COLORS['grid'],
        'zerolinecolor': COLORS['grid'],
        'showgrid': True,
        'showline': True
    }
}

CANDLESTICK = {
    'increasing': '#00bc8c', 
    'decreasing': '#e74c3c'  
}

LINE_PLOT = {
    'line_color': COLORS['primary'],
    'line_width': 2
}
