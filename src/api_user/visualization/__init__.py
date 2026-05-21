"""Visualization package for the crypto dashboard."""
from .callbacks import register_callbacks
from .fetch_data import fetch_historical_data, get_available_date_range
from .plots.lineplot import create_lineplot
from .plots.candlestickplot import create_candlestickplot
from .plots.volumeplot import create_volumeplot
from .plots.volatilityplot import create_volatility_plot
from .layout.theme import COLORS, PLOT_LAYOUT
from .layout.controls import (
    create_date_range_slider,
    create_trading_pair_dropdown,
    create_atr_period_input,
)


def init_app():
    """Initialize and return the Dash application."""
    from .dash_app import create_app

    return create_app()
