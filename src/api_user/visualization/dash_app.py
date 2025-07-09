import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.api_user.visualization import (
    # Core components
    register_callbacks,
    # Data functions
    fetch_historical_data,
    get_available_date_range,
    # Plot functions
    create_lineplot,
    create_candlestickplot,
    create_volumeplot,
    create_volatility_plot,
    # Layout components
    COLORS,
    PLOT_LAYOUT,
    create_date_range_slider,
    create_trading_pair_dropdown,
    create_atr_period_input,
)

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc


def create_app():
    """Create and configure the Dash application."""
    # Default trading pair
    TRADING_PAIR = "BTCUSDT"

    # Get the full date range
    min_date, max_date = get_available_date_range()
    print(f"Available date range: {min_date} to {max_date}")

    # Fetch the dataset for the dashboard
    df = fetch_historical_data()
    if not df.empty:
        print("Sample data:")
        print(df[["open_datetime", "close_datetime", "open", "close"]].head())
    # BOOTSTRAP, CERULEAN, DARKLY, FLATLY, LITERA, LUX, MATERIA, MINTY, PULSE, SANDSTONE, SIMPLEX, SKETCHY, SLATE, SOLAR, SPACELAB, UNITED
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

    # Set the title of the app
    app.title = "Crypto Dashboard"

    # Define styles
    chart_container_style = {
        "border": f"1px solid {COLORS['border']}",
        "borderRadius": "8px",
        "padding": "20px",
        "marginBottom": "30px",
        "backgroundColor": COLORS["panel"],
        "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
    }

    # Set up the layout
    app.layout = html.Div(
        children=[
            html.H1(
                "Crypto Dashboard",
                style={"textAlign": "center", "marginBottom": "20px"},
            ),
            # Data info section with trading pair selector
            html.Div(
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
                                "",
                                style={
                                    "color": COLORS["text"],
                                    "marginBottom": "8px",
                                    "fontWeight": "bold",
                                    "textAlign": "left",
                                    "paddingLeft": "10px",
                                },
                            ),
                            create_trading_pair_dropdown("trading-pair-dropdown"),
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
                                f"Displaying: {len(df):,} records",
                                style={"margin": "5px 0"},
                            ),
                            html.Div(
                                f"Available Range: {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}",
                                style={"margin": "5px 0", "color": COLORS["text"]},
                            ),
                            html.Div(
                                f"Displaying: {df['close_datetime'].min().strftime('%Y-%m-%d')} to {df['close_datetime'].max().strftime('%Y-%m-%d')}",
                                style={"margin": "5px 0"},
                            ),
                        ],
                    ),
                ],
            ),
            # Main content container
            html.Div(
                style={"maxWidth": "1400px", "margin": "0 auto", "padding": "0 20px"},
                children=[
                    html.Div(
                        style=chart_container_style,
                        children=[
                            dcc.Graph(
                                id="close-price-graph",
                                figure=create_lineplot(df, trading_pair=TRADING_PAIR),
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
                                    create_date_range_slider(
                                        df, "lineplot-time-slider"
                                    ),
                                ],
                            ),
                        ],
                    ),
                    # Candlestick Chart Section
                    html.Div(
                        style=chart_container_style,
                        children=[
                            dcc.Graph(
                                id="candlestick-graph",
                                figure=create_candlestickplot(
                                    df, trading_pair=TRADING_PAIR
                                ),
                                style={"marginBottom": "20px"},
                            ),
                            html.Div(
                                style={"padding": "0 15px"},
                                children=[
                                    html.Div(
                                        "Date Range:",
                                        style={
                                            "color": COLORS["text"],
                                            "marginBottom": "10px",
                                            "fontWeight": "bold",
                                        },
                                    ),
                                    create_date_range_slider(
                                        df, "candlestick-time-slider"
                                    ),
                                ],
                            ),
                        ],
                    ),
                    # Volume Chart Section
                    html.Div(
                        style=chart_container_style,
                        children=[
                            dcc.Graph(
                                id="volume-graph",
                                figure=create_volumeplot(df),
                                style={"marginBottom": "20px"},
                            ),
                            html.Div(
                                style={"padding": "0 15px"},
                                children=[
                                    html.Div(
                                        "Date Range:",
                                        style={
                                            "color": COLORS["text"],
                                            "marginBottom": "10px",
                                            "fontWeight": "bold",
                                        },
                                    ),
                                    create_date_range_slider(df, "volume-time-slider"),
                                ],
                            ),
                        ],
                    ),
                    # Volatility Chart Section
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
                                children=[create_atr_period_input("atr-period-input")],
                            ),
                            dcc.Graph(
                                id="volatility-graph",
                                figure=create_volatility_plot(df),
                                style={"marginBottom": "20px"},
                            ),
                            html.Div(
                                style={"padding": "0 15px"},
                                children=[
                                    html.Div(
                                        "Date Range:",
                                        style={
                                            "color": COLORS["text"],
                                            "marginBottom": "10px",
                                            "fontWeight": "bold",
                                        },
                                    ),
                                    create_date_range_slider(
                                        df, "volatility-time-slider"
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        ]
    )

    # Register callbacks
    register_callbacks(app, fetch_historical_data)

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
