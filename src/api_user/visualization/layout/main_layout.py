from dash import dcc, html

from .control_panel import create_control_panel
from .historical_layout import create_historical_layout
from .streaming_layout import create_streaming_layout


def create_main_layout():
    # hidden range sliders required by callbacks
    hidden_sliders = html.Div(
        style={"display": "none"},
        children=[
            dcc.RangeSlider(id="line-slider", min=0, max=100, step=1, value=[0, 100]),
            dcc.RangeSlider(id="candle-slider", min=0, max=100, step=1, value=[0, 100]),
            dcc.RangeSlider(id="volume-slider", min=0, max=100, step=1, value=[0, 100]),
            dcc.RangeSlider(
                id="volatility-slider", min=0, max=100, step=1, value=[0, 100]
            ),
        ],
    )

    return html.Div(
        children=[
            create_control_panel(),
            create_streaming_layout(),
            create_historical_layout(),
            hidden_sliders,
        ]
    )
