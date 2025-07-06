#/plots
"""
Visualization package for the crypto dashboard.

This module contains the main visualization components for the crypto dashboard,
including plots, layouts, and callbacks.
"""

# Import from submodules
from .callbacks import register_callbacks
from .fetch_data import fetch_historical_data, get_available_date_range

# Re-export plot functions
from .plots.lineplot import create_lineplot
from .plots.candlestickplot import create_candlestickplot
from .plots.volumeplot import create_volumeplot
from .plots.volatilityplot import create_volatility_plot

# Re-export layout components
from .layout.theme import COLORS, PLOT_LAYOUT
from .layout.controls import (
    create_date_range_slider,
    create_trading_pair_dropdown,
    create_atr_period_input
)

# Initialize the app when imported
from .dash_app import create_app
app = create_app()

def init_app():
    """Initialize and return the Dash application.
    
    This function ensures the app is properly initialized and can be used
    as the main entry point for running the application.
    """
    return app