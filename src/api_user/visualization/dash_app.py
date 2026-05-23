import dash
import dash_bootstrap_components as dbc

from api_user.visualization.callbacks import register_callbacks
from api_user.visualization.layout.main_layout import create_main_layout


def create_app() -> dash.Dash:
    app = dash.Dash(
        __name__,
        external_stylesheets=[dbc.themes.DARKLY],
        suppress_callback_exceptions=True,
    )
    app.title = "Crypto Dashboard"
    app.layout = create_main_layout()
    register_callbacks(app)
    return app


app = create_app()
server = app.server


if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=8050)  # nosec
