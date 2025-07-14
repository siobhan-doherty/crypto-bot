import pandas as pd
from dash import dcc, html
from .theme import COLORS


def create_range_selector(y_axis_title):
    """
    Creates a range selector layout configuration for Plotly figures.
    
    Args:
        y_axis_title (str): Title for the y-axis
    
    Returns:
        dict: Plotly layout configuration with range selector
    """
    return {
        'xaxis': {
            'type': 'date',
            'tickformat': '%H:%M:%S',
            'rangeslider': {'visible': False},
            'rangeselector': {
                'buttons': [
                    {'count': 15, 'label': '15m', 'step': 'minute', 'stepmode': 'backward'},
                    {'count': 1, 'label': '1h', 'step': 'hour', 'stepmode': 'backward'},
                    {'count': 6, 'label': '6h', 'step': 'hour', 'stepmode': 'backward'},
                    {'count': 1, 'label': '1d', 'step': 'day', 'stepmode': 'backward'},
                    {'step': 'all'}
                ],
                'bgcolor': COLORS['background'],
                'activecolor': COLORS['primary'],    
                'font': {'color': COLORS['text']}  
            }
        },
        'yaxis': {'title': y_axis_title}
    }

def create_date_range_slider(
    df, id=None, min_date_col="close_datetime", max_date_col="close_datetime"
):
    """
    Create a RangeSlider component with date-based configuration.

    Args:
        df (pd.DataFrame): The dataframe containing the date columns
        id (str): The ID for the RangeSlider component
        min_date_col (str): Column name for minimum date
        max_date_col (str): Column name for maximum date

    Returns:
        html.Div: Container with RangeSlider or error message
    """
    # Check if DataFrame is empty or required columns are missing
    if df.empty or min_date_col not in df.columns or max_date_col not in df.columns:
        return html.Div(
            "Date range slider not available: No data or missing date columns.",
            style={"color": "#ff6b6b", "padding": "10px"},
        )

    try:
        min_date = df[min_date_col].min()
        max_date = df[max_date_col].max()

        min_timestamp = int(pd.Timestamp(min_date).timestamp())
        max_timestamp = int(pd.Timestamp(max_date).timestamp())

        num_marks = min(10, len(df))
        date_range = pd.date_range(start=min_date, end=max_date, periods=num_marks)

        marks = {}
        for ts in date_range:
            ts_timestamp = int(ts.timestamp())
            if min_timestamp <= ts_timestamp <= max_timestamp:
                marks[ts_timestamp] = {
                    "label": ts.strftime("%b %d\n%H:%M"),
                    "style": {
                        "color": "#fff",
                        "white-space": "pre",
                        "transform": "translateX(-50%)",
                        "text-align": "center",
                        "font-size": "12px",
                        "margin-top": "5px",
                    },
                }

        # Add marks for the start and end dates if they're not already included
        if min_timestamp not in marks:
            min_date_dt = pd.Timestamp(min_date)
            marks[min_timestamp] = {
                "label": min_date_dt.strftime("%b %d\n%H:%M"),
                "style": {
                    "color": "#fff",
                    "white-space": "pre",
                    "transform": "translateX(0)",
                    "text-align": "left",
                    "font-size": "12px",
                    "margin-top": "5px",
                },
            }
        if max_timestamp not in marks:
            max_date_dt = pd.Timestamp(max_date)
            marks[max_timestamp] = {
                "label": max_date_dt.strftime("%b %d\n%H:%M"),
                "style": {
                    "color": "#fff",
                    "white-space": "pre",
                    "transform": "translateX(-100%)",
                    "text-align": "right",
                    "font-size": "12px",
                    "margin-top": "5px",
                },
            }

        # Set default value to full range
        value = [min_timestamp, max_timestamp]

        return dcc.RangeSlider(
            id=id,
            min=min_timestamp,
            max=max_timestamp,
            value=value,
            marks=marks,
            step=None,
            tooltip=None,
            allowCross=False,
        )

    except Exception as e:
        print(f"Error creating date range slider: {str(e)}")
        return html.Div(
            f"Error creating date range slider: {str(e)}",
            style={"color": "#ff6b6b", "padding": "10px"},
        )


def create_trading_pair_dropdown(dropdown_id, id=None, multi=False, value=None):
    options = [
        {"label": "BTC/USDT", "value": "BTCUSDT"},
        {"label": "ETH/USDT", "value": "ETHUSDT"},
    ]

    if value is None:
        value = "BTCUSDT" if not multi else ["BTCUSDT", "ETHUSDT"]

    return dcc.Dropdown(
        id=dropdown_id,
        className="custom-dropdown",
        options=options,
        value=value,
        multi=multi,
        clearable=not multi,  # Don't allow clearing when multi-select
        searchable=False,
    )


def create_atr_period_input(id=None, default_period=14):
    """
    Create a numeric input for ATR period selection.

    Args:
        id (str): The ID for the input component
        default_period (int): Default ATR period (default: 14)

    Returns:
        html.Div: Styled numeric input component
    """
    return html.Div(
        [
            html.Label(
                "Average True Range Period:",
                style={"color": "white", "marginRight": "10px", "fontSize": "14px"},
            ),
            dcc.Input(
                id=id,
                type="number",
                min=5,
                max=50,
                step=1,
                value=default_period,
                style={
                    "width": "60px",
                    "marginRight": "10px",
                    "backgroundColor": "#2d2d2d",
                    "color": "white",
                    "border": "1px solid #00bc8c",
                    "borderRadius": "4px",
                    "padding": "4px 8px",
                },
            ),
        ],
        style={"display": "flex", "alignItems": "center"},
    )
