import dash 
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import pandas as pd
from fetch_data import fetch_historical_data
from plots.lineplot import create_lineplot
from plots.candlestickplot import create_candlestickplot



# BOOTSTRAP, CERULEAN, DARKLY, FLATLY, LITERA, LUX, MATERIA, MINTY, PULSE, SANDSTONE, SIMPLEX, SKETCHY, SLATE, SOLAR, SPACELAB, UNITED
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

df = fetch_historical_data()

app.layout = html.Div([
    html.H1('Crypto Dashboard', style={'textAlign': 'center'}),
    html.Div(style={'margin': '20px', 'padding': '20px'}, children=[
        html.Span('Available Data:     ' + str(len(df)) + ' records'),
        html.Br(),
        html.Span('Earliest Data:   ' + str(df['close_time'].min().strftime('%Y-%m-%d %H:%M:%S'))),
        html.Br(),
        html.Span('Latest Data:     ' + str(df['close_time'].max().strftime('%Y-%m-%d %H:%M:%S')))]),
    html.Div(style={ 'padding': '50px'}, children=[
        html.H2('Close Price of BITCUSDT', style={'textAlign': 'center'}),
        html.Br(),
        dcc.DatePickerRange(
            id='date-picker',
            display_format='YYYY-MM-DD',    
            min_date_allowed=df['close_time'].min(),
            max_date_allowed=df['close_time'].max(),
            start_date=df['close_time'].min(),
            end_date=df['close_time'].max()
        ),
        
        dcc.Graph(
            id='close-price-graph',
            figure=create_lineplot(df)
        ),
        dcc.Graph(
            id='candlestick-graph',
            figure=create_candlestickplot(df)
        )
    ])
])

@app.callback(
    Output('close-price-graph', 'figure'),
    Input('date-picker', 'start_date'),
    Input('date-picker', 'end_date')
)


def update_lineplot(start_date, end_date):
    df = fetch_historical_data()
    if df.empty:
        return {'data': [], 'layout': {}}
        
    # Convert close_time to datetime if it's not already
    if not pd.api.types.is_datetime64_any_dtype(df['close_time']):
        df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
    
    df = df.sort_values('close_time')
    
    if start_date and end_date:
        df = df[(df['close_time'] >= pd.to_datetime(start_date)) & (df['close_time'] <= pd.to_datetime(end_date))]
    
    return {    
        'data': [{
            'x': df['close_time'],
            'y': df['close'],
            'type': 'line',
            'name': 'Close Price'
        }],
        'layout': {
            'title': 'BITCUSDT Close Price',
            'xaxis': {
                'title': 'Time',
                'type': 'date',
                'rangeselector': {
                    'buttons': [
                        {'count': 1, 'label': '1d', 'step': 'day', 'stepmode': 'backward'},
                        {'count': 7, 'label': '1w', 'step': 'day', 'stepmode': 'backward'},
                        {'step': 'all'}
                    ]
                }
            },
            'yaxis': {'title': 'Close Price (USDT)'},
            'margin': {'l': 60, 'r': 30, 't': 80, 'b': 120},
            'height': 600,
            'showlegend': False
        }
    }

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)
