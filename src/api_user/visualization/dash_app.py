import dash 
from dash import html, dcc
import dash_bootstrap_components as dbc
import pandas as pd
from fetch_data import fetch_historical_data
from plots.lineplot import create_lineplot
from plots.candlestickplot import create_candlestickplot
from callbacks.callbacks import register_callbacks
from layout.controls import create_date_range_slider



# BOOTSTRAP, CERULEAN, DARKLY, FLATLY, LITERA, LUX, MATERIA, MINTY, PULSE, SANDSTONE, SIMPLEX, SKETCHY, SLATE, SOLAR, SPACELAB, UNITED
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

df = fetch_historical_data()

app.layout = html.Div(children=[
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
        create_date_range_slider(df, 'lineplot-time-slider')]),
        html.Div(style={ 'padding': '50px'}, children=[
           
            html.H2('Candlestick of BITCUSDT', style={'textAlign': 'center'}),
            html.Br(),
            dcc.Graph(
                id='candlestick-graph',
                figure=create_candlestickplot(df)
            ),
             create_date_range_slider(df, 'candlestick-time-slider')
        ])
])


register_callbacks(app, fetch_historical_data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)
