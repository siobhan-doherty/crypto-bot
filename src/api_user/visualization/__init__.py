"""Visualization package for the crypto dashboard."""

from .callbacks import register_callbacks
from .fetch_data import fetch_historical_data, get_available_date_range
from .layout.controls import (
    create_atr_period_input,
    create_date_range_slider,
    create_trading_pair_dropdown,
)
from .layout.theme import COLORS, PLOT_LAYOUT
from .plots.candlestickplot import create_candlestickplot
from .plots.lineplot import create_lineplot
from .plots.volatilityplot import create_volatility_plot
from .plots.volumeplot import create_volumeplot

__all__ = [
    "register_callbacks",
    "fetch_historical_data",
    "get_available_date_range",
    "create_atr_period_input",
    "create_date_range_slider",
    "create_trading_pair_dropdown",
    "COLORS",
    "PLOT_LAYOUT",
    "create_candlestickplot",
    "create_lineplot",
    "create_volatility_plot",
    "create_volumeplot",
]


def init_app():
    """Initialize and return the Dash application."""
    from .dash_app import create_app

    return create_app()
