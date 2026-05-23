from dash import html

from .control_panel import create_control_panel
from .historical_layout import create_historical_layout
from .streaming_layout import create_streaming_layout


def create_main_layout():
    return html.Div(
        [create_control_panel(), create_streaming_layout(), create_historical_layout()]
    )
