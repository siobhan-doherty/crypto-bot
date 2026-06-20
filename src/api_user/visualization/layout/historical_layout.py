from dash import dcc, html

from api_user.visualization.data_store import prepare_data
from api_user.visualization.layout.controls import create_atr_period_input
from api_user.visualization.layout.theme import COLORS
from api_user.visualization.plots.candlestickplot import create_candlestickplot
from api_user.visualization.plots.lineplot import create_lineplot
from api_user.visualization.plots.volatilityplot import create_volatility_plot
from api_user.visualization.plots.volumeplot import create_volumeplot
from api_user.visualization.utils import filter_df


def create_historical_layout():
    """
    Create layout for historical data view of dashboard.
    Returns: dash.html.Div: The layout component
    """
    # define styles
    chart_container_style = {
        "border": f"1px solid {COLORS['border']}",
        "borderRadius": "8px",
        "padding": "20px",
        "marginBottom": "30px",
        "backgroundColor": COLORS["panel"],
        "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
    }

    # fetch data and prepare filtered DataFrame for initial placeholder plots
    full_df = prepare_data()
    filtered_df = filter_df(full_df)

    # hidden trigger to initialise slider range updates, see callbacks.py
    data_init_trigger = html.Div(
        id="data-init-trigger", style={"display": "none"}, children="0"
    )

    layout = html.Div(
        style={"maxWidth": "1400px", "margin": "0 auto", "padding": "0 20px"},
        children=[
            data_init_trigger,
            # line plot container, slider is hidden in main_layout.py
            html.Div(
                style=chart_container_style,
                children=[
                    dcc.Graph(
                        id="historical-lineplot",
                        figure=create_lineplot(filtered_df),
                        style={"marginBottom": "20px"},
                    ),
                ],
            ),
            # candlestick plot container
            html.Div(
                style=chart_container_style,
                children=[
                    dcc.Graph(
                        id="historical-candleplot",
                        figure=create_candlestickplot(filtered_df),
                        style={"marginBottom": "20px"},
                    ),
                ],
            ),
            # volume plot container
            html.Div(
                style=chart_container_style,
                children=[
                    dcc.Graph(
                        id="historical-volumeplot",
                        figure=create_volumeplot(filtered_df),
                        style={"marginBottom": "20px"},
                    ),
                ],
            ),
            # volatility plot container, slider hidden, ATR input visible
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
                ],
            ),
        ],
    )

    return layout
