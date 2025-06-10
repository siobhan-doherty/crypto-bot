import os
import dash 
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
from pymongo import MongoClient
import pandas as pd
from pymongo.errors import ConnectionFailure

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://crypto_project:dst123@localhost:27017/')

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.server_info()
    db = client["cryptobot"]
    collection = db["historical_data"]
    print("Successfully connected to MongoDB")
except ConnectionFailure as e:
    print(f"Could not connect to MongoDB: {e}")
    raise


# BOOTSTRAP, CERULEAN, DARKLY, FLATLY, LITERA, LUX, MATERIA, MINTY, PULSE, SANDSTONE, SIMPLEX, SKETCHY, SLATE, SOLAR, SPACELAB, UNITED
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.MINTY])


def fetch_data_from_mongo():
    data = list(collection.find())
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
    return df

df = fetch_data_from_mongo()

def create_figure(df):
    if df.empty:
        return {'data': [], 'layout': {}}
        
    df = df.sort_values('close_time')
    
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
                'rangeslider': {'visible': True, 'thickness': 0.1},
                'type': 'date'
            },
            'yaxis': {'title': 'Close Price (USDT)'},
            'margin': {'l': 60, 'r': 30, 't': 80, 'b': 100},
            'height': 600
        }
    }

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
            figure=create_figure(df)
        )
    ])
])

@app.callback(
    Output('close-price-graph', 'figure'),
    Input('date-picker', 'start_date'),
    Input('date-picker', 'end_date')
)
def update_graph(start_date, end_date):
    df = fetch_data_from_mongo()
    if df.empty:
        return {'data': [], 'layout': {}}
        
    # Convert close_time to datetime if it's not already
    if not pd.api.types.is_datetime64_any_dtype(df['close_time']):
        df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
    
    # Sort by time to ensure the line is drawn correctly
    df = df.sort_values('close_time')
    
    # Filter the DataFrame based on the selected date range
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
    app.run(debug=True, host = 'localhost', port = 8080)
