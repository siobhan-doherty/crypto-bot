"""
Theme configuration for the visualization components.
Defines colors and styles to maintain consistency across all plots.
"""

COLORS = {
    'background': '#222222',  # dark gray
    'panel': '#2d2d2d',       # slightly lighter gray
    'grid': 'rgba(255, 255, 255, 0.1)',  # semi-transparent white
    'text': '#f8f9fa',        # light gray/white
    'primary': '#00bc8c',     # Teal/Green
    'secondary': '#e74c3c',   # Red
    'border': 'rgba(39, 41, 61, 0.5)'  # semi-transparent dark gray
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

VOLUME_PLOT = {
    'bar_color': COLORS['primary'],
    'line_width': 2
}

