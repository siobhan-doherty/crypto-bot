from dash import html
from .historical_layout import create_historical_layout
from .control_panel import create_control_panel
from api_user.visualization.layout.streaming_layout import create_streaming_layout

layout = html.Div(
    [create_control_panel(), create_streaming_layout(), create_historical_layout()]
)
