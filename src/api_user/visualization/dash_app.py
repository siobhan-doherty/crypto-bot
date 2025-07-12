import sys
from pathlib import Path
from dash_extensions import WebSocket
from src.api_user.visualization.plots.lineplot import create_lineplot

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
from src.api_user.visualization import (
    # Core components
    register_callbacks,
    # Data functions
    fetch_historical_data,
    get_available_date_range,
    COLORS
)
from .layout_historical import create_layout_historical

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from .layout.theme import COLORS
from .layout.controls import get_range_selector_config
Y_VALUE = "close"

def create_app():
    """Create and configure the Dash application."""
    TRADING_PAIR = "BTCUSDT"

    # Get the full date range
    min_date, max_date = get_available_date_range()
    print(f"Available date range: {min_date} to {max_date}")

    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

    app.title = "Crypto Dashboard"

    # Set up the layout using the historical layout component
    #app.layout = create_layout_historical(df, TRADING_PAIR, COLORS)
    data_points = []
    app.layout = html.Div([
        html.Div([
            html.H2(
                f"{TRADING_PAIR} Real-time Price",
                style={
                    'color': COLORS['text'],
                    'textAlign': 'center',
                    'marginBottom': '20px'
                }
            ),
            dcc.Graph(
                id="real-time",
                style={
                    'backgroundColor': COLORS['background'],
                    'borderRadius': '8px',
                    'boxShadow': '0 2px 5px rgba(0,0,0,0.2)'
                },
                config={
                    'displayModeBar': True,
                    'scrollZoom': True,
                    'displaylogo': False
                }
            ),
            WebSocket(id="ws", url=f'ws://localhost:8000/ws/stream/{TRADING_PAIR}'),
        ], style={
            'maxWidth': '1200px',
            'margin': '0 auto',
            'padding': '20px',
            'backgroundColor': COLORS['background']
        })
    ], style={
        'backgroundColor': COLORS['background'],
        'minHeight': '100vh',
        'padding': '20px 0'
    })

    # Register callbacks
    register_callbacks(app, fetch_historical_data=None)

    return app

if __name__ == "__main__":
    # This block runs when the script is executed directly
    try:
        # Try relative import first (works when run as a module)
        from . import init_app
    except ImportError:
        # Fall back to absolute import (works when run directly)
        import sys
        from pathlib import Path

        project_root = Path(__file__).parent.parent.parent.parent
        sys.path.insert(0, str(project_root))
        from src.api_user.visualization import init_app

    app = init_app()
    app.run_server(debug=True, host="0.0.0.0", port=8050)
