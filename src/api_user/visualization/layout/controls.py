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

def create_trading_pair_dropdown(dropdown_id, multi=False, value=None):
    options=[
        {'label': 'BTC/USDT', 'value': 'BTCUSDT'},
        {'label': 'ETH/USDT', 'value': 'ETHUSDT'}
    ]
    
    if value is None:
        value = 'BTCUSDT' if not multi else ['BTCUSDT', 'ETHUSDT']
    
    return dcc.Dropdown(
        id=dropdown_id,
        className='custom-dropdown',
        options=options,
        value=value,
        multi=multi,
        clearable=not multi,  # Don't allow clearing when multi-select
        searchable=False,
    )

def create_atr_period_input(input_id, default_period=14):
    """
    Create a numeric input for ATR period selection.
    
    Args:
        input_id (str): The ID for the input component
        default_period (int): Default ATR period (default: 14)
        
    Returns:
        html.Div: Styled numeric input component
    """
    return html.Div([
        html.Label('Average True Range Period:', style={
            'color': 'white',
            'marginRight': '10px',
            'fontSize': '14px'
        }),
        dcc.Input(
            id=input_id,
            type='number',
            min=5,
            max=50,
            step=1,
            value=default_period,
            style={
                'width': '60px',
                'marginRight': '10px',
                'backgroundColor': '#2d2d2d',
                'color': 'white',
                'border': '1px solid #00bc8c',
                'borderRadius': '4px',
                'padding': '4px 8px'
            }
        )
    ], style={'display': 'flex', 'alignItems': 'center'})