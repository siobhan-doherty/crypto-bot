import dash 
from dash import html, dcc
import dash_bootstrap_components as dbc
import pandas as pd
from fetch_data import fetch_historical_data
from plots.lineplot import create_lineplot
from plots.candlestickplot import create_candlestickplot
from callbacks.callbacks import register_callbacks
from layout.controls import create_date_range_slider, create_date_picker_range



# BOOTSTRAP, CERULEAN, DARKLY, FLATLY, LITERA, LUX, MATERIA, MINTY, PULSE, SANDSTONE, SIMPLEX, SKETCHY, SLATE, SOLAR, SPACELAB, UNITED
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

df = fetch_historical_data()

# Common style for chart containers
chart_container_style = {
    'border': '1px solid #2d2d2d',
    'borderRadius': '8px',
    'padding': '20px',
    'marginBottom': '30px',
    'backgroundColor': '#2d2d2d',
    'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
}

app.layout = html.Div(children=[
    # Header with data info
    html.H1('Crypto Dashboard', style={'textAlign': 'center', 'marginBottom': '20px'}),
    
    # Data info section
    html.Div(style={
        'margin': '20px auto',
        'padding': '15px',
        'maxWidth': '800px',
        'backgroundColor': '#2d2d2d',
        'borderRadius': '8px',
        'textAlign': 'center'
    }, children=[
        html.Div(f'Available Data: {len(df)} records', style={'margin': '5px 0'}),
        html.Div(f'Earliest Data: {df["close_time"].min().strftime("%Y-%m-%d %H:%M:%S")}', 
                style={'margin': '5px 0'}),
        html.Div(f'Latest Data: {df["close_time"].max().strftime("%Y-%m-%d %H:%M:%S")}', 
                style={'margin': '5px 0'})
    ]),
    
    # Main content container
    html.Div(style={
        'maxWidth': '1400px',
        'margin': '0 auto',
        'padding': '0 20px'
    }, children=[
        # Line Plot Section
        html.Div(style=chart_container_style, children=[
            html.H2('Close Price', style={
                'textAlign': 'center',
                'color': '#f8f9fa',
                'marginBottom': '20px'
            }),
            dcc.Graph(
                id='close-price-graph',
                figure=create_lineplot(df),
                style={'marginBottom': '20px'}
            ),
            html.Div(style={'padding': '0 15px'}, children=[
                html.Div('Date Range:', style={
                    'color': '#f8f9fa',
                    'marginBottom': '10px',
                    'fontWeight': 'bold'
                }),
                create_date_range_slider(df, 'lineplot-time-slider')
            ])
        ]),
        
        # Candlestick Chart Section
        html.Div(style=chart_container_style, children=[
            html.H2('Candlestick Chart', style={
                'textAlign': 'center',
                'color': '#f8f9fa',
                'marginBottom': '20px'
            }),
            dcc.Graph(
                id='candlestick-graph',
                figure=create_candlestickplot(df),
                style={'marginBottom': '20px'}
            ),
            html.Div(style={'padding': '0 15px'}, children=[
                html.Div('Date Range:', style={
                    'color': '#f8f9fa',
                    'marginBottom': '10px',
                    'fontWeight': 'bold'
                }),
                create_date_range_slider(df, 'candlestick-time-slider')
            ])
        ])
    ])
])


register_callbacks(app, fetch_historical_data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)
