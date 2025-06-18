import dash 
from dash import html, dcc
import dash_bootstrap_components as dbc
from fetch_data import fetch_historical_data
from plots.lineplot import create_lineplot
from plots.candlestickplot import create_candlestickplot
from plots.volumeplot import create_volumeplot
from plots.volatilityplot import create_volatility_plot
from callbacks.callbacks import register_callbacks
from layout.controls import (
    create_date_range_slider, 
    create_trading_pair_dropdown, 
    create_atr_period_input
)
from layout.theme import COLORS


# BOOTSTRAP, CERULEAN, DARKLY, FLATLY, LITERA, LUX, MATERIA, MINTY, PULSE, SANDSTONE, SIMPLEX, SKETCHY, SLATE, SOLAR, SPACELAB, UNITED
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

df = fetch_historical_data()
# default trading pair
TRADING_PAIR = 'BTCUSDT'


chart_container_style = {
    'border': f'1px solid {COLORS["border"]}',
    'borderRadius': '8px',
    'padding': '20px',
    'marginBottom': '30px',
    'backgroundColor': COLORS['panel'],
    'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
}

app.layout = html.Div(children=[
    html.H1('Crypto Dashboard', style={'textAlign': 'center', 'marginBottom': '20px'}),
    
    # Data info section with trading pair selector
    html.Div(style={
        'display': 'flex',
        'justifyContent': 'space-between',
        'alignItems': 'center',
        'margin': '20px auto',
        'padding': '15px',
        'maxWidth': '1000px',
        'backgroundColor': COLORS['panel'],
        'borderRadius': '8px',
        'color': COLORS['text']
    }, children=[
        html.Div(style={'width': '30%'}, children=[
            html.Div('', style={
                'color': COLORS['text'],
                'marginBottom': '8px',
                'fontWeight': 'bold',
                'textAlign': 'left',
                'paddingLeft': '10px'
            }),
            create_trading_pair_dropdown('trading-pair-dropdown')
        ]),
        html.Div(style={
            'width': '65%',
            'textAlign': 'right',
            'paddingRight': '20px'
        }, children=[
            html.Div(f'Available Data: {len(df)} records', style={'margin': '5px 0'}),
            html.Div(f'Earliest Data: {df["close_time"].min().strftime("%Y-%m-%d %H:%M:%S")}', 
                   style={'margin': '5px 0'}),
            html.Div(f'Latest Data: {df["close_time"].max().strftime("%Y-%m-%d %H:%M:%S")}', 
                   style={'margin': '5px 0'})
        ])
    ]),
    
    # Main content container
    html.Div(style={
        'maxWidth': '1400px',
        'margin': '0 auto',
        'padding': '0 20px'
    }, children=[
        html.Div(style=chart_container_style, children=[
            dcc.Graph(
                id='close-price-graph',
                figure=create_lineplot(df, trading_pair = TRADING_PAIR),
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
            dcc.Graph(
                id='candlestick-graph',
                figure=create_candlestickplot(df,trading_pair = TRADING_PAIR),
                style={'marginBottom': '20px'}
            ),
            html.Div(style={'padding': '0 15px'}, children=[
                html.Div('Date Range:', style={
                    'color': COLORS['text'],
                    'marginBottom': '10px',
                    'fontWeight': 'bold'
                }),
                create_date_range_slider(df, 'candlestick-time-slider')
            ])
        ]),
        
        # Volume Chart Section
        html.Div(style=chart_container_style, children=[
            dcc.Graph(
                id='volume-graph',
                figure=create_volumeplot(df),
                style={'marginBottom': '20px'}
            ),
            html.Div(style={'padding': '0 15px'}, children=[
                html.Div('Date Range:', style={
                    'color': COLORS['text'],
                    'marginBottom': '10px',
                    'fontWeight': 'bold'
                }),
                create_date_range_slider(df, 'volume-time-slider')
            ])
        ]),
        
        # Volatility Chart Section
        html.Div(style=chart_container_style, children=[
            html.Div(style={
                'display': 'flex',
                'justifyContent': 'flex-end',
                'marginBottom': '10px',
                'alignItems': 'center'
            }, children=[
                create_atr_period_input('atr-period-input')
            ]),
            dcc.Graph(
                id='volatility-graph',
                figure=create_volatility_plot(df),
                style={'marginBottom': '20px'}
            ),
            html.Div(style={'padding': '0 15px'}, children=[
                html.Div('Date Range:', style={
                    'color': COLORS['text'],
                    'marginBottom': '10px',
                    'fontWeight': 'bold'
                }),
                create_date_range_slider(df, 'volatility-time-slider')
            ])
        ])
    ])
])


register_callbacks(app, fetch_historical_data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)
