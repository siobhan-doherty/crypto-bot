import dash
import dash_bootstrap_components as dbc
from .layout.main_layout import layout


def create_app():
    """Create and configure the Dash application."""
    app = dash.Dash(
        __name__,
        external_stylesheets = [dbc.themes.DARKLY],
        suppress_callback_exceptions = True,
    )
    app.title = "Crypto Dashboard"
    app.layout = layout

    from .callbacks import register_callbacks

    register_callbacks(app)
    return app


if __name__ == "__main__":
    from . import init_app

    app = init_app()
    app.run_server(debug = True, host = "0.0.0.0", port = 8050)
