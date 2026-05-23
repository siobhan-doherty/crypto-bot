from dash import dcc, html

from api_user.visualization.data_store import prepare_data
from api_user.visualization.layout.controls import (
    create_atr_period_input,
    create_date_range_slider,
)
from api_user.visualization.layout.theme import COLORS
from api_user.visualization.plots.candlestickplot import create_candlestickplot
from api_user.visualization.plots.lineplot import create_lineplot
from api_user.visualization.plots.volatilityplot import create_volatility_plot
from api_user.visualization.plots.volumeplot import create_volumeplot
from api_user.visualization.utils import filter_df


def create_historical_layout():
    """
    Create the layout for the historical data view of the dashboard
    Returns: dash.html.Div: The layout component
    """
    # Define styles
    chart_container_style = {
        "border": f"1px solid {COLORS['border']}",
        "borderRadius": "8px",
        "padding": "20px",
        "marginBottom": "30px",
        "backgroundColor": COLORS["panel"],
        "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
    }

    full_df = prepare_data()
    # use data filtered by symbol for all plots but volatility
    filtered_df = filter_df(full_df)
    # Add hidden input to trigger initial data load
    data_init_trigger = html.Div(id="data-init-trigger", style={"display": "none"})

    layout = html.Div(
        style={"maxWidth": "1400px", "margin": "0 auto", "padding": "0 20px"},
        children=[
            data_init_trigger,
            # Line Plot Container
            html.Div(
                style=chart_container_style,
                children=[
                    dcc.Graph(
                        id="historical-lineplot",
                        figure=create_lineplot(filtered_df),
                        style={"marginBottom": "20px"},
                    ),
                    html.Div(
                        style={"padding": "0 15px"},
                        children=[
                            html.Div(
                                "Date Range:",
                                style={
                                    "color": "#f8f9fa",
                                    "marginBottom": "10px",
                                    "fontWeight": "bold",
                                },
                            ),
                            create_date_range_slider(filtered_df, id="line-slider"),
                        ],
                    ),
                ],
            ),
            # Candlestick Plot Container
            html.Div(
                style=chart_container_style,
                children=[
                    dcc.Graph(
                        id="historical-candleplot",
                        figure=create_candlestickplot(filtered_df),
                        style={"marginBottom": "20px"},
                    ),
                    html.Div(
                        style={"padding": "0 15px"},
                        children=[
                            html.Div(
                                "Date Range:",
                                style={
                                    "color": "#f8f9fa",
                                    "marginBottom": "10px",
                                    "fontWeight": "bold",
                                },
                            ),
                            create_date_range_slider(filtered_df, id="candle-slider"),
                        ],
                    ),
                ],
            ),
            # Volume Plot Container
            html.Div(
                style=chart_container_style,
                children=[
                    dcc.Graph(
                        id="historical-volumeplot",
                        figure=create_volumeplot(filtered_df),
                        style={"marginBottom": "20px"},
                    ),
                    html.Div(
                        style={"padding": "0 15px"},
                        children=[
                            html.Div(
                                "Date Range:",
                                style={
                                    "color": "#f8f9fa",
                                    "marginBottom": "10px",
                                    "fontWeight": "bold",
                                },
                            ),
                            create_date_range_slider(filtered_df, id="volume-slider"),
                        ],
                    ),
                ],
            ),
            # Volatility Plot Container
            html.Div(
                style=chart_container_style,
                children=[
                    html.Div(
                        style={
                            "display": "flex",
                            "justifyContent": "flex-end",
                            "marginBottom": "10px",
                            "alignItems": "center",
                        },
                        children=[create_atr_period_input(id="atr-period-input")],
                    ),
                    dcc.Graph(
                        id="historical-volatilityplot",
                        figure=create_volatility_plot(full_df),
                        style={"marginBottom": "20px"},
                    ),
                    html.Div(
                        style={"padding": "0 15px"},
                        children=[
                            html.Div(
                                "Date Range:",
                                style={
                                    "color": "#f8f9fa",
                                    "marginBottom": "10px",
                                    "fontWeight": "bold",
                                },
                            ),
                            create_date_range_slider(full_df, id="volatility-slider"),
                        ],
                    ),
                ],
            ),
        ],
    )

    return layout
