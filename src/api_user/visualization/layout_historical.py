from dash import dcc, html
from pathlib import Path
import sys

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

def create_layout_historical(df, TRADING_PAIR, COLORS):
    """
    Create the layout for the historical data view of the dashboard
    
    Args:
        df: DataFrame containing the historical data
        TRADING_PAIR: Current trading pair being displayed
        COLORS: Dictionary of color values for the theme
        
    Returns:
        dash.html.Div: The layout component
    """
    # Get min and max dates from the dataframe
    min_date = df['close_datetime'].min()
    max_date = df['close_datetime'].max()
    
    # Define styles
    chart_container_style = {
        "border": f"1px solid {COLORS['border']}",
        "borderRadius": "8px",
        "padding": "20px",
        "marginBottom": "30px",
        "backgroundColor": COLORS["panel"],
        "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
    }
    
    return html.Div(
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
                                "Available Range: "
                                f"{min_date.strftime('%Y-%m-%d')} "
                                f"to {max_date.strftime('%Y-%m-%d')}",
                                style={"margin": "5px 0", "color": COLORS["text"]},
                            ),
                            html.Div(
                                "Displaying: "
                                f"{df['close_datetime'].min().strftime('%Y-%m-%d')} to "
                                f"{df['close_datetime'].max().strftime('%Y-%m-%d')}",
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
                    # Close Price Graph
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
                    # Candlestick Chart
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
                    # Volume Chart
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
                    # Volatility Chart
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