from dash import html, dcc
from dash_extensions import WebSocket
from .theme import COLORS


def create_streaming_layout(trading_pair="BTCUSDT"):
    """
    Create the streaming layout for real-time price updates

    Args:
        trading_pair (str): The trading pair to display (default: "BTCUSDT")

    Returns:
        dash.html.Div: The streaming layout component
    """
    ws_component = WebSocket(id="ws", url="ws://localhost:8000/ws/stream")

    graph_component = dcc.Graph(
        id="real-time",
        style={
            "backgroundColor": COLORS["background"],
            "borderRadius": "8px",
            "boxShadow": "0 2px 5px rgba(0,0,0,0.2)",
            "height": "600px",
        },
        config={"displayModeBar": True, "scrollZoom": True, "displaylogo": False},
    )

    # Add a store component to maintain data state
    data_store = dcc.Store(id="ws-data-store", data={})

    return html.Div(
        children=[
            html.H2(
                id="trading-pair-title",
                style={
                    "color": COLORS["text"],
                    "textAlign": "center",
                    "marginBottom": "20px",
                },
            ),
            html.Div(
                id="ws-status",
                style={
                    "color": COLORS["text"],
                    "textAlign": "center",
                    "marginBottom": "10px",
                },
            ),
            html.Div(
                id="data-status",
                style={
                    "color": COLORS["text"],
                    "textAlign": "center",
                    "marginBottom": "10px",
                },
            ),
            graph_component,
            data_store,
            ws_component,
        ],
        style={
            "maxWidth": "1200px",
            "margin": "0 auto",
            "padding": "20px",
            "backgroundColor": COLORS["background"],
        },
    )
