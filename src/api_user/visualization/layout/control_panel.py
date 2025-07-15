from dash import html
from .theme import COLORS
from .controls import create_trading_pair_dropdown
from ..fetch_data import get_available_date_range


def create_control_panel(df=None):
    """
    Create the control panel component with trading pair selector and data info.

    Args:
        df: Optional DataFrame containing the data for displaying record count

    Returns:
        dash.html.Div: The control panel component
    """
    min_date, max_date = get_available_date_range()

    return html.Div(
        style={
            "display": "flex",
            "justifyContent": "space-between",
            "alignItems": "center",
            "margin": "20px auto",
            "padding": "15px",
            "maxWidth": "1000px",
            "backgroundColor": COLORS["panel"],
            "borderRadius": "8px",
            "color": COLORS["text"],
        },
        children=[
            html.Div(
                style={"width": "30%"},
                children=[
                    html.Div(
                        "Trading Pair",
                        style={
                            "color": COLORS["text"],
                            "marginBottom": "8px",
                            "fontWeight": "bold",
                            "textAlign": "left",
                            "paddingLeft": "10px",
                        },
                    ),
                    create_trading_pair_dropdown(
                        "trading-pair-dropdown", id="trading-pair-dropdown"
                    ),
                ],
            ),
            html.Div(
                style={
                    "width": "65%",
                    "textAlign": "right",
                    "paddingRight": "20px",
                },
                children=[
                    html.Div(
                        "Historical Data Range:",
                        style={"margin": "5px 0"},
                    ),
                    html.Div(
                        f"From: {min_date.strftime('%Y-%m-%d')}"
                        if min_date
                        else "No data available",
                        style={"margin": "5px 0"},
                    ),
                    html.Div(
                        f"To: {max_date.strftime('%Y-%m-%d')}" if max_date else "",
                        style={"margin": "5px 0"},
                    ),
                    html.Div(
                        f"Displaying: {len(df):,} records" if df is not None else "",
                        style={"margin": "5px 0"},
                    ),
                ],
            ),
        ],
    )
