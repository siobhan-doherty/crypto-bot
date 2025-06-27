#@app.callback(
#    Output('close-price-graph', 'figure'),
#    Input('date-picker', 'start_date'),
#    Input('date-picker', 'end_date')
#)


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


#def update_lineplot(start_date, end_date):
    #df = fetch_historical_data()
    #if df.empty:
    #    return {'data': [], 'layout': {}}
    #    
    ## Convert close_time to datetime if it's not already
    #if not pd.api.types.is_datetime64_any_dtype(df['close_time']):
    #    df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
    #
    #df = df.sort_values('close_time')
    #
    #if start_date and end_date:
    #    df = df[(df['close_time'] >= pd.to_datetime(start_date)) & (df['close_time'] <= pd.to_datetime(end_date))]
    #
    #return {    
    #    'data': [{
    #        'x': df['close_time'],
    #        'y': df['close'],
    #        'type': 'line',
    #        'name': 'Close Price'
    #    }],
    #    'layout': {
    #        'title': 'BITCUSDT Close Price',
    #        'xaxis': {
    #            'title': 'Time',
    #            'type': 'date',
    #            'rangeselector': {
    #                'buttons': [
    #                    {'count': 1, 'label': '1d', 'step': 'day', 'stepmode': 'backward'},
    #                    {'count': 7, 'label': '1w', 'step': 'day', 'stepmode': 'backward'},
    #                    {'step': 'all'}
    #                ]
    #            }
    #        },
    #        'yaxis': {'title': 'Close Price (USDT)'},
    #        'margin': {'l': 60, 'r': 30, 't': 80, 'b': 120},
    #        'height': 600,
    #        'showlegend': False
    #    }
    #}
