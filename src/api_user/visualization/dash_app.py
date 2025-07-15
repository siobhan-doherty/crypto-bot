import sys
from pathlib import Path
from .layout.main_layout import layout

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
import dash
import dash_bootstrap_components as dbc


def create_app():
    """Create and configure the Dash application."""
    app = dash.Dash(
        __name__,
        external_stylesheets=[dbc.themes.DARKLY],
        suppress_callback_exceptions=True,
    )

    app.title = "Crypto Dashboard"
    app.layout = layout

    # Import and register callbacks
    from .callbacks import register_callbacks

    register_callbacks(app)

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
