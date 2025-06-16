import pandas as pd
from dash import dcc, html
from dash.dash_table.Format import Format, Scheme

def create_date_picker_range(df, picker_id, min_date_col='close_time', max_date_col='close_time'):
    """
    Create a DatePickerRange component with date-based configuration.
    
    Args:
        df (pd.DataFrame): The dataframe containing the date columns
        picker_id (str): The ID for the DatePickerRange component
        min_date_col (str): Column name for minimum date
        max_date_col (str): Column name for maximum date
        
    Returns:
        dcc.DatePickerRange: Configured DatePickerRange component
    """
    return dcc.DatePickerRange(
        id=picker_id,
        display_format='YYYY-MM-DD',
        min_date_allowed=df[min_date_col].min(),
        max_date_allowed=df[max_date_col].max(),
        start_date=df[min_date_col].min(),
        end_date=df[max_date_col].max(),
        style={
            'display': 'flex',
            'justifyContent': 'center',
            'gap': '20px',
            'color': '#f8f9fa'
        }
    )


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