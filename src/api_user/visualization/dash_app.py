import os
import sys
from pathlib import Path
from dash_extensions import WebSocket

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.api_user.visualization import (
    # Core components
    register_callbacks,
    # Data functions
    fetch_historical_data,
    get_available_date_range,
    COLORS,
    PLOT_LAYOUT
)
from .layout_historical import create_layout_historical

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc


def create_app():
    """Create and configure the Dash application."""
    # Default trading pair
    TRADING_PAIR = "BTCUSDT"

    # Get the full date range
    min_date, max_date = get_available_date_range()
    print(f"Available date range: {min_date} to {max_date}")

    # Fetch the dataset for the dashboard
    df = fetch_historical_data()
    if not df.empty:
        print("Sample data:")
        print(df[["open_datetime", "close_datetime", "open", "close"]].head())
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

    # Set the title of the app
    app.title = "Crypto Dashboard"

    # Set up the layout using the historical layout component
    app.layout = create_layout_historical(df, TRADING_PAIR, COLORS)

    # Register callbacks
    register_callbacks(app, fetch_historical_data)

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
