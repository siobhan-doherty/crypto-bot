import pandas as pd
from dash import dcc, html
from dash.dash_table.Format import Format, Scheme

def create_date_range_slider(df, slider_id, min_date_col='close_time', max_date_col='close_time'):
    """
    Create a RangeSlider component with date-based configuration.
    
    Args:
        df (pd.DataFrame): The dataframe containing the date columns
        slider_id (str): The ID for the RangeSlider component
        min_date_col (str): Column name for minimum date
        max_date_col (str): Column name for maximum date
        
    Returns:
        dcc.RangeSlider: Configured RangeSlider component
    """
    min_timestamp = int(pd.Timestamp(df[min_date_col].min()).timestamp())
    max_timestamp = int(pd.Timestamp(df[max_date_col].max()).timestamp())
    
    date_range = pd.date_range(
        start=df[min_date_col].min(),
        end=df[max_date_col].max(),
        periods=10
    )
    
    marks = {
        int(ts.timestamp()): {'label': ts.strftime('%Y-%m-%d')}
        for ts in date_range
    }
    
    return dcc.RangeSlider(
        id=slider_id,
        min=min_timestamp,
        max=max_timestamp,
        value=[min_timestamp, max_timestamp],
        marks=marks,
        step=None
    )

def create_trading_pair_dropdown(dropdown_id):
    options=[
            {'label': 'BTC/USDT', 'value': 'BTCUSDT'},
            {'label': 'ETH/USDT', 'value': 'ETHUSDT'},
            {'label': 'ETH/BTC', 'value': 'ETHBTC'},
        ]
    return dcc.Dropdown(
        id=dropdown_id,
        options=options,
        value='BTCUSDT',
        style={'width': '200px'}
    )